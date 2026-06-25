from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.models.managed_portfolio import ManagedPortfolioRequest
from app.models.user import User
from app.services.managed_portfolio import (
    build_net_report,
    create_managed_request,
    list_user_requests,
    serialize_request,
    update_request_report,
)

router = APIRouter(prefix="/managed-portfolios", tags=["managed-portfolios"])


@router.post("/requests")
async def create_request(
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        item = await create_managed_request(session=session, user=current_user, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_request(item)


@router.get("/requests")
async def my_requests(
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    items = await list_user_requests(session=session, user_id=current_user.id, limit=limit)
    return {
        "items": [serialize_request(item) for item in items],
        "count": len(items),
        "summary_fa": "درخواست‌های مدیریت/کپی‌پرتفوی شما.",
    }


@router.post("/net-report")
async def net_report(payload: dict = Body(...), current_user: User = Depends(get_current_user)):
    capital_amount = float(payload.get("capital_amount") or 0)
    if capital_amount <= 0:
        raise HTTPException(status_code=400, detail="capital_amount must be greater than zero")
    return build_net_report(
        capital_amount=capital_amount,
        gross_profit_percent=float(payload.get("gross_profit_percent") or 0),
        fee_percent=float(payload.get("fee_percent") if payload.get("fee_percent") is not None else 5),
        tax_percent=float(payload.get("tax_percent") if payload.get("tax_percent") is not None else 0),
    )


@router.patch("/requests/{request_id}/report")
async def patch_report(
    request_id: int,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = await session.get(ManagedPortfolioRequest, request_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Request not found")
    updated = await update_request_report(
        session=session,
        item=item,
        gross_profit_percent=float(payload.get("gross_profit_percent") or 0),
    )
    return serialize_request(updated)
