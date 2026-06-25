from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import get_current_user, get_session, to_user_response
from app.models.subscription import Plan, Subscription
from app.models.crypto_payment import CryptoPaymentInvoice
from app.models.managed_portfolio import ManagedPortfolioRequest
from app.models.comment import Comment
from app.models.user import User
from app.schemas.admin import (
    AssignSubscriptionRequest,
    PlanCreateRequest,
    PlanResponse,
    PlanUpdateRequest,
    SubscriptionResponse,
    UserUpdateRequest,
    UserWithSubscriptionResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


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


def managed_request_response(item: ManagedPortfolioRequest) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "country": item.country,
        "capital_amount": item.capital_amount,
        "capital_currency": item.capital_currency,
        "preferred_market": item.preferred_market,
        "risk_level": item.risk_level,
        "payout_currency": item.payout_currency,
        "fee_percent": item.fee_percent,
        "tax_percent": item.tax_percent,
        "status": item.status,
        "notes": item.notes,
        "compliance_note": item.compliance_note,
        "latest_report": item.latest_report,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def crypto_invoice_response(item: CryptoPaymentInvoice) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "managed_request_id": item.managed_request_id,
        "purpose": item.purpose,
        "amount": item.amount,
        "currency": item.currency,
        "network": item.network,
        "deposit_address": item.deposit_address,
        "memo": item.memo,
        "status": item.status,
        "tx_hash": item.tx_hash,
        "payer_wallet": item.payer_wallet,
        "note": item.note,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "expires_at": item.expires_at.isoformat() if item.expires_at else None,
        "paid_at": item.paid_at.isoformat() if item.paid_at else None,
        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
    }


def comment_response(comment: Comment, user: User | None = None) -> dict:
    return {
        "id": comment.id,
        "user_id": comment.user_id,
        "user_email": user.email if user else None,
        "target_type": comment.target_type,
        "target_id": comment.target_id,
        "content": comment.content,
        "language": comment.language,
        "status": comment.status,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }


async def get_active_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    now = datetime.now(timezone.utc)
    stmt = (
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
    return await session.scalar(stmt)


@router.get("/users", response_model=list[UserWithSubscriptionResponse])
async def list_users(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    users = (await session.scalars(select(User).order_by(User.id))).all()
    response = []
    for user in users:
        user_payload = to_user_response(user).model_dump()
        subscription = await get_active_subscription(session, user.id)
        user_payload["subscription"] = subscription_response(subscription) if subscription else None
        response.append(UserWithSubscriptionResponse(**user_payload))
    return response


@router.patch("/users/{user_id}", response_model=UserWithSubscriptionResponse)
async def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    subscription = await get_active_subscription(session, user.id)
    user_payload = to_user_response(user).model_dump()
    user_payload["subscription"] = subscription_response(subscription) if subscription else None
    return UserWithSubscriptionResponse(**user_payload)


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    plans = (await session.scalars(select(Plan).order_by(Plan.id))).all()
    return [plan_response(plan) for plan in plans]


@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PlanCreateRequest,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    code = payload.code.strip().lower()
    existing_plan = await session.scalar(select(Plan).where(Plan.code == code))
    if existing_plan:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Plan code already exists")

    plan = Plan(**payload.model_dump(exclude={"code"}), code=code)
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan_response(plan)


@router.patch("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: int,
    payload: PlanUpdateRequest,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    plan = await session.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    await session.commit()
    await session.refresh(plan)
    return plan_response(plan)


@router.post("/users/{user_id}/subscription", response_model=SubscriptionResponse)
async def assign_subscription(
    user_id: int,
    payload: AssignSubscriptionRequest,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    plan = await session.scalar(select(Plan).where(Plan.code == payload.plan_code.strip().lower()))
    if plan is None or plan.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active plan not found")

    await session.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id, Subscription.status == "active")
        .execution_options(populate_existing=True)
    )
    existing_subscriptions = (
        await session.scalars(
            select(Subscription).where(Subscription.user_id == user_id, Subscription.status == "active")
        )
    ).all()
    for subscription in existing_subscriptions:
        subscription.status = "cancelled"

    now = datetime.now(timezone.utc)
    days = payload.days or plan.interval_days
    subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status="active",
        starts_at=now,
        ends_at=now + timedelta(days=days),
    )
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription, attribute_names=["plan"])
    return subscription_response(subscription)


@router.get("/managed-requests")
async def admin_managed_requests(
    status_filter: str | None = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    stmt = select(ManagedPortfolioRequest).order_by(desc(ManagedPortfolioRequest.created_at)).limit(min(max(limit, 1), 500))
    if status_filter:
        stmt = stmt.where(ManagedPortfolioRequest.status == status_filter)
    items = (await session.scalars(stmt)).all()
    return {"items": [managed_request_response(item) for item in items], "count": len(items)}


@router.patch("/managed-requests/{request_id}")
async def admin_update_managed_request(
    request_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    item = await session.get(ManagedPortfolioRequest, request_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Managed request not found")
    allowed = {"pending_review", "approved", "active", "rejected", "settled", "cancelled"}
    if "status" in payload:
        next_status = str(payload["status"])
        if next_status not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
        item.status = next_status
    if "notes" in payload:
        item.notes = payload["notes"]
    if "compliance_note" in payload:
        item.compliance_note = payload["compliance_note"]
    await session.commit()
    await session.refresh(item)
    return managed_request_response(item)


@router.get("/crypto-invoices")
async def admin_crypto_invoices(
    status_filter: str | None = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    stmt = select(CryptoPaymentInvoice).order_by(desc(CryptoPaymentInvoice.created_at)).limit(min(max(limit, 1), 500))
    if status_filter:
        stmt = stmt.where(CryptoPaymentInvoice.status == status_filter)
    items = (await session.scalars(stmt)).all()
    return {"items": [crypto_invoice_response(item) for item in items], "count": len(items)}


@router.patch("/crypto-invoices/{invoice_id}")
async def admin_update_crypto_invoice(
    invoice_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    item = await session.get(CryptoPaymentInvoice, invoice_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    allowed = {"pending_payment", "pending_review", "confirmed", "rejected", "expired", "refunded"}
    if "status" in payload:
        next_status = str(payload["status"])
        if next_status not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
        item.status = next_status
        if next_status in {"confirmed", "rejected", "refunded"}:
            item.reviewed_at = datetime.now(timezone.utc)
    if "note" in payload:
        item.note = payload["note"]
    await session.commit()
    await session.refresh(item)
    return crypto_invoice_response(item)


@router.get("/comments")
async def admin_comments(
    status_filter: str | None = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    stmt = (
        select(Comment, User)
        .join(User, User.id == Comment.user_id)
        .order_by(desc(Comment.created_at))
        .limit(min(max(limit, 1), 500))
    )
    if status_filter:
        stmt = stmt.where(Comment.status == status_filter)
    rows = (await session.execute(stmt)).all()
    return {"items": [comment_response(comment, user) for comment, user in rows], "count": len(rows)}


@router.patch("/comments/{comment_id}")
async def admin_update_comment(
    comment_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    item = await session.get(Comment, comment_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    allowed = {"visible", "hidden", "review"}
    if "status" in payload:
        next_status = str(payload["status"])
        if next_status not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
        item.status = next_status
    await session.commit()
    await session.refresh(item)
    return comment_response(item)
