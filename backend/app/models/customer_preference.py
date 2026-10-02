"""Customer Memory & Preferences Model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class CustomerPreference(Base):
    __tablename__ = "customer_preferences"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"pref_{uuid.uuid4().hex[:8]}")
    user_id: Mapped[str] = mapped_column(String(100), default="demo_user", unique=True, index=True)
    merchant_id: Mapped[str] = mapped_column(String(50), default="merchant_001")
    
    preferred_categories: Mapped[list] = mapped_column(JSON, default=lambda: ["shoes", "fitness"])
    preferred_brands: Mapped[list] = mapped_column(JSON, default=lambda: ["ProRunner", "SwiftBook"])
    preferred_colors: Mapped[list] = mapped_column(JSON, default=lambda: ["black", "blue"])
    budget_min: Mapped[float] = mapped_column(Float, default=1000.0)
    budget_max: Mapped[float] = mapped_column(Float, default=5000.0)
    notes: Mapped[str] = mapped_column(Text, default="Prefers lightweight and ergonomic gear")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
