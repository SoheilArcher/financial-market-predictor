from datetime import datetime, timedelta

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CryptoPaymentInvoice(Base):
    __tablename__ = "crypto_payment_invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    managed_request_id: Mapped[int | None] = mapped_column(
        ForeignKey("managed_portfolio_requests.id"),
        nullable=True,
        index=True,
    )
    purpose: Mapped[str] = mapped_column(String(40), default="managed_portfolio", index=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(20), default="USDT", index=True)
    network: Mapped[str] = mapped_column(String(30), default="TRC20", index=True)
    deposit_address: Mapped[str] = mapped_column(String(255))
    memo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending_payment", index=True)
    tx_hash: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    payer_wallet: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.utcnow() + timedelta(hours=2),
        index=True,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
