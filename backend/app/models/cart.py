"""Cart and CartItem models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"cart_{uuid.uuid4().hex[:8]}")
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(50), ForeignKey("merchants.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, checked_out, abandoned
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"ci_{uuid.uuid4().hex[:8]}")
    cart_id: Mapped[str] = mapped_column(String(50), ForeignKey("carts.id"), nullable=False)
    product_id: Mapped[str] = mapped_column(String(50), ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")
