import asyncio
from datetime import datetime, timezone
from typing import Any

from app.collectors.binance import fetch_binance_klines, save_binance_candles
from app.services.analyzer import analyze_market


DEFAULT_MARKET_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "LINKUSDT",
    "AVAXUSDT",
    "TONUSDT",
]


def normalize_symbols(symbols: str | None) -> list[str]:
    if not symbols:
        return DEFAULT_MARKET_SYMBOLS
    normalized = []
    for item in symbols.split(","):
        symbol = item.strip().upper().replace("/", "")
        if symbol and symbol not in normalized:
            normalized.append(symbol)
    return normalized[:20] or DEFAULT_MARKET_SYMBOLS


def kline_to_candle(kline: list[Any]) -> dict[str, Any]:
    return {
        "timestamp": datetime.fromtimestamp(kline[0] / 1000, tz=timezone.utc),
        "open": float(kline[1]),
        "high": float(kline[2]),
        "low": float(kline[3]),
        "close": float(kline[4]),
        "volume": float(kline[5]),
    }


def price_change_percent(candles: list[dict[str, Any]]) -> float:
    if len(candles) < 2:
        return 0.0
    first_open = float(candles[0]["open"])
    last_close = float(candles[-1]["close"])
    if first_open == 0:
        return 0.0
    return round(((last_close - first_open) / first_open) * 100, 2)


def build_market_summary(items: list[dict[str, Any]], timeframe: str) -> dict[str, Any]:
    valid = [item for item in items if item.get("signal") != "ERROR"]
    if not valid:
        return {
            "market_bias": "UNKNOWN",
            "summary_fa": "فعلاً داده کافی برای گزارش کلی بازار وجود ندارد.",
        }

    long_count = sum(1 for item in valid if item["signal"] == "LONG")
    short_count = sum(1 for item in valid if item["signal"] == "SHORT")
    wait_count = sum(1 for item in valid if item["signal"] in {"WAIT", "NO_DATA"})
    avg_change = round(sum(item["change_percent"] for item in valid) / len(valid), 2)
    avg_confidence = round(sum(item.get("confidence", 0) for item in valid) / len(valid), 1)

    if long_count > short_count and avg_change >= 0:
        market_bias = "BULLISH"
        summary = "غلبه با نمادهای صعودی است؛ بازار در این تایم‌فریم تمایل مثبت دارد."
    elif short_count > long_count and avg_change <= 0:
        market_bias = "BEARISH"
        summary = "فشار فروش در چند نماد اصلی بیشتر است؛ بازار نیاز به احتیاط دارد."
    else:
        market_bias = "MIXED"
        summary = "بازار جهت یکدست ندارد؛ بهتر است فقط نمادهای قوی‌تر جداگانه بررسی شوند."

    top_movers = sorted(valid, key=lambda item: item["change_percent"], reverse=True)[:3]
    weak_movers = sorted(valid, key=lambda item: item["change_percent"])[:3]
    strongest_signals = sorted(valid, key=lambda item: item.get("confidence", 0), reverse=True)[:5]

    return {
        "timeframe": timeframe,
        "market_bias": market_bias,
        "symbols_count": len(valid),
        "long_count": long_count,
        "short_count": short_count,
        "wait_count": wait_count,
        "average_change_percent": avg_change,
        "average_confidence": avg_confidence,
        "top_movers": [
            {"symbol": item["symbol"], "change_percent": item["change_percent"], "signal": item["signal"]}
            for item in top_movers
        ],
        "weak_movers": [
            {"symbol": item["symbol"], "change_percent": item["change_percent"], "signal": item["signal"]}
            for item in weak_movers
        ],
        "strongest_signals": [
            {
                "symbol": item["symbol"],
                "signal": item["signal"],
                "confidence": item.get("confidence", 0),
                "risk": item.get("risk", "UNKNOWN"),
            }
            for item in strongest_signals
        ],
        "summary_fa": summary,
    }


async def analyze_symbol_live(symbol: str, timeframe: str, limit: int) -> dict[str, Any]:
    try:
        klines = await fetch_binance_klines(symbol=symbol, interval=timeframe, limit=limit)
        candles = [kline_to_candle(kline) for kline in klines]
        result = analyze_market(candles=candles, symbol=symbol, timeframe=timeframe)
        result["change_percent"] = price_change_percent(candles)
        result["source"] = "Binance"
        result["last_candle_at"] = candles[-1]["timestamp"] if candles else None
        await save_binance_candles(symbol=symbol, interval=timeframe, limit=limit)
        return result
    except Exception as exc:
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": "ERROR",
            "confidence": 0,
            "risk": "UNKNOWN",
            "change_percent": 0,
            "message": str(exc),
        }


async def build_market_report(
    symbols: list[str],
    timeframe: str = "5m",
    limit: int = 100,
) -> dict[str, Any]:
    tasks = [analyze_symbol_live(symbol=symbol, timeframe=timeframe, limit=limit) for symbol in symbols]
    items = await asyncio.gather(*tasks)
    summary = build_market_summary(items, timeframe=timeframe)
    return {
        "exchange": "Binance",
        "generated_at": datetime.now(timezone.utc),
        "summary": summary,
        "items": sorted(
            items,
            key=lambda item: (item.get("signal") == "ERROR", -item.get("confidence", 0)),
        ),
        "disclaimer": "این گزارش تحلیل آماری بازار است و توصیه مالی محسوب نمی‌شود.",
    }
