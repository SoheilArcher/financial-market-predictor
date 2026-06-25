from fastapi import APIRouter, Body, Depends, HTTPException

from app.api.auth import get_current_user
from app.models.user import User
from app.services.iran_yield import build_iran_fixed_income_quote

router = APIRouter(prefix="/iran-yield", tags=["iran-yield"])


@router.post("/quote")
async def iran_fixed_income_quote(
    payload: dict = Body(...),
    current_user: User = Depends(get_current_user),
):
    try:
        return build_iran_fixed_income_quote(
            capital_amount=float(payload.get("capital_amount") or 0),
            annual_return_percent=float(payload.get("annual_return_percent") or 35),
            platform_fee_percent=float(payload.get("platform_fee_percent") if payload.get("platform_fee_percent") is not None else 5),
            tax_percent=float(payload.get("tax_percent") if payload.get("tax_percent") is not None else 0),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
