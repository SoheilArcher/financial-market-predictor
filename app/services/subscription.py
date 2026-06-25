from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.subscription import Subscription
from app.models.usage import AnalysisUsage
from app.models.user import User


async def get_active_subscription(
    session: AsyncSession,
    user_id: int,
) -> Subscription | None:
    now = datetime.now(timezone.utc)
    return await session.scalar(
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .where(
            Subscription.user_id == user_id,
            Subscription.status == "active",
            Subscription.ends_at > now,
        )
        .order_by(Subscription.ends_at.desc())
        .limit(1)
    )


async def authorize_analysis(
    session: AsyncSession,
    user: User,
    symbol: str,
    timeframe: str,
) -> dict[str, int | str | list[str]]:
    subscription = await get_active_subscription(session, user.id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required",
        )

    plan = subscription.plan
    allowed_timeframes = plan.allowed_timeframes or []
    if allowed_timeframes and timeframe not in allowed_timeframes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Timeframe is not allowed for current plan",
                "plan": plan.code,
                "allowed_timeframes": allowed_timeframes,
            },
        )

    today = datetime.now(timezone.utc).date()
    usage = await session.scalar(
        select(AnalysisUsage).where(
            AnalysisUsage.user_id == user.id,
            AnalysisUsage.usage_date == today,
        )
    )
    if usage is None:
        usage = AnalysisUsage(user_id=user.id, usage_date=today, count=0)
        session.add(usage)
        await session.flush()

    if usage.count >= plan.max_analyses_per_day:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Daily analysis limit reached",
                "plan": plan.code,
                "limit": plan.max_analyses_per_day,
                "used": usage.count,
            },
        )

    usage.count += 1
    usage.last_symbol = symbol
    usage.last_timeframe = timeframe
    await session.commit()

    return {
        "plan": plan.code,
        "daily_limit": plan.max_analyses_per_day,
        "daily_used": usage.count,
        "daily_remaining": max(plan.max_analyses_per_day - usage.count, 0),
        "allowed_timeframes": allowed_timeframes,
    }

