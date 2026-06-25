from fastapi import APIRouter, Depends

from app.api.auth import get_current_user
from app.models.user import User
from app.services.news_analyzer import build_news_report

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/market")
async def market_news(
    symbols: str | None = None,
    limit: int = 20,
    _: User = Depends(get_current_user),
):
    return await build_news_report(symbols=symbols, limit=limit)
