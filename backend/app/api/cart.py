"""Cart API — cart management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import CartCreate, CartItemCreate
from app.services import cart_service

router = APIRouter()


@router.post("/cart")
def create_cart(data: CartCreate, db: Session = Depends(get_db)):
    """Create a new cart."""
    cart = cart_service.get_or_create_cart(db, data.user_id, data.merchant_id)
    return cart_service.get_cart_details(db, cart.id)


@router.get("/cart/{cart_id}")
def get_cart(cart_id: str, db: Session = Depends(get_db)):
    """Get cart with items."""
    details = cart_service.get_cart_details(db, cart_id)
    if not details:
        raise HTTPException(status_code=404, detail="Cart not found")
    return details


@router.post("/cart/{cart_id}/items")
def add_to_cart(cart_id: str, data: CartItemCreate, db: Session = Depends(get_db)):
    """Add item to cart."""
    item = cart_service.add_item(db, cart_id, data.product_id, data.quantity)
    if not item:
        raise HTTPException(status_code=400, detail="Could not add item to cart")
    return cart_service.get_cart_details(db, cart_id)


@router.delete("/cart/{cart_id}/items/{product_id}")
def remove_from_cart(cart_id: str, product_id: str, db: Session = Depends(get_db)):
    """Remove item from cart."""
    success = cart_service.remove_item(db, cart_id, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    return cart_service.get_cart_details(db, cart_id)


@router.get("/cart/{cart_id}/calculate")
def calculate_cart(cart_id: str, db: Session = Depends(get_db)):
    """Calculate cart totals."""
    return cart_service.calculate_cart(db, cart_id)
