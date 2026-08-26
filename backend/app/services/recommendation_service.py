"""Recommendation Engine — Deterministic multi-factor scoring, upsell/cross-sell generation, and analytics tracking."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.product import Product
from app.models.recommendation_event import RecommendationEvent


def calculate_recommendation_score(
    product: Product,
    target_category: Optional[str] = None,
    budget_cap: Optional[float] = None,
    preferred_tags: Optional[List[str]] = None,
) -> int:
    """
    Deterministic scoring:
    Category Match: +35 pts
    Budget Fit: +25 pts
    Stock Availability: +20 pts
    Tag/Preference Fit: +10 pts
    Baseline Popularity: +10 pts
    """
    score = 10  # Baseline popularity score

    # Category match
    if target_category and product.category.lower() == target_category.lower():
        score += 35

    # Budget match
    if budget_cap is not None:
        if product.price <= budget_cap:
            score += 25
        elif product.price <= budget_cap * 1.15:
            score += 10
    else:
        score += 20

    # Stock availability
    if product.stock >= 20:
        score += 20
    elif product.stock > 0:
        score += 10

    # Tags / preferences
    if preferred_tags and product.tags:
        matches = len(set(product.tags) & set(preferred_tags))
        score += min(10, matches * 5)

    return min(100, score)


def get_recommendations(
    db: Session,
    product_id: str,
    recommendation_type: str = "cross_sell",
    merchant_id: str = "merchant_001",
    limit: int = 3,
) -> List[dict]:
    """Get algorithmic product recommendations with deterministic scoring."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return []

    metadata = product.metadata_extra or {}

    if recommendation_type == "cross_sell":
        return _get_cross_sell(db, product, metadata, limit)
    elif recommendation_type == "upsell":
        return _get_upsell(db, product, metadata, merchant_id, limit)
    elif recommendation_type == "similar":
        return _get_similar(db, product, merchant_id, limit)
    return []


def _get_cross_sell(db: Session, product: Product, metadata: dict, limit: int) -> List[dict]:
    """Get complementary cross-sell products."""
    cross_sell_ids = metadata.get("cross_sell", [])
    recommendations = []

    if cross_sell_ids:
        products = db.query(Product).filter(
            Product.id.in_(cross_sell_ids),
            Product.active == True,
            Product.stock > 0,
        ).limit(limit).all()

        for p in products:
            score = calculate_recommendation_score(p, target_category=p.category)
            recommendations.append({
                "product": _product_to_dict(p),
                "type": "cross_sell",
                "score": score,
                "reason": f"Frequently paired with {product.name} (Complementary accessory)",
            })

    return recommendations


def _get_upsell(db: Session, product: Product, metadata: dict, merchant_id: str, limit: int) -> List[dict]:
    """Get higher-value tier upsell products in the same category."""
    upsell_id = metadata.get("upsell")
    recommendations = []

    if upsell_id:
        upsell_product = db.query(Product).filter(
            Product.id == upsell_id,
            Product.active == True,
        ).first()
        if upsell_product:
            price_diff = upsell_product.price - product.price
            score = calculate_recommendation_score(upsell_product, target_category=product.category)
            recommendations.append({
                "product": _product_to_dict(upsell_product),
                "type": "upsell",
                "score": score,
                "reason": f"Upgrade to {upsell_product.name} for ₹{price_diff:,.0f} more (Enhanced specifications)",
                "price_difference": price_diff,
            })

    # Search for higher-priced active items in same category
    if len(recommendations) < limit:
        higher = db.query(Product).filter(
            Product.category == product.category,
            Product.price > product.price,
            Product.id != product.id,
            Product.active == True,
            Product.merchant_id == merchant_id,
        ).order_by(Product.price.asc()).limit(limit - len(recommendations)).all()

        for p in higher:
            if not any(r["product"]["id"] == p.id for r in recommendations):
                price_diff = p.price - product.price
                score = calculate_recommendation_score(p, target_category=product.category)
                recommendations.append({
                    "product": _product_to_dict(p),
                    "type": "upsell",
                    "score": score,
                    "reason": f"Premium option: {p.name} (+₹{price_diff:,.0f})",
                    "price_difference": price_diff,
                })

    return recommendations[:limit]


