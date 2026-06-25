import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.binance import fetch_binance_klines
from app.models.signal import SignalRecord
from app.models.user import User


def _percent(change_from: float, change_to: float) -> float:
    if not change_from:
        return 0.0
    return round(((change_to - change_from) / change_from) * 100, 3)


async def record_signal(
    session: AsyncSession,
    user: User,
    analysis: dict[str, Any],
    source: str = "analysis",
) -> SignalRecord | None:
    signal = analysis.get("signal")
    if signal not in {"LONG", "SHORT", "WAIT", "NO_DATA"}:
        return None

    levels = analysis.get("levels") or {}
    record = SignalRecord(
        user_id=user.id,
        source=source,
        symbol=str(analysis.get("symbol", "")).upper(),
        timeframe=str(analysis.get("timeframe", "")),
        signal=signal,
        confidence=float(analysis.get("confidence") or 0),
        entry_price=analysis.get("price"),
        stop_loss=levels.get("stop_loss"),
        take_profit=levels.get("take_profit"),
        reasons_json=json.dumps(analysis.get("reasons") or [], ensure_ascii=False),
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


def _build_advice(record: SignalRecord, current_price: float) -> tuple[str, str]:
    if record.signal == "LONG":
        if record.stop_loss and current_price <= record.stop_loss:
            return (
                "حد ضرر لمس شده است؛ خروج یا کاهش ریسک منطقی‌تر از میانگین کم کردن است.",
                "Stop loss has been reached; exiting or reducing risk is safer than averaging down.",
            )
        if record.entry_price and current_price < record.entry_price:
            return (
                "معامله وارد ضرر شده؛ تا وقتی تایید جدید نداریم حجم اضافه نکن و حد ضرر را جابه‌جا نکن.",
                "The trade is in drawdown; do not add size or move the stop without fresh confirmation.",
            )
    if record.signal == "SHORT":
        if record.stop_loss and current_price >= record.stop_loss:
            return (
                "حد ضرر فروش لمس شده است؛ بهتر است سناریوی فروش باطل تلقی شود.",
                "Short stop loss has been reached; the short scenario should be treated as invalid.",
            )
        if record.entry_price and current_price > record.entry_price:
            return (
                "فروش وارد ضرر شده؛ صبر برای تایید برگشت یا خروج پله‌ای ریسک را کم می‌کند.",
                "The short is in drawdown; wait for reversal confirmation or reduce exposure.",
            )
    return (
        "فعلاً مدیریت معامله طبق حد ضرر و حد سود اولیه انجام شود؛ ورود جدید نیاز به تایید تازه دارد.",
        "Manage the trade using the original stop and target; new entries need fresh confirmation.",
    )


async def evaluate_record(record: SignalRecord) -> SignalRecord:
    if not record.entry_price or record.signal not in {"LONG", "SHORT", "WAIT"}:
        record.status = "neutral"
        record.evaluated_at = datetime.now(timezone.utc)
        return record

    klines = await fetch_binance_klines(symbol=record.symbol, interval=record.timeframe, limit=500)
    since = record.created_at
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    candles = [
        {
            "timestamp": datetime.fromtimestamp(item[0] / 1000, tz=timezone.utc),
            "high": float(item[2]),
            "low": float(item[3]),
            "close": float(item[4]),
        }
        for item in klines
        if datetime.fromtimestamp(item[0] / 1000, tz=timezone.utc) >= since
    ]
    if not candles:
        return record

    current_price = candles[-1]["close"]
    highs = [item["high"] for item in candles]
    lows = [item["low"] for item in candles]

    if record.signal == "LONG":
        record.outcome_percent = _percent(record.entry_price, current_price)
        record.max_favorable_percent = _percent(record.entry_price, max(highs))
        record.max_adverse_percent = _percent(record.entry_price, min(lows))
        if record.take_profit and max(highs) >= record.take_profit:
            record.status = "correct"
        elif record.stop_loss and min(lows) <= record.stop_loss:
            record.status = "wrong"
        else:
            record.status = "correct" if current_price > record.entry_price else "wrong"
    elif record.signal == "SHORT":
        record.outcome_percent = _percent(record.entry_price, current_price) * -1
        record.max_favorable_percent = _percent(record.entry_price, min(lows)) * -1
        record.max_adverse_percent = _percent(record.entry_price, max(highs)) * -1
        if record.take_profit and min(lows) <= record.take_profit:
            record.status = "correct"
        elif record.stop_loss and max(highs) >= record.stop_loss:
            record.status = "wrong"
        else:
            record.status = "correct" if current_price < record.entry_price else "wrong"
    else:
        move = abs(_percent(record.entry_price, current_price))
        record.outcome_percent = move
        record.status = "correct" if move < 1 else "neutral"

    record.advice_fa, record.advice_en = _build_advice(record, current_price)
    record.evaluated_at = datetime.now(timezone.utc)
    return record


async def evaluate_recent_signals(
    session: AsyncSession,
    days: int = 7,
    user_id: int | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> dict[str, Any]:
    since = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 90)))
    stmt = select(SignalRecord).where(SignalRecord.created_at >= since)
    if user_id:
        stmt = stmt.where(SignalRecord.user_id == user_id)
    if symbol:
        stmt = stmt.where(SignalRecord.symbol == symbol.upper())
    if timeframe:
        stmt = stmt.where(SignalRecord.timeframe == timeframe)
    records = (await session.scalars(stmt.order_by(SignalRecord.created_at.desc()).limit(1000))).all()

    for record in records:
        if record.status == "pending":
            try:
                await evaluate_record(record)
            except Exception:
                continue
    await session.commit()

    evaluated = [record for record in records if record.status in {"correct", "wrong", "neutral"}]
    pending = sum(1 for record in records if record.status == "pending")
    correct = sum(1 for record in evaluated if record.status == "correct")
    wrong = sum(1 for record in evaluated if record.status == "wrong")
    neutral = sum(1 for record in evaluated if record.status == "neutral")
    reviewed = len(evaluated)
    total = len(records)
    accuracy = round((correct / reviewed) * 100, 2) if reviewed else 0

    by_timeframe: dict[str, dict[str, Any]] = {}
    for record in evaluated:
        bucket = by_timeframe.setdefault(record.timeframe, {"total": 0, "correct": 0, "wrong": 0, "neutral": 0})
        bucket["total"] += 1
        bucket[record.status] += 1
    for bucket in by_timeframe.values():
        bucket["accuracy"] = round((bucket["correct"] / bucket["total"]) * 100, 2) if bucket["total"] else 0

    return {
        "days": days,
        "total": total,
        "reviewed": reviewed,
        "pending": pending,
        "correct": correct,
        "wrong": wrong,
        "neutral": neutral,
        "accuracy": accuracy,
        "by_timeframe": by_timeframe,
        "recent": [
            {
                "id": record.id,
                "symbol": record.symbol,
                "timeframe": record.timeframe,
                "signal": record.signal,
                "status": record.status,
                "confidence": record.confidence,
                "entry_price": record.entry_price,
                "outcome_percent": record.outcome_percent,
                "max_favorable_percent": record.max_favorable_percent,
                "max_adverse_percent": record.max_adverse_percent,
                "advice_fa": record.advice_fa,
                "advice_en": record.advice_en,
                "created_at": record.created_at,
                "evaluated_at": record.evaluated_at,
            }
            for record in records[:50]
        ],
    }
