from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.models.user import User
from app.services.exchange_standards import get_exchange_standard, list_exchange_standards
from app.services.prediction_tracker import save_prediction_from_payload
from app.services.trade_plan import build_trade_plan

router = APIRouter(prefix="/trade", tags=["trade"])


@router.get("/plan/{symbol:path}")
async def trade_plan(
    symbol: str,
    exchange: str = "Binance",
    timeframe: str = "5m",
    limit: int = Query(150, ge=50, le=500),
    account_size: float = Query(1000, gt=0),
    risk_percent: float = Query(1.0, gt=0, le=5),
    entry_price: float | None = Query(None, gt=0),
    side: str | None = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await build_trade_plan(
        exchange=exchange,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        account_size=account_size,
        risk_percent=risk_percent,
        entry_price=entry_price,
        side=side,
    )
    prediction = await save_prediction_from_payload(
        session=session,
        source_type="trade_plan",
        payload=result,
        user_id=current_user.id,
        symbol=result.get("symbol") or symbol,
        timeframe=timeframe,
    )
    if prediction:
        result["performance_prediction_id"] = prediction.id
    return result


@router.get("/exchanges")
async def exchange_standards(current_user: User = Depends(get_current_user)):
    return list_exchange_standards()


@router.get("/exchanges/{exchange_name}")
async def exchange_standard(exchange_name: str, current_user: User = Depends(get_current_user)):
    return get_exchange_standard(exchange_name)
