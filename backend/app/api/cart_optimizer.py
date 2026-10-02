"""Cart Optimizer API (Part 22)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import CartOptimizerRequest, CartOptimizerResponse, ApplyOptimizationRequest
from app.services import cart_optimizer_service

router = APIRouter(prefix="/cart-optimizer", tags=["Cart Optimizer"])


@router.post("/optimize", response_model=CartOptimizerResponse, summary="Propose Cart Optimization")
def optimize_cart(
    req: CartOptimizerRequest,
    db: Session = Depends(get_db),
):
    """
    Generates optimization proposals for the specified strategy (MINIMUM_PRICE, BEST_VALUE, BEST_QUALITY, MAXIMUM_SAVING).
    Changes are not applied until confirmed.
    """
    res = cart_optimizer_service.optimize_cart(db, cart_id=req.cart_id, mode=req.mode)
    if res.get("error"):
        raise HTTPException(status_code=400, detail=res.get("message", "Could not optimize cart"))
    return res


@router.post("/apply", summary="Apply Cart Optimization")
def apply_optimization(
    req: ApplyOptimizationRequest,
    db: Session = Depends(get_db),
):
    """Applies the approved optimization strategy to the user's active cart."""
    res = cart_optimizer_service.apply_cart_optimization(db, cart_id=req.cart_id, mode=req.mode)
    if res.get("error"):
        raise HTTPException(status_code=400, detail=res.get("message", "Failed to apply optimization"))
    return res
