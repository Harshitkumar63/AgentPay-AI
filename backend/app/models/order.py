"""Order model supporting complete state machine and agent governance."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"order_{uuid.uuid4().hex[:8]}")
    merchant_id: Mapped[str] = mapped_column(String(50), ForeignKey("merchants.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    cart_id: Mapped[str] = mapped_column(String(50), ForeignKey("carts.id"), nullable=True)
    agent_id: Mapped[str] = mapped_column(String(50), nullable=True)
    agent_session_id: Mapped[str] = mapped_column(String(100), nullable=True)
    approval_id: Mapped[str] = mapped_column(String(50), nullable=True)
    razorpay_order_id: Mapped[str] = mapped_column(String(100), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    
    # State Machine: CART, CHECKOUT_PENDING, POLICY_CHECKED, APPROVAL_PENDING, APPROVED, ORDER_CREATED, PAYMENT_PENDING, PAYMENT_AUTHORIZED, PAYMENT_CAPTURED, COMPLETED, PAYMENT_FAILED, CANCELLED, EXPIRED
    status: Mapped[str] = mapped_column(String(30), default="ORDER_CREATED")
    payment_status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, authorized, captured, failed, refunded
    receipt: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    order_type: Mapped[str] = mapped_column(String(30), default="normal")  # normal, ai_assisted, upsell, cross_sell
    
    timeline: Mapped[list] = mapped_column(JSON, default=list)
    decision_factors: Mapped[dict] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    payments = relationship("Payment", back_populates="order")
