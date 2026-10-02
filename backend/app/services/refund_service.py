"""Refund Service — Managed refund state machine and human authorization (Part 19)."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.refund import Refund
from app.models.order import Order
from app.models.payment import Payment
from app.services import audit_service, approval_service, policy_service


def create_refund_request(
    db: Session,
    order_id: str,
    amount: float,
    reason: str = "Customer requested cancellation",
    user_id: str = "demo_user",
    merchant_id: str = "merchant_001",
) -> Dict[str, Any]:
    """
    Creates a refund request and routes through policy and human approval gating.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": True, "message": "Order not found"}

    if order.payment_status != "captured":
        return {"error": True, "message": f"Cannot refund order with payment status '{order.payment_status}'."}

    # Policy and risk evaluation for refund
    risk_level = "HIGH" if amount > 2000 else "MEDIUM"
    risk_score = 75 if amount > 2000 else 45

    # Create human approval for refund
    approval = approval_service.create_approval_request(
        db=db,
        amount=amount,
        action="process_refund",
        order_id=order_id,
        merchant_id=merchant_id,
        user_id=user_id,
        risk_level=risk_level,
        risk_score=risk_score,
        reason=f"Refund request of ₹{amount:,.2f} for Order {order_id}: {reason}",
    )

    refund = Refund(
        order_id=order_id,
        payment_id=None,
        merchant_id=merchant_id,
        user_id=user_id,
        amount=amount,
        currency=order.currency or "INR",
        reason=reason,
        status="APPROVAL_PENDING",
        risk_level=risk_level,
        risk_score=risk_score,
        approval_id=approval.id,
    )
    db.add(refund)
    db.commit()
    db.refresh(refund)

    # Audit log
    audit_service.create_audit_log(
        db,
        actor_type="user",
        actor_id=user_id,
        action="REFUND_REQUESTED",
        resource_type="refund",
        resource_id=refund.id,
        amount=amount,
        currency=refund.currency,
        reason=reason,
        approval_status="PENDING",
        result="PENDING",
    )

    return {
        "refund_id": refund.id,
        "order_id": order.id,
        "amount": refund.amount,
        "status": refund.status,
        "approval_id": approval.id,
        "requires_approval": True,
        "message": "Refund request initiated. Awaiting human approval authorization.",
    }


def decide_refund(
    db: Session,
    refund_id: str,
    status: str,  # APPROVED or REJECTED
    approved_by: str = "merchant_admin",
    decision_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Approve or reject a refund."""
    refund = db.query(Refund).filter(Refund.id == refund_id).first()
    if not refund:
        return {"error": True, "message": "Refund record not found"}

    normalized = status.upper()
    if normalized == "APPROVED":
        refund.status = "COMPLETED"
        refund.approved_by = approved_by
        refund.decision_reason = decision_reason or f"Approved by {approved_by}"
        refund.completed_at = datetime.now(timezone.utc)

        # Update order status
        order = db.query(Order).filter(Order.id == refund.order_id).first()
        if order:
            order.payment_status = "refunded"
            order.status = "CANCELLED"
            order.timeline = (order.timeline or []) + [{
                "step": "REFUND_COMPLETED",
                "status": "REFUNDED",
                "timestamp": str(datetime.now(timezone.utc)),
                "actor": approved_by,
                "amount": refund.amount,
            }]
    else:
        refund.status = "REJECTED"
        refund.approved_by = approved_by
        refund.decision_reason = decision_reason or "Refund request declined."

    db.commit()
    db.refresh(refund)

    # Audit log
    audit_service.create_audit_log(
        db,
        actor_type="user",
        actor_id=approved_by,
        action=f"REFUND_{refund.status}",
        resource_type="refund",
        resource_id=refund.id,
        amount=refund.amount,
        reason=refund.decision_reason,
        result="SUCCESS" if refund.status == "COMPLETED" else "BLOCKED",
    )

    return {
        "success": True,
        "refund_id": refund.id,
        "status": refund.status,
        "order_id": refund.order_id,
        "message": f"Refund has been {refund.status.lower()}.",
    }


def list_refunds(db: Session, merchant_id: str = "merchant_001") -> List[Refund]:
    """List all refunds for merchant."""
    return db.query(Refund).filter(Refund.merchant_id == merchant_id).order_by(Refund.created_at.desc()).all()
