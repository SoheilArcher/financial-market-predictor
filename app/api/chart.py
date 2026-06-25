from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.models.user import User
from app.services.chart_data import build_chart_data
from app.services.pair_data import build_pair_chart_data, parse_pair
from app.services.subscription import authorize_analysis

router = APIRouter(prefix="/chart", tags=["chart"])


@router.get("/{symbol:path}")
async def get_chart(
    symbol: str,
    timeframe: str = "5m",
    limit: int = 150,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    pair = parse_pair(symbol)
    normalized_symbol = symbol.upper().replace("/", "")
    usage_symbol = f"CHART:{symbol.upper()}" if pair else f"CHART:{normalized_symbol}"
    usage = await authorize_analysis(
        session=session,
        user=current_user,
        symbol=usage_symbol,
        timeframe=timeframe,
    )
    if pair:
        chart = await build_pair_chart_data(
            base=pair[0],
            quote=pair[1],
            timeframe=timeframe,
            limit=max(60, min(limit, 500)),
        )
    else:
        chart = await build_chart_data(
            symbol=normalized_symbol,
            timeframe=timeframe,
            limit=max(60, min(limit, 500)),
        )
    chart["subscription"] = usage
    return chart
