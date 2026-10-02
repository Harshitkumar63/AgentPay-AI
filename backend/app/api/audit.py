"""Audit API — Tamper-Evident Audit Trail Viewing & Cryptographic Hash Chain Verification (Phase 15)."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import AuditLogRead, AgentActionRead
from app.services import audit_service

router = APIRouter()


@router.get("/admin/audit/verify", summary="Verify Tamper-Evident Hash Chain Integrity")
@router.get("/audit/verify", summary="Verify Tamper-Evident Hash Chain Integrity (Public View)")
def verify_audit_chain(db: Session = Depends(get_db)):
    """
    Validates cryptographic integrity of the entire audit trail from genesis.
    Returns {"valid": true, "events_checked": N} or {"valid": false, "broken_at": "audit_id"}.
    """
    return audit_service.verify_audit_trail(db)


@router.get("/audit", summary="List Audit Logs")
@router.get("/admin/audit", summary="List Audit Logs (Admin View)")
def list_audit_logs(
    action: Optional[str] = None,
    agent_id: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """List tamper-evident audit logs with chained event hashes and metadata."""
    logs = audit_service.get_audit_logs(db, skip=skip, limit=limit, action=action, agent_id=agent_id)
    return [
        {
            "id": log.id,
            "event_type": log.event_type,
            "agent_id": log.agent_id,
            "request_id": log.request_id,
            "session_id": log.session_id,
            "actor_type": log.actor_type,
            "actor_id": log.actor_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "amount": log.amount,
            "currency": log.currency,
            "reason": log.reason,
            "policy_result": log.policy_result,
            "approval_status": log.approval_status,
            "result": log.result,
            "payload": log.payload or {},
            "metadata_extra": log.metadata_extra or {},
            "previous_hash": log.previous_hash,
            "event_hash": log.event_hash,
            "created_at": str(log.created_at),
        }
        for log in logs
    ]


@router.get("/audit/{audit_id}", summary="Get Single Audit Log")
def get_audit_log(audit_id: str, db: Session = Depends(get_db)):
    """Get single audit log."""
    log = audit_service.get_audit_log(db, audit_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return {
        "id": log.id,
        "event_type": log.event_type,
        "agent_id": log.agent_id,
        "request_id": log.request_id,
        "session_id": log.session_id,
        "actor_type": log.actor_type,
        "actor_id": log.actor_id,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "amount": log.amount,
        "currency": log.currency,
        "reason": log.reason,
        "policy_result": log.policy_result,
        "approval_status": log.approval_status,
        "result": log.result,
        "payload": log.payload or {},
        "metadata_extra": log.metadata_extra or {},
        "previous_hash": log.previous_hash,
        "event_hash": log.event_hash,
        "created_at": str(log.created_at),
    }


@router.get("/agent-actions", response_model=List[AgentActionRead])
def list_agent_actions(
    session_id: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """List agent actions."""
    return audit_service.get_agent_actions(db, session_id=session_id, skip=skip, limit=limit)
