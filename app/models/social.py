from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnalystProfile(Base):
    __tablename__ = "analyst_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    public_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    market_focus: Mapped[str] = mapped_column(String(40), default="crypto")
    is_public: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class AnalystFollow(Base):
    __tablename__ = "analyst_follows"
    __table_args__ = (UniqueConstraint("follower_user_id", "analyst_user_id", name="uq_analyst_follow"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    follower_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    analyst_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class SharedAnalysis(Base):
    __tablename__ = "shared_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    signal_record_id: Mapped[int | None] = mapped_column(ForeignKey("signal_records.id"), nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String(50), index=True)
    timeframe: Mapped[str] = mapped_column(String(10), index=True)
    signal: Mapped[str] = mapped_column(String(20), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    title: Mapped[str | None] = mapped_column(String(180), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class PortfolioSetting(Base):
    __tablename__ = "portfolio_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    market_type: Mapped[str] = mapped_column(String(30), default="crypto")
    capital: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(12), default="USDT")
    risk_percent: Mapped[float] = mapped_column(Float, default=1)
    max_position_percent: Mapped[float] = mapped_column(Float, default=20)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
