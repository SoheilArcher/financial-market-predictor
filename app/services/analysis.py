from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.market import Exchange, Symbol, Candle


def ema(values: list[float], period: int) -> float:
    if len(values) < period:
        return sum(values) / len(values)

    k = 2 / (period + 1)
    ema_value = values[0]

    for price in values[1:]:
        ema_value = price * k + ema_value * (1 - k)

    return ema_value


async def analyze_symbol(
    exchange_name: str = "Binance",
    symbol: str = "BTCUSDT",
    timeframe: str = "5m",
    limit: int = 100,
):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Candle)
            .join(Symbol)
            .join(Exchange)
            .where(
                Exchange.name == exchange_name,
                Symbol.symbol == symbol,
                Candle.timeframe == timeframe,
            )
            .order_by(Candle.timestamp.desc())
            .limit(limit)
        )

        result = await session.execute(stmt)
        candles = list(reversed(result.scalars().all()))

        if len(candles) < 50:
            return {
                "symbol": symbol,
                "status": "not_enough_data",
                "message": "Need at least 50 candles"
            }

        closes = [float(c.close) for c in candles]

        last_price = closes[-1]
        ema20 = ema(closes[-50:], 20)
        ema50 = ema(closes[-50:], 50)

        if last_price > ema20 > ema50:
            trend = "Bullish"
            signal = "WATCH_LONG"
            confidence = 65
        elif last_price < ema20 < ema50:
            trend = "Bearish"
            signal = "WATCH_SHORT"
            confidence = 65
        else:
            trend = "Neutral"
            signal = "WAIT"
            confidence = 45

        return {
            "exchange": exchange_name,
            "symbol": symbol,
            "timeframe": timeframe,
            "price": round(last_price, 2),
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "trend": trend,
            "signal": signal,
            "confidence": confidence,
            "disclaimer": "This is a statistical market analysis, not financial advice."
        }
