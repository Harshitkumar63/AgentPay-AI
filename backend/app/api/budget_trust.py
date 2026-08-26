"""Agent Budget and Trust Score API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import budget_service, trust_service
from app.schemas.schemas import AgentBudgetRead, AgentBudgetUpdate, AgentTrustRead

router = APIRouter(prefix="/agent", tags=["Agent Budget & Trust Governance"])


@router.get("/budget", response_model=AgentBudgetRead, summary="Get Agent Spending Budget")
def get_agent_budget(
    agent_id: str = Query(default="default_agent"),
    merchant_id: str = Query(default="merchant_001"),
    db: Session = Depends(get_db),
):
    """Retrieve agent spending limits, daily budget, spent today, and remaining capacity."""
    budget = budget_service.get_or_create_budget(db, agent_id=agent_id, merchant_id=merchant_id)
    return budget


@router.put("/budget", response_model=AgentBudgetRead, summary="Update Agent Spending Budget")
def update_agent_budget(
    req: AgentBudgetUpdate,
    agent_id: str = Query(default="default_agent"),
    merchant_id: str = Query(default="merchant_001"),
    db: Session = Depends(get_db),
):
    """Update configured agent spending budget limits."""
    budget = budget_service.update_budget_limits(
        db=db,
        agent_id=agent_id,
        merchant_id=merchant_id,
        daily_limit=req.daily_limit,
        per_transaction_limit=req.per_transaction_limit,
    )
    return budget


@router.get("/trust", response_model=AgentTrustRead, summary="Get Agent Trust Score")
def get_agent_trust(
    agent_id: str = Query(default="default_agent"),
    db: Session = Depends(get_db),
):
    """Retrieve the server-calculated trust score and reliability signals for an agent."""
    trust = trust_service.get_or_create_trust(db, agent_id=agent_id)
    return trust
