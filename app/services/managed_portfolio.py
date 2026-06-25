from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.managed_portfolio import ManagedPortfolioRequest
from app.models.user import User

RISK_CAPS = {
    "low": {"max_risk_per_trade": 0.5, "max_daily_drawdown": 1.5},
    "medium": {"max_risk_per_trade": 1.0, "max_daily_drawdown": 3.0},
    "high": {"max_risk_per_trade": 2.0, "max_daily_drawdown": 5.0},
}

COMPLIANCE_NOTE_FA = (
    "این بخش فقط ثبت درخواست و گزارش مدیریتی است و خودش دریافت وجه، اجرای معامله، "
    "نگهداری دارایی مشتری یا پرداخت رمزارزی انجام نمی‌دهد. فعال‌سازی اجرای واقعی باید "
    "بعد از قرارداد، احراز هویت و بررسی حقوقی انجام شود."
)


def _risk_level(value: str | None) -> str:
    normalized = (value or "medium").lower()
    return normalized if normalized in RISK_CAPS else "medium"


def build_net_report(
    *,
    capital_amount: float,
    gross_profit_percent: float = 0.0,
    fee_percent: float = 5.0,
    tax_percent: float = 0.0,
) -> dict[str, Any]:
    gross_profit = capital_amount * (gross_profit_percent / 100)
    fee_amount = max(0.0, gross_profit) * (fee_percent / 100)
    tax_amount = max(0.0, gross_profit) * (tax_percent / 100)
    net_profit = gross_profit - fee_amount - tax_amount
    return {
        "capital_amount": round(capital_amount, 4),
        "gross_profit_percent": round(gross_profit_percent, 4),
        "gross_profit": round(gross_profit, 4),
        "fee_percent": round(fee_percent, 4),
        "fee_amount": round(fee_amount, 4),
        "tax_percent": round(tax_percent, 4),
        "tax_amount": round(tax_amount, 4),
        "net_profit": round(net_profit, 4),
        "net_return_percent": round((net_profit / capital_amount) * 100, 4) if capital_amount else 0.0,
        "summary_fa": "گزارش خالص بعد از کسر کارمزد و مالیات/هزینه تخمینی محاسبه شد.",
    }


def serialize_request(item: ManagedPortfolioRequest) -> dict[str, Any]:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "country": item.country,
        "capital_amount": item.capital_amount,
        "capital_currency": item.capital_currency,
        "preferred_market": item.preferred_market,
        "risk_level": item.risk_level,
        "payout_currency": item.payout_currency,
        "fee_percent": item.fee_percent,
        "tax_percent": item.tax_percent,
        "status": item.status,
        "notes": item.notes,
        "compliance_note": item.compliance_note,
        "latest_report": item.latest_report,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


async def create_managed_request(
    *,
    session: AsyncSession,
    user: User,
    payload: dict[str, Any],
) -> ManagedPortfolioRequest:
    capital_amount = float(payload.get("capital_amount") or 0)
    if capital_amount <= 0:
        raise ValueError("capital_amount must be greater than zero")

    risk_level = _risk_level(payload.get("risk_level"))
    fee_percent = float(payload.get("fee_percent") if payload.get("fee_percent") is not None else 5.0)
    tax_percent = float(payload.get("tax_percent") if payload.get("tax_percent") is not None else 0.0)
    report = build_net_report(
        capital_amount=capital_amount,
        gross_profit_percent=float(payload.get("gross_profit_percent") or 0),
        fee_percent=fee_percent,
        tax_percent=tax_percent,
    )
    report["risk_rules"] = RISK_CAPS[risk_level]
    report["generated_at"] = datetime.now(timezone.utc).isoformat()

    item = ManagedPortfolioRequest(
        user_id=user.id,
        country=payload.get("country") or user.country,
        capital_amount=capital_amount,
        capital_currency=str(payload.get("capital_currency") or "USDT").upper(),
        preferred_market=str(payload.get("preferred_market") or "crypto"),
        risk_level=risk_level,
        payout_currency=str(payload.get("payout_currency") or "USDT").upper(),
        fee_percent=fee_percent,
        tax_percent=tax_percent,
        notes=payload.get("notes"),
        compliance_note=COMPLIANCE_NOTE_FA,
        latest_report=report,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def list_user_requests(
    *,
    session: AsyncSession,
    user_id: int,
    limit: int = 20,
) -> list[ManagedPortfolioRequest]:
    result = await session.execute(
        select(ManagedPortfolioRequest)
        .where(ManagedPortfolioRequest.user_id == user_id)
        .order_by(desc(ManagedPortfolioRequest.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_request_report(
    *,
    session: AsyncSession,
    item: ManagedPortfolioRequest,
    gross_profit_percent: float,
) -> ManagedPortfolioRequest:
    item.latest_report = build_net_report(
        capital_amount=item.capital_amount,
        gross_profit_percent=gross_profit_percent,
        fee_percent=item.fee_percent,
        tax_percent=item.tax_percent,
    )
    item.latest_report["risk_rules"] = RISK_CAPS[_risk_level(item.risk_level)]
    item.latest_report["generated_at"] = datetime.now(timezone.utc).isoformat()
    await session.commit()
    await session.refresh(item)
    return item
