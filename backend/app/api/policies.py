"""Policies API — merchant policy management, risk evaluation, and policy simulator."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import PolicyRead, PolicyUpdate, PolicyCheckResult, PolicySimulateRequest, PolicySimulateResponse
from app.services import policy_service

router = APIRouter()


@router.get("/policies")
def get_policies(merchant_id: str = "merchant_001", db: Session = Depends(get_db)):
    """Get merchant policy."""
    policy = policy_service.get_merchant_policy(db, merchant_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.put("/policies")
def update_policies(
    data: PolicyUpdate,
    merchant_id: str = "merchant_001",
    db: Session = Depends(get_db),
):
    """Update merchant policy."""
    policy = policy_service.update_policy(db, merchant_id, data.model_dump(exclude_unset=True))
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.post("/policies/check")
def check_policy(
    merchant_id: str = "merchant_001",
    amount: float = 0.0,
    discount_percentage: float = 0.0,
    action: str = "create_order",
    db: Session = Depends(get_db),
):
    """Check if a purchase amount and parameters pass policy and risk gating."""
    return policy_service.check_purchase_policy(
        db,
        merchant_id=merchant_id,
        amount=amount,
        discount_percentage=discount_percentage,
        action=action,
    )


@router.post("/policies/simulate", response_model=PolicySimulateResponse)
def simulate_policy(req: PolicySimulateRequest, db: Session = Depends(get_db)):
    """Interactive Policy Simulator (Phase 28) for real-time compliance testing."""
    return policy_service.simulate_policy(
        db=db,
        merchant_id=req.merchant_id,
        amount=req.amount,
        discount_percentage=req.discount_percentage,
        action=req.action,
    )
