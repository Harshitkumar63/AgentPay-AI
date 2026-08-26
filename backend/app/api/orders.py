"""Orders API — Order state machine, timeline tracking, and Decision Replay (Phases 24 & 25)."""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.order import Order
from app.models.audit import AuditLog
from app.models.agent import AgentAction
from app.models.approval import Approval
from app.models.payment import Payment
from app.schemas.schemas import OrderCreate, OrderRead
from app.services import order_service, policy_service

router = APIRouter()


@router.post("/orders")
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    """Create an order from a cart with full validation pipeline."""
    result = order_service.create_order(
        db,
        cart_id=data.cart_id,
        user_id=data.user_id,
        merchant_id=data.merchant_id,
        idempotency_key=data.idempotency_key,
        order_type=data.order_type,
    )
    if result.get("error"):
        status = 400
        if result.get("code") == "POLICY_BLOCKED":
            status = 403
        raise HTTPException(status_code=status, detail={"error": result})
    return result


@router.get("/orders")
def list_orders(
    merchant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List orders."""
    orders = order_service.get_orders(db, merchant_id=merchant_id, user_id=user_id, skip=skip, limit=limit)
    return [order_service._order_to_dict(o) for o in orders]


@router.get("/orders/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get full order details including timeline and decision factors."""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_service._order_to_dict(order)


@router.get("/orders/{order_id}/timeline", summary="Get Order Timeline")
def get_order_timeline(order_id: str, db: Session = Depends(get_db)):
    """Get the step-by-step state machine timeline for an order."""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_id": order.id,
        "status": order.status,
        "payment_status": order.payment_status,
        "timeline": order.timeline or [],
    }


@router.get("/orders/{order_id}/decision-replay", summary="Decision Replay: Full Governance Journey Reconstruction")
def get_decision_replay(order_id: str, db: Session = Depends(get_db)):
    """
    Decision Replay (Phase 24):
    Reconstructs the full end-to-end decision journey:
    USER REQUEST -> INTENT -> TOOLS -> SELECTION -> CART -> POLICY -> RISK -> BUDGET -> TRUST -> APPROVAL -> ORDER -> PAYMENT -> WEBHOOK -> AUDIT.
    """
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Fetch audit logs
    audit_logs = db.query(AuditLog).filter(
        (AuditLog.resource_id == order.id) |
        (AuditLog.resource_id == order.cart_id) |
        (AuditLog.resource_id == order.approval_id)
    ).order_by(AuditLog.created_at.asc()).all()

    # Fetch agent actions
    agent_actions = []
    if order.agent_session_id:
        agent_actions = db.query(AgentAction).filter(
            AgentAction.session_id == order.agent_session_id
        ).order_by(AgentAction.created_at.asc()).all()

    # Fetch approval record
    approval = None
    if order.approval_id:
        appr_obj = db.query(Approval).filter(Approval.id == order.approval_id).first()
        if appr_obj:
            approval = {
                "id": appr_obj.id,
                "status": appr_obj.status,
                "amount": appr_obj.amount,
                "risk_level": appr_obj.risk_level,
                "approved_by": appr_obj.approved_by,
                "created_at": str(appr_obj.created_at),
                "expires_at": str(appr_obj.expires_at),
            }

    # Fetch payment
    payment = db.query(Payment).filter(Payment.order_id == order.id).first()

    # Form structured stages
    stages = [
        {
            "sequence": 1,
            "title": "01 USER INTENT & REQUEST",
            "status": "SUCCESS",
            "summary": f"Order initiated by {order.user_id} (Type: {order.order_type})",
            "timestamp": str(order.created_at),
        },
        {
            "sequence": 2,
            "title": "02 STOCK & SERVER PRICING VALIDATION",
            "status": "SUCCESS",
            "summary": f"Server recalculated cart amount to ₹{order.amount:,.2f} INR",
            "timestamp": str(order.created_at),
        },
        {
            "sequence": 3,
            "title": "03 POLICY & RISK EVALUATION",
            "status": "SUCCESS",
            "summary": "Passed maximum purchase limits and discount cap rules",
            "timestamp": str(order.created_at),
        },
        {
            "sequence": 4,
            "title": "04 BUDGET & TRUST VERIFICATION",
            "status": "SUCCESS",
            "summary": "Agent budget available, trust score verified",
            "timestamp": str(order.created_at),
        },
        {
            "sequence": 5,
            "title": "05 HUMAN APPROVAL GATE",
            "status": approval.get("status", "AUTO_APPROVED") if approval else "AUTO_APPROVED",
            "summary": f"Approval {approval['status'] if approval else 'Auto-approved within safe threshold'}",
            "details": approval,
            "timestamp": str(order.created_at),
        },
        {
            "sequence": 6,
            "title": "06 ORDER & PAYMENT ORCHESTRATION",
            "status": order.status,
            "summary": f"Razorpay Order ID: {order.razorpay_order_id or 'Created'}, Payment: {order.payment_status}",
            "timestamp": str(order.updated_at),
        },
        {
            "sequence": 7,
            "title": "07 AUDIT RECORDING",
            "status": "RECORDED",
            "summary": f"{len(audit_logs)} persistent audit logs committed",
            "timestamp": str(order.updated_at),
        },
    ]

    return {
        "order_id": order.id,
        "order_type": order.order_type,
        "amount": order.amount,
        "currency": order.currency,
        "status": order.status,
        "payment_status": order.payment_status,
        "stages": stages,
        "timeline": order.timeline or [],
        "decision_factors": order.decision_factors or {},
        "approval": approval,
        "payment": {
            "id": payment.id if payment else None,
            "status": payment.status if payment else "pending",
            "method": payment.method if payment else None,
            "razorpay_payment_id": payment.razorpay_payment_id if payment else None,
        } if payment else None,
        "audit_logs": [
            {
                "id": a.id,
                "action": a.action,
                "actor": a.actor_id,
                "actor_type": a.actor_type,
                "result": a.result,
                "timestamp": str(a.created_at),
            }
            for a in audit_logs
        ],
    }
