"""Customer Support Agent API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import SupportQueryRequest, SupportQueryResponse
from app.services import support_agent_service

router = APIRouter(prefix="/support", tags=["Customer Support Agent"])


@router.post("/query", response_model=SupportQueryResponse, summary="Query Customer Support Agent")
def query_support_agent(
    req: SupportQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Submits inquiry to Customer Support Agent.
    Grounded in real database order, payment, and refund records without hallucination.
    """
    return support_agent_service.handle_support_query(
        db=db,
        query=req.query,
        user_id=req.user_id,
        order_id=req.order_id,
        merchant_id=req.merchant_id,
    )
