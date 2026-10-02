"""AI Inventory Agent API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import InventoryIntelligenceResponse
from app.services import inventory_agent_service

router = APIRouter(prefix="/inventory", tags=["AI Inventory Agent"])


@router.get("/intelligence", response_model=InventoryIntelligenceResponse, summary="Get Inventory Risk Intelligence")
def get_inventory_intelligence(
    merchant_id: str = Query(default="merchant_001"),
    db: Session = Depends(get_db),
):
    """Retrieve stockout risk, overstock risk, days remaining, and automated supply chain recommendations."""
    return inventory_agent_service.get_inventory_intelligence(db, merchant_id=merchant_id)
