from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.database import AsyncSessionLocal
from app.models.market import Exchange, Symbol, Candle
from app.models.user import User
from app.services.analyzer import analyze_market
from app.services.subscription import authorize_analysis

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
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    usage = await authorize_analysis(
        session=session,
        user=current_user,
        symbol=symbol.upper(),
        timeframe=timeframe,
    )
    candles = await fetch_candles(exchange_name, symbol, timeframe, limit)
    result = analyze_market(
        candles=candles,
        symbol=symbol,
        timeframe=timeframe,
    )
    result["subscription"] = usage
    return result

