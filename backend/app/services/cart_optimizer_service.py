"""Cart Optimizer Service (Part 22).

Analyzes cart composition to propose optimizations for price, value, quality, or savings.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.cart import Cart
from app.models.product import Product
from app.services import cart_service


def optimize_cart(
    db: Session,
    cart_id: str,
    mode: str = "BEST_VALUE",  # MINIMUM_PRICE, BEST_VALUE, BEST_QUALITY, MAXIMUM_SAVING
) -> Dict[str, Any]:
    """
    Generates optimization proposals for the current cart without applying changes until user confirms.
    """
    cart = cart_service.get_cart(db, cart_id)
    if not cart or not cart.items:
        return {"error": True, "message": "Cart is empty or not found"}

    calc = cart_service.calculate_cart(db, cart_id)
    current_total = calc["total"]
    suggestions = []
    projected_savings = 0.0

    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            continue

        if mode in ("MINIMUM_PRICE", "MAXIMUM_SAVING"):
            # Find cheaper alternative in same category
            cheaper = db.query(Product).filter(
                Product.category == product.category,
                Product.price < product.price,
                Product.id != product.id,
                Product.active == True,
                Product.stock > 0,
            ).order_by(Product.price.asc()).first()

            if cheaper:
                diff = (product.price - cheaper.price) * item.quantity
                projected_savings += diff
                suggestions.append({
                    "action": "REPLACE",
                    "original_product_id": product.id,
                    "original_product_name": product.name,
                    "suggested_product_id": cheaper.id,
                    "suggested_product_name": cheaper.name,
                    "price_difference": -round(diff, 2),
                    "reason": f"Switching saves ₹{diff:,.2f} while retaining core {product.category} functionality.",
                })

        elif mode == "BEST_VALUE":
            # Check if there's a bundle or upgrade with higher affinity/savings
            meta = product.metadata_extra or {}
            cross_sells = meta.get("cross_sell", [])
            if cross_sells:
                cs_prod = db.query(Product).filter(Product.id == cross_sells[0], Product.stock > 0).first()
                if cs_prod:
                    suggestions.append({
                        "action": "ADD_ACCESSORY",
                        "original_product_id": product.id,
                        "original_product_name": product.name,
                        "suggested_product_id": cs_prod.id,
                        "suggested_product_name": cs_prod.name,
                        "price_difference": round(cs_prod.price, 2),
                        "reason": f"High-affinity pairing: {cs_prod.name} boosts utility for {product.name}.",
                    })

        elif mode == "BEST_QUALITY":
            # Premium tier upgrade
            meta = product.metadata_extra or {}
            upsell_id = meta.get("upsell")
            if upsell_id:
                up_prod = db.query(Product).filter(Product.id == upsell_id, Product.stock > 0).first()
                if up_prod:
                    diff = (up_prod.price - product.price) * item.quantity
                    suggestions.append({
                        "action": "REPLACE",
                        "original_product_id": product.id,
                        "original_product_name": product.name,
                        "suggested_product_id": up_prod.id,
                        "suggested_product_name": up_prod.name,
                        "price_difference": round(diff, 2),
                        "reason": f"Top-tier performance upgrade: {up_prod.name} (+₹{diff:,.2f}).",
                    })

    optimized_total = max(0.0, current_total - projected_savings)

    return {
        "cart_id": cart_id,
        "mode": mode,
        "current_total": current_total,
        "optimized_total": round(optimized_total, 2),
        "savings": round(projected_savings, 2),
        "suggestions": suggestions,
        "status": "PROPOSED",
        "disclaimer": "Optimization requires customer approval before modifying cart items.",
    }


def apply_cart_optimization(db: Session, cart_id: str, mode: str = "MINIMUM_PRICE") -> Dict[str, Any]:
    """Applies the optimization recommendations to the cart after explicit user approval."""
    proposal = optimize_cart(db, cart_id, mode)
    if proposal.get("error"):
        return proposal

    for sug in proposal.get("suggestions", []):
        if sug["action"] == "REPLACE" and sug.get("original_product_id") and sug.get("suggested_product_id"):
            cart_service.remove_item(db, cart_id, sug["original_product_id"])
            cart_service.add_item(db, cart_id, sug["suggested_product_id"], quantity=1)

    return {
        "success": True,
        "cart": cart_service.get_cart_details(db, cart_id),
        "applied_mode": mode,
        "message": "Cart optimized successfully according to selected strategy.",
    }
