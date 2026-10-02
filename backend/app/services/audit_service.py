"""Audit Service — Tamper-Evident Audit Trail with Cryptographic Hash Chaining (Phase 15)."""

import uuid
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.agent import AgentAction
from app.utils.correlation import get_current_request_id, get_current_session_id, get_current_agent_id

GENESIS_HASH = "0" * 64


def format_audit_timestamp(dt: Any) -> str:
    """Canonicalize timestamp string representation across SQLite and Postgres."""
    if dt is None:
        return ""
    if isinstance(dt, str):
        return dt.split("+")[0].strip()
    if hasattr(dt, "tzinfo") and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().split("+")[0].strip()


def compute_audit_hash(
    audit_id: str,
    timestamp_str: str,
    actor_type: str,
    actor_id: str,
    action: str,
    resource_id: Optional[str],
    payload_dict: dict,
    previous_hash: str,
    amount: Optional[float] = None,
    currency: Optional[str] = None,
) -> str:
    """
    Deterministically computes SHA-256 hash chaining previous hash and event contents:
    H(event_data + previous_hash)
    """
    serialized_payload = json.dumps(payload_dict or {}, sort_keys=True)
    amt_str = f"{amount:.2f}" if amount is not None else ""
    curr_str = currency or ""
    raw = f"{audit_id}|{timestamp_str}|{actor_type}|{actor_id}|{action}|{resource_id or ''}|{amt_str}|{curr_str}|{serialized_payload}|{previous_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


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
    event_type: str = "GOVERNANCE_EVENT",
    agent_id: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    payload: Optional[dict] = None,
) -> AuditLog:
    """Create a tamper-evident audit log chained cryptographically to the preceding log."""
    now = datetime.now(timezone.utc)
    ts_str = format_audit_timestamp(now)
    req_id = request_id or get_current_request_id()
    sess_id = session_id or get_current_session_id()
    ag_id = agent_id or (actor_id if actor_type == "ai_agent" else get_current_agent_id())

    # Retrieve last recorded event hash for chaining
    last_audit = db.query(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).first()
    prev_hash = last_audit.event_hash if (last_audit and last_audit.event_hash) else GENESIS_HASH

    combined_payload = dict(payload or {})
    if metadata_extra:
        combined_payload.update(metadata_extra)
    if amount is not None:
        combined_payload["amount"] = amount
    if currency:
        combined_payload["currency"] = currency

    audit_id = f"audit_{uuid.uuid4().hex[:10]}"
    audit = AuditLog(
        id=audit_id,
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
        payload=combined_payload,
        event_type=event_type,
        agent_id=ag_id,
        request_id=req_id,
        session_id=sess_id,
        previous_hash=prev_hash,
        created_at=now,
    )

    # Compute deterministic event hash
    audit.event_hash = compute_audit_hash(
        audit_id=audit_id,
        timestamp_str=ts_str,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        resource_id=resource_id,
        payload_dict=combined_payload,
        previous_hash=prev_hash,
        amount=amount,
        currency=currency,
    )

    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


def verify_audit_trail(db: Session) -> Dict[str, Any]:
    """
    Verifies full cryptographic integrity of the audit log chain.
    Returns:
    - {"valid": True, "events_checked": N}
    - {"valid": False, "broken_at": "audit_xyz", "expected_hash": "...", "found_hash": "..."}
    """
    logs = db.query(AuditLog).order_by(AuditLog.created_at.asc(), AuditLog.id.asc()).all()
    if not logs:
        return {"valid": True, "events_checked": 0, "message": "No audit records to verify."}

    expected_prev = GENESIS_HASH

    for idx, log in enumerate(logs):
        # 1. Verify previous hash link
        if log.previous_hash != expected_prev:
            return {
                "valid": False,
                "broken_at": log.id,
                "event_index": idx,
                "reason": f"Broken chain link: previous_hash '{log.previous_hash}' does not match expected previous hash '{expected_prev}'.",
            }

        # 2. Re-compute event hash
        ts_str = format_audit_timestamp(log.created_at)
        expected_hash = compute_audit_hash(
            audit_id=log.id,
            timestamp_str=ts_str,
            actor_type=log.actor_type,
            actor_id=log.actor_id,
            action=log.action,
            resource_id=log.resource_id,
            payload_dict=log.payload or log.metadata_extra or {},
            previous_hash=expected_prev,
            amount=log.amount,
            currency=log.currency,
        )

        if log.event_hash != expected_hash:
            return {
                "valid": False,
                "broken_at": log.id,
                "event_index": idx,
                "reason": f"Payload tamper detected on log '{log.id}': recalculated hash does not match stored event_hash.",
            }

        expected_prev = log.event_hash

    return {
        "valid": True,
        "events_checked": len(logs),
        "latest_hash": expected_prev,
    }


def get_audit_logs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    action: Optional[str] = None,
    actor_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> List[AuditLog]:
    """Get audit logs with optional filters."""
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    if actor_id:
        q = q.filter(AuditLog.actor_id == actor_id)
    if agent_id:
        q = q.filter(AuditLog.agent_id == agent_id)
    return q.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset(skip).limit(limit).all()


def get_audit_log(db: Session, audit_id: str) -> Optional[AuditLog]:
    """Get single audit log."""
    return db.query(AuditLog).filter(AuditLog.id == audit_id).first()


def create_agent_action(
    db: Session,
    session_id: str,
    action: str,
    tool_name: str,
    input_data: Optional[dict] = None,
    output_data: Optional[dict] = None,
    status: str = "SUCCESS",
    duration_ms: Optional[int] = None,
    request_id: Optional[str] = None,
    tool_call_id: Optional[str] = None,
    sequence_number: int = 1,
    event_type: str = "TOOL_EXECUTION",
    error_message: Optional[str] = None,
) -> AgentAction:
    """Create an agent action record for tool execution tracing."""
    agent_action = AgentAction(
        session_id=session_id,
        request_id=request_id or get_current_request_id(),
        tool_call_id=tool_call_id,
        sequence_number=sequence_number,
        action=action,
        tool_name=tool_name,
        event_type=event_type,
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


def get_agent_actions(
    db: Session,
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[AgentAction]:
    """Get agent action history."""
    q = db.query(AgentAction)
    if session_id:
        q = q.filter(AgentAction.session_id == session_id)
    if agent_id:
        q = q.filter(AgentAction.agent_id == agent_id)
    return q.order_by(AgentAction.created_at.desc()).offset(skip).limit(limit).all()
