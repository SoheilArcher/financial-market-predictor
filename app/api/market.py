from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.database import AsyncSessionLocal
from app.models.market import Exchange, Symbol, Candle
from app.models.user import User
from app.services.analyzer import analyze_market
from app.services.commodity_data import analyze_commodity_symbol, is_commodity_symbol, normalize_commodity_symbol
from app.services.live_price import attach_live_price, fetch_live_price
from app.services.pair_data import analyze_pair_symbol, parse_pair
from app.services.prediction_tracker import save_prediction_from_payload
from app.services.signal_journal import record_signal
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


@router.get("/analyze/{exchange_name}/{symbol:path}")
async def analyze_symbol(
    exchange_name: str,
    symbol: str,
    timeframe: str = "5m",
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    pair = parse_pair(symbol)
    usage = await authorize_analysis(
        session=session,
        user=current_user,
        symbol=symbol.upper(),
        timeframe=timeframe,
    )
    if pair:
        result = await analyze_pair_symbol(symbol=symbol, timeframe=timeframe, limit=limit)
    elif is_commodity_symbol(symbol):
        result = await analyze_commodity_symbol(
            symbol=normalize_commodity_symbol(symbol) or symbol,
            timeframe=timeframe,
            limit=limit,
        )
    else:
        candles = await fetch_candles(exchange_name, symbol, timeframe, limit)
        result = analyze_market(
            candles=candles,
            symbol=symbol.upper(),
            timeframe=timeframe,
        )
        try:
            live_price = await fetch_live_price(symbol=symbol, exchange=exchange_name)
            attach_live_price(result, live_price)
        except Exception as exc:
            result["live_price"] = {
                "exchange": exchange_name,
                "symbol": symbol.upper(),
                "status": "unavailable",
                "message": str(exc),
            }
    record = await record_signal(session=session, user=current_user, analysis=result)
    if record:
        result["signal_record_id"] = record.id
    prediction = await save_prediction_from_payload(
        session=session,
        source_type="analysis",
        payload=result,
        user_id=current_user.id,
        symbol=result.get("symbol") or symbol,
        timeframe=timeframe,
    )
    if prediction:
        result["performance_prediction_id"] = prediction.id
    result["subscription"] = usage
    return result
