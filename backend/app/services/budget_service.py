"""Agent Budget Service — server-side daily and per-transaction spending limits."""

from datetime import datetime, timezone, date
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.agent import AgentBudget
from app.services import audit_service


def get_or_create_budget(
    db: Session,
    agent_id: str = "default_agent",
    merchant_id: str = "merchant_001",
) -> AgentBudget:
    """Get active budget for agent or initialize with default limits."""
    budget = db.query(AgentBudget).filter(
        AgentBudget.agent_id == agent_id,
        AgentBudget.merchant_id == merchant_id,
    ).first()

    today = datetime.now(timezone.utc).date()

    if not budget:
        budget = AgentBudget(
            agent_id=agent_id,
            merchant_id=merchant_id,
            daily_limit=10000.0,
            per_transaction_limit=5000.0,
            spent_today=0.0,
            last_reset_date=today,
        )
        db.add(budget)
        db.commit()
        db.refresh(budget)
        return budget

    # Auto-reset daily budget if date changed
    if budget.last_reset_date != today:
        budget.spent_today = 0.0
        budget.last_reset_date = today
        db.commit()
        db.refresh(budget)

    return budget


def check_budget_limit(
    db: Session,
    amount: float,
    agent_id: str = "default_agent",
    merchant_id: str = "merchant_001",
) -> Dict[str, Any]:
    """
    Check if the requested purchase fits within per-transaction and daily remaining budget.
    """
    budget = get_or_create_budget(db, agent_id, merchant_id)

    # 1. Per-transaction limit check
    if amount > budget.per_transaction_limit:
        return {
            "allowed": False,
            "reason": f"Amount ₹{amount:,.2f} exceeds agent single-transaction limit of ₹{budget.per_transaction_limit:,.2f}",
            "limit_type": "PER_TRANSACTION_LIMIT",
            "requested_amount": amount,
            "per_transaction_limit": budget.per_transaction_limit,
            "daily_limit": budget.daily_limit,
            "spent_today": budget.spent_today,
            "remaining_budget": budget.remaining_daily_budget,
        }

    # 2. Daily remaining budget check
    if amount > budget.remaining_daily_budget:
        return {
            "allowed": False,
            "reason": f"Amount ₹{amount:,.2f} exceeds agent remaining daily budget of ₹{budget.remaining_daily_budget:,.2f} (Daily limit: ₹{budget.daily_limit:,.2f}, Spent today: ₹{budget.spent_today:,.2f})",
            "limit_type": "DAILY_BUDGET_EXCEEDED",
            "requested_amount": amount,
            "per_transaction_limit": budget.per_transaction_limit,
            "daily_limit": budget.daily_limit,
            "spent_today": budget.spent_today,
            "remaining_budget": budget.remaining_daily_budget,
        }

    return {
        "allowed": True,
        "reason": f"Within agent spending budget limits (Remaining: ₹{budget.remaining_daily_budget - amount:,.2f})",
        "limit_type": "NONE",
        "requested_amount": amount,
        "per_transaction_limit": budget.per_transaction_limit,
        "daily_limit": budget.daily_limit,
        "spent_today": budget.spent_today,
        "remaining_budget": budget.remaining_daily_budget,
    }


def record_spending(
    db: Session,
    amount: float,
    agent_id: str = "default_agent",
    merchant_id: str = "merchant_001",
) -> AgentBudget:
    """Deduct budget once payment is authorized/captured."""
    budget = get_or_create_budget(db, agent_id, merchant_id)
    budget.spent_today += amount
    db.commit()
    db.refresh(budget)

    audit_service.create_audit_log(
        db,
        actor_type="ai_agent",
        actor_id=agent_id,
        action="AGENT_BUDGET_DEDUCTED",
        resource_type="budget",
        resource_id=budget.id,
        amount=amount,
        currency="INR",
        result="SUCCESS",
        metadata_extra={
            "spent_today": budget.spent_today,
            "remaining_budget": budget.remaining_daily_budget,
            "daily_limit": budget.daily_limit,
        },
    )

    return budget


def update_budget_limits(
    db: Session,
    agent_id: str = "default_agent",
    merchant_id: str = "merchant_001",
    daily_limit: Optional[float] = None,
    per_transaction_limit: Optional[float] = None,
) -> AgentBudget:
    """Update configured budget limits."""
    budget = get_or_create_budget(db, agent_id, merchant_id)
    if daily_limit is not None:
        budget.daily_limit = daily_limit
    if per_transaction_limit is not None:
        budget.per_transaction_limit = per_transaction_limit
    db.commit()
    db.refresh(budget)
    return budget
