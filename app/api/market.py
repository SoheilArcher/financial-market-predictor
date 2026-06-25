from fastapi import APIRouter
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.market import Exchange, Symbol, Candle
from app.services.analyzer import analyze_market

router = APIRouter(prefix="/market", tags=["market"])


async def fetch_candles(exchange_name: str, symbol: str, timeframe: str, limit: int):
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
        candles = result.scalars().all()

        return [
            {
                "timestamp": c.timestamp,
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": float(c.volume),
            }
            for c in reversed(candles)
        ]


@router.get("/candles/{exchange_name}/{symbol}")
async def get_candles(
    exchange_name: str,
    symbol: str,
    timeframe: str = "5m",
    limit: int = 100,
):
    return await fetch_candles(exchange_name, symbol, timeframe, limit)


@router.get("/analyze/{exchange_name}/{symbol}")
async def analyze_symbol(
    exchange_name: str,
    symbol: str,
    timeframe: str = "5m",
    limit: int = 100,
):
    candles = await fetch_candles(exchange_name, symbol, timeframe, limit)

    return analyze_market(
        candles=candles,
        symbol=symbol,
        timeframe=timeframe,
    )
