from fastapi import APIRouter

from app.services.analysis import analyze_symbol

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/{symbol}")
async def get_analysis(
    symbol: str,
    exchange: str = "Binance",
    timeframe: str = "5m",
):
    return await analyze_symbol(
        exchange_name=exchange,
        symbol=symbol.upper(),
        timeframe=timeframe,
    )
