"""Approval Service — Human-in-the-loop authorization gating with 5-minute expiration."""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.approval import Approval
from app.models.order import Order
from app.services import audit_service, trust_service


def create_approval_request(
    db: Session,
    amount: float,
    action: str = "create_order",
    agent_session_id: Optional[str] = None,
    order_id: Optional[str] = None,
    merchant_id: str = "merchant_001",
    user_id: str = "demo_user",
    risk_level: str = "HIGH",
    risk_score: int = 80,
    policy_result: Optional[dict] = None,
    reason: str = "Sensitive financial transaction requires human verification",
    ttl_minutes: int = 5,
) -> Approval:
    """Create a new expiring approval record."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ttl_minutes)

    approval = Approval(
        agent_session_id=agent_session_id,
        order_id=order_id,
        merchant_id=merchant_id,
        user_id=user_id,
        action=action,
        amount=amount,
        currency="INR",
        risk_level=risk_level,
        risk_score=risk_score,
        policy_result=policy_result or {},
        reason=reason,
        status="PENDING",
        created_at=now,
        expires_at=expires_at,
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)

    # Record audit event
    audit_service.create_audit_log(
        db,
        actor_type="system",
        actor_id="approval_service",
        action="APPROVAL_REQUESTED",
        resource_type="approval",
        resource_id=approval.id,
        amount=amount,
        currency="INR",
        reason=reason,
        approval_status="PENDING",
        result="PENDING",
        metadata_extra={"risk_level": risk_level, "risk_score": risk_score, "expires_at": str(expires_at), "order_id": order_id},
    )

    trust_service.record_trust_event(db, "approval_requested")

    return approval


def get_approval(db: Session, approval_id: str) -> Optional[Approval]:
    """Retrieve approval and update status to EXPIRED if past expiration date."""
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        return None

    if approval.status == "PENDING" and approval.is_expired:
        approval.status = "EXPIRED"
        db.commit()
        db.refresh(approval)

    return approval


def list_approvals(
    db: Session,
    merchant_id: str = "merchant_001",
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Approval]:
    """List approvals with optional status filter."""
    q = db.query(Approval).filter(Approval.merchant_id == merchant_id)
    if status:
        q = q.filter(Approval.status == status)
    approvals = q.order_by(Approval.created_at.desc()).limit(limit).all()

    # Expire pending on read
    now = datetime.now(timezone.utc)
    changed = False
    for a in approvals:
        if a.status == "PENDING" and a.is_expired:
            a.status = "EXPIRED"
            changed = True
    if changed:
        db.commit()

    return approvals


def decide_approval(
    db: Session,
    approval_id: str,
    status: str,  # APPROVED, REJECTED
    approved_by: str = "merchant_admin",
    decision_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit human approval decision."""
    approval = get_approval(db, approval_id)
    if not approval:
        return {"error": True, "code": "APPROVAL_NOT_FOUND", "message": "Approval request not found"}

    if approval.status == "EXPIRED":
        return {
            "error": True,
            "code": "APPROVAL_EXPIRED",
            "message": "Approval window expired (5-minute TTL exceeded). Please initiate checkout again.",
        }

    if approval.status != "PENDING":
        return {
            "error": True,
            "code": "ALREADY_DECIDED",
            "message": f"Approval was already {approval.status.lower()}",
        }

    normalized_status = status.upper()
    if normalized_status not in ("APPROVED", "REJECTED"):
        return {"error": True, "code": "INVALID_STATUS", "message": "Status must be APPROVED or REJECTED"}

    approval.status = normalized_status
    approval.approved_by = approved_by
    approval.decision_reason = decision_reason or f"Decision submitted by {approved_by}"
    approval.decided_at = datetime.now(timezone.utc)

    # Update associated order if present
    if approval.order_id:
        order = db.query(Order).filter(Order.id == approval.order_id).first()
        if order:
            if normalized_status == "APPROVED":
                order.status = "APPROVED"
                order.timeline = (order.timeline or []) + [{
                    "step": "HUMAN_APPROVAL_GRANTED",
                    "status": "APPROVED",
                    "timestamp": str(datetime.now(timezone.utc)),
                    "actor": approved_by,
                }]
            else:
                order.status = "CANCELLED"
                order.timeline = (order.timeline or []) + [{
                    "step": "HUMAN_APPROVAL_REJECTED",
                    "status": "REJECTED",
                    "timestamp": str(datetime.now(timezone.utc)),
                    "actor": approved_by,
                }]

    db.commit()
    db.refresh(approval)

    # Audit log
    audit_service.create_audit_log(
        db,
        actor_type="user",
        actor_id=approved_by,
        action=f"APPROVAL_{normalized_status}",
        resource_type="approval",
        resource_id=approval.id,
        amount=approval.amount,
        currency=approval.currency,
        reason=approval.decision_reason,
        approval_status=normalized_status,
        result="SUCCESS" if normalized_status == "APPROVED" else "BLOCKED",
    )

    # Update trust signals
    if normalized_status == "APPROVED":
        trust_service.record_trust_event(db, "approval_granted")
    else:
        trust_service.record_trust_event(db, "approval_rejected")

    return {
        "success": True,
        "approval_id": approval.id,
        "status": approval.status,
        "order_id": approval.order_id,
        "amount": approval.amount,
    }


def validate_approval(
    db: Session,
    approval_id: str,
    expected_amount: Optional[float] = None,
) -> Dict[str, Any]:
    """Verify approval is valid, approved, and not expired."""
    approval = get_approval(db, approval_id)
    if not approval:
        return {"valid": False, "code": "APPROVAL_NOT_FOUND", "reason": "Approval record not found"}

    if approval.status == "EXPIRED" or approval.is_expired:
        return {"valid": False, "code": "APPROVAL_EXPIRED", "reason": "Approval expired (5-minute TTL elapsed)"}

    if approval.status != "APPROVED":
        return {"valid": False, "code": "NOT_APPROVED", "reason": f"Approval status is {approval.status}"}

    if expected_amount is not None and abs(approval.amount - expected_amount) > 0.01:
        return {"valid": False, "code": "AMOUNT_MISMATCH", "reason": f"Approved amount ₹{approval.amount} does not match order total ₹{expected_amount}"}

    return {"valid": True, "approval": approval}
