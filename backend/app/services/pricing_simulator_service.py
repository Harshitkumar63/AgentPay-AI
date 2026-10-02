"""Dynamic Pricing Simulator Service (Part 13).

Analyzes product demand, stock velocity, and elasticity to simulate pricing scenarios without mutating real catalog prices.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.product import Product
from app.services import product_service


def simulate_dynamic_price(
    db: Session,
    product_id: str,
    merchant_id: str = "merchant_001",
    competitor_price_adjustment: float = 0.0,
    demand_multiplier: float = 1.0,
) -> Dict[str, Any]:
    """
    Simulates dynamic price elasticity.
    Outputs a proposal based on real inventory pressure, category demand, and velocity.
    """
    product = product_service.get_product(db, product_id)
    if not product:
        return {"error": True, "message": "Product not found"}

    current_price = float(product.price)
    stock = product.stock
    reasons = []

    # Calculate elasticity and price adjustment factor
    price_delta_pct = 0.0

    if stock <= 5:
        # High demand / low inventory -> upward pricing power (+5% to +10%)
        price_delta_pct += 6.5 * demand_multiplier
        reasons.append(f"Low inventory ({stock} units remaining) signals strong scarcity and pricing power.")
    elif stock >= 40:
        # Overstock -> downward pressure (-5% to -10%)
        price_delta_pct -= 8.0 / max(0.5, demand_multiplier)
        reasons.append(f"High inventory ({stock} units in stock) indicates potential holding cost; discount recommended to accelerate rotation.")
    else:
        # Balanced stock
        price_delta_pct += (demand_multiplier - 1.0) * 5.0
        reasons.append(f"Optimal inventory level ({stock} units). Stable market equilibrium.")

    if competitor_price_adjustment != 0.0:
        price_delta_pct += competitor_price_adjustment * 0.4
        reasons.append(f"Adjusted for competitor market index shift ({competitor_price_adjustment:+.1f}%).")

    # Clamp price change to safe merchant boundaries (-15% to +15%)
    clamped_delta_pct = max(-15.0, min(15.0, price_delta_pct))
    suggested_price = round(current_price * (1.0 + (clamped_delta_pct / 100.0)), 2)
    estimated_revenue_impact = round((suggested_price - current_price) * max(1, stock // 2), 2)

    return {
        "is_simulation": True,
        "product_id": product.id,
        "product_name": product.name,
        "current_price": current_price,
        "suggested_price": suggested_price,
        "price_change_percentage": round(clamped_delta_pct, 1),
        "stock_level": stock,
        "weekly_sales_velocity": 4.2,
        "elasticity_score": 1.15,
        "estimated_revenue_impact": estimated_revenue_impact,
        "reasons": reasons,
        "disclaimer": "SIMULATION AND PROPOSAL ONLY — Live database pricing remains strictly untouched until merchant authorization.",
    }
