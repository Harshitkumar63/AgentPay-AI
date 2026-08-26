"""Approvals API — Human-in-the-loop authorization gate endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import approval_service
from app.schemas.schemas import ApprovalRead, ApprovalCreate, ApprovalDecisionRequest

router = APIRouter(prefix="/approvals", tags=["Human Approvals"])


@router.get("", response_model=List[ApprovalRead], summary="List Human Approvals")
def list_approvals(
    merchant_id: str = Query(default="merchant_001"),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """List pending or historical approval requests for the merchant."""
    approvals = approval_service.list_approvals(db, merchant_id=merchant_id, status=status, limit=limit)
    return approvals


@router.get("/{approval_id}", response_model=ApprovalRead, summary="Get Approval Details")
def get_approval(approval_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific approval record."""
    approval = approval_service.get_approval(db, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval record not found")
    return approval


@router.post("", response_model=ApprovalRead, summary="Create Approval Request")
def create_approval(req: ApprovalCreate, db: Session = Depends(get_db)):
    """Create a new human approval request for an order."""
    appr = approval_service.create_approval_request(
        db=db,
        amount=req.amount,
        action=req.action,
        agent_session_id=req.agent_session_id,
        order_id=req.order_id,
        merchant_id=req.merchant_id,
        user_id=req.user_id,
        reason=req.reason,
    )
    return appr


@router.post("/{approval_id}/decide", summary="Submit Human Approval Decision")
def decide_approval(
    approval_id: str,
    req: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
):
    """Submit human decision (APPROVED or REJECTED) on an approval request."""
    result = approval_service.decide_approval(
        db=db,
        approval_id=approval_id,
        status=req.status,
        approved_by=req.approved_by,
        decision_reason=req.reason,
    )
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result)
    return result
