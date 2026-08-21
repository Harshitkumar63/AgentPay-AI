"""Webhook API — Razorpay webhook handling with signature verification and idempotency."""

import json
import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.payment_service import razorpay_service
from app.services import audit_service
from app.models.order import Order
from app.models.payment import Payment

logger = logging.getLogger("agentpay.webhooks")

router = APIRouter()

# Track processed webhook events for idempotency
_processed_events: set = set()


@router.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Razorpay webhook events.
    - Verifies signature
    - Processes events idempotently
    - Updates payment/order status
    - Creates audit logs
    """
    body = await request.body()
    body_str = body.decode("utf-8")
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Verify signature
    if not razorpay_service.verify_webhook_signature(body_str, signature):
        logger.warning("Webhook signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payload = json.loads(body_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = payload.get("event", "")
    event_id = payload.get("id", "")

    # Idempotency: skip already processed events
    if event_id and event_id in _processed_events:
        logger.info(f"Webhook event already processed: {event_id}")
        return {"status": "already_processed"}

    logger.info(f"Processing webhook event: {event} (ID: {event_id})")

    try:
        if event == "payment.authorized":
            _handle_payment_authorized(db, payload)
        elif event == "payment.captured":
            _handle_payment_captured(db, payload)
        elif event == "payment.failed":
            _handle_payment_failed(db, payload)
        elif event == "order.paid":
            _handle_order_paid(db, payload)
        else:
            logger.info(f"Unhandled webhook event: {event}")

        # Mark as processed
        if event_id:
            _processed_events.add(event_id)
            # Keep set bounded
            if len(_processed_events) > 10000:
                _processed_events.clear()

    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        audit_service.create_audit_log(
            db,
            actor_type="webhook",
            actor_id="razorpay",
            action="WEBHOOK_ERROR",
            reason=str(e),
            result="FAILURE",
            metadata_extra={"event": event, "event_id": event_id},
        )
        # Return 200 to prevent Razorpay retries on processing errors
        return {"status": "error_logged"}

    return {"status": "processed"}


def _handle_payment_authorized(db: Session, payload: dict):
    """Handle payment.authorized event."""
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    rz_order_id = payment_entity.get("order_id")
    rz_payment_id = payment_entity.get("id")

    order = db.query(Order).filter(Order.razorpay_order_id == rz_order_id).first()
    if not order:
        logger.warning(f"Order not found for Razorpay order: {rz_order_id}")
        return

    order.payment_status = "authorized"

    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if payment:
        payment.razorpay_payment_id = rz_payment_id
        payment.status = "authorized"
        payment.method = payment_entity.get("method")

    db.commit()

    audit_service.create_audit_log(
        db,
        actor_type="webhook",
        actor_id="razorpay",
        action="PAYMENT_AUTHORIZED",
        resource_type="payment",
        resource_id=payment.id if payment else None,
        amount=order.amount,
        currency=order.currency,
        result="SUCCESS",
        metadata_extra={"razorpay_payment_id": rz_payment_id},
    )


def _handle_payment_captured(db: Session, payload: dict):
    """Handle payment.captured event."""
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    rz_order_id = payment_entity.get("order_id")
    rz_payment_id = payment_entity.get("id")

    order = db.query(Order).filter(Order.razorpay_order_id == rz_order_id).first()
    if not order:
        logger.warning(f"Order not found for Razorpay order: {rz_order_id}")
        return

    order.payment_status = "captured"
    order.status = "confirmed"

    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if payment:
        payment.razorpay_payment_id = rz_payment_id
        payment.status = "captured"
        payment.method = payment_entity.get("method")

    db.commit()

    audit_service.create_audit_log(
        db,
        actor_type="webhook",
        actor_id="razorpay",
        action="PAYMENT_CAPTURED",
        resource_type="payment",
        resource_id=payment.id if payment else None,
        amount=order.amount,
        currency=order.currency,
        result="SUCCESS",
        metadata_extra={"razorpay_payment_id": rz_payment_id},
    )


def _handle_payment_failed(db: Session, payload: dict):
    """Handle payment.failed event."""
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    rz_order_id = payment_entity.get("order_id")
    rz_payment_id = payment_entity.get("id")
    error_code = payment_entity.get("error_code", "")
    error_desc = payment_entity.get("error_description", "")

    order = db.query(Order).filter(Order.razorpay_order_id == rz_order_id).first()
    if not order:
        return

    order.payment_status = "failed"

    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if payment:
        payment.razorpay_payment_id = rz_payment_id
        payment.status = "failed"
        payment.error_code = error_code
        payment.error_description = error_desc

    db.commit()

    audit_service.create_audit_log(
        db,
        actor_type="webhook",
        actor_id="razorpay",
        action="PAYMENT_FAILED",
        resource_type="payment",
        resource_id=payment.id if payment else None,
        amount=order.amount,
        currency=order.currency,
        result="FAILURE",
        reason=f"{error_code}: {error_desc}",
        metadata_extra={"razorpay_payment_id": rz_payment_id},
    )


def _handle_order_paid(db: Session, payload: dict):
    """Handle order.paid event."""
    order_entity = payload.get("payload", {}).get("order", {}).get("entity", {})
    rz_order_id = order_entity.get("id")

    order = db.query(Order).filter(Order.razorpay_order_id == rz_order_id).first()
    if not order:
        return

    order.payment_status = "captured"
    order.status = "confirmed"
    db.commit()

    audit_service.create_audit_log(
        db,
        actor_type="webhook",
        actor_id="razorpay",
        action="ORDER_PAID",
        resource_type="order",
        resource_id=order.id,
        amount=order.amount,
        currency=order.currency,
        result="SUCCESS",
    )
