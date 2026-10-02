"""Audit log model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class AuditLog(Base):
    """Tamper-Evident Audit Log entity with cryptographic hash chaining."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"audit_{uuid.uuid4().hex[:10]}")
    event_type: Mapped[str] = mapped_column(String(100), default="GOVERNANCE_EVENT", index=True)
    agent_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    request_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ai_agent, user, system, webhook
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # CREATE_ORDER, PAYMENT_ATTEMPT, etc.
    resource_type: Mapped[str] = mapped_column(String(50), nullable=True)  # order, payment, cart, product
    resource_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    policy_result: Mapped[str] = mapped_column(String(30), nullable=True)  # ALLOWED, BLOCKED
    approval_status: Mapped[str] = mapped_column(String(30), nullable=True)  # APPROVED, REJECTED, PENDING
    result: Mapped[str] = mapped_column(String(30), nullable=True)  # SUCCESS, FAILURE, PENDING
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_extra: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Cryptographic Hash Chaining for Tamper-Evident Integrity
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
