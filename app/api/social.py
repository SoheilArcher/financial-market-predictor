from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.models.user import User
from app.services.social_trading import (
    analyst_consensus,
    evaluate_analyst,
    follow_analyst,
    followed_analyst_ids,
    get_or_create_profile,
    get_portfolio,
    list_top_analysts,
    list_following,
    position_sizing,
    profile_to_dict,
    publish_latest_signal,
    shared_to_dict,
    unfollow_analyst,
    upsert_portfolio,
    upsert_profile,
)

router = APIRouter(prefix="/social", tags=["social"])


class ProfilePayload(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    market_focus: str | None = None
    is_public: bool = True


class PublishPayload(BaseModel):
    signal_record_id: int | None = None
    title: str | None = None
    note: str | None = None


class PortfolioPayload(BaseModel):
    market_type: str = "crypto"
    capital: float
    currency: str = "USDT"
    risk_percent: float = 1
    max_position_percent: float = 20


class SizingPayload(BaseModel):
    signal: dict[str, Any]
    consensus: dict[str, Any] | None = None


@router.get("/me")
async def my_social_profile(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    profile = await get_or_create_profile(session, current_user)
    stats = await evaluate_analyst(session, current_user.id)
    portfolio = await get_portfolio(session, current_user)
    following = await list_following(session, current_user)
    return {
        "profile": profile_to_dict(profile),
        "stats": stats,
        "following": following,
        "portfolio": {
            "market_type": portfolio.market_type,
            "capital": portfolio.capital,
            "currency": portfolio.currency,
            "risk_percent": portfolio.risk_percent,
            "max_position_percent": portfolio.max_position_percent,
        },
    }


@router.put("/profile")
async def save_profile(
    payload: ProfilePayload,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    profile = await upsert_profile(
        session=session,
        user=current_user,
        display_name=payload.display_name,
        bio=payload.bio,
        market_focus=payload.market_focus,
        is_public=payload.is_public,
    )
    return {"profile": profile_to_dict(profile)}


@router.post("/publish")
async def publish_analysis(
    payload: PublishPayload,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        shared = await publish_latest_signal(
            session=session,
            user=current_user,
            signal_record_id=payload.signal_record_id,
            title=payload.title,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"shared_analysis": shared_to_dict(shared)}


@router.get("/analysts/top")
async def top_analysts(
    days: int = 30,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    following = await followed_analyst_ids(session, current_user.id)
    items = await list_top_analysts(session, days=days, limit=limit)
    for item in items:
        item["following"] = item["profile"]["user_id"] in following
        item["is_me"] = item["profile"]["user_id"] == current_user.id
    return {"items": items}


@router.get("/following")
async def my_following(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return {"items": await list_following(session, current_user)}


@router.post("/analysts/{analyst_user_id}/follow")
async def follow(
    analyst_user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return await follow_analyst(session, current_user, analyst_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/analysts/{analyst_user_id}/follow")
async def unfollow(
    analyst_user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await unfollow_analyst(session, current_user, analyst_user_id)


@router.get("/consensus")
async def consensus(
    symbol: str,
    timeframe: str | None = None,
    days: int = Query(default=7, ge=1, le=90),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    return await analyst_consensus(session, symbol=symbol, timeframe=timeframe, days=days)


@router.put("/portfolio")
async def save_portfolio(
    payload: PortfolioPayload,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    setting = await upsert_portfolio(
        session=session,
        user=current_user,
        market_type=payload.market_type,
        capital=payload.capital,
        currency=payload.currency,
        risk_percent=payload.risk_percent,
        max_position_percent=payload.max_position_percent,
    )
    return {
        "portfolio": {
            "market_type": setting.market_type,
            "capital": setting.capital,
            "currency": setting.currency,
            "risk_percent": setting.risk_percent,
            "max_position_percent": setting.max_position_percent,
        }
    }


@router.post("/position-size")
async def calculate_position_size(
    payload: SizingPayload,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    portfolio = await get_portfolio(session, current_user)
    return position_sizing(payload.signal, portfolio, payload.consensus)
