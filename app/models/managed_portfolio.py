from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ManagedPortfolioRequest(Base):
    __tablename__ = "managed_portfolio_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    capital_amount: Mapped[float] = mapped_column(Float)
    capital_currency: Mapped[str] = mapped_column(String(12), default="USDT")
    preferred_market: Mapped[str] = mapped_column(String(40), default="crypto")
    risk_level: Mapped[str] = mapped_column(String(20), default="medium", index=True)
    payout_currency: Mapped[str] = mapped_column(String(20), default="USDT")
    fee_percent: Mapped[float] = mapped_column(Float, default=5.0)
    tax_percent: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(30), default="pending_review", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    compliance_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    latest_report: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
