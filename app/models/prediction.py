from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PerformancePrediction(Base):
    __tablename__ = "performance_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(String(30), index=True)
    symbol: Mapped[str] = mapped_column(String(50), index=True)
    market_type: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    timeframe: Mapped[str] = mapped_column(String(10), index=True)
    direction: Mapped[str] = mapped_column(String(10), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    entry_price: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    result: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    max_price_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_price_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    pnl_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason_fa: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
