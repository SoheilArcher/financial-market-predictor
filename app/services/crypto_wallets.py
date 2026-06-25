from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crypto_wallet import UserCryptoWallet
from app.models.user import User
from app.services.crypto_payments import SUPPORTED_NETWORKS, validate_currency_network

SELF_CUSTODY_NOTE_FA = (
    "برای کاربران ایران، مسیر امن‌تر این است که کیف پول غیرامانی خودشان را ثبت کنند. "
    "این بخش به صرافی داخلی یا خارجی وصل نیست و برای دور زدن محدودیت هیچ سرویس ثالثی طراحی نشده است."
)


def _validate_address(address: str, network: str) -> str:
    value = (address or "").strip()
    if len(value) < 20 or len(value) > 140:
        raise ValueError("wallet_address length is invalid")
    if network == "TRC20" and not value.startswith("T"):
        raise ValueError("TRC20 USDT address should usually start with T")
    if network in {"ERC20", "BEP20"} and not value.startswith("0x"):
        raise ValueError(f"{network} address should usually start with 0x")
    return value


def serialize_wallet(wallet: UserCryptoWallet) -> dict[str, Any]:
    return {
        "id": wallet.id,
        "user_id": wallet.user_id,
        "label": wallet.label,
        "currency": wallet.currency,
        "network": wallet.network,
        "wallet_address": wallet.wallet_address,
        "wallet_type": wallet.wallet_type,
        "status": wallet.status,
        "note": wallet.note,
        "created_at": wallet.created_at.isoformat() if wallet.created_at else None,
        "updated_at": wallet.updated_at.isoformat() if wallet.updated_at else None,
        "summary_fa": SELF_CUSTODY_NOTE_FA,
    }


async def create_wallet(
    *,
    session: AsyncSession,
    user: User,
    payload: dict[str, Any],
) -> UserCryptoWallet:
    currency, network = validate_currency_network(payload.get("currency") or "USDT", payload.get("network") or "TRC20")
    if currency not in SUPPORTED_NETWORKS:
        raise ValueError("unsupported currency")
    address = _validate_address(str(payload.get("wallet_address") or ""), network)
    wallet_type = str(payload.get("wallet_type") or "self_custody")
    if wallet_type != "self_custody":
        raise ValueError("Only self_custody wallets are supported for this product")

    wallet = UserCryptoWallet(
        user_id=user.id,
        label=str(payload.get("label") or "Main wallet")[:80],
        currency=currency,
        network=network,
        wallet_address=address,
        wallet_type="self_custody",
        note=payload.get("note"),
    )
    session.add(wallet)
    await session.commit()
    await session.refresh(wallet)
    return wallet


async def list_wallets(
    *,
    session: AsyncSession,
    user_id: int,
    limit: int = 20,
) -> list[UserCryptoWallet]:
    result = await session.execute(
        select(UserCryptoWallet)
        .where(UserCryptoWallet.user_id == user_id)
        .order_by(desc(UserCryptoWallet.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())
