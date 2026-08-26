"""Recommendation and cross-sell/upsell tracking event model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class RecommendationEvent(Base):
    __tablename__ = "recommendation_events"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"recevt_{uuid.uuid4().hex[:10]}")
    merchant_id: Mapped[str] = mapped_column(String(50), default="merchant_001", index=True)
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # recommendation, upsell, cross_sell, similar
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # shown, clicked, added, purchased
    source_product_id: Mapped[str] = mapped_column(String(50), nullable=True)
    recommended_product_id: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), default="demo_user")
    session_id: Mapped[str] = mapped_column(String(100), nullable=True)
    order_id: Mapped[str] = mapped_column(String(50), nullable=True)
    revenue_attributed: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_extra: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
