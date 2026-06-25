from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.models.user import User
from app.services.performance_evaluator import (
    build_performance_summary,
    evaluate_pending_predictions,
    list_predictions,
    serialize_prediction,
)
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


@router.get("/summary")
async def performance_summary(
    symbol: str | None = None,
    timeframe: str | None = None,
    limit: int = Query(500, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    predictions = await list_predictions(
        session=session,
        user_id=current_user.id,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )
    return build_performance_summary(predictions)


@router.get("/history")
async def performance_history(
    symbol: str | None = None,
    timeframe: str | None = None,
    limit: int = Query(90, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    predictions = await list_predictions(
        session=session,
        user_id=current_user.id,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )
    return {
        "items": [serialize_prediction(item) for item in predictions],
        "count": len(predictions),
        "summary_fa": "تاریخچه پیش‌بینی‌های ثبت‌شده کاربر.",
    }


@router.get("/by-symbol/{symbol}")
async def performance_by_symbol(
    symbol: str,
    timeframe: str | None = None,
    limit: int = Query(500, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    predictions = await list_predictions(
        session=session,
        user_id=current_user.id,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )
    return build_performance_summary(predictions)


@router.get("/by-timeframe/{timeframe}")
async def performance_by_timeframe(
    timeframe: str,
    symbol: str | None = None,
    limit: int = Query(500, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    predictions = await list_predictions(
        session=session,
        user_id=current_user.id,
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )
    return build_performance_summary(predictions)


@router.post("/evaluate-pending")
async def evaluate_pending(
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await evaluate_pending_predictions(
        session=session,
        user_id=current_user.id,
        limit=limit,
    )
