"""Payments API — Razorpay payment creation and verification."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import PaymentCreate, PaymentVerify
from app.services import payment_service

router = APIRouter()


@router.post("/payments/create")
def create_payment(data: PaymentCreate, db: Session = Depends(get_db)):
    """Create a Razorpay payment for an order."""
    result = payment_service.create_payment_for_order(db, data.order_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail={"error": result})
    return result


@router.post("/payments/verify")
def verify_payment(data: PaymentVerify, db: Session = Depends(get_db)):
    """Verify Razorpay payment signature and update status."""
    result = payment_service.verify_and_update_payment(
        db,
        razorpay_order_id=data.razorpay_order_id,
        razorpay_payment_id=data.razorpay_payment_id,
        razorpay_signature=data.razorpay_signature,
    )
    if result.get("error"):
        raise HTTPException(status_code=400, detail={"error": result})
    return result


@router.get("/payments/{order_id}")
def get_payment_status(order_id: str, db: Session = Depends(get_db)):
    """Get payment status for an order."""
    result = payment_service.get_payment_status(db, order_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result)
    return result
