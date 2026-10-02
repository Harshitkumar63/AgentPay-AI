"""Refund model for controlled human-in-the-loop refund workflow."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Refund(Base):
    __tablename__ = "refunds"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"ref_{uuid.uuid4().hex[:10]}")
    order_id: Mapped[str] = mapped_column(String(50), ForeignKey("orders.id"), nullable=False, index=True)
    payment_id: Mapped[str] = mapped_column(String(50), nullable=True)
    merchant_id: Mapped[str] = mapped_column(String(50), default="merchant_001", index=True)
    user_id: Mapped[str] = mapped_column(String(100), default="demo_user")
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    reason: Mapped[str] = mapped_column(Text, default="Customer requested refund")
    
    # State machine: REQUESTED -> APPROVAL_PENDING -> APPROVED -> REJECTED -> PROCESSING -> COMPLETED -> FAILED
    status: Mapped[str] = mapped_column(String(30), default="REQUESTED")
    risk_level: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    risk_score: Mapped[int] = mapped_column(default=50)
    approval_id: Mapped[str] = mapped_column(String(50), nullable=True)
    approved_by: Mapped[str] = mapped_column(String(100), nullable=True)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=True)
    metadata_extra: Mapped[dict] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
