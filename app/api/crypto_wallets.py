from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_session
from app.models.user import User
from app.services.crypto_wallets import create_wallet, list_wallets, serialize_wallet

router = APIRouter(prefix="/crypto-wallets", tags=["crypto-wallets"])


@router.post("")
async def register_wallet(
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        wallet = await create_wallet(session=session, user=current_user, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_wallet(wallet)


@router.get("")
async def my_wallets(
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    wallets = await list_wallets(session=session, user_id=current_user.id, limit=limit)
    return {
        "items": [serialize_wallet(wallet) for wallet in wallets],
        "count": len(wallets),
        "summary_fa": "کیف پول‌های غیرامانی ثبت‌شده برای پرداخت/تسویه کریپتویی.",
    }
