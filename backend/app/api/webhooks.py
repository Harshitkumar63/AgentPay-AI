"""Webhook API — Razorpay webhook handling with persistent logging, signature verification, and idempotency."""

import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.payment_service import razorpay_service
from app.services import audit_service
from app.models.order import Order
from app.models.payment import Payment
from app.models.webhook import WebhookEvent

logger = logging.getLogger("agentpay.webhooks")

router = APIRouter()

# In-memory fast cache for duplicate detection
_processed_events: set = set()


@router.get("/webhooks", summary="List Webhook Events for Monitor")
def list_webhook_events(
    limit: int = Query(default=50, le=200),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve recorded webhook events for the Webhook Monitor UI (Phase 21)."""
    q = db.query(WebhookEvent)
    if status:
        q = q.filter(WebhookEvent.status == status)
    events = q.order_by(WebhookEvent.created_at.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "event_id": e.event_id,
            "event_type": e.event_type,
            "order_id": e.order_id,
            "payment_id": e.payment_id,
            "status": e.status,
            "error_message": e.error_message,
            "retry_count": e.retry_count,
            "payload_summary": {
                "event": e.event_type,
                "amount": e.payload.get("payload", {}).get("payment", {}).get("entity", {}).get("amount", 0) / 100,
            } if e.payload else {},
            "created_at": str(e.created_at),
        }
        for e in events
    ]


@router.post("/webhooks/simulate", summary="Simulate Webhook Event (Demo/Test)")
def simulate_webhook_event(
    event_type: str = "payment.captured",
    razorpay_order_id: Optional[str] = None,
    razorpay_payment_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Allows simulated webhook execution for testing webhook handling and idempotency."""
    import uuid
    evt_id = f"evt_sim_{uuid.uuid4().hex[:8]}"
    rz_ord = razorpay_order_id or f"order_demo_{uuid.uuid4().hex[:8]}"
    rz_pay = razorpay_payment_id or f"pay_demo_{uuid.uuid4().hex[:8]}"

    payload = {
        "entity": "event",
        "account_id": "acc_demo_merchant",
        "event": event_type,
        "contains": ["payment", "order"],
        "payload": {
            "payment": {
                "entity": {
                    "id": rz_pay,
                    "entity": "payment",
                    "amount": 249900,
                    "currency": "INR",
                    "status": "captured" if "captured" in event_type else ("failed" if "failed" in event_type else "authorized"),
                    "order_id": rz_ord,
                    "method": "card",
                    "error_code": "BAD_REQUEST_ERROR" if "failed" in event_type else None,
                    "error_description": "Payment was declined by bank" if "failed" in event_type else None,
                }
            },
            "order": {
                "entity": {
                    "id": rz_ord,
                    "entity": "order",
                    "amount": 249900,
                    "status": "paid" if "captured" in event_type else "attempted",
                }
            },
        },
        "created_at": 1700000000,
    }

    # Process payload directly
    return _process_webhook_payload(db, payload, event_id=evt_id, event=event_type)


@router.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Razorpay webhook events.
    - Verifies raw signature
    - Processes events idempotently
    - Updates payment/order status
    - Records persistent WebhookEvent log
    - Creates immutable audit logs
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

    return _process_webhook_payload(db, payload, event_id=event_id, event=event)


def _process_webhook_payload(db: Session, payload: dict, event_id: str, event: str) -> dict:
    """Internal idempotent webhook processor."""
    # Check duplicate in memory or DB
    is_duplicate = False
    if event_id:
        if event_id in _processed_events:
            is_duplicate = True
        else:
            existing_evt = db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first()
            if existing_evt:
                is_duplicate = True

    if is_duplicate:
        logger.info(f"Webhook event already processed (idempotency guard): {event_id}")
        # Log duplicate attempt
        db_dup = WebhookEvent(
            event_id=event_id,
            event_type=event,
            status="ignored_duplicate",
            payload=payload,
            retry_count=1,
        )
        db.add(db_dup)
        db.commit()
        return {"status": "already_processed", "event_id": event_id, "message": "Duplicate event safely ignored"}

    logger.info(f"Processing webhook event: {event} (ID: {event_id})")

    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    rz_order_id = payment_entity.get("order_id") or payload.get("payload", {}).get("order", {}).get("entity", {}).get("id")
    rz_payment_id = payment_entity.get("id")

    status = "processed"
    err_msg = None

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
            logger.info(f"Unhandled webhook event type: {event}")

        if event_id:
            _processed_events.add(event_id)
            if len(_processed_events) > 10000:
                _processed_events.clear()

    except Exception as e:
        status = "failed"
        err_msg = str(e)
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

    # Persist webhook event record
    webhook_log = WebhookEvent(
        event_id=event_id or f"evt_{id(payload)}",
        event_type=event,
        order_id=rz_order_id,
        payment_id=rz_payment_id,
        status=status,
        payload=payload,
        error_message=err_msg,
    )
    db.add(webhook_log)
    db.commit()

    return {"status": status, "event_id": event_id, "event": event}


def _handle_payment_authorized(db: Session, payload: dict):
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    rz_order_id = payment_entity.get("order_id")
    rz_payment_id = payment_entity.get("id")

    order = db.query(Order).filter(Order.razorpay_order_id == rz_order_id).first()
    if not order:
        return

    order.payment_status = "authorized"
    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if payment:
        payment.razorpay_payment_id = rz_payment_id
        payment.status = "authorized"
        payment.method = payment_entity.get("method", "card")

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
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    rz_order_id = payment_entity.get("order_id")
    rz_payment_id = payment_entity.get("id")

    order = db.query(Order).filter(Order.razorpay_order_id == rz_order_id).first()
    if not order:
        return

    order.payment_status = "captured"
    order.status = "confirmed"

    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if payment:
        payment.razorpay_payment_id = rz_payment_id
        payment.status = "captured"
        payment.method = payment_entity.get("method", "card")

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
        metadata_extra={"razorpay_payment_id": rz_payment_id, "razorpay_order_id": rz_order_id},
    )


def _handle_payment_failed(db: Session, payload: dict):
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    rz_order_id = payment_entity.get("order_id")
    rz_payment_id = payment_entity.get("id")
    error_code = payment_entity.get("error_code", "PAYMENT_FAILED")
    error_desc = payment_entity.get("error_description", "Payment transaction failed")

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
