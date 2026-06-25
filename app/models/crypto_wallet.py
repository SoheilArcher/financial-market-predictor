from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserCryptoWallet(Base):
    __tablename__ = "user_crypto_wallets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    label: Mapped[str] = mapped_column(String(80), default="Main wallet")
    currency: Mapped[str] = mapped_column(String(20), default="USDT", index=True)
    network: Mapped[str] = mapped_column(String(30), default="TRC20", index=True)
    wallet_address: Mapped[str] = mapped_column(String(255), index=True)
    wallet_type: Mapped[str] = mapped_column(String(30), default="self_custody", index=True)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
