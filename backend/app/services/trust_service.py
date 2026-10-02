"""Agent Trust Score Service — Server-side algorithmic risk & reliability scoring with factor breakdown (Phase 8)."""

from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.models.agent import AgentTrust, Agent
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
            velocity_violations=0,
            total_approvals_requested=10,
            total_approvals_granted=9,
        )
        db.add(trust)
        db.commit()
        db.refresh(trust)
    return trust


def calculate_trust_score_with_factors(trust: AgentTrust) -> Tuple[int, List[str]]:
    """
    Calculate dynamic score (0-100) with deterministic factor explanations:
    Base = 100
    - Policy violation: -15 pts each
    - Payment failure: -8 pts each
    - Duplicate request: -5 pts each
    - Velocity violation: -10 pts each
    + Successful tx bonus: +1 pt each (max +15)
    * Factored by Approval Rate
    """
    base = 100
    factors: List[str] = [f"Base Trust: {base}"]

    penalties = 0
    if trust.policy_violations > 0:
        p_val = trust.policy_violations * 15
        penalties += p_val
        factors.append(f"-{p_val} pts ({trust.policy_violations} policy violations)")

    if trust.failed_payments > 0:
        p_val = trust.failed_payments * 8
        penalties += p_val
        factors.append(f"-{p_val} pts ({trust.failed_payments} payment failures)")

    if trust.duplicate_requests > 0:
        p_val = trust.duplicate_requests * 5
        penalties += p_val
        factors.append(f"-{p_val} pts ({trust.duplicate_requests} duplicate requests)")

    if getattr(trust, "velocity_violations", 0) > 0:
        p_val = trust.velocity_violations * 10
        penalties += p_val
        factors.append(f"-{p_val} pts ({trust.velocity_violations} velocity breaches)")

    bonuses = min(15, trust.successful_transactions * 1)
    if bonuses > 0:
        factors.append(f"+{bonuses} pts ({trust.successful_transactions} successful transactions)")

    approval_multiplier = max(0.5, trust.approval_rate / 100.0)
    if approval_multiplier < 1.0:
        factors.append(f"Approval rate factor: {trust.approval_rate}%")

    raw_score = (base - penalties + bonuses) * approval_multiplier
    final_score = int(max(0, min(100, raw_score)))
    return final_score, factors


def calculate_trust_score(trust: AgentTrust) -> int:
    score, _ = calculate_trust_score_with_factors(trust)
    return score


def get_trust_tier_limit(trust_score: int) -> Tuple[str, float, bool]:
    """
    Connect trust score to dynamic spending limits (Section 9):
    - 90-100: limit ₹10,000 (Tier 1: TRUSTED)
    - 70-89:  limit ₹5,000  (Tier 2: STANDARD)
    - 50-69:  limit ₹2,000  (Tier 3: RESTRICTED)
    - <50:    limit ₹0      (Tier 4: CRITICAL_APPROVAL_MANDATORY)
    """
    if trust_score >= 90:
        return "TRUSTED", 10000.0, False
    elif trust_score >= 70:
        return "STANDARD", 5000.0, False
    elif trust_score >= 50:
        return "RESTRICTED", 2000.0, False
    else:
        return "CRITICAL_GATED", 0.0, True


def record_trust_event(
    db: Session,
    event_type: str,  # success, payment_failed, policy_violation, duplicate_request, velocity_violation, approval_granted, approval_rejected, approval_requested
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
    elif event_type == "velocity_violation":
        trust.velocity_violations = getattr(trust, "velocity_violations", 0) + 1
    elif event_type == "approval_granted":
        trust.total_approvals_requested += 1
        trust.total_approvals_granted += 1
    elif event_type == "approval_rejected":
        trust.total_approvals_requested += 1
    elif event_type == "approval_requested":
        trust.total_approvals_requested += 1

    trust.trust_score = calculate_trust_score(trust)

    # Sync to agent record if exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent:
        agent.trust_score = trust.trust_score
        tier, limit, req_appr = get_trust_tier_limit(trust.trust_score)
        agent.risk_level = "LOW" if trust.trust_score >= 80 else ("MEDIUM" if trust.trust_score >= 60 else "HIGH")

    db.commit()
    db.refresh(trust)

    return trust


def get_trust_assessment(
    db: Session,
    agent_id: str = "default_agent",
) -> Dict[str, Any]:
    """Get trust score, factor breakdown, and dynamic transaction tier."""
    trust = get_or_create_trust(db, agent_id)
    score, factors = calculate_trust_score_with_factors(trust)
    if score != trust.trust_score:
        trust.trust_score = score
        db.commit()
        db.refresh(trust)

    tier, dynamic_limit, human_approval_mandatory = get_trust_tier_limit(trust.trust_score)

    return {
        "agent_id": trust.agent_id,
        "trust_score": trust.trust_score,
        "risk_tier": trust.risk_tier,
        "trust_level": tier,
        "dynamic_transaction_limit": dynamic_limit,
        "human_approval_mandatory": human_approval_mandatory,
        "factors": factors,
        "signals": {
            "successful_transactions": trust.successful_transactions,
            "failed_payments": trust.failed_payments,
            "policy_violations": trust.policy_violations,
            "duplicate_requests": trust.duplicate_requests,
            "velocity_violations": getattr(trust, "velocity_violations", 0),
            "total_approvals_requested": trust.total_approvals_requested,
            "total_approvals_granted": trust.total_approvals_granted,
            "approval_rate": f"{trust.approval_rate}%",
        },
        "disclaimer": "Agent trust score is an application-level risk signal calculated deterministically.",
    }
