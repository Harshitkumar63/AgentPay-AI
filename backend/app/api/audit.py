"""Audit API — audit log viewing."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import AuditLogRead, AgentActionRead
from app.services import audit_service

router = APIRouter()


@router.get("/audit", response_model=List[AuditLogRead])
def list_audit_logs(
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """List audit logs."""
    return audit_service.get_audit_logs(db, skip=skip, limit=limit, action=action)


@router.get("/audit/{audit_id}", response_model=AuditLogRead)
def get_audit_log(audit_id: str, db: Session = Depends(get_db)):
    """Get single audit log."""
    log = audit_service.get_audit_log(db, audit_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log


@router.get("/agent-actions", response_model=List[AgentActionRead])
def list_agent_actions(
    session_id: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """List agent actions."""
    return audit_service.get_agent_actions(db, session_id=session_id, skip=skip, limit=limit)
