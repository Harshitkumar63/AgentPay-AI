"""Admin Approvals API — Human-in-the-Loop authorization queue (Phase 10)."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import approval_service

router = APIRouter(prefix="/admin/approvals", tags=["Admin Human Approvals"])


class ApprovalDecisionRequest(BaseModel):
    decision_reason: Optional[str] = Field(None, example="Approved by merchant supervisor")
    approved_by: Optional[str] = Field("merchant_admin", example="merchant_admin")


@router.get("", summary="List Human Approval Queue")
def list_admin_approvals(
    status: Optional[str] = Query(default=None, example="PENDING"),
    merchant_id: str = Query(default="merchant_001"),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """List pending and resolved approval authorizations."""
    approvals = approval_service.list_approvals(db, merchant_id=merchant_id, status=status, limit=limit)
    return [
        {
            "id": a.id,
            "agent_session_id": a.agent_session_id,
            "order_id": a.order_id,
            "merchant_id": a.merchant_id,
            "user_id": a.user_id,
            "action": a.action,
            "amount": a.amount,
            "currency": a.currency,
            "risk_level": a.risk_level,
            "risk_score": a.risk_score,
            "policy_result": a.policy_result or {},
            "reason": a.reason,
            "status": a.status,
            "decision_reason": a.decision_reason,
            "approved_by": a.approved_by,
            "created_at": str(a.created_at),
            "expires_at": str(a.expires_at),
            "decided_at": str(a.decided_at) if a.decided_at else None,
            "is_expired": a.is_expired,
        }
        for a in approvals
    ]


@router.get("/{id}", summary="Get Approval Request Details")
def get_admin_approval(id: str, db: Session = Depends(get_db)):
    """Retrieve full verification parameters for an approval request."""
    approval = approval_service.get_approval(db, id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    return {
        "id": approval.id,
        "agent_session_id": approval.agent_session_id,
        "order_id": approval.order_id,
        "merchant_id": approval.merchant_id,
        "user_id": approval.user_id,
        "action": approval.action,
        "amount": approval.amount,
        "currency": approval.currency,
        "risk_level": approval.risk_level,
        "risk_score": approval.risk_score,
        "policy_result": approval.policy_result or {},
        "reason": approval.reason,
        "status": approval.status,
        "decision_reason": approval.decision_reason,
        "approved_by": approval.approved_by,
        "created_at": str(approval.created_at),
        "expires_at": str(approval.expires_at),
        "decided_at": str(approval.decided_at) if approval.decided_at else None,
        "is_expired": approval.is_expired,
    }


@router.post("/{id}/approve", summary="Authorize & Approve Transaction")
def approve_request(
    id: str,
    req: Optional[ApprovalDecisionRequest] = None,
    db: Session = Depends(get_db),
):
    """Approve a gated financial transaction before 5-minute TTL expires."""
    approved_by = req.approved_by if req and req.approved_by else "merchant_admin"
    reason = req.decision_reason if req and req.decision_reason else "Approved by merchant admin"

    res = approval_service.decide_approval(
        db=db,
        approval_id=id,
        status="APPROVED",
        approved_by=approved_by,
        decision_reason=reason,
    )
    if res.get("error"):
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/{id}/reject", summary="Reject Transaction")
def reject_request(
    id: str,
    req: Optional[ApprovalDecisionRequest] = None,
    db: Session = Depends(get_db),
):
    """Reject a gated financial transaction."""
    approved_by = req.approved_by if req and req.approved_by else "merchant_admin"
    reason = req.decision_reason if req and req.decision_reason else "Rejected by merchant admin"

    res = approval_service.decide_approval(
        db=db,
        approval_id=id,
        status="REJECTED",
        approved_by=approved_by,
        decision_reason=reason,
    )
    if res.get("error"):
        raise HTTPException(status_code=400, detail=res["message"])
    return res
