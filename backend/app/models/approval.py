"""Approval model for human-in-the-loop authorization gating."""

import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import String, Float, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"appr_{uuid.uuid4().hex[:10]}")
    agent_session_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    order_id: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    merchant_id: Mapped[str] = mapped_column(String(50), default="merchant_001")
    user_id: Mapped[str] = mapped_column(String(100), default="demo_user")
    action: Mapped[str] = mapped_column(String(100), default="create_order")
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    risk_level: Mapped[str] = mapped_column(String(20), default="HIGH")  # LOW, MEDIUM, HIGH
    risk_score: Mapped[int] = mapped_column(default=80)
    policy_result: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(Text, default="Financial transaction requires human approval")
    status: Mapped[str] = mapped_column(String(30), default="PENDING")  # PENDING, APPROVED, REJECTED, EXPIRED
    decision_reason: Mapped[str] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def is_expired(self) -> bool:
        if self.status != "PENDING":
            return False
        now = datetime.now(timezone.utc)
        exp = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
        return now > exp
