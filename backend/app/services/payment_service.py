"""Payment service — Razorpay Test Mode integration, signature verification, and failure recovery."""

import uuid
import hmac
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.config import settings
from app.models.payment import Payment
from app.models.order import Order
from app.services import (
    audit_service,
    budget_service,
    trust_service,
    approval_service,
)

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

        # Demo mode fallback
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

        # Demo mode — accept signature
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
    """Create Razorpay order and payment record after approval validation."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": True, "code": "ORDER_NOT_FOUND", "message": "Order not found"}

    # Check if order requires approval and verify approval status
    if order.approval_id:
        appr_check = approval_service.validate_approval(db, order.approval_id, expected_amount=order.amount)
        if not appr_check["valid"]:
            return {
                "error": True,
                "code": appr_check["code"],
                "message": f"Payment initialization blocked: {appr_check['reason']}",
            }

    # Re-use existing payment record on retry if exists
    existing_payment = db.query(Payment).filter(Payment.order_id == order.id, Payment.status != "failed").first()
    if existing_payment and order.razorpay_order_id:
        return {
            "payment_id": existing_payment.id,
            "order_id": order.id,
            "razorpay_order_id": order.razorpay_order_id,
            "razorpay_key_id": settings.razorpay_key_id or "demo_key",
            "amount": int(order.amount * 100),
            "currency": order.currency,
            "receipt": order.receipt,
            "demo": not settings.razorpay_configured,
        }

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

    # Update order
    order.razorpay_order_id = rz_order["id"]
    order.status = "PAYMENT_PENDING"
    now_str = str(datetime.now(timezone.utc))
    order.timeline = (order.timeline or []) + [
        {"step": "RAZORPAY_ORDER_CREATED", "status": "COMPLETED", "timestamp": now_str, "actor": "payment_service", "razorpay_order_id": rz_order["id"]},
    ]

    # Create or update payment record
    payment = Payment(
        order_id=order.id,
        amount=order.amount,
        currency=order.currency,
        status="created",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Audit log
    audit_service.create_audit_log(
        db,
        actor_type="system",
        actor_id="payment_service",
        action="PAYMENT_INITIALIZED",
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
    """Verify payment signature and update state machine."""
    order = db.query(Order).filter(Order.razorpay_order_id == razorpay_order_id).first()
    if not order:
        return {"error": True, "code": "ORDER_NOT_FOUND", "message": "Order not found"}

    is_valid = razorpay_service.verify_payment_signature(
        razorpay_order_id, razorpay_payment_id, razorpay_signature
    )

    if not is_valid:
        trust_service.record_trust_event(db, "payment_failed", agent_id=order.agent_id or "default_agent")
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

    # Update payment record
    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if payment:
        payment.razorpay_payment_id = razorpay_payment_id
        payment.status = "captured"
        payment.method = "razorpay"

    # Update order state machine
    order.payment_status = "captured"
    order.status = "COMPLETED"
    now_str = str(datetime.now(timezone.utc))
    order.timeline = (order.timeline or []) + [
        {"step": "PAYMENT_SIGNATURE_VERIFIED", "status": "COMPLETED", "timestamp": now_str, "actor": "payment_service"},
        {"step": "PAYMENT_CAPTURED", "status": "COMPLETED", "timestamp": now_str, "actor": "payment_service", "razorpay_payment_id": razorpay_payment_id},
        {"step": "ORDER_COMPLETED", "status": "SUCCESS", "timestamp": now_str, "actor": "system"},
    ]

    # Deduct agent budget
    if order.agent_id:
        budget_service.record_spending(db, order.amount, agent_id=order.agent_id, merchant_id=order.merchant_id)

    # Record trust success
    trust_service.record_trust_event(db, "success", agent_id=order.agent_id or "default_agent")

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
        "order_status": "COMPLETED",
    }


def record_payment_failure(
    db: Session,
    razorpay_order_id: str,
    razorpay_payment_id: Optional[str] = None,
    error_code: str = "PAYMENT_FAILED",
    error_description: str = "Payment transaction was declined or failed",
) -> dict:
    """Safely record payment failure and enable retry without duplicate orders."""
    order = db.query(Order).filter(Order.razorpay_order_id == razorpay_order_id).first()
    if not order:
        return {"error": True, "message": "Order not found"}

    order.payment_status = "failed"
    order.status = "PAYMENT_FAILED"
    now_str = str(datetime.now(timezone.utc))
    order.timeline = (order.timeline or []) + [
        {"step": "PAYMENT_FAILED", "status": "FAILED", "timestamp": now_str, "actor": "payment_gateway", "error_code": error_code, "reason": error_description},
    ]

    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if payment:
        payment.status = "failed"
        payment.error_code = error_code
        payment.error_description = error_description
        if razorpay_payment_id:
            payment.razorpay_payment_id = razorpay_payment_id

    # Update trust signals
    trust_service.record_trust_event(db, "payment_failed", agent_id=order.agent_id or "default_agent")

    db.commit()

    audit_service.create_audit_log(
        db,
        actor_type="system",
        actor_id="payment_service",
        action="PAYMENT_FAILED",
        resource_type="order",
        resource_id=order.id,
        amount=order.amount,
        currency=order.currency,
        reason=f"{error_code}: {error_description}",
        result="FAILURE",
    )

    return {
        "success": False,
        "order_id": order.id,
        "payment_status": "failed",
        "can_retry": True,
        "message": "Payment failed. You can safely retry payment without creating a duplicate order.",
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
        "timeline": order.timeline or [],
    }
