"""Customer Memory & Preferences API (Part 21)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.customer_preference import CustomerPreference
from app.schemas.schemas import CustomerPreferenceRead, CustomerPreferenceUpdate

router = APIRouter(prefix="/customer-memory", tags=["Customer Memory & Preferences"])


@router.get("", response_model=CustomerPreferenceRead, summary="Get Customer Shopping Memory")
def get_customer_preferences(
    user_id: str = Query(default="demo_user"),
    db: Session = Depends(get_db),
):
    """Retrieve saved customer shopping preferences for personalized recommendations."""
    pref = db.query(CustomerPreference).filter(CustomerPreference.user_id == user_id).first()
    if not pref:
        pref = CustomerPreference(user_id=user_id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.put("", response_model=CustomerPreferenceRead, summary="Update Customer Shopping Memory")
def update_customer_preferences(
    req: CustomerPreferenceUpdate,
    user_id: str = Query(default="demo_user"),
    db: Session = Depends(get_db),
):
    """Update preferred categories, brands, price ranges, and notes."""
    pref = db.query(CustomerPreference).filter(CustomerPreference.user_id == user_id).first()
    if not pref:
        pref = CustomerPreference(user_id=user_id)
        db.add(pref)

    data = req.model_dump(exclude_unset=True)
    for k, v in data.items():
        if v is not None and hasattr(pref, k):
            setattr(pref, k, v)

    db.commit()
    db.refresh(pref)
    return pref


@router.delete("", summary="Clear Customer Shopping Memory")
def delete_customer_preferences(
    user_id: str = Query(default="demo_user"),
    db: Session = Depends(get_db),
):
    """Delete customer preferences (Right to be forgotten)."""
    pref = db.query(CustomerPreference).filter(CustomerPreference.user_id == user_id).first()
    if pref:
        db.delete(pref)
        db.commit()
    return {"success": True, "message": "Customer preferences reset."}
