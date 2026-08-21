"""Orders API — order creation and management."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import OrderCreate, OrderRead
from app.services import order_service

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
        if result["code"] == "POLICY_BLOCKED":
            status = 403
        raise HTTPException(status_code=status, detail={"error": result})
    return result


@router.get("/orders", response_model=List[OrderRead])
def list_orders(
    merchant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List orders."""
    return order_service.get_orders(db, merchant_id=merchant_id, user_id=user_id, skip=skip, limit=limit)


@router.get("/orders/{order_id}", response_model=OrderRead)
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get order by ID."""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
