"""Controlled AI Negotiation API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import NegotiationProposalRequest, NegotiationProposalResponse
from app.services import negotiation_service

router = APIRouter(prefix="/negotiation", tags=["AI Negotiation Engine"])


@router.post("/propose", response_model=NegotiationProposalResponse, summary="Propose Price Negotiation")
def propose_negotiation(
    req: NegotiationProposalRequest,
    db: Session = Depends(get_db),
):
    """
    Submits a price offer proposal. The backend validates against merchant discount policy and profit margins.
    Returns the transparent breakdown and final offer.
    """
    result = negotiation_service.propose_negotiation_offer(
        db=db,
        product_id=req.product_id,
        requested_price=req.requested_price,
        merchant_id=req.merchant_id,
        agent_id=req.agent_id,
    )
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("message", "Negotiation rejected"))
    return result
