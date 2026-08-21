"""Policy model for financial action gating."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"pol_{uuid.uuid4().hex[:8]}")
    merchant_id: Mapped[str] = mapped_column(String(50), ForeignKey("merchants.id"), nullable=False)
    max_purchase_amount: Mapped[float] = mapped_column(Float, default=5000.0)
    max_discount_percentage: Mapped[float] = mapped_column(Float, default=20.0)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_refund_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    allowed_actions: Mapped[dict] = mapped_column(JSON, default=lambda: ["search", "recommend", "add_to_cart", "create_order"])
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    merchant = relationship("Merchant", back_populates="policies")
