"""Refunds API — Managed refund state machine and human authorization."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import RefundCreate, RefundRead, RefundDecisionRequest
from app.services import refund_service

router = APIRouter(prefix="/refunds", tags=["Refund Workflow"])


@router.get("", response_model=List[RefundRead], summary="List Refund Requests")
def list_refunds(
    merchant_id: str = Query(default="merchant_001"),
    db: Session = Depends(get_db),
):
    """List all refund requests with current state and approval status."""
    return refund_service.list_refunds(db, merchant_id=merchant_id)


@router.post("/request", summary="Create Refund Request")
def create_refund(
    req: RefundCreate,
    db: Session = Depends(get_db),
):
    """Initiate a refund request. Automatically creates an expiring human approval record."""
    res = refund_service.create_refund_request(
        db=db,
        order_id=req.order_id,
        amount=req.amount,
        reason=req.reason,
        user_id=req.user_id,
        merchant_id=req.merchant_id,
    )
    if res.get("error"):
        raise HTTPException(status_code=400, detail=res.get("message", "Refund request failed"))
    return res


@router.post("/{refund_id}/decide", summary="Approve or Reject Refund")
def decide_refund(
    refund_id: str,
    req: RefundDecisionRequest,
    db: Session = Depends(get_db),
):
    """Authorize or reject a pending refund."""
    res = refund_service.decide_refund(
        db=db,
        refund_id=refund_id,
        status=req.status,
        approved_by=req.approved_by,
        decision_reason=req.decision_reason,
    )
    if res.get("error"):
        raise HTTPException(status_code=400, detail=res.get("message", "Refund decision failed"))
    return res
