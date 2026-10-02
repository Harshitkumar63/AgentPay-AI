"""Admin Agent Management Endpoints (Phase 2 & 25)."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import agent_registry_service
from app.models.agent import Agent

router = APIRouter(prefix="/admin/agents", tags=["Admin Agent Registry"])


class AgentCreateRequest(BaseModel):
    name: str = Field(..., example="Autonomous Shopping Agent")
    description: str = Field("", example="Searches catalog and negotiates discounts")
    role: str = Field("shopping", example="shopping")
    owner: str = Field("admin", example="admin")
    permissions: Optional[List[str]] = Field(default=None, example=["catalog.read", "product.search", "cart.write", "checkout.request"])
    daily_budget: float = Field(10000.0, example=10000.0)
    transaction_limit: float = Field(5000.0, example=5000.0)
    metadata_extra: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    permissions: Optional[List[str]] = None
    daily_budget: Optional[float] = None
    transaction_limit: Optional[float] = None
    metadata_extra: Optional[Dict[str, Any]] = None


class AgentDetailResponse(BaseModel):
    id: str
    agent_id: str
    name: str
    description: str
    role: str
    owner: str
    status: str
    permissions: List[str]
    daily_budget: float
    per_transaction_limit: float
    transaction_limit: float
    hourly_limit: float
    trust_score: int
    risk_level: str
    circuit_breaker_state: Optional[str] = "CLOSED"
    circuit_breaker_tripped: bool = False
    api_key_prefix: Optional[str] = None
    created_at: str
    updated_at: str
    last_activity: str


@router.post("", summary="Register New Agent & Issue API Key")
def register_agent(req: AgentCreateRequest, db: Session = Depends(get_db)):
    """
    Registers an external or internal agent in the registry and generates an API key.
    The raw API key is returned ONLY once in this response and hashed in the database.
    """
    result = agent_registry_service.create_agent(
        db=db,
        name=req.name,
        description=req.description,
        role=req.role,
        owner=req.owner,
        permissions=req.permissions,
        daily_budget=req.daily_budget,
        transaction_limit=req.transaction_limit,
        metadata_extra=req.metadata_extra,
    )
    agent = result["agent"]
    return {
        "success": True,
        "agent": {
            "id": agent.id,
            "agent_id": agent.id,
            "name": agent.name,
            "role": agent.role,
            "status": agent.status,
            "permissions": agent.permissions,
            "daily_budget": agent.daily_budget,
            "transaction_limit": agent.transaction_limit,
            "api_key_prefix": agent.api_key_prefix,
            "created_at": str(agent.created_at),
        },
        "api_key": result["api_key"],
        "message": result["message"],
    }


@router.get("", summary="List All Registered Agents")
def list_agents(db: Session = Depends(get_db)):
    """Retrieve all agents in the registry with governance limits and status."""
    agents = agent_registry_service.get_agents(db)
    return [
        {
            "id": a.id,
            "agent_id": a.id,
            "name": a.name,
            "description": a.description,
            "role": a.role,
            "owner": a.owner,
            "status": a.status,
            "permissions": a.permissions,
            "daily_budget": a.daily_budget,
            "per_transaction_limit": a.per_transaction_limit,
            "transaction_limit": a.transaction_limit,
            "trust_score": a.trust_score,
            "risk_level": a.risk_level,
            "circuit_breaker_state": a.circuit_breaker_state or "CLOSED",
            "circuit_breaker_tripped": a.circuit_breaker_tripped,
            "api_key_prefix": a.api_key_prefix,
            "created_at": str(a.created_at),
            "updated_at": str(a.updated_at),
            "last_activity": str(a.last_activity),
        }
        for a in agents
    ]


@router.get("/{agent_id}", summary="Get Detailed Agent Profile")
def get_agent_profile(agent_id: str, db: Session = Depends(get_db)):
    """Retrieve full profile, permissions, trust metrics, and circuit breaker status."""
    agent = agent_registry_service.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "id": agent.id,
        "agent_id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "role": agent.role,
        "owner": agent.owner,
        "status": agent.status,
        "permissions": agent.permissions,
        "daily_budget": agent.daily_budget,
        "per_transaction_limit": agent.per_transaction_limit,
        "transaction_limit": agent.transaction_limit,
        "hourly_limit": agent.hourly_limit,
        "trust_score": agent.trust_score,
        "risk_level": agent.risk_level,
        "circuit_breaker_state": agent.circuit_breaker_state or "CLOSED",
        "circuit_breaker_tripped": agent.circuit_breaker_tripped,
        "circuit_breaker_reason": agent.circuit_breaker_reason,
        "api_key_prefix": agent.api_key_prefix,
        "metadata_extra": agent.metadata_extra or {},
        "created_at": str(agent.created_at),
        "updated_at": str(agent.updated_at),
        "last_activity": str(agent.last_activity),
    }


@router.patch("/{agent_id}", summary="Update Agent Configuration & Permissions")
def update_agent_profile(
    agent_id: str,
    req: AgentUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update permissions, budgets, or metadata for an agent."""
    agent = agent_registry_service.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if req.name is not None:
        agent.name = req.name
    if req.description is not None:
        agent.description = req.description
    if req.role is not None:
        agent.role = req.role
    if req.status is not None:
        agent.status = req.status.upper()
    if req.permissions is not None:
        agent.permissions = req.permissions
    if req.daily_budget is not None:
        agent.daily_budget = req.daily_budget
    if req.transaction_limit is not None:
        agent.per_transaction_limit = req.transaction_limit
    if req.metadata_extra is not None:
        agent.metadata_extra = req.metadata_extra

    db.commit()
    db.refresh(agent)

    return {
        "success": True,
        "agent_id": agent.id,
        "message": f"Agent '{agent.name}' updated successfully.",
    }


@router.post("/{agent_id}/rotate-key", summary="Rotate Agent API Key")
def rotate_key(agent_id: str, db: Session = Depends(get_db)):
    """Generate a new secure API key and invalidate previous key hash."""
    res = agent_registry_service.rotate_agent_key(db, agent_id)
    if res.get("error"):
        raise HTTPException(status_code=404, detail=res["message"])
    return res


@router.post("/{agent_id}/pause", summary="Pause Agent Operations")
def pause_agent(
    agent_id: str,
    reason: str = Query(default="Merchant requested pause"),
    db: Session = Depends(get_db),
):
    """Emergency pause: immediately halts agent financial operations."""
    return agent_registry_service.update_agent_status(db, agent_id, "PAUSED", reason)


@router.post("/{agent_id}/resume", summary="Resume Agent Operations")
def resume_agent(
    agent_id: str,
    reason: str = Query(default="Merchant resumed agent"),
    db: Session = Depends(get_db),
):
    """Resume agent normal operational status."""
    return agent_registry_service.update_agent_status(db, agent_id, "ACTIVE", reason)
