"""Admin System Controls & Global Kill Switch API (Phase 4)."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.system_control_service import system_control_service

router = APIRouter(prefix="/admin/system", tags=["Admin System Controls"])


@router.get("/status", summary="Get System Operational & Kill Switch Status")
def get_system_status():
    """Retrieve global kill switch and module enable/disable statuses."""
    return system_control_service.get_status()


@router.post("/pause", summary="Emergency Global Freeze (All Writes & Payments)")
def pause_all(
    reason: str = Query(default="Emergency global freeze initiated by administrator"),
    actor_id: str = Query(default="admin"),
    db: Session = Depends(get_db),
):
    """Emergency shutdown: freezes all financial operations, order writes, and agent executions."""
    return system_control_service.pause_all(db=db, reason=reason, actor_id=actor_id)


@router.post("/resume", summary="Resume All Normal System Operations")
def resume_all(
    reason: str = Query(default="System resumed normal operations"),
    actor_id: str = Query(default="admin"),
    db: Session = Depends(get_db),
):
    """Resume all normal operations across payments, orders, and agents."""
    return system_control_service.resume_all(db=db, reason=reason, actor_id=actor_id)


@router.post("/pause-payments", summary="Pause Financial Payments & Checkouts")
def pause_payments(
    reason: str = Query(default="Payment processing paused for maintenance"),
    actor_id: str = Query(default="admin"),
    db: Session = Depends(get_db),
):
    """Pauses payment and order creation while keeping catalog read, search, and analytics active."""
    return system_control_service.pause_payments(db=db, reason=reason, actor_id=actor_id)


@router.post("/pause-agents", summary="Pause Autonomous AI Agent Execution")
def pause_agents(
    reason: str = Query(default="Autonomous AI agent executions paused"),
    actor_id: str = Query(default="admin"),
    db: Session = Depends(get_db),
):
    """Pauses autonomous agent executions while human operations remain active."""
    return system_control_service.pause_agents(db=db, reason=reason, actor_id=actor_id)
