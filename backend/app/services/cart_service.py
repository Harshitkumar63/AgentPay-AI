"""Cart service — cart management operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.cart import Cart, CartItem
from app.models.product import Product


def create_cart(db: Session, user_id: str, merchant_id: str) -> Cart:
    """Create a new cart."""
    cart = Cart(user_id=user_id, merchant_id=merchant_id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def get_cart(db: Session, cart_id: str) -> Optional[Cart]:
    """Get a cart by ID with items."""
    return db.query(Cart).filter(Cart.id == cart_id).first()


def get_or_create_cart(db: Session, user_id: str, merchant_id: str) -> Cart:
    """Get active cart or create new one."""
    cart = db.query(Cart).filter(
        Cart.user_id == user_id,
        Cart.merchant_id == merchant_id,
        Cart.status == "active",
    ).first()
    if not cart:
        cart = create_cart(db, user_id, merchant_id)
    return cart


def add_item(db: Session, cart_id: str, product_id: str, quantity: int = 1) -> Optional[CartItem]:
    """Add item to cart or update quantity if already exists."""
    cart = get_cart(db, cart_id)
    if not cart or cart.status != "active":
        return None

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or not product.active:
        return None

    # Check if already in cart
    existing = db.query(CartItem).filter(
        CartItem.cart_id == cart_id,
        CartItem.product_id == product_id,
    ).first()

    if existing:
        existing.quantity += quantity
        db.commit()
        db.refresh(existing)
        return existing

    item = CartItem(
        cart_id=cart_id,
        product_id=product_id,
        quantity=quantity,
        unit_price=product.price,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_item(db: Session, cart_id: str, product_id: str) -> bool:
    """Remove item from cart."""
    item = db.query(CartItem).filter(
        CartItem.cart_id == cart_id,
        CartItem.product_id == product_id,
    ).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def calculate_cart(db: Session, cart_id: str) -> dict:
    """Calculate cart totals."""
    cart = get_cart(db, cart_id)
    if not cart:
        return {"subtotal": 0, "discount": 0, "tax": 0, "total": 0, "item_count": 0}

    subtotal = sum(item.unit_price * item.quantity for item in cart.items)
    discount = 0
    tax = 0
    total = subtotal - discount + tax

    return {
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "tax": round(tax, 2),
        "total": round(total, 2),
        "item_count": sum(item.quantity for item in cart.items),
    }


def get_cart_details(db: Session, cart_id: str) -> dict:
    """Get full cart details with product info."""
    cart = get_cart(db, cart_id)
    if not cart:
        return None

    items = []
    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        items.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": product.name if product else "Unknown",
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "subtotal": round(item.unit_price * item.quantity, 2),
        })

    calc = calculate_cart(db, cart_id)
    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "merchant_id": cart.merchant_id,
        "status": cart.status,
        "items": items,
        "subtotal": calc["subtotal"],
        "total": calc["total"],
        "item_count": calc["item_count"],
    }
