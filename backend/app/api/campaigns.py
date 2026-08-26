"""Campaign Proposals API — AI Campaign Builder and merchant activation flow."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import analytics_service

router = APIRouter(prefix="/campaigns", tags=["AI Campaign Builder"])


class CreateCampaignRequest(BaseModel):
    product_id: str
    title: str
    discount_percentage: float = 10.0
    budget: float = 1500.0
    duration_days: int = 3
    target_audience: str = "All Store Visitors"
    merchant_id: str = "merchant_001"


@router.get("", summary="List AI Campaign Proposals")
def list_campaigns(
    merchant_id: str = Query(default="merchant_001"),
    db: Session = Depends(get_db),
):
    """List proposed and active growth campaigns."""
    return analytics_service.list_campaigns(db, merchant_id=merchant_id) if hasattr(analytics_service, 'list_campaigns') else analytics_service.list_campaign_proposals(db, merchant_id=merchant_id)


@router.post("/propose", summary="Propose New AI Campaign")
def propose_campaign(
    req: CreateCampaignRequest,
    db: Session = Depends(get_db),
):
    """Generate or submit an AI Campaign proposal."""
    proposal = analytics_service.create_campaign_proposal(
        db=db,
        product_id=req.product_id,
        title=req.title,
        discount_percentage=req.discount_percentage,
        budget=req.budget,
        duration_days=req.duration_days,
        target_audience=req.target_audience,
        merchant_id=req.merchant_id,
    )
    return proposal


@router.post("/{campaign_id}/activate", summary="Activate AI Campaign")
def activate_campaign(
    campaign_id: str,
    approved_by: str = Query(default="merchant_admin"),
    db: Session = Depends(get_db),
):
    """Authorize and activate a proposed marketing campaign."""
    result = analytics_service.activate_campaign_proposal(
        db=db,
        proposal_id=campaign_id,
        approved_by=approved_by,
    )
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result
