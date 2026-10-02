"""A/B Testing Experiments and Variants Models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"exp_{uuid.uuid4().hex[:8]}")
    merchant_id: Mapped[str] = mapped_column(String(50), default="merchant_001", index=True)
    product_id: Mapped[str] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="RUNNING")  # RUNNING, PAUSED, COMPLETED
    ai_recommendation: Mapped[str] = mapped_column(Text, default="")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    variants = relationship("ExperimentVariant", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentVariant(Base):
    __tablename__ = "experiment_variants"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"var_{uuid.uuid4().hex[:8]}")
    experiment_id: Mapped[str] = mapped_column(String(50), ForeignKey("experiments.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # Variant A, Variant B
    price: Mapped[float] = mapped_column(Float, nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0)
    orders: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)

    experiment = relationship("Experiment", back_populates="variants")

    @property
    def conversion_rate(self) -> float:
        if self.views == 0:
            return 0.0
        return round((self.orders / self.views) * 100, 2)

    @property
    def aov(self) -> float:
        if self.orders == 0:
            return 0.0
        return round(self.revenue / self.orders, 2)
