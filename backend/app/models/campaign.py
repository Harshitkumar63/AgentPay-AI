"""Campaign proposal model for AI-driven growth campaigns."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class CampaignProposal(Base):
    __tablename__ = "campaign_proposals"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"camp_{uuid.uuid4().hex[:10]}")
    merchant_id: Mapped[str] = mapped_column(String(50), default="merchant_001", index=True)
    product_id: Mapped[str] = mapped_column(String(50), nullable=True)
    product_name: Mapped[str] = mapped_column(String(300), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    target_audience: Mapped[str] = mapped_column(String(200), default="All Store Visitors")
    discount_percentage: Mapped[float] = mapped_column(Float, default=10.0)
    budget: Mapped[float] = mapped_column(Float, default=1500.0)
    duration_days: Mapped[int] = mapped_column(Integer, default=3)
    estimated_opportunity: Mapped[float] = mapped_column(Float, default=0.0)
    evidence: Mapped[str] = mapped_column(Text, default="")
    risk_level: Mapped[str] = mapped_column(String(20), default="HIGH")
    status: Mapped[str] = mapped_column(String(30), default="proposed")  # proposed, approved, rejected, active, completed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
