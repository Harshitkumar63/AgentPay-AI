"""Audit service — create and query audit logs."""

from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.agent import AgentAction
import time


def create_audit_log(
    db: Session,
    actor_type: str,
    actor_id: str,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    amount: Optional[float] = None,
    currency: Optional[str] = None,
    reason: Optional[str] = None,
    policy_result: Optional[str] = None,
    approval_status: Optional[str] = None,
    result: Optional[str] = None,
    metadata_extra: Optional[dict] = None,
) -> AuditLog:
    """Create an audit log entry."""
    audit = AuditLog(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        amount=amount,
        currency=currency,
        reason=reason,
        policy_result=policy_result,
        approval_status=approval_status,
        result=result,
        metadata_extra=metadata_extra or {},
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


def get_audit_logs(db: Session, skip: int = 0, limit: int = 50, action: Optional[str] = None) -> List[AuditLog]:
    """Get audit logs with optional filtering."""
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    return q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()


def get_audit_log(db: Session, audit_id: str) -> Optional[AuditLog]:
    """Get single audit log."""
    return db.query(AuditLog).filter(AuditLog.id == audit_id).first()


def create_agent_action(
    db: Session,
    session_id: str,
    action: str,
    tool_name: str,
    input_data: dict = None,
    output_data: dict = None,
    status: str = "success",
    error_message: Optional[str] = None,
    duration_ms: Optional[int] = None,
) -> AgentAction:
    """Record an agent tool call action."""
    agent_action = AgentAction(
        session_id=session_id,
        action=action,
        tool_name=tool_name,
        input_data=input_data or {},
        output_data=output_data or {},
        status=status,
        error_message=error_message,
        duration_ms=duration_ms,
    )
    db.add(agent_action)
    db.commit()
    db.refresh(agent_action)
    return agent_action


def get_agent_actions(db: Session, session_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[AgentAction]:
    """Get agent actions with optional session filter."""
    q = db.query(AgentAction)
    if session_id:
        q = q.filter(AgentAction.session_id == session_id)
    return q.order_by(AgentAction.created_at.desc()).offset(skip).limit(limit).all()
