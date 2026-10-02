"""Dynamic Pricing Simulator API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import PricingSimulationRequest, PricingSimulationResponse
from app.services import pricing_simulator_service

router = APIRouter(prefix="/pricing", tags=["Dynamic Pricing Simulator"])


@router.post("/simulate", response_model=PricingSimulationResponse, summary="Simulate Dynamic Pricing")
def simulate_pricing(
    req: PricingSimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Simulates dynamic price elasticity based on inventory pressure and demand velocity.
    Strictly a simulation/proposal — live pricing is unchanged.
    """
    result = pricing_simulator_service.simulate_dynamic_price(
        db=db,
        product_id=req.product_id,
        merchant_id=req.merchant_id,
        competitor_price_adjustment=req.competitor_price_adjustment or 0.0,
        demand_multiplier=req.demand_multiplier or 1.0,
    )
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result.get("message", "Product not found"))
    return result
