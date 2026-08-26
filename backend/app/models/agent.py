"""Agent models for session tracing, budget governance, trust scores, and external AI agents."""

import uuid
from datetime import datetime, timezone, date
from sqlalchemy import String, Float, Integer, DateTime, Date, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class AgentAction(Base):
    """Detailed execution trace card for AI agent tool calls."""
    __tablename__ = "agent_actions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"aa_{uuid.uuid4().hex[:8]}")
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    request_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    tool_call_id: Mapped[str] = mapped_column(String(100), nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer, default=1)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), default="TOOL_EXECUTION")
    input_data: Mapped[dict] = mapped_column(JSON, default=dict)
    output_data: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="SUCCESS")  # PENDING, RUNNING, SUCCESS, FAILED, BLOCKED, WAITING_APPROVAL
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Agent(Base):
    """Registered external or internal AI agent."""
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"agent_{uuid.uuid4().hex[:8]}")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(256), nullable=True, unique=True)
    api_key_prefix: Mapped[str] = mapped_column(String(20), nullable=True)
    scopes: Mapped[dict] = mapped_column(JSON, default=lambda: ["catalog:read", "cart:write", "checkout:create", "payment:read"])
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AgentBudget(Base):
    """Spending limits and budget monitoring for an AI agent."""
    __tablename__ = "agent_budgets"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"ab_{uuid.uuid4().hex[:8]}")
    agent_id: Mapped[str] = mapped_column(String(50), default="default_agent", unique=True)
    merchant_id: Mapped[str] = mapped_column(String(50), default="merchant_001")
    daily_limit: Mapped[float] = mapped_column(Float, default=10000.0)
    per_transaction_limit: Mapped[float] = mapped_column(Float, default=5000.0)
    spent_today: Mapped[float] = mapped_column(Float, default=0.0)
    last_reset_date: Mapped[date] = mapped_column(Date, default=lambda: datetime.now(timezone.utc).date())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def remaining_daily_budget(self) -> float:
        return max(0.0, self.daily_limit - self.spent_today)


class AgentTrust(Base):
    """Trust score and behavioural signals for an AI agent."""
    __tablename__ = "agent_trust_scores"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"at_{uuid.uuid4().hex[:8]}")
    agent_id: Mapped[str] = mapped_column(String(50), default="default_agent", unique=True)
    trust_score: Mapped[int] = mapped_column(Integer, default=90)  # 0 to 100
    successful_transactions: Mapped[int] = mapped_column(Integer, default=10)
    failed_payments: Mapped[int] = mapped_column(Integer, default=0)
    policy_violations: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_requests: Mapped[int] = mapped_column(Integer, default=0)
    total_approvals_requested: Mapped[int] = mapped_column(Integer, default=10)
    total_approvals_granted: Mapped[int] = mapped_column(Integer, default=9)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def approval_rate(self) -> float:
        if self.total_approvals_requested == 0:
            return 100.0
        return round((self.total_approvals_granted / self.total_approvals_requested) * 100, 1)

    @property
    def risk_tier(self) -> str:
        if self.trust_score >= 90:
            return "LOW"
        elif self.trust_score >= 70:
            return "MEDIUM"
        return "HIGH"
