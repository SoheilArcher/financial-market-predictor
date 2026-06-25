from datetime import datetime, timezone
from typing import Any

from app.collectors.binance import fetch_binance_klines, save_binance_candles
from app.services.analyzer import calculate_ema, calculate_rsi


def ema_series(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = []
    for index in range(len(values)):
        if index + 1 < period:
            result.append(None)
        else:
            result.append(calculate_ema(values[: index + 1], period))
    return result


def rsi_series(values: list[float], period: int = 14) -> list[float | None]:
    result: list[float | None] = []
    for index in range(len(values)):
        if index < period:
            result.append(None)
        else:
            result.append(calculate_rsi(values[: index + 1], period))
    return result


def kline_to_candle(kline: list[Any]) -> dict[str, Any]:
    return {
        "time": int(kline[0] / 1000),
        "timestamp": datetime.fromtimestamp(kline[0] / 1000, tz=timezone.utc).isoformat(),
        "open": float(kline[1]),
        "high": float(kline[2]),
        "low": float(kline[3]),
        "close": float(kline[4]),
        "volume": float(kline[5]),
    }


async def build_chart_data(symbol: str, timeframe: str = "5m", limit: int = 150) -> dict[str, Any]:
    klines = await fetch_binance_klines(symbol=symbol, interval=timeframe, limit=limit)
    candles = [kline_to_candle(item) for item in klines]
    closes = [item["close"] for item in candles]
    ema20 = ema_series(closes, 20)
    ema50 = ema_series(closes, 50)
    rsi14 = rsi_series(closes, 14)

    await save_binance_candles(symbol=symbol, interval=timeframe, limit=limit)

    return {
        "exchange": "Binance",
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": candles,
        "indicators": {
            "ema20": ema20,
            "ema50": ema50,
            "rsi14": rsi14,
        },
        "last": candles[-1] if candles else None,
        "disclaimer": "Chart data is for analysis only, not financial advice.",
    }
