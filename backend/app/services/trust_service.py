"""Agent Trust Score Service — server-side algorithmic risk & reliability scoring."""

from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.agent import AgentTrust
from app.services import audit_service


def get_or_create_trust(
    db: Session,
    agent_id: str = "default_agent",
) -> AgentTrust:
    """Get active trust record for agent or initialize baseline."""
    trust = db.query(AgentTrust).filter(AgentTrust.agent_id == agent_id).first()
    if not trust:
        trust = AgentTrust(
            agent_id=agent_id,
            trust_score=90,
            successful_transactions=10,
            failed_payments=0,
            policy_violations=0,
            duplicate_requests=0,
            total_approvals_requested=10,
            total_approvals_granted=9,
        )
        db.add(trust)
        db.commit()
        db.refresh(trust)
    return trust


def calculate_trust_score(trust: AgentTrust) -> int:
    """
    Calculate dynamic score (0-100):
    Base = 100
    - Policy violation: -15 pts each
    - Payment failure: -8 pts each
    - Duplicate request: -5 pts each
    + Successful tx bonus: +1 pt each (max +15)
    * Factored by Approval Rate
    """
    base = 100
    penalties = (
        (trust.policy_violations * 15)
        + (trust.failed_payments * 8)
        + (trust.duplicate_requests * 5)
    )
    bonuses = min(15, trust.successful_transactions * 1)
    approval_multiplier = max(0.5, trust.approval_rate / 100.0)

    raw_score = (base - penalties + bonuses) * approval_multiplier
    final_score = int(max(0, min(100, raw_score)))
    return final_score


def record_trust_event(
    db: Session,
    event_type: str,  # success, payment_failed, policy_violation, duplicate_request, approval_granted, approval_rejected
    agent_id: str = "default_agent",
) -> AgentTrust:
    """Record an agent behavioural event and recalculate trust score server-side."""
    trust = get_or_create_trust(db, agent_id)

    if event_type == "success":
        trust.successful_transactions += 1
    elif event_type == "payment_failed":
        trust.failed_payments += 1
    elif event_type == "policy_violation":
        trust.policy_violations += 1
    elif event_type == "duplicate_request":
        trust.duplicate_requests += 1
    elif event_type == "approval_granted":
        trust.total_approvals_requested += 1
        trust.total_approvals_granted += 1
    elif event_type == "approval_rejected":
        trust.total_approvals_requested += 1
    elif event_type == "approval_requested":
        trust.total_approvals_requested += 1

    trust.trust_score = calculate_trust_score(trust)
    db.commit()
    db.refresh(trust)

    return trust


def get_trust_assessment(
    db: Session,
    agent_id: str = "default_agent",
) -> Dict[str, Any]:
    """Get trust score, signals breakdown, and risk tier."""
    trust = get_or_create_trust(db, agent_id)
    # Recalculate on read
    new_score = calculate_trust_score(trust)
    if new_score != trust.trust_score:
        trust.trust_score = new_score
        db.commit()
        db.refresh(trust)

    return {
        "agent_id": trust.agent_id,
        "trust_score": trust.trust_score,
        "risk_tier": trust.risk_tier,
        "signals": {
            "successful_transactions": trust.successful_transactions,
            "failed_payments": trust.failed_payments,
            "policy_violations": trust.policy_violations,
            "duplicate_requests": trust.duplicate_requests,
            "total_approvals_requested": trust.total_approvals_requested,
            "total_approvals_granted": trust.total_approvals_granted,
            "approval_rate": f"{trust.approval_rate}%",
        },
        "disclaimer": "Agent trust score is an application-level risk signal, not a guarantee of transaction safety.",
    }
