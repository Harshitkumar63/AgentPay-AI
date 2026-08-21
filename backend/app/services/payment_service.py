"""Payment service — Razorpay integration abstraction with demo mode fallback."""

import uuid
import hmac
import hashlib
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.payment import Payment
from app.models.order import Order
from app.services import audit_service

logger = logging.getLogger("agentpay.payments")


class RazorpayService:
    """
    Abstraction over Razorpay APIs.
    Uses real Razorpay Test Mode when configured, otherwise demo mode.
    """

    def __init__(self):
        self._client = None
        if settings.razorpay_configured and not settings.demo_mode:
            try:
                import razorpay
                self._client = razorpay.Client(
                    auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
                )
                logger.info("Razorpay client initialized (TEST MODE)")
            except Exception as e:
                logger.warning(f"Failed to initialize Razorpay client: {e}")

    @property
    def is_live(self) -> bool:
        return self._client is not None

    def create_razorpay_order(self, amount: float, currency: str = "INR", receipt: str = None, notes: dict = None) -> dict:
        """Create a Razorpay order. Amount in rupees — converted to paise for API."""
        amount_paise = int(amount * 100)

        if self.is_live:
            try:
                order_data = {
                    "amount": amount_paise,
                    "currency": currency,
                    "receipt": receipt or f"receipt_{uuid.uuid4().hex[:12]}",
                    "notes": notes or {},
                }
                rz_order = self._client.order.create(data=order_data)
                return {
                    "id": rz_order["id"],
                    "amount": rz_order["amount"],
                    "currency": rz_order["currency"],
                    "receipt": rz_order.get("receipt"),
                    "status": rz_order["status"],
                    "demo": False,
                }
            except Exception as e:
                logger.error(f"Razorpay order creation failed: {e}")
                raise

        # Demo mode
        demo_id = f"order_demo_{uuid.uuid4().hex[:12]}"
        return {
            "id": demo_id,
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
            "status": "created",
            "demo": True,
        }

    def fetch_razorpay_order(self, razorpay_order_id: str) -> dict:
        """Fetch order details from Razorpay."""
        if self.is_live:
            return self._client.order.fetch(razorpay_order_id)

        return {
            "id": razorpay_order_id,
            "status": "created",
            "demo": True,
        }

    def fetch_payment(self, razorpay_payment_id: str) -> dict:
        """Fetch payment details from Razorpay."""
        if self.is_live:
            return self._client.payment.fetch(razorpay_payment_id)

        return {
            "id": razorpay_payment_id,
            "status": "captured",
            "amount": 0,
            "method": "demo",
            "demo": True,
        }

    def verify_payment_signature(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        """Verify Razorpay payment signature."""
        if self.is_live:
            try:
                self._client.utility.verify_payment_signature({
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_signature": razorpay_signature,
                })
                return True
            except Exception:
                return False

        # Demo mode — accept any signature
        return True

    def verify_webhook_signature(self, body: str, signature: str) -> bool:
        """Verify Razorpay webhook signature."""
        if not settings.razorpay_webhook_secret:
            # Demo mode — accept
            return True

        expected = hmac.new(
            settings.razorpay_webhook_secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()


        return hmac.compare_digest(expected, signature)


# Singleton
razorpay_service = RazorpayService()


def create_payment_for_order(db: Session, order_id: str) -> dict:
    """Create Razorpay order and payment record."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": True, "code": "ORDER_NOT_FOUND", "message": "Order not found"}

    # Create Razorpay order
    try:
        rz_order = razorpay_service.create_razorpay_order(
            amount=order.amount,
            currency=order.currency,
            receipt=order.receipt,
            notes={"order_id": order.id, "merchant_id": order.merchant_id},
        )
    except Exception as e:
        audit_service.create_audit_log(
            db,
            actor_type="system",
            actor_id="payment_service",
            action="PAYMENT_CREATION_FAILED",
            resource_type="order",
            resource_id=order.id,
            amount=order.amount,
            reason=str(e),
            result="FAILURE",
        )
        return {"error": True, "code": "RAZORPAY_ERROR", "message": str(e)}

    # Update order with Razorpay order ID
    order.razorpay_order_id = rz_order["id"]
    order.status = "confirmed"

    # Create payment record
    payment = Payment(
        order_id=order.id,
        amount=order.amount,
        currency=order.currency,
        status="created",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Audit
    audit_service.create_audit_log(
        db,
        actor_type="system",
        actor_id="payment_service",
        action="PAYMENT_CREATED",
        resource_type="payment",
        resource_id=payment.id,
        amount=order.amount,
        currency=order.currency,
        result="SUCCESS",
        metadata_extra={"razorpay_order_id": rz_order["id"], "demo": rz_order.get("demo", False)},
    )

    return {
        "payment_id": payment.id,
        "order_id": order.id,
        "razorpay_order_id": rz_order["id"],
        "razorpay_key_id": settings.razorpay_key_id or "demo_key",
        "amount": int(order.amount * 100),  # paise
        "currency": order.currency,
        "receipt": order.receipt,
        "demo": rz_order.get("demo", False),
    }


def verify_and_update_payment(
    db: Session,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> dict:
    """Verify payment signature and update records."""
    # Find order
    order = db.query(Order).filter(Order.razorpay_order_id == razorpay_order_id).first()
    if not order:
        return {"error": True, "code": "ORDER_NOT_FOUND", "message": "Order not found"}

    # Verify signature
    is_valid = razorpay_service.verify_payment_signature(
        razorpay_order_id, razorpay_payment_id, razorpay_signature
    )

    if not is_valid:
        audit_service.create_audit_log(
            db,
            actor_type="system",
            actor_id="payment_service",
            action="PAYMENT_VERIFICATION_FAILED",
            resource_type="order",
            resource_id=order.id,
            amount=order.amount,
            result="FAILURE",
            reason="Invalid payment signature",
        )
        return {"error": True, "code": "INVALID_SIGNATURE", "message": "Payment signature verification failed"}

    # Update payment
    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if payment:
        payment.razorpay_payment_id = razorpay_payment_id
        payment.status = "captured"
        payment.method = "razorpay"

    # Update order
    order.payment_status = "captured"
    order.status = "confirmed"

    db.commit()

    audit_service.create_audit_log(
        db,
        actor_type="system",
        actor_id="payment_service",
        action="PAYMENT_CAPTURED",
        resource_type="payment",
        resource_id=payment.id if payment else None,
        amount=order.amount,
        currency=order.currency,
        result="SUCCESS",
        metadata_extra={
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_order_id": razorpay_order_id,
        },
    )

    return {
        "success": True,
        "order_id": order.id,
        "payment_status": "captured",
    }


def get_payment_status(db: Session, order_id: str) -> dict:
    """Get payment status for an order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": True, "message": "Order not found"}

    payment = db.query(Payment).filter(Payment.order_id == order_id).first()

    return {
        "order_id": order.id,
        "order_status": order.status,
        "payment_status": order.payment_status,
        "razorpay_order_id": order.razorpay_order_id,
        "razorpay_payment_id": payment.razorpay_payment_id if payment else None,
        "amount": order.amount,
        "currency": order.currency,
    }
