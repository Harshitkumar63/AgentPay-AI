"""Analytics API — revenue, product, Merchant AI Copilot, and growth center."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import analytics_service
from app.schemas.schemas import CopilotQueryRequest, CopilotQueryResponse

router = APIRouter()


@router.get("/analytics/revenue")
def get_revenue(
    merchant_id: str = "merchant_001",
    days: int = Query(default=30, le=365),
    db: Session = Depends(get_db),
):
    """Get real-time aggregated revenue analytics."""
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
    """Get AI growth recommendations with clear estimated vs actual distinctions."""
    return analytics_service.get_growth_recommendations(db, merchant_id=merchant_id)


@router.post("/analytics/copilot", response_model=CopilotQueryResponse)
def merchant_ai_copilot(req: CopilotQueryRequest, db: Session = Depends(get_db)):
    """Merchant AI Copilot (Phase 26) grounded in store database metrics."""
    return analytics_service.query_merchant_copilot(db, query=req.query, merchant_id=req.merchant_id)
