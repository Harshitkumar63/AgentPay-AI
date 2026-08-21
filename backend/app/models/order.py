"""Order model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"order_{uuid.uuid4().hex[:8]}")
    merchant_id: Mapped[str] = mapped_column(String(50), ForeignKey("merchants.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    cart_id: Mapped[str] = mapped_column(String(50), ForeignKey("carts.id"), nullable=True)
    razorpay_order_id: Mapped[str] = mapped_column(String(100), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    status: Mapped[str] = mapped_column(String(30), default="created")  # created, confirmed, fulfilled, cancelled
    payment_status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, authorized, captured, failed, refunded
    receipt: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    order_type: Mapped[str] = mapped_column(String(30), default="normal")  # normal, ai_assisted, upsell, cross_sell
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    payments = relationship("Payment", back_populates="order")
