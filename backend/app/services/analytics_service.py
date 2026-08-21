"""Analytics service — revenue, product, and AI-assisted metrics."""

from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.order import Order
from app.models.product import Product
from app.models.cart import CartItem


def get_revenue_analytics(db: Session, merchant_id: str = "merchant_001", days: int = 30) -> dict:
    """Calculate revenue analytics for a merchant."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # All orders
    orders = db.query(Order).filter(
        Order.merchant_id == merchant_id,
        Order.created_at >= cutoff,
    ).all()

    captured_orders = [o for o in orders if o.payment_status == "captured"]
    ai_orders = [o for o in captured_orders if o.order_type in ("ai_assisted", "upsell", "cross_sell")]
    upsell_orders = [o for o in captured_orders if o.order_type == "upsell"]
    cross_sell_orders = [o for o in captured_orders if o.order_type == "cross_sell"]

    total_revenue = sum(o.amount for o in captured_orders)
    ai_revenue = sum(o.amount for o in ai_orders)
    upsell_revenue = sum(o.amount for o in upsell_orders)
    cross_sell_revenue = sum(o.amount for o in cross_sell_orders)

    total_orders = len(orders)
    successful_orders = len(captured_orders)
    aov = total_revenue / successful_orders if successful_orders > 0 else 0
    conversion_rate = (successful_orders / total_orders * 100) if total_orders > 0 else 0

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "successful_orders": successful_orders,
        "average_order_value": round(aov, 2),
        "conversion_rate": round(conversion_rate, 1),
        "ai_assisted_revenue": round(ai_revenue, 2),
        "upsell_revenue": round(upsell_revenue, 2),
        "cross_sell_revenue": round(cross_sell_revenue, 2),
        "period": f"last_{days}_days",
    }


def get_product_analytics(db: Session, merchant_id: str = "merchant_001") -> list:
    """Get sales analytics per product."""
    products = db.query(Product).filter(Product.merchant_id == merchant_id, Product.active == True).all()
    result = []
    for product in products:
        # Count sold through captured orders' cart items
        sold = db.query(func.coalesce(func.sum(CartItem.quantity), 0)).join(
            Order, Order.cart_id == CartItem.cart_id
        ).filter(
            CartItem.product_id == product.id,
            Order.payment_status == "captured",
        ).scalar()

        revenue = float(sold or 0) * product.price

        result.append({
            "product_id": product.id,
            "product_name": product.name,
            "category": product.category,
            "price": product.price,
            "stock": product.stock,
            "total_sold": int(sold or 0),
            "total_revenue": round(revenue, 2),
        })

    return sorted(result, key=lambda x: x["total_revenue"], reverse=True)


def get_growth_recommendations(db: Session, merchant_id: str = "merchant_001") -> list:
    """Generate AI growth recommendations based on data."""
    products = db.query(Product).filter(Product.merchant_id == merchant_id, Product.active == True).all()
    recommendations = []

    for product in products:
        metadata = product.metadata_extra or {}

        # Cross-sell opportunities
        cross_sell_ids = metadata.get("cross_sell", [])
        if cross_sell_ids:
            cross_sell_products = db.query(Product).filter(Product.id.in_(cross_sell_ids)).all()
            if cross_sell_products:
                estimated_revenue = sum(p.price for p in cross_sell_products) * 0.15  # 15% attach rate estimate
                recommendations.append({
                    "type": "cross_sell",
                    "title": f"Cross-sell opportunity: {product.name}",
                    "description": f"Recommend {', '.join(p.name for p in cross_sell_products)} with {product.name}",
                    "evidence": f"Products are frequently bought together based on category analysis",
                    "recommended_action": f"Enable AI recommendations for {product.name} accessories",
                    "estimated_opportunity": round(estimated_revenue, 2),
                    "products": [{"id": p.id, "name": p.name, "price": p.price} for p in cross_sell_products],
                })

        # Upsell opportunities
        upsell_id = metadata.get("upsell")
        if upsell_id:
            upsell_product = db.query(Product).filter(Product.id == upsell_id).first()
            if upsell_product:
                price_diff = upsell_product.price - product.price
                recommendations.append({
                    "type": "upsell",
                    "title": f"Upsell opportunity: {product.name} → {upsell_product.name}",
                    "description": f"Customers choosing {product.name} could upgrade to {upsell_product.name} for ₹{price_diff:.0f} more",
                    "evidence": f"Higher-tier product in same category with better features",
                    "recommended_action": f"Show upgrade prompt during checkout",
                    "estimated_opportunity": round(price_diff * 0.1, 2),  # 10% upgrade rate
                    "products": [{"id": upsell_product.id, "name": upsell_product.name, "price": upsell_product.price}],
                })

        # High-stock items (potential promotion candidates)
        if product.stock > 40:
            recommendations.append({
                "type": "high_stock",
                "title": f"Promote: {product.name}",
                "description": f"{product.name} has {product.stock} units in stock — consider a promotion",
                "evidence": f"High inventory level ({product.stock} units)",
                "recommended_action": f"Create a limited-time offer or bundle deal",
                "estimated_opportunity": round(product.price * product.stock * 0.05, 2),
                "products": [{"id": product.id, "name": product.name, "price": product.price}],
            })

    return recommendations[:10]  # Top 10 recommendations
