"""Order service — order creation with idempotency and policy checks."""

import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.order import Order
from app.models.cart import Cart
from app.services import cart_service, policy_service, audit_service
from app.services.product_service import check_inventory


def create_order(
    db: Session,
    cart_id: str,
    user_id: str,
    merchant_id: str,
    idempotency_key: Optional[str] = None,
    order_type: str = "normal",
    actor_id: str = "system",
    actor_type: str = "user",
) -> dict:
    """
    Create an order from a cart with full validation pipeline:
    1. Validate cart
    2. Check inventory
    3. Calculate amount
    4. Run policy engine
    5. Determine approval requirement
    6. Create audit event
    7. Create order
    """
    # Idempotency check
    if idempotency_key:
        existing = db.query(Order).filter(Order.idempotency_key == idempotency_key).first()
        if existing:
            return {
                "order": _order_to_dict(existing),
                "status": "existing",
                "message": "Order already exists for this idempotency key",
            }

    # 1. Validate cart
    cart = cart_service.get_cart(db, cart_id)
    if not cart:
        return {"error": True, "code": "CART_NOT_FOUND", "message": "Cart not found"}
    if not cart.items:
        return {"error": True, "code": "CART_EMPTY", "message": "Cart is empty"}
    if cart.status != "active":
        return {"error": True, "code": "CART_NOT_ACTIVE", "message": "Cart is not active"}

    # 2. Check inventory for all items
    for item in cart.items:
        inv = check_inventory(db, item.product_id, item.quantity)
        if not inv["available"]:
            return {
                "error": True,
                "code": "INSUFFICIENT_STOCK",
                "message": f"Insufficient stock for product {item.product_id}: {inv['reason']}",
            }

    # 3. Calculate amount
    calc = cart_service.calculate_cart(db, cart_id)
    amount = calc["total"]

    # 4. Policy check
    policy_result = policy_service.check_purchase_policy(db, merchant_id, amount)

    # 5. Create audit event
    audit_service.create_audit_log(
        db,
        actor_type=actor_type,
        actor_id=actor_id,
        action="CREATE_ORDER",
        resource_type="order",
        amount=amount,
        currency="INR",
        reason=f"Order creation from cart {cart_id}",
        policy_result="ALLOWED" if policy_result["allowed"] else "BLOCKED",
        approval_status="PENDING" if policy_result["requires_approval"] else "AUTO_APPROVED",
    )

    if not policy_result["allowed"]:
        return {
            "error": True,
            "code": "POLICY_BLOCKED",
            "message": policy_result["reason"],
            "policy": policy_result,
        }

    # 6. Create order
    receipt = f"receipt_{uuid.uuid4().hex[:12]}"
    order = Order(
        merchant_id=merchant_id,
        user_id=user_id,
        cart_id=cart_id,
        amount=amount,
        currency="INR",
        status="created",
        payment_status="pending",
        receipt=receipt,
        idempotency_key=idempotency_key or f"idem_{uuid.uuid4().hex[:12]}",
        order_type=order_type,
    )
    db.add(order)

    # Mark cart as checked out
    cart.status = "checked_out"

    db.commit()
    db.refresh(order)

    return {
        "order": _order_to_dict(order),
        "status": "created",
        "requires_approval": policy_result["requires_approval"],
        "policy": policy_result,
        "message": "Order created successfully",
    }


def get_order(db: Session, order_id: str) -> Optional[Order]:
    """Get order by ID."""
    return db.query(Order).filter(Order.id == order_id).first()


def get_orders(db: Session, merchant_id: Optional[str] = None, user_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Order]:
    """Get orders with optional filters."""
    q = db.query(Order)
    if merchant_id:
        q = q.filter(Order.merchant_id == merchant_id)
    if user_id:
        q = q.filter(Order.user_id == user_id)
    return q.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def update_order_status(db: Session, order_id: str, status: str = None, payment_status: str = None, razorpay_order_id: str = None) -> Optional[Order]:
    """Update order status fields."""
    order = get_order(db, order_id)
    if not order:
        return None
    if status:
        order.status = status
    if payment_status:
        order.payment_status = payment_status
    if razorpay_order_id:
        order.razorpay_order_id = razorpay_order_id
    db.commit()
    db.refresh(order)
    return order


def _order_to_dict(order: Order) -> dict:
    return {
        "id": order.id,
        "merchant_id": order.merchant_id,
        "user_id": order.user_id,
        "cart_id": order.cart_id,
        "razorpay_order_id": order.razorpay_order_id,
        "amount": order.amount,
        "currency": order.currency,
        "status": order.status,
        "payment_status": order.payment_status,
        "receipt": order.receipt,
        "order_type": order.order_type,
        "created_at": str(order.created_at),
        "updated_at": str(order.updated_at),
    }
