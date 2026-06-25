from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import get_current_user, get_session
from app.models.subscription import Plan, Subscription
from app.models.user import User
from app.schemas.admin import PlanResponse, SubscriptionResponse

router = APIRouter(prefix="/subscription", tags=["subscription"])


def plan_response(plan: Plan) -> PlanResponse:
    return PlanResponse(
        id=plan.id,
        code=plan.code,
        name=plan.name,
        price=plan.price,
        currency=plan.currency,
        interval_days=plan.interval_days,
        max_analyses_per_day=plan.max_analyses_per_day,
        allowed_timeframes=plan.allowed_timeframes or [],
        status=plan.status,
    )


def subscription_response(subscription: Subscription) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        plan=plan_response(subscription.plan),
        status=subscription.status,
        starts_at=subscription.starts_at,
        ends_at=subscription.ends_at,
    )


@router.get("/plans", response_model=list[PlanResponse])
async def public_plans(session: AsyncSession = Depends(get_session)):
    plans = (
        await session.scalars(
            select(Plan).where(Plan.status == "active").order_by(Plan.price, Plan.id)
        )
    ).all()
    return [plan_response(plan) for plan in plans]


@router.get("/me", response_model=SubscriptionResponse | None)
async def my_subscription(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    now = datetime.now(timezone.utc)
    subscription = await session.scalar(
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .where(
            Subscription.user_id == current_user.id,
            Subscription.status == "active",
            Subscription.ends_at > now,
        )
        .order_by(Subscription.ends_at.desc())
        .limit(1)
    )
    return subscription_response(subscription) if subscription else None

