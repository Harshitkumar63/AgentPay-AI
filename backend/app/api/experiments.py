"""AI A/B Testing & Experimentation API (Part 24)."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import ExperimentRead, ExperimentCreate
from app.services import ab_testing_service

router = APIRouter(prefix="/experiments", tags=["AI A/B Testing"])


@router.get("", response_model=List[ExperimentRead], summary="List A/B Experiments")
def list_experiments(
    merchant_id: str = Query(default="merchant_001"),
    db: Session = Depends(get_db),
):
    """List all active and completed A/B pricing experiments with statistical variant metrics."""
    return ab_testing_service.get_experiments(db, merchant_id=merchant_id)


@router.post("", response_model=ExperimentRead, summary="Create A/B Experiment")
def create_experiment(
    req: ExperimentCreate,
    db: Session = Depends(get_db),
):
    """Launch a new controlled A/B pricing test."""
    return ab_testing_service.create_experiment(
        db=db,
        product_id=req.product_id,
        name=req.name,
        hypothesis=req.hypothesis,
        variant_a_price=req.variant_a_price,
        variant_b_price=req.variant_b_price,
        merchant_id=req.merchant_id,
    )
