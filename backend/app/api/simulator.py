"""What-If Business Simulator API (Part 23)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import BusinessSimulationRequest, BusinessSimulationResponse
from app.services import simulation_service

router = APIRouter(prefix="/simulator", tags=["What-If Business Simulator"])


@router.post("/what-if", response_model=BusinessSimulationResponse, summary="Run What-If Scenario Simulation")
def simulate_what_if(
    req: BusinessSimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Simulates the projected impact of discount depths, inventory replenishment, and price adjustments.
    Data is strictly labeled as a simulation estimate.
    """
    return simulation_service.run_what_if_simulation(
        db=db,
        merchant_id=req.merchant_id,
        discount_percentage=req.discount_percentage,
        inventory_increase_percentage=req.inventory_increase_percentage,
        price_adjustment_percentage=req.price_adjustment_percentage,
        promoted_category=req.promoted_category,
    )
