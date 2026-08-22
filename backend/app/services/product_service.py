"""Product service — CRUD and search operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from app.models.product import Product
from app.schemas.schemas import ProductCreate, ProductUpdate
import re


def slugify(text: str) -> str:
    """Create URL-safe slug from text."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


def create_product(db: Session, data: ProductCreate) -> Product:
    """Create a new product."""
    product = Product(
        merchant_id=data.merchant_id,
        name=data.name,
        slug=slugify(data.name),
        description=data.description,
        category=data.category,
        price=data.price,
        currency=data.currency,
        stock=data.stock,
        active=data.active,
        image_url=data.image_url,
        tags=data.tags,
        metadata_extra=data.metadata_extra,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_product(db: Session, product_id: str) -> Optional[Product]:
    """Get a single product by ID."""
    return db.query(Product).filter(Product.id == product_id).first()


def get_products(db: Session, merchant_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Product]:
    """Get all products, optionally filtered by merchant."""
    q = db.query(Product).filter(Product.active == True)
    if merchant_id:
        q = q.filter(Product.merchant_id == merchant_id)
    return q.offset(skip).limit(limit).all()


def update_product(db: Session, product_id: str, data: ProductUpdate) -> Optional[Product]:
    """Update a product."""
    product = get_product(db, product_id)
    if not product:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: str) -> bool:
    """Soft-delete a product by setting active=False."""
    product = get_product(db, product_id)
    if not product:
        return False
    product.active = False
    db.commit()
    return True


def search_products(
    db: Session,
    query: Optional[str] = None,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
    color: Optional[str] = None,
    tags: Optional[List[str]] = None,
    merchant_id: str = "merchant_001",
) -> List[Product]:
    """Search products with filters — used by AI agent."""
    q = db.query(Product).filter(
        Product.active == True,
        Product.merchant_id == merchant_id,
    )

    if category:
        q = q.filter(func.lower(Product.category).contains(category.lower()))

    if max_price is not None:
        q = q.filter(Product.price <= max_price)

    if min_price is not None:
        q = q.filter(Product.price >= min_price)

    if query:
        # Strip common action words for natural language search
        stop_words = {"find", "search", "show", "me", "i", "want", "need", "looking", "for",
                       "a", "an", "the", "some", "get", "buy", "purchase", "under", "below",
                       "above", "over", "than", "with", "and", "or", "in", "of", "to"}
        words = [w for w in query.lower().split() if w not in stop_words and not w.startswith("₹") and not w.replace(".", "").isdigit()]

        if words:
            # Build OR conditions for each keyword
            keyword_conditions = []
            for word in words:
                term = f"%{word}%"
                keyword_conditions.append(
                    or_(
                        func.lower(Product.name).like(term),
                        func.lower(Product.description).like(term),
                        func.lower(Product.category).like(term),
                        func.lower(Product.tags).like(term),
                    )
                )
            q = q.filter(or_(*keyword_conditions))

    results = q.all()

    # Post-filter by color and tags (stored in JSON)
    if color:
        color_lower = color.lower()
        results = [
            p for p in results
            if color_lower in str(p.tags).lower()
            or color_lower in str(p.metadata_extra).lower()
            or color_lower in p.name.lower()
            or color_lower in p.description.lower()
        ]

    if tags:
        tags_lower = [t.lower() for t in tags]
        results = [
            p for p in results
            if any(t in [tag.lower() for tag in (p.tags or [])] for t in tags_lower)
        ]

    return results


def check_inventory(db: Session, product_id: str, quantity: int = 1) -> dict:
    """Check if a product has sufficient stock."""
    product = get_product(db, product_id)
    if not product:
        return {"available": False, "reason": "Product not found", "stock": 0}
    if not product.active:
        return {"available": False, "reason": "Product is not available", "stock": 0}
    if product.stock < quantity:
        return {
            "available": False,
            "reason": f"Insufficient stock. Available: {product.stock}, Requested: {quantity}",
            "stock": product.stock,
        }
    return {"available": True, "stock": product.stock, "reason": "In stock"}


def compare_products(db: Session, product_ids: List[str]) -> dict:
    """Compare multiple products side-by-side (Phase 7)."""
    products = db.query(Product).filter(Product.id.in_(product_ids), Product.active == True).all()
    if not products:
        return {"error": "No valid products found for comparison", "products": []}

    comparison_items = []
    for p in products:
        meta = p.metadata_extra or {}
        # Deterministic pro/con & suitability analysis
        pros = []
        cons = []
        suitability_score = 85

        if p.stock > 10:
            pros.append("High stock availability")
        else:
            cons.append("Limited quantity in stock")

        if p.price < 3000:
            pros.append("High value budget-friendly pricing")
            suitability_score += 5
        elif p.price > 10000:
            pros.append("Premium professional tier performance")

        if meta.get("colors"):
            pros.append(f"Available in multiple colors: {', '.join(meta['colors'])}")

        comparison_items.append({
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": p.price,
            "currency": p.currency,
            "stock": p.stock,
            "available": p.stock > 0,
            "tags": p.tags or [],
            "features": meta,
            "pros": pros,
            "cons": cons,
            "suitability_score": suitability_score,
            "image_url": p.image_url,
        })

    # Best recommendation pick
    best_product = max(comparison_items, key=lambda x: x["suitability_score"])

    return {
        "compared_count": len(comparison_items),
        "products": comparison_items,
        "recommendation": {
            "recommended_product_id": best_product["id"],
            "recommended_product_name": best_product["name"],
            "reason": f"Top suitability score ({best_product['suitability_score']}/100) based on pricing, features, and verified availability.",
        },
    }

