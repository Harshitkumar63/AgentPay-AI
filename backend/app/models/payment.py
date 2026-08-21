"""Payment model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"pay_{uuid.uuid4().hex[:8]}")
    order_id: Mapped[str] = mapped_column(String(50), ForeignKey("orders.id"), nullable=False)
    razorpay_payment_id: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    status: Mapped[str] = mapped_column(String(30), default="created")  # created, authorized, captured, failed, refunded
    method: Mapped[str] = mapped_column(String(50), nullable=True)
    error_code: Mapped[str] = mapped_column(String(100), nullable=True)
    error_description: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    order = relationship("Order", back_populates="payments")
