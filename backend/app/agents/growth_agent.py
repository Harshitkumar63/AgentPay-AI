"""Growth Agent — analyzes merchant data for revenue growth insights."""

from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services import analytics_service


def analyze_growth(db: Session, merchant_id: str = "merchant_001") -> Dict[str, Any]:
    """Run growth analysis and generate recommendations."""
    revenue = analytics_service.get_revenue_analytics(db, merchant_id)
    products = analytics_service.get_product_analytics(db, merchant_id)
    recommendations = analytics_service.get_growth_recommendations(db, merchant_id)

    return {
        "revenue_summary": revenue,
        "top_products": products[:5],
        "recommendations": recommendations,
        "insights": _generate_insights(revenue, products),
    }


def _generate_insights(revenue: dict, products: list) -> list:
    """Generate text insights from analytics data."""
    insights = []

    if revenue["total_orders"] > 0:
        insights.append({
            "type": "revenue",
            "text": f"Total revenue: ₹{revenue['total_revenue']:,.2f} from {revenue['total_orders']} orders",
            "metric": "revenue",
        })

    if revenue["ai_assisted_revenue"] > 0:
        ai_pct = (revenue["ai_assisted_revenue"] / max(revenue["total_revenue"], 1)) * 100
        insights.append({
            "type": "ai_impact",
            "text": f"AI-assisted revenue accounts for {ai_pct:.1f}% of total revenue",
            "metric": "ai_revenue",
        })

    if revenue["average_order_value"] > 0:
        insights.append({
            "type": "aov",
            "text": f"Average order value is ₹{revenue['average_order_value']:,.2f}. Cross-selling can increase this by 15-25%.",
            "metric": "aov",
        })

    # High-stock products
    high_stock = [p for p in products if p.get("stock", 0) > 30 and p.get("total_sold", 0) == 0]
    if high_stock:
        insights.append({
            "type": "opportunity",
            "text": f"{len(high_stock)} products have high stock but low sales — consider promotions",
            "metric": "inventory",
        })

    return insights
