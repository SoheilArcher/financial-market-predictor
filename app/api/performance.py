from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.models.user import User
from app.services.signal_journal import evaluate_recent_signals

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/signals")
async def signal_performance(
    days: int = 7,
    symbol: str | None = None,
    timeframe: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await evaluate_recent_signals(
        session=session,
        days=days,
        user_id=current_user.id,
        symbol=symbol,
        timeframe=timeframe,
    )
