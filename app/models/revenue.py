from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RevenueShareRule(Base):
    __tablename__ = "revenue_share_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="Default revenue split")
    owner_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=50)
    contributor_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=50)
    currency: Mapped[str] = mapped_column(String(12), default="USD")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class RevenueContributor(Base):
    __tablename__ = "revenue_contributors"
    __table_args__ = (UniqueConstraint("user_id", name="uq_revenue_contributor_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    manual_weight: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=1)
    role_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    payout_method: Mapped[str | None] = mapped_column(String(80), nullable=True)
    payout_account: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RevenuePool(Base):
    __tablename__ = "revenue_pools"

    id: Mapped[int] = mapped_column(primary_key=True)
    period: Mapped[str] = mapped_column(String(20), index=True)
    gross_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    system_costs: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    net_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    currency: Mapped[str] = mapped_column(String(12), default="USD")
    owner_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=50)
    contributor_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=50)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RevenuePayout(Base):
    __tablename__ = "revenue_payouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("revenue_pools.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    payout_type: Mapped[str] = mapped_column(String(30), default="contributor", index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    currency: Mapped[str] = mapped_column(String(12), default="USD")
    score: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    reason_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
