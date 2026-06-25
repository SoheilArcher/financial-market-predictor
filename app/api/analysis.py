from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.models.user import User
from app.services.analysis import analyze_symbol
from app.services.subscription import authorize_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/{symbol}")
async def get_analysis(
    symbol: str,
    exchange: str = "Binance",
    timeframe: str = "5m",
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    usage = await authorize_analysis(
        session=session,
        user=current_user,
        symbol=symbol.upper(),
        timeframe=timeframe,
    )
    result = await analyze_symbol(
        exchange_name=exchange,
        symbol=symbol.upper(),
        timeframe=timeframe,
    )
    result["subscription"] = usage
    return result

