"""Products API — CRUD and AI-readable catalog endpoints."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import ProductCreate, ProductUpdate, ProductRead, CatalogProduct, CatalogResponse
from app.services import product_service
from app.models.merchant import Merchant

router = APIRouter()


@router.get("/products", response_model=List[ProductRead])
def list_products(
    merchant_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all active products."""
    return product_service.get_products(db, merchant_id=merchant_id, skip=skip, limit=limit)


@router.post("/products", response_model=ProductRead, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product."""
    return product_service.create_product(db, data)


@router.get("/products/{product_id}", response_model=ProductRead)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """Get product by ID."""
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Product not found"}})
    return product


@router.put("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: str, data: ProductUpdate, db: Session = Depends(get_db)):
    """Update a product."""
    product = product_service.update_product(db, product_id, data)
    if not product:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Product not found"}})
    return product


@router.delete("/products/{product_id}")
def delete_product(product_id: str, db: Session = Depends(get_db)):
    """Soft-delete a product."""
    success = product_service.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Product not found"}})
    return {"message": "Product deleted"}


# ── AI-Readable Catalog ──────────────────────────────────

@router.get("/agent/catalog")
def get_catalog(merchant_id: str = "merchant_001", db: Session = Depends(get_db)):
    """
    AI-readable product catalog.
    Optimized for consumption by AI agents and external AI buyers.
    """
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    products = product_service.get_products(db, merchant_id=merchant_id)

    catalog_products = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "category": p.category,
            "price": p.price,
            "currency": p.currency,
            "availability": p.stock > 0 and p.active,
            "stock": p.stock,
            "tags": p.tags or [],
            "purchase_allowed": p.active and p.stock > 0,
            "metadata": p.metadata_extra or {},
        }
        for p in products
    ]

    return {
        "merchant": {
            "id": merchant.id,
            "name": merchant.name,
            "currency": merchant.currency,
            "description": merchant.description,
        },
        "products": catalog_products,
        "total_products": len(catalog_products),
    }


@router.get("/agent/catalog/{product_id}")
def get_catalog_product(product_id: str, db: Session = Depends(get_db)):
    """Get single product in AI-readable format."""
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "price": product.price,
        "currency": product.currency,
        "availability": product.stock > 0 and product.active,
        "stock": product.stock,
        "tags": product.tags or [],
        "purchase_allowed": product.active and product.stock > 0,
        "metadata": product.metadata_extra or {},
    }
