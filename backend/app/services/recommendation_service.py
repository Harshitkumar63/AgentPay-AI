"""Recommendation service — cross-sell, upsell, and similar product logic."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.product import Product


def get_recommendations(
    db: Session,
    product_id: str,
    recommendation_type: str = "cross_sell",
    merchant_id: str = "merchant_001",
    limit: int = 3,
) -> List[dict]:
    """
    Get product recommendations based on type.
    Uses metadata_extra cross_sell/upsell fields and category matching.
    """
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
    """Get cross-sell recommendations from metadata relationships."""
    cross_sell_ids = metadata.get("cross_sell", [])
    recommendations = []

    if cross_sell_ids:
        products = db.query(Product).filter(
            Product.id.in_(cross_sell_ids),
            Product.active == True,
            Product.stock > 0,
        ).limit(limit).all()

        for p in products:
            recommendations.append({
                "product": _product_to_dict(p),
                "type": "cross_sell",
                "reason": f"Frequently bought together with {product.name}",
            })

    return recommendations


def _get_upsell(db: Session, product: Product, metadata: dict, merchant_id: str, limit: int) -> List[dict]:
    """Get upsell recommendations — higher-priced products in same category."""
    upsell_id = metadata.get("upsell")
    recommendations = []

    if upsell_id:
        upsell_product = db.query(Product).filter(
            Product.id == upsell_id,
            Product.active == True,
        ).first()
        if upsell_product:
            price_diff = upsell_product.price - product.price
            recommendations.append({
                "product": _product_to_dict(upsell_product),
                "type": "upsell",
                "reason": f"For ₹{price_diff:.0f} more, get {upsell_product.name} with premium features",
                "price_difference": price_diff,
            })

    # Also find higher-priced products in same category
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
                recommendations.append({
                    "product": _product_to_dict(p),
                    "type": "upsell",
                    "reason": f"Upgrade to {p.name} for ₹{price_diff:.0f} more with better features",
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
            "reason": f"Similar {product.category} product",
        }
        for p in similar
    ]


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
    }
