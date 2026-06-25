from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import PerformancePrediction
from app.services.commodity_data import is_commodity_symbol
from app.services.pair_data import parse_pair

SOURCE_TYPES = {"analysis", "report", "radar", "trade_plan", "news_signal"}
TIMEFRAME_EXPIRY_MULTIPLIER = {
    "1m": timedelta(hours=1),
    "5m": timedelta(hours=4),
    "15m": timedelta(hours=12),
    "1h": timedelta(days=2),
    "4h": timedelta(days=7),
    "1d": timedelta(days=30),
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _direction_from_payload(payload: dict[str, Any]) -> str:
    value = (
        payload.get("direction")
        or payload.get("signal")
        or payload.get("side")
        or payload.get("current_signal")
        or "WAIT"
    )
    normalized = str(value).upper()
    if normalized in {"BUY", "LONG"}:
        return "LONG"
    if normalized in {"SELL", "SHORT"}:
        return "SHORT"
    return "WAIT"


def _market_type(symbol: str, payload: dict[str, Any]) -> str:
    if payload.get("market_type"):
        return str(payload["market_type"])
    if parse_pair(symbol):
        return "pair"
    if is_commodity_symbol(symbol):
        return "commodity"
    return "crypto"


def _expires_at(timeframe: str, created_at: datetime) -> datetime:
    return created_at + TIMEFRAME_EXPIRY_MULTIPLIER.get(timeframe, timedelta(hours=4))


def _extract_trade_levels(payload: dict[str, Any], direction: str) -> tuple[float | None, float | None, float | None]:
    plan = payload.get("plan") or {}
    analysis = payload.get("analysis") or {}
    levels = payload.get("levels") or analysis.get("levels") or {}
    entry = _to_float(payload.get("entry_price")) or _to_float(payload.get("price")) or _to_float(analysis.get("price"))
    stop_loss = _to_float(payload.get("stop_loss")) or _to_float(plan.get("stop_loss")) or _to_float(levels.get("stop_loss"))
    take_profit = _to_float(payload.get("take_profit")) or _to_float(levels.get("take_profit"))

    take_profits = plan.get("take_profits") or payload.get("take_profits") or []
    if take_profit is None and take_profits:
        first_target = take_profits[0] if isinstance(take_profits[0], dict) else {"price": take_profits[0]}
        take_profit = _to_float(first_target.get("price"))

    if entry and stop_loss and take_profit is None:
        risk = abs(entry - stop_loss)
        take_profit = entry + risk if direction == "LONG" else entry - risk

    if entry and stop_loss is None:
        stop_loss = entry * (0.985 if direction == "LONG" else 1.015)

    if entry and take_profit is None:
        take_profit = entry * (1.02 if direction == "LONG" else 0.98)

    return entry, stop_loss, take_profit


async def save_prediction_from_payload(
    *,
    session: AsyncSession,
    source_type: str,
    payload: dict[str, Any],
    user_id: int | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> PerformancePrediction | None:
    if source_type not in SOURCE_TYPES:
        source_type = "analysis"

    direction = _direction_from_payload(payload)
    if direction == "WAIT":
        return None

    selected_symbol = (symbol or payload.get("symbol") or "UNKNOWN").upper()
    selected_timeframe = timeframe or payload.get("timeframe") or "5m"
    entry, stop_loss, take_profit = _extract_trade_levels(payload, direction)
    if not entry or not stop_loss or not take_profit:
        return None

    now = utc_now()
    prediction = PerformancePrediction(
        user_id=user_id,
        source_type=source_type,
        symbol=selected_symbol,
        market_type=_market_type(selected_symbol, payload),
        timeframe=selected_timeframe,
        direction=direction,
        confidence=float(payload.get("confidence") or 0),
        entry_price=float(entry),
        stop_loss=float(stop_loss),
        take_profit=float(take_profit),
        created_at=now,
        expires_at=_expires_at(selected_timeframe, now),
        result="PENDING",
        reason_fa="سیگنال جهت‌دار ثبت شد و بعد از رسیدن قیمت به حد سود/ضرر یا پایان اعتبار ارزیابی می‌شود.",
        raw_payload=payload,
    )
    session.add(prediction)
    await session.commit()
    await session.refresh(prediction)
    return prediction


async def save_report_predictions(
    *,
    session: AsyncSession,
    report: dict[str, Any],
    user_id: int | None = None,
) -> list[int]:
    saved_ids: list[int] = []
    timeframe = report.get("timeframe")
    for item in report.get("items") or []:
        prediction = await save_prediction_from_payload(
            session=session,
            source_type="report",
            payload=item,
            user_id=user_id,
            symbol=item.get("symbol"),
            timeframe=timeframe or item.get("timeframe"),
        )
        if prediction:
            saved_ids.append(prediction.id)
    return saved_ids
