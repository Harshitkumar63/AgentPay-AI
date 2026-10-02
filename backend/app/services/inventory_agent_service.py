"""AI Inventory Agent Service (Part 14).

Computes real-time stockout risk, overstock risk, inventory velocity, and actionable supply-chain recommendations.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.product import Product
from app.models.cart import CartItem
from app.models.order import Order


def get_inventory_intelligence(db: Session, merchant_id: str = "merchant_001") -> Dict[str, Any]:
    """
    Evaluates real database product stock against sales volume to detect
    stockout and overstock risks.
    """
    products = db.query(Product).filter(
        Product.merchant_id == merchant_id,
        Product.active == True,
    ).all()

    items = []
    high_stockout = []
    overstock = []

    for product in products:
        # Calculate sales count from captured orders
        sold_count = db.query(func.coalesce(func.sum(CartItem.quantity), 0)).join(
            Order, Order.cart_id == CartItem.cart_id
        ).filter(
            CartItem.product_id == product.id,
            Order.payment_status == "captured",
        ).scalar() or 0

        # Weekly sales baseline
        weekly_sales = max(1, int(sold_count) // 4) if sold_count > 0 else (4 if product.stock < 15 else 2)
        daily_velocity = round(weekly_sales / 7.0, 2)
        days_remaining = int(product.stock / max(0.1, daily_velocity))

        # Risk classifications
        if product.stock <= 5 or days_remaining <= 7:
            stockout_risk = "HIGH"
            overstock_risk = "LOW"
            rec = f"Urgent restock needed: order {max(20, weekly_sales * 4)} units."
            action = "RESTOCK"
        elif product.stock >= 40 and days_remaining >= 60:
            stockout_risk = "LOW"
            overstock_risk = "HIGH"
            rec = "High capital lock-in: propose a 10-15% discount promotion."
            action = "PROMOTION"
        elif product.stock <= 15 or days_remaining <= 14:
            stockout_risk = "MEDIUM"
            overstock_risk = "LOW"
            rec = "Prepare replenishment order in next replenishment cycle."
            action = "MONITOR"
        else:
            stockout_risk = "LOW"
            overstock_risk = "LOW"
            rec = "Optimal inventory level."
            action = "MAINTAIN"

        item_data = {
            "product_id": product.id,
            "product_name": product.name,
            "category": product.category,
            "price": product.price,
            "stock": product.stock,
            "weekly_sales": weekly_sales,
            "sales_velocity_daily": daily_velocity,
            "estimated_days_remaining": days_remaining,
            "stockout_risk": stockout_risk,
            "overstock_risk": overstock_risk,
            "recommendation": rec,
            "suggested_action": action,
        }

        items.append(item_data)
        if stockout_risk == "HIGH":
            high_stockout.append(item_data)
        elif overstock_risk == "HIGH":
            overstock.append(item_data)

    return {
        "merchant_id": merchant_id,
        "total_products": len(products),
        "high_stockout_items": high_stockout,
        "overstock_items": overstock,
        "all_inventory": items,
    }
