from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin import require_admin
from app.api.auth import get_session
from app.models.user import User
from app.services.revenue_share import (
    create_pool,
    get_or_create_rule,
    list_contributors,
    list_pools,
    mark_payout_paid,
    pool_summary,
    recalculate_pool,
    save_rule,
    upsert_contributor,
)

router = APIRouter(prefix="/admin/revenue", tags=["admin-revenue"])


class RulePayload(BaseModel):
    owner_percent: float = Field(ge=0, le=100)
    contributor_percent: float = Field(ge=0, le=100)
    currency: str = Field(default="USD", max_length=12)
    name: str = Field(default="Default revenue split", max_length=120)


class ContributorPayload(BaseModel):
    user_id: int
    manual_weight: float = Field(default=1, ge=0)
    role_label: str | None = Field(default=None, max_length=80)
    payout_method: str | None = Field(default=None, max_length=80)
    payout_account: str | None = None
    note: str | None = None
    status: str = Field(default="active", pattern="^(active|paused)$")


class PoolPayload(BaseModel):
    period: str = Field(max_length=20)
    gross_revenue: float = Field(ge=0)
    system_costs: float = Field(default=0, ge=0)
    note: str | None = None


@router.get("/rule")
async def revenue_rule(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    rule = await get_or_create_rule(session)
    return {
        "id": rule.id,
        "name": rule.name,
        "owner_percent": float(rule.owner_percent),
        "contributor_percent": float(rule.contributor_percent),
        "currency": rule.currency,
        "status": rule.status,
    }


@router.put("/rule")
async def update_revenue_rule(
    payload: RulePayload,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    try:
        rule = await save_rule(
            session,
            owner_percent=payload.owner_percent,
            contributor_percent=payload.contributor_percent,
            currency=payload.currency,
            name=payload.name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "id": rule.id,
        "name": rule.name,
        "owner_percent": float(rule.owner_percent),
        "contributor_percent": float(rule.contributor_percent),
        "currency": rule.currency,
        "status": rule.status,
    }


@router.get("/contributors")
async def contributors(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    return {"items": await list_contributors(session)}


@router.post("/contributors")
async def save_contributor(
    payload: ContributorPayload,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    try:
        contributor = await upsert_contributor(
            session=session,
            user_id=payload.user_id,
            manual_weight=payload.manual_weight,
            role_label=payload.role_label,
            payout_method=payload.payout_method,
            payout_account=payload.payout_account,
            note=payload.note,
            status=payload.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"id": contributor.id, "user_id": contributor.user_id, "status": contributor.status}


@router.get("/pools")
async def pools(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    return {"items": await list_pools(session)}


@router.post("/pools")
async def save_pool(
    payload: PoolPayload,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    pool = await create_pool(
        session=session,
        period=payload.period,
        gross_revenue=payload.gross_revenue,
        system_costs=payload.system_costs,
        note=payload.note,
    )
    return await pool_summary(session, pool.id)


@router.post("/pools/{pool_id}/recalculate")
async def recalculate(
    pool_id: int,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    try:
        return await recalculate_pool(session, pool_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/pools/{pool_id}")
async def pool_detail(
    pool_id: int,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    try:
        return await pool_summary(session, pool_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/payouts/{payout_id}/paid")
async def payout_paid(
    payout_id: int,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    try:
        return await mark_payout_paid(session, payout_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
