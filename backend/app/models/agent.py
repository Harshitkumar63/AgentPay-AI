"""Agent models for Multi-Agent Registry, session tracing, budget governance, trust scores, and circuit breakers."""

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
    """Registered external or internal AI agent in the Multi-Agent Registry."""
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"agent_{uuid.uuid4().hex[:8]}")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    role: Mapped[str] = mapped_column(String(50), default="shopping")  # shopping, payment, growth, support, security, buyer
    
    owner: Mapped[str] = mapped_column(String(100), default="system")
    
    # Statuses: ACTIVE, PAUSED, DISABLED, SUSPENDED
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    
    # Fine-grained Permissions:
    # catalog.read, product.search, product.compare, recommendation.read,
    # cart.create, cart.write, checkout.request, order.create, order.read,
    # payment.read, refund.request, campaign.propose, campaign.activate,
    # analytics.read, audit.read, approval.request
    permissions: Mapped[list] = mapped_column(JSON, default=lambda: ["catalog.read", "product.search", "product.compare", "cart.create", "cart.write", "checkout.request", "order.create"])
    
    daily_budget: Mapped[float] = mapped_column(Float, default=10000.0)
    per_transaction_limit: Mapped[float] = mapped_column(Float, default=5000.0)
    hourly_limit: Mapped[float] = mapped_column(Float, default=7500.0)
    trust_score: Mapped[int] = mapped_column(Integer, default=90)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW")
    
    # Circuit Breaker state
    failed_payment_count: Mapped[int] = mapped_column(Integer, default=0)
    last_failure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    circuit_breaker_state: Mapped[str] = mapped_column(String(20), default="CLOSED")  # CLOSED, OPEN, HALF_OPEN
    circuit_breaker_tripped: Mapped[bool] = mapped_column(Boolean, default=False)
    circuit_breaker_reason: Mapped[str] = mapped_column(String(300), nullable=True)
    circuit_breaker_opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Security & API Auth
    api_key_hash: Mapped[str] = mapped_column(String(256), nullable=True, unique=True, index=True)
    api_key_prefix: Mapped[str] = mapped_column(String(20), nullable=True)
    scopes: Mapped[list] = mapped_column(JSON, default=lambda: ["catalog:read", "cart:write", "checkout:create", "payment:read"])
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_extra: Mapped[dict] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    @property
    def agent_id(self) -> str:
        return self.id

    @property
    def transaction_limit(self) -> float:
        return self.per_transaction_limit


class AgentBudget(Base):
    """Spending limits and budget monitoring for an AI agent."""
    __tablename__ = "agent_budgets"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"ab_{uuid.uuid4().hex[:8]}")
    agent_id: Mapped[str] = mapped_column(String(50), default="default_agent", unique=True)
    merchant_id: Mapped[str] = mapped_column(String(50), default="merchant_001")
    daily_limit: Mapped[float] = mapped_column(Float, default=10000.0)
    per_transaction_limit: Mapped[float] = mapped_column(Float, default=5000.0)
    hourly_limit: Mapped[float] = mapped_column(Float, default=7500.0)
    spent_today: Mapped[float] = mapped_column(Float, default=0.0)
    spent_this_hour: Mapped[float] = mapped_column(Float, default=0.0)
    transaction_count_today: Mapped[int] = mapped_column(Integer, default=0)
    transaction_count_hour: Mapped[int] = mapped_column(Integer, default=0)
    transaction_count_minute: Mapped[int] = mapped_column(Integer, default=0)
    last_reset_date: Mapped[date] = mapped_column(Date, default=lambda: datetime.now(timezone.utc).date())
    last_reset_hour: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_reset_minute: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def remaining_daily_budget(self) -> float:
        return max(0.0, self.daily_limit - self.spent_today)

    @property
    def remaining_hourly_budget(self) -> float:
        return max(0.0, self.hourly_limit - self.spent_this_hour)


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
    velocity_violations: Mapped[int] = mapped_column(Integer, default=0)
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
