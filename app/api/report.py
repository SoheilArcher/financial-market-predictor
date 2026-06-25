from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.models.user import User
from app.services.market_report import build_market_report, normalize_symbols
from app.services.subscription import authorize_analysis

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/market")
async def market_report(
    symbols: str | None = None,
    timeframe: str = "5m",
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    selected_symbols = normalize_symbols(symbols)
    usage = await authorize_analysis(
        session=session,
        user=current_user,
        symbol="MARKET_REPORT",
        timeframe=timeframe,
    )
    report = await build_market_report(
        symbols=selected_symbols,
        timeframe=timeframe,
        limit=max(50, min(limit, 300)),
    )
    report["subscription"] = usage
    return report