def _get_similar(db: Session, product: Product, merchant_id: str, limit: int) -> List[dict]:
    """Get similar products in the same category."""
    similar = db.query(Product).filter(
        Product.category == product.category,
        Product.id != product.id,
        Product.active == True,
        Product.merchant_id == merchant_id,
    ).limit(limit).all()

    return [
        {
            "product": _product_to_dict(p),
            "type": "similar",
            "score": calculate_recommendation_score(p, target_category=product.category),
            "reason": f"Alternative option in {product.category}",
        }
        for p in similar
    ]


def record_recommendation_event(
    db: Session,
    recommendation_type: str,  # recommendation, upsell, cross_sell
    event_type: str,  # shown, clicked, added, purchased
    recommended_product_id: str,
    source_product_id: Optional[str] = None,
    user_id: str = "demo_user",
    session_id: Optional[str] = None,
    order_id: Optional[str] = None,
    revenue_attributed: float = 0.0,
    merchant_id: str = "merchant_001",
) -> RecommendationEvent:
    """Record recommendation lifecycle event in the database."""
    evt = RecommendationEvent(
        merchant_id=merchant_id,
        recommendation_type=recommendation_type,
        event_type=event_type,
        source_product_id=source_product_id,
        recommended_product_id=recommended_product_id,
        user_id=user_id,
        session_id=session_id,
        order_id=order_id,
        revenue_attributed=revenue_attributed,
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt


def get_recommendation_analytics(
    db: Session,
    merchant_id: str = "merchant_001",
) -> Dict[str, Any]:
    """
    Compute recommendation, upsell, and cross-sell performance metrics from real database events.
    """
    def _compute_stats(rec_type: str):
        shown = db.query(RecommendationEvent).filter(
            RecommendationEvent.merchant_id == merchant_id,
            RecommendationEvent.recommendation_type == rec_type,
            RecommendationEvent.event_type == "shown",
        ).count()

        clicked = db.query(RecommendationEvent).filter(
            RecommendationEvent.merchant_id == merchant_id,
            RecommendationEvent.recommendation_type == rec_type,
            RecommendationEvent.event_type == "clicked",
        ).count()

        added = db.query(RecommendationEvent).filter(
            RecommendationEvent.merchant_id == merchant_id,
            RecommendationEvent.recommendation_type == rec_type,
            RecommendationEvent.event_type == "added",
        ).count()

        purchased = db.query(RecommendationEvent).filter(
            RecommendationEvent.merchant_id == merchant_id,
            RecommendationEvent.recommendation_type == rec_type,
            RecommendationEvent.event_type == "purchased",
        ).count()

        revenue = db.query(func.coalesce(func.sum(RecommendationEvent.revenue_attributed), 0.0)).filter(
            RecommendationEvent.merchant_id == merchant_id,
            RecommendationEvent.recommendation_type == rec_type,
            RecommendationEvent.event_type == "purchased",
        ).scalar() or 0.0

        ctr = (clicked / shown * 100) if shown > 0 else 0.0
        conversion = (purchased / clicked * 100) if clicked > 0 else 0.0

        return {
            "shown": shown,
            "clicked": clicked,
            "added": added,
            "purchased": purchased,
            "ctr": round(ctr, 1),
            "conversion_rate": round(conversion, 1),
            "revenue": round(float(revenue), 2),
        }

    return {
        "recommendations": _compute_stats("recommendation"),
        "upsell": _compute_stats("upsell"),
        "cross_sell": _compute_stats("cross_sell"),
    }


def _product_to_dict(product: Product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "price": product.price,
        "currency": product.currency,
        "stock": product.stock,
        "image_url": product.image_url,
        "tags": product.tags or [],
        "metadata": product.metadata_extra or {},
    }
