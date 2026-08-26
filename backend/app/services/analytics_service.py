"""Analytics service — Revenue attribution, recommendation analytics, Merchant AI Copilot, and AI Campaign Proposals."""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.order import Order
from app.models.product import Product
from app.models.cart import CartItem
from app.models.payment import Payment
from app.models.audit import AuditLog
from app.models.campaign import CampaignProposal
from app.services.recommendation_service import get_recommendation_analytics


def get_revenue_analytics(db: Session, merchant_id: str = "merchant_001", days: int = 30) -> dict:
    """Calculate revenue analytics for a merchant strictly from database records."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # All orders in period
    orders = db.query(Order).filter(
        Order.merchant_id == merchant_id,
        Order.created_at >= cutoff,
    ).all()

    captured_orders = [o for o in orders if o.payment_status == "captured"]
    failed_orders = [o for o in orders if o.payment_status == "failed"]
    ai_orders = [o for o in captured_orders if o.order_type in ("ai_assisted", "upsell", "cross_sell")]
    upsell_orders = [o for o in captured_orders if o.order_type == "upsell"]
    cross_sell_orders = [o for o in captured_orders if o.order_type == "cross_sell"]

    # Blocked actions count from audit logs
    blocked_count = db.query(AuditLog).filter(
        AuditLog.policy_result == "BLOCKED"
    ).count()

    total_revenue = sum(o.amount for o in captured_orders)
    ai_revenue = sum(o.amount for o in ai_orders)
    upsell_revenue = sum(o.amount for o in upsell_orders)
    cross_sell_revenue = sum(o.amount for o in cross_sell_orders)

    total_orders = len(orders)
    successful_orders = len(captured_orders)
    aov = total_revenue / successful_orders if successful_orders > 0 else 0.0
    conversion_rate = (successful_orders / total_orders * 100) if total_orders > 0 else 0.0

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "successful_orders": successful_orders,
        "average_order_value": round(aov, 2),
        "conversion_rate": round(conversion_rate, 1),
        "ai_assisted_revenue": round(ai_revenue, 2),
        "upsell_revenue": round(upsell_revenue, 2),
        "cross_sell_revenue": round(cross_sell_revenue, 2),
        "failed_payments_count": len(failed_orders),
        "blocked_actions_count": blocked_count,
        "period": f"last_{days}_days",
    }


def get_product_analytics(db: Session, merchant_id: str = "merchant_001") -> list:
    """Get sales analytics per product with real aggregated totals."""
    products = db.query(Product).filter(Product.merchant_id == merchant_id, Product.active == True).all()
    result = []
    for product in products:
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


def get_growth_opportunities(db: Session, merchant_id: str = "merchant_001") -> list:
    """
    Generate AI growth opportunities with explicit separation between
    ACTUAL REVENUE and ESTIMATED OPPORTUNITY.
    """
    products = db.query(Product).filter(Product.merchant_id == merchant_id, Product.active == True).all()
    opportunities = []

    for product in products:
        metadata = product.metadata_extra or {}

        # Cross-sell opportunity
        cross_sell_ids = metadata.get("cross_sell", [])
        if cross_sell_ids:
            cross_sell_products = db.query(Product).filter(Product.id.in_(cross_sell_ids)).all()
            if cross_sell_products:
                estimated_opp = sum(p.price for p in cross_sell_products) * 0.18
                opportunities.append({
                    "type": "cross_sell",
                    "title": f"Cross-sell Bundle: {product.name}",
                    "description": f"Recommend {', '.join(p.name for p in cross_sell_products)} with {product.name}",
                    "evidence": "High catalog affinity based on co-purchase accessories tags",
                    "recommended_action": f"Show one-click cross-sell add-on during shopping agent discovery",
                    "estimated_opportunity": round(estimated_opp, 2),
                    "actual_revenue_to_date": 0.0,
                    "products": [{"id": p.id, "name": p.name, "price": p.price} for p in cross_sell_products],
                })

        # Upsell opportunity
        upsell_id = metadata.get("upsell")
        if upsell_id:
            upsell_product = db.query(Product).filter(Product.id == upsell_id).first()
            if upsell_product:
                price_diff = upsell_product.price - product.price
                opportunities.append({
                    "type": "upsell",
                    "title": f"Tier Upgrade: {product.name} → {upsell_product.name}",
                    "description": f"Users viewing {product.name} can upgrade to {upsell_product.name} (+₹{price_diff:,.0f})",
                    "evidence": "Higher tier product in same category with superior margin",
                    "recommended_action": "Present tier upgrade comparison card in AI shopping recommendations",
                    "estimated_opportunity": round(price_diff * 0.15, 2),
                    "actual_revenue_to_date": 0.0,
                    "products": [{"id": upsell_product.id, "name": upsell_product.name, "price": upsell_product.price}],
                })

        # High inventory promotion opportunity
        if product.stock >= 25:
            est_campaign = round(product.price * product.stock * 0.12, 2)
            opportunities.append({
                "type": "high_stock",
                "title": f"Inventory Acceleration: {product.name}",
                "description": f"{product.name} has {product.stock} units in stock — ideal for targeted promotional campaign",
                "evidence": f"Stock level ({product.stock} units) exceeds normal rotation velocity",
                "recommended_action": "Propose an AI Flash Promotion campaign with 10% discount",
                "estimated_opportunity": est_campaign,
                "actual_revenue_to_date": 0.0,
                "products": [{"id": product.id, "name": product.name, "price": product.price}],
            })

    return opportunities[:10]


# Alias for backward compatibility
get_growth_recommendations = get_growth_opportunities



def query_merchant_copilot(db: Session, query: str, merchant_id: str = "merchant_001") -> Dict[str, Any]:
    """
    Merchant AI Copilot (Phase 29):
    Answers merchant inquiries grounded in real database analytics.
    """
    revenue = get_revenue_analytics(db, merchant_id)
    product_stats = get_product_analytics(db, merchant_id)
    growth_opps = get_growth_opportunities(db, merchant_id)
    rec_analytics = get_recommendation_analytics(db, merchant_id)

    q = query.lower()
    answer_parts = []
    actions = []
    proposed_campaign = None

    if "revenue" in q or "fall" in q or "drop" in q or "why" in q:
        answer_parts.append(
            f"Based on real store performance over the last 30 days, total revenue is ₹{revenue['total_revenue']:,.2f} "
            f"across {revenue['successful_orders']} captured orders (AOV: ₹{revenue['average_order_value']:,.2f}, Conversion: {revenue['conversion_rate']}%)."
        )
        if revenue["ai_assisted_revenue"] > 0:
            pct = (revenue["ai_assisted_revenue"] / max(revenue["total_revenue"], 1)) * 100
            answer_parts.append(f"AI-assisted transactions account for ₹{revenue['ai_assisted_revenue']:,.2f} ({pct:.1f}% of total).")
        else:
            answer_parts.append("AI-assisted checkout hasn't been active yet; activating AI discovery in AI Shop can lift conversions.")

        if revenue["failed_payments_count"] > 0:
            answer_parts.append(f"There were {revenue['failed_payments_count']} failed payment attempts recorded.")

        actions.extend([
            "Enable cross-selling widgets on top-selling products",
            "Review failed payment records in Webhook Monitor",
            "Deploy AI Campaign Proposal for high-stock products",
        ])

    elif "promote" in q or "product" in q or "traffic" in q:
        high_stock = [p for p in product_stats if p["stock"] >= 20]
        if high_stock:
            top = high_stock[0]
            answer_parts.append(
                f"We recommend promoting **{top['product_name']}** (Stock: {top['stock']} units, Price: ₹{top['price']:,.2f}). "
                f"It has high inventory availability and strong margin potential."
            )
            proposed_campaign = {
                "id": f"camp_{top['product_id']}",
                "title": f"Flash Promotion: {top['product_name']}",
                "product_id": top["product_id"],
                "product_name": top["product_name"],
                "target_audience": f"Recent viewers of {top['category']}",
                "discount_percentage": 10.0,
                "budget": 1500.0,
                "duration_days": 3,
                "estimated_opportunity": round(top["price"] * 10 * 0.15, 2),
                "risk_level": "HIGH",
                "status": "proposed",
            }
            actions.append(f"Review and approve Campaign for {top['product_name']}")
        else:
            answer_parts.append("Inventory is evenly distributed across categories. Focus on cross-selling accessories with core electronics and shoes.")

    elif "cross-sell" in q or "upsell" in q:
        cs = rec_analytics.get("cross_sell", {})
        up = rec_analytics.get("upsell", {})
        answer_parts.append(
            f"Cross-sell metrics: {cs.get('purchased', 0)} purchases generated ₹{cs.get('revenue', 0):,.2f} (CTR: {cs.get('ctr', 0)}%). "
            f"Upsell metrics: {up.get('purchased', 0)} purchases generated ₹{up.get('revenue', 0):,.2f}."
        )
        actions.extend([
            "Review AI Growth Center opportunities",
            "Pair Running Shoes with Running Socks",
            "Pair SwiftBook Laptop with Laptop Sleeve and Wireless Mouse",
        ])

    else:
        answer_parts.append(
            f"Merchant Store Overview: ₹{revenue['total_revenue']:,.2f} total revenue across {revenue['successful_orders']} captured orders, "
            f"{len(growth_opps)} active AI growth opportunities detected."
        )
        actions.extend([
            "Review AI Growth Center opportunities",
            "Test Policy limits with Policy Simulator",
            "Inspect Agent Trace for customer shopping sessions",
        ])

    return {
        "answer": " ".join(answer_parts),
        "metrics_used": revenue,
        "suggested_actions": actions,
        "proposed_campaign": proposed_campaign,
    }


def create_campaign_proposal(
    db: Session,
    product_id: str,
    title: str,
    discount_percentage: float = 10.0,
    budget: float = 1500.0,
    duration_days: int = 3,
    target_audience: str = "All Store Visitors",
    merchant_id: str = "merchant_001",
) -> CampaignProposal:
    """Create a new AI-generated campaign proposal (Phase 30)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    product_name = product.name if product else "Target Product"
    est_opp = (product.price * 10 * 0.15) if product else 2500.0

    proposal = CampaignProposal(
        merchant_id=merchant_id,
        product_id=product_id,
        product_name=product_name,
        title=title,
        description=f"AI proposed {discount_percentage}% discount campaign for {product_name} targeting {target_audience}.",
        target_audience=target_audience,
        discount_percentage=discount_percentage,
        budget=budget,
        duration_days=duration_days,
        estimated_opportunity=est_opp,
        evidence=f"Product has high inventory velocity potential with {product.stock if product else 0} units in stock.",
        status="proposed",
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


def list_campaign_proposals(
    db: Session,
    merchant_id: str = "merchant_001",
) -> List[CampaignProposal]:
    """List all campaign proposals."""
    return db.query(CampaignProposal).filter(CampaignProposal.merchant_id == merchant_id).order_by(CampaignProposal.created_at.desc()).all()


def activate_campaign_proposal(
    db: Session,
    proposal_id: str,
    approved_by: str = "merchant_admin",
) -> Dict[str, Any]:
    """Approve and activate a campaign proposal."""
    prop = db.query(CampaignProposal).filter(CampaignProposal.id == proposal_id).first()
    if not prop:
        return {"error": True, "message": "Campaign proposal not found"}

    prop.status = "active"
    prop.activated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(prop)

    return {
        "success": True,
        "campaign_id": prop.id,
        "status": "active",
        "message": f"Campaign '{prop.title}' has been approved and activated.",
    }
