from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.binance import fetch_binance_klines
from app.models.prediction import PerformancePrediction
from app.services.chart_data import kline_to_candle
from app.services.commodity_data import fetch_commodity_candles, is_commodity_symbol, normalize_commodity_symbol
from app.services.pair_data import build_pair_candles, parse_pair


TERMINAL_RESULTS = {"WIN", "LOSS", "EXPIRED", "NO_DATA"}


def _parse_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _pnl_percent(prediction: PerformancePrediction, exit_price: float) -> float:
    if prediction.direction == "SHORT":
        return round(((prediction.entry_price - exit_price) / prediction.entry_price) * 100, 4)
    return round(((exit_price - prediction.entry_price) / prediction.entry_price) * 100, 4)


async def fetch_prediction_candles(prediction: PerformancePrediction, limit: int = 500) -> list[dict[str, Any]]:
    symbol = prediction.symbol
    timeframe = prediction.timeframe
    if parse_pair(symbol):
        base, quote = parse_pair(symbol) or ("", "")
        return await build_pair_candles(base=base, quote=quote, timeframe=timeframe, limit=limit)
    if is_commodity_symbol(symbol):
        normalized = normalize_commodity_symbol(symbol) or symbol
        return await fetch_commodity_candles(normalized, timeframe=timeframe, limit=limit)

    normalized = symbol.upper().replace("/", "")
    klines = await fetch_binance_klines(symbol=normalized, interval=timeframe, limit=limit)
    return [kline_to_candle(item) for item in klines]


async def evaluate_prediction(
    *,
    session: AsyncSession,
    prediction: PerformancePrediction,
) -> PerformancePrediction:
    now = datetime.now(timezone.utc)
    try:
        candles = await fetch_prediction_candles(prediction)
    except Exception as exc:
        prediction.result = "NO_DATA"
        prediction.evaluated_at = now
        prediction.reason_fa = f"داده کندل برای ارزیابی در دسترس نبود: {exc}"
        await session.commit()
        await session.refresh(prediction)
        return prediction

    start = _parse_time(prediction.created_at)
    end = _parse_time(prediction.expires_at)
    selected = []
    for candle in candles:
        candle_time = _parse_time(candle.get("timestamp"))
        if not candle_time or not start or not end:
            continue
        if start < candle_time <= end:
            selected.append(candle)

    if not selected:
        prediction.result = "NO_DATA"
        prediction.evaluated_at = now
        prediction.reason_fa = "بعد از زمان صدور سیگنال تا پایان اعتبار، کندل قابل اتکا پیدا نشد."
        await session.commit()
        await session.refresh(prediction)
        return prediction

    selected.sort(key=lambda c: _parse_time(c.get("timestamp")) or now)
    prediction.max_price_after = max(float(item["high"]) for item in selected)
    prediction.min_price_after = min(float(item["low"]) for item in selected)

    for candle in selected:
        high = float(candle["high"])
        low = float(candle["low"])
        if prediction.direction == "LONG":
            stop_hit = low <= prediction.stop_loss
            target_hit = high >= prediction.take_profit
            if stop_hit and target_hit:
                prediction.result = "LOSS"
                prediction.exit_price = prediction.stop_loss
                prediction.reason_fa = "در همان کندل هم حد سود و هم حد ضرر لمس شد؛ برای احتیاط نتیجه ضرر ثبت شد."
                break
            if target_hit:
                prediction.result = "WIN"
                prediction.exit_price = prediction.take_profit
                prediction.reason_fa = "قیمت بعد از سیگنال لانگ قبل از حد ضرر به حد سود رسید."
                break
            if stop_hit:
                prediction.result = "LOSS"
                prediction.exit_price = prediction.stop_loss
                prediction.reason_fa = "قیمت بعد از سیگنال لانگ قبل از حد سود به حد ضرر رسید."
                break
        elif prediction.direction == "SHORT":
            stop_hit = high >= prediction.stop_loss
            target_hit = low <= prediction.take_profit
            if stop_hit and target_hit:
                prediction.result = "LOSS"
                prediction.exit_price = prediction.stop_loss
                prediction.reason_fa = "در همان کندل هم حد سود و هم حد ضرر لمس شد؛ برای احتیاط نتیجه ضرر ثبت شد."
                break
            if target_hit:
                prediction.result = "WIN"
                prediction.exit_price = prediction.take_profit
                prediction.reason_fa = "قیمت بعد از سیگنال شورت قبل از حد ضرر به حد سود رسید."
                break
            if stop_hit:
                prediction.result = "LOSS"
                prediction.exit_price = prediction.stop_loss
                prediction.reason_fa = "قیمت بعد از سیگنال شورت قبل از حد سود به حد ضرر رسید."
                break

    if prediction.result == "PENDING":
        if end and now >= end:
            last_close = float(selected[-1]["close"])
            prediction.result = "EXPIRED"
            prediction.exit_price = last_close
            prediction.reason_fa = "تا پایان اعتبار سیگنال، نه حد سود لمس شد و نه حد ضرر؛ با آخرین قیمت بسته‌شدن محاسبه شد."
        else:
            await session.commit()
            await session.refresh(prediction)
            return prediction

    if prediction.exit_price is not None:
        prediction.pnl_percent = _pnl_percent(prediction, prediction.exit_price)
    prediction.evaluated_at = now
    await session.commit()
    await session.refresh(prediction)
    return prediction


