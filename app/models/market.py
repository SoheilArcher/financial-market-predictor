from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Exchange(Base):
    __tablename__ = "exchanges"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(20), default="crypto")
    status: Mapped[str] = mapped_column(String(20), default="active")

    symbols: Mapped[list["Symbol"]] = relationship(back_populates="exchange")


class Symbol(Base):
    __tablename__ = "symbols"

    id: Mapped[int] = mapped_column(primary_key=True)
    exchange_id: Mapped[int] = mapped_column(ForeignKey("exchanges.id"))
    symbol: Mapped[str] = mapped_column(String(50), index=True)
    base_asset: Mapped[str] = mapped_column(String(20))
    quote_asset: Mapped[str] = mapped_column(String(20))

    exchange: Mapped["Exchange"] = relationship(back_populates="symbols")
    candles: Mapped[list["Candle"]] = relationship(back_populates="symbol_ref")

    __table_args__ = (
        UniqueConstraint("exchange_id", "symbol", name="uq_exchange_symbol"),
    )


class Candle(Base):
    __tablename__ = "candles"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("symbols.id"), index=True)
    timeframe: Mapped[str] = mapped_column(String(10), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    open: Mapped[float] = mapped_column(Numeric(20, 8))
    high: Mapped[float] = mapped_column(Numeric(20, 8))
    low: Mapped[float] = mapped_column(Numeric(20, 8))
    close: Mapped[float] = mapped_column(Numeric(20, 8))
    volume: Mapped[float] = mapped_column(Numeric(30, 8))

    symbol_ref: Mapped["Symbol"] = relationship(back_populates="candles")

    __table_args__ = (
        UniqueConstraint("symbol_id", "timeframe", "timestamp", name="uq_candle"),
    )
