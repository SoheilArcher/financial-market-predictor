from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnalysisUsage(Base):
    __tablename__ = "analysis_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    usage_date: Mapped[date] = mapped_column(Date, index=True)
    count: Mapped[int] = mapped_column(default=0)
    last_symbol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_timeframe: Mapped[str | None] = mapped_column(String(10), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_analysis_usage_user_date"),
    )

