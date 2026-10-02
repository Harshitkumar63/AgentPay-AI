"""Agent Registry & Governance API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import AgentRead, AgentUpdate, AgentKillSwitchRequest, AgentSafetyResponse
from app.services import agent_registry_service, safety_certification_service

router = APIRouter(prefix="/agents", tags=["Multi-Agent Registry & Governance"])


@router.get("", response_model=List[AgentRead], summary="List Registered AI Agents")
def list_agents(db: Session = Depends(get_db)):
    """List all registered specialized agents (ShoppingBot, PaymentBot, GrowthBot, SupportBot, SecurityBot)."""
    return agent_registry_service.get_agents(db)


@router.get("/{agent_id}", response_model=AgentRead, summary="Get Agent Details")
def get_agent_details(agent_id: str, db: Session = Depends(get_db)):
    """Retrieve details, status, permissions, and circuit breaker health for a specific agent."""
    agent = agent_registry_service.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/{agent_id}/status", summary="Emergency Agent Kill Switch & Status Control")
def set_agent_status(
    agent_id: str,
    req: AgentKillSwitchRequest,
    db: Session = Depends(get_db),
):
    """Emergency kill switch: set agent status to ACTIVE, PAUSED, or DISABLED."""
    res = agent_registry_service.update_agent_status(
        db=db,
        agent_id=agent_id,
        status=req.status,
        reason=req.reason or "Merchant dashboard control",
    )
    if res.get("error"):
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.get("/{agent_id}/safety", response_model=AgentSafetyResponse, summary="Agent Safety Certification Report")
def get_agent_safety_certification(agent_id: str, db: Session = Depends(get_db)):
    """Execute 10 automated safety checks and return the Agent Safety Certification Score."""
    return safety_certification_service.run_agent_safety_certification(db, agent_id=agent_id)
