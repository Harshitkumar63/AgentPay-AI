"""Policies API — merchant policy management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import PolicyRead, PolicyUpdate, PolicyCheckResult
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
    merchant_id: str = "merchant_001",
    data: PolicyUpdate = None,
    db: Session = Depends(get_db),
):
    """Update merchant policy."""
    if data is None:
        raise HTTPException(status_code=400, detail="No data provided")
    policy = policy_service.update_policy(db, merchant_id, data.model_dump(exclude_unset=True))
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.post("/policies/check")
def check_policy(
    merchant_id: str = "merchant_001",
    amount: float = 0,
    db: Session = Depends(get_db),
):
    """Check if a purchase amount passes policy."""
    return policy_service.check_purchase_policy(db, merchant_id, amount)
