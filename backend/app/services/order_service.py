"""Order service — Order state machine, idempotency, server-side price validation, and approval gating."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.order import Order
from app.models.cart import Cart
from app.services import (
    cart_service,
    policy_service,
    audit_service,
    approval_service,
    trust_service,
)
from app.services.product_service import check_inventory


VALID_TRANSITIONS = {
    "CART": ["CHECKOUT_PENDING"],
    "CHECKOUT_PENDING": ["POLICY_CHECKED", "CANCELLED"],
    "POLICY_CHECKED": ["APPROVAL_PENDING", "APPROVED", "CANCELLED"],
    "APPROVAL_PENDING": ["APPROVED", "CANCELLED", "EXPIRED"],
    "APPROVED": ["ORDER_CREATED", "CANCELLED"],
    "ORDER_CREATED": ["PAYMENT_PENDING", "CANCELLED"],
    "PAYMENT_PENDING": ["PAYMENT_AUTHORIZED", "PAYMENT_CAPTURED", "PAYMENT_FAILED", "CANCELLED"],
    "PAYMENT_AUTHORIZED": ["PAYMENT_CAPTURED", "PAYMENT_FAILED", "CANCELLED"],
    "PAYMENT_CAPTURED": ["COMPLETED"],
    "COMPLETED": [],
    "PAYMENT_FAILED": ["PAYMENT_PENDING", "CANCELLED"],
    "CANCELLED": [],
    "EXPIRED": [],
}


def create_order(
    db: Session,
    cart_id: str,
    user_id: str,
    merchant_id: str,
    idempotency_key: Optional[str] = None,
    order_type: str = "normal",
    actor_id: str = "system",
    actor_type: str = "user",
    agent_session_id: Optional[str] = None,
) -> dict:
    """
    Create an order from a cart with full validation pipeline:
    1. Check Idempotency Key
    2. Validate Cart & Server-Side Pricing
    3. Re-Verify Stock
    4. Run Policy & Risk Engine
    5. Check Agent Budget & Trust
    6. Generate Expiring Approval if Required
    7. Form State Machine Order Record
    """
    # 1. Idempotency check
    if idempotency_key:
        existing = db.query(Order).filter(Order.idempotency_key == idempotency_key).first()
        if existing:
            trust_service.record_trust_event(db, "duplicate_request", agent_id=actor_id)
            audit_service.create_audit_log(
                db,
                actor_type=actor_type,
                actor_id=actor_id,
                action="IDEMPOTENT_ORDER_RETRIEVED",
                resource_type="order",
                resource_id=existing.id,
                amount=existing.amount,
                result="SUCCESS",
                metadata_extra={"idempotency_key": idempotency_key},
            )
            return {
                "order": _order_to_dict(existing),
                "status": "existing",
                "message": "Order already exists for this idempotency key (Idempotent response)",
            }

    # 2. Validate cart
    cart = cart_service.get_cart(db, cart_id)
    if not cart:
        return {"error": True, "code": "CART_NOT_FOUND", "message": "Cart not found"}
    if not cart.items:
        return {"error": True, "code": "CART_EMPTY", "message": "Cart is empty"}
    if cart.status not in ("active", "checked_out"):
        return {"error": True, "code": "CART_NOT_ACTIVE", "message": "Cart is not active"}

    # 3. Check live inventory for all items
    for item in cart.items:
        inv = check_inventory(db, item.product_id, item.quantity)
        if not inv["available"]:
            return {
                "error": True,
                "code": "INSUFFICIENT_STOCK",
                "message": f"Insufficient stock for product {item.product_id}: {inv['reason']}",
            }

    # 4. Server-side price calculation
    calc = cart_service.calculate_cart(db, cart_id)
    amount = calc["total"]

    # 5. Policy & Risk Engine check
    policy_result = policy_service.check_purchase_policy(
        db,
        merchant_id=merchant_id,
        amount=amount,
        action="create_order",
        agent_id=actor_id,
    )

    if not policy_result["allowed"]:
        audit_service.create_audit_log(
            db,
            actor_type=actor_type,
            actor_id=actor_id,
            action="ORDER_POLICY_BLOCKED",
            resource_type="cart",
            resource_id=cart_id,
            amount=amount,
            currency="INR",
            reason=policy_result["reason"],
            policy_result="BLOCKED",
            result="FAILURE",
        )
        return {
            "error": True,
            "code": "POLICY_BLOCKED",
            "message": policy_result["reason"],
            "policy": policy_result,
        }

    # 6. Create human approval record if required
    approval = None
    if policy_result.get("requires_approval"):
        approval = approval_service.create_approval_request(
            db=db,
            amount=amount,
            action="create_order",
            agent_session_id=agent_session_id,
            merchant_id=merchant_id,
            user_id=user_id,
            risk_level=policy_result.get("risk_level", "HIGH"),
            risk_score=policy_result.get("risk_score", 80),
            policy_result=policy_result,
            reason=f"Order checkout of ₹{amount:,.2f} gated for human verification",
        )

    # 7. Create order record
    now_str = str(datetime.now(timezone.utc))
    receipt = f"receipt_{uuid.uuid4().hex[:12]}"
    initial_status = "APPROVAL_PENDING" if approval else "ORDER_CREATED"

    timeline_events = [
        {"step": "CART_CREATED", "status": "COMPLETED", "timestamp": str(cart.created_at), "actor": "user"},
        {"step": "STOCK_VERIFIED", "status": "COMPLETED", "timestamp": now_str, "actor": "inventory_service"},
        {"step": "SERVER_PRICE_CALCULATED", "status": "COMPLETED", "timestamp": now_str, "actor": "cart_service"},
        {"step": "POLICY_CHECKED", "status": "ALLOWED", "timestamp": now_str, "actor": "policy_engine"},
        {"step": "RISK_EVALUATED", "status": policy_result.get("risk_level", "LOW"), "timestamp": now_str, "actor": "risk_engine"},
    ]

    if approval:
        timeline_events.append({
            "step": "APPROVAL_REQUESTED",
            "status": "PENDING",
            "timestamp": now_str,
            "actor": "approval_service",
            "approval_id": approval.id,
            "expires_at": str(approval.expires_at),
        })
    else:
        timeline_events.append({
            "step": "ORDER_INITIALIZED",
            "status": "CREATED",
            "timestamp": now_str,
            "actor": "order_service",
        })

    decision_factors = policy_service.explain_decision("create_order", {
        "amount": amount,
        "policy": policy_result,
    })

    order = Order(
        merchant_id=merchant_id,
        user_id=user_id,
        cart_id=cart_id,
        agent_id=actor_id if actor_type == "ai_agent" else None,
        agent_session_id=agent_session_id,
        approval_id=approval.id if approval else None,
        amount=amount,
        currency="INR",
        status=initial_status,
        payment_status="pending",
        receipt=receipt,
        idempotency_key=idempotency_key or f"idem_{uuid.uuid4().hex[:12]}",
        order_type=order_type,
        timeline=timeline_events,
        decision_factors=decision_factors,
    )
    db.add(order)

    # Link approval to order
    if approval:
        approval.order_id = order.id

    # Mark cart as checked out
    cart.status = "checked_out"

    db.commit()
    db.refresh(order)

    # Audit log
    audit_service.create_audit_log(
        db,
        actor_type=actor_type,
        actor_id=actor_id,
        action="ORDER_CREATED",
        resource_type="order",
        resource_id=order.id,
        amount=amount,
        currency="INR",
        reason=f"Order creation from cart {cart_id}",
        policy_result="ALLOWED",
        approval_status="PENDING" if approval else "AUTO_APPROVED",
        result="SUCCESS",
        metadata_extra={"approval_id": approval.id if approval else None},
    )

    return {
        "order": _order_to_dict(order),
        "status": "created",
        "requires_approval": bool(approval),
        "approval": {
            "id": approval.id,
            "status": approval.status,
            "expires_at": str(approval.expires_at),
        } if approval else None,
        "policy": policy_result,
        "message": "Order initiated successfully" if not approval else "Order created and awaiting human approval authorization",
    }


def get_order(db: Session, order_id: str) -> Optional[Order]:
    """Get order by ID."""
    return db.query(Order).filter(Order.id == order_id).first()


def get_orders(
    db: Session,
    merchant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Order]:
    """Get orders with optional filters."""
    q = db.query(Order)
    if merchant_id:
        q = q.filter(Order.merchant_id == merchant_id)
    if user_id:
        q = q.filter(Order.user_id == user_id)
    return q.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def update_order_timeline(db: Session, order: Order, step_name: str, status: str, actor: str, extra: dict = None):
    """Add event to order timeline."""
    event = {
        "step": step_name,
        "status": status,
        "timestamp": str(datetime.now(timezone.utc)),
        "actor": actor,
    }
    if extra:
        event.update(extra)
    order.timeline = (order.timeline or []) + [event]
    db.commit()
    db.refresh(order)


def _order_to_dict(order: Order) -> dict:
    return {
        "id": order.id,
        "merchant_id": order.merchant_id,
        "user_id": order.user_id,
        "cart_id": order.cart_id,
        "agent_id": order.agent_id,
        "agent_session_id": order.agent_session_id,
        "approval_id": order.approval_id,
        "razorpay_order_id": order.razorpay_order_id,
        "amount": order.amount,
        "currency": order.currency,
        "status": order.status,
        "payment_status": order.payment_status,
        "receipt": order.receipt,
        "order_type": order.order_type,
        "timeline": order.timeline or [],
        "decision_factors": order.decision_factors or {},
        "created_at": str(order.created_at),
        "updated_at": str(order.updated_at),
    }
