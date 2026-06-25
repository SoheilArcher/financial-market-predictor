from fastapi import APIRouter, Depends, Query

from app.api.auth import get_current_user
from app.models.user import User
from app.services.symbol_search import build_symbol_suggestions

router = APIRouter(prefix="/symbols", tags=["symbols"])


@router.get("/search")
async def search_symbols(
    q: str = Query("", max_length=40),
    limit: int = Query(12, ge=1, le=30),
    current_user: User = Depends(get_current_user),
):
    return {
        "items": build_symbol_suggestions(q, limit),
        "user_id": current_user.id,
    }