async def evaluate_pending_predictions(
    *,
    session: AsyncSession,
    user_id: int | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    conditions = [PerformancePrediction.result == "PENDING"]
    if user_id is not None:
        conditions.append(PerformancePrediction.user_id == user_id)
    result = await session.execute(
        select(PerformancePrediction)
        .where(and_(*conditions))
        .order_by(PerformancePrediction.created_at.asc())
        .limit(limit)
    )
    predictions = result.scalars().all()
    counts: dict[str, int] = defaultdict(int)
    evaluated_ids = []
    for prediction in predictions:
        updated = await evaluate_prediction(session=session, prediction=prediction)
        counts[updated.result] += 1
        evaluated_ids.append(updated.id)
    return {
        "checked": len(predictions),
        "counts": dict(counts),
        "evaluated_ids": evaluated_ids,
        "summary_fa": f"{len(predictions)} پیش‌بینی بررسی شد.",
    }


def serialize_prediction(prediction: PerformancePrediction) -> dict[str, Any]:
    return {
        "id": prediction.id,
        "user_id": prediction.user_id,
        "source_type": prediction.source_type,
        "symbol": prediction.symbol,
        "market_type": prediction.market_type,
        "timeframe": prediction.timeframe,
        "direction": prediction.direction,
        "confidence": prediction.confidence,
        "entry_price": prediction.entry_price,
        "stop_loss": prediction.stop_loss,
        "take_profit": prediction.take_profit,
        "created_at": prediction.created_at.isoformat() if prediction.created_at else None,
        "expires_at": prediction.expires_at.isoformat() if prediction.expires_at else None,
        "evaluated_at": prediction.evaluated_at.isoformat() if prediction.evaluated_at else None,
        "result": prediction.result,
        "max_price_after": prediction.max_price_after,
        "min_price_after": prediction.min_price_after,
        "exit_price": prediction.exit_price,
        "pnl_percent": prediction.pnl_percent,
        "reason_fa": prediction.reason_fa,
    }


def _rate(items: list[PerformancePrediction]) -> float:
    wins = sum(1 for item in items if item.result == "WIN")
    losses = sum(1 for item in items if item.result == "LOSS")
    denominator = wins + losses
    return round((wins / denominator) * 100, 2) if denominator else 0.0


def _confidence_bucket(confidence: float) -> str:
    if confidence < 50:
        return "0-49"
    if confidence < 70:
        return "50-69"
    if confidence < 85:
        return "70-84"
    return "85-100"


def build_performance_summary(predictions: list[PerformancePrediction]) -> dict[str, Any]:
    evaluated = [item for item in predictions if item.result in TERMINAL_RESULTS]
    wins = [item for item in evaluated if item.result == "WIN"]
    losses = [item for item in evaluated if item.result == "LOSS"]
    expired = [item for item in evaluated if item.result == "EXPIRED"]
    pnl_items = [item for item in evaluated if item.pnl_percent is not None]

    by_symbol: dict[str, list[PerformancePrediction]] = defaultdict(list)
    by_timeframe: dict[str, list[PerformancePrediction]] = defaultdict(list)
    by_confidence: dict[str, list[PerformancePrediction]] = defaultdict(list)
    for item in predictions:
        by_symbol[item.symbol].append(item)
        by_timeframe[item.timeframe].append(item)
        by_confidence[_confidence_bucket(float(item.confidence or 0))].append(item)

    symbol_scores = {
        symbol: round(sum(item.pnl_percent or 0 for item in items) / max(1, len([i for i in items if i.pnl_percent is not None])), 4)
        for symbol, items in by_symbol.items()
        if any(item.pnl_percent is not None for item in items)
    }
    best_symbol = max(symbol_scores, key=symbol_scores.get) if symbol_scores else None
    worst_symbol = min(symbol_scores, key=symbol_scores.get) if symbol_scores else None

    return {
        "total_signals": len(predictions),
        "evaluated_signals": len(evaluated),
        "win_count": len(wins),
        "loss_count": len(losses),
        "expired_count": len(expired),
        "no_data_count": sum(1 for item in evaluated if item.result == "NO_DATA"),
        "win_rate": _rate(evaluated),
        "average_pnl_percent": round(sum(item.pnl_percent or 0 for item in pnl_items) / len(pnl_items), 4) if pnl_items else 0.0,
        "best_symbol": best_symbol,
        "worst_symbol": worst_symbol,
        "win_rate_by_symbol": {symbol: _rate(items) for symbol, items in sorted(by_symbol.items())},
        "win_rate_by_timeframe": {timeframe: _rate(items) for timeframe, items in sorted(by_timeframe.items())},
        "win_rate_by_confidence_bucket": {bucket: _rate(items) for bucket, items in sorted(by_confidence.items())},
        "last_90_signals": [serialize_prediction(item) for item in sorted(predictions, key=lambda item: item.created_at, reverse=True)[:90]],
        "summary_fa": "این آمار فقط بر اساس سیگنال‌های غیر WAIT و داده کندل واقعی محاسبه شده است.",
    }


async def list_predictions(
    *,
    session: AsyncSession,
    user_id: int | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
    limit: int = 90,
) -> list[PerformancePrediction]:
    conditions = []
    if user_id is not None:
        conditions.append(PerformancePrediction.user_id == user_id)
    if symbol:
        conditions.append(PerformancePrediction.symbol == symbol.upper())
    if timeframe:
        conditions.append(PerformancePrediction.timeframe == timeframe)
    stmt = select(PerformancePrediction).order_by(desc(PerformancePrediction.created_at)).limit(limit)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    result = await session.execute(stmt)
    return list(result.scalars().all())
