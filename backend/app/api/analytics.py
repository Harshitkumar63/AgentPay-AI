"""Analytics API — revenue, product, and growth analytics."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import analytics_service

router = APIRouter()


@router.get("/analytics/revenue")
def get_revenue(
    merchant_id: str = "merchant_001",
    days: int = Query(default=30, le=365),
    db: Session = Depends(get_db),
):
    """Get revenue analytics."""
    return analytics_service.get_revenue_analytics(db, merchant_id=merchant_id, days=days)


@router.get("/analytics/products")
def get_product_analytics(
    merchant_id: str = "merchant_001",
    db: Session = Depends(get_db),
):
    """Get product sales analytics."""
    return analytics_service.get_product_analytics(db, merchant_id=merchant_id)


@router.get("/analytics/ai")
def get_ai_analytics(
    merchant_id: str = "merchant_001",
    db: Session = Depends(get_db),
):
    """Get AI growth recommendations."""
    return analytics_service.get_growth_recommendations(db, merchant_id=merchant_id)
