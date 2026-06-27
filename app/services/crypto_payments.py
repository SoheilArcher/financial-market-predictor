import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crypto_payment import CryptoPaymentInvoice
from app.models.user import User

SUPPORTED_NETWORKS = {
    "USDT": ["TRC20", "ERC20", "BEP20"],
    "BTC": ["BTC"],
    "ETH": ["ERC20"],
}


def _address_env(currency: str, network: str) -> str:
    return f"CRYPTO_DEPOSIT_{currency.upper()}_{network.upper()}_ADDRESS"


def get_deposit_address(currency: str, network: str) -> str | None:
    return os.getenv(_address_env(currency, network)) or os.getenv("CRYPTO_DEPOSIT_DEFAULT_ADDRESS")


def validate_currency_network(currency: str, network: str) -> tuple[str, str]:
    selected_currency = (currency or "USDT").upper()
    selected_network = (network or "TRC20").upper()
    allowed = SUPPORTED_NETWORKS.get(selected_currency)
    if not allowed or selected_network not in allowed:
        raise ValueError(f"Unsupported crypto payment route: {selected_currency} on {selected_network}")
    return selected_currency, selected_network


def serialize_invoice(invoice: CryptoPaymentInvoice) -> dict[str, Any]:
    return {
        "id": invoice.id,
        "user_id": invoice.user_id,
        "managed_request_id": invoice.managed_request_id,
        "purpose": invoice.purpose,
        "amount": invoice.amount,
        "currency": invoice.currency,
        "network": invoice.network,
        "deposit_address": invoice.deposit_address,
        "memo": invoice.memo,
        "status": invoice.status,
        "tx_hash": invoice.tx_hash,
        "payer_wallet": invoice.payer_wallet,
        "note": invoice.note,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
        "expires_at": invoice.expires_at.isoformat() if invoice.expires_at else None,
        "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
        "reviewed_at": invoice.reviewed_at.isoformat() if invoice.reviewed_at else None,
        "warning_fa": "فقط دقیقاً روی همین شبکه پرداخت کنید. پرداخت روی شبکه اشتباه ممکن است قابل بازیابی نباشد.",
    }


async def create_crypto_invoice(
    *,
    session: AsyncSession,
    user: User,
    amount: float,
    currency: str = "USDT",
    network: str = "TRC20",
    purpose: str = "managed_portfolio",
    managed_request_id: int | None = None,
) -> CryptoPaymentInvoice:
    if amount <= 0:
        raise ValueError("amount must be greater than zero")
    selected_currency, selected_network = validate_currency_network(currency, network)
    address = get_deposit_address(selected_currency, selected_network)
    if not address:
        raise ValueError(
            f"Deposit address is not configured. Set {_address_env(selected_currency, selected_network)}"
        )

    invoice = CryptoPaymentInvoice(
        user_id=user.id,
        managed_request_id=managed_request_id,
        purpose=purpose,
        amount=float(amount),
        currency=selected_currency,
        network=selected_network,
        deposit_address=address,
        memo=f"NT-{user.id}-{int(datetime.now(timezone.utc).timestamp())}",
    )
    session.add(invoice)
    await session.commit()
    await session.refresh(invoice)
    return invoice


async def list_user_invoices(
    *,
    session: AsyncSession,
    user_id: int,
    limit: int = 20,
) -> list[CryptoPaymentInvoice]:
    result = await session.execute(
        select(CryptoPaymentInvoice)
        .where(CryptoPaymentInvoice.user_id == user_id)
        .order_by(desc(CryptoPaymentInvoice.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())


async def submit_payment_proof(
    *,
    session: AsyncSession,
    invoice: CryptoPaymentInvoice,
    tx_hash: str,
    payer_wallet: str | None = None,
    note: str | None = None,
) -> CryptoPaymentInvoice:
    invoice.tx_hash = tx_hash.strip()
    invoice.payer_wallet = payer_wallet
    invoice.note = note
    invoice.status = "pending_review"
    invoice.paid_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(invoice)
    return invoice


def validate_tx_hash(tx_hash: str, network: str) -> str:
    value = (tx_hash or "").strip()
    net = (network or "").upper()
    if net in {"ERC20", "BEP20"}:
        body = value[2:] if value.lower().startswith("0x") else value
        if not (len(body) == 64 and all(c in "0123456789abcdefABCDEF" for c in body)):
            raise ValueError("Invalid EVM transaction hash format")
        return "0x" + body.lower()
    if net == "TRC20":
        if not (len(value) == 64 and all(c in "0123456789abcdefABCDEF" for c in value)):
            raise ValueError("Invalid TRC20 transaction hash format")
        return value.lower()
    if net == "BTC":
        if not (len(value) == 64 and all(c in "0123456789abcdefABCDEF" for c in value)):
            raise ValueError("Invalid BTC transaction hash format")
        return value.lower()
    if len(value) < 16:
        raise ValueError("Transaction hash is too short")
    return value
