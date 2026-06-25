from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import get_current_user
from app.models.user import User
from app.services.iran_market import build_iran_market_overview, find_iran_symbol, search_iran_symbols

router = APIRouter(prefix="/iran-market", tags=["iran-market"])


@router.get("/overview")
async def iran_market_overview(
    symbols: str | None = None,
    limit: int = Query(12, ge=1, le=30),
    current_user: User = Depends(get_current_user),
):
    try:
        return await build_iran_market_overview(symbols=symbols, limit=limit)
    except Exception as exc:
        return {
            "market_type": "iran",
            "symbols": [],
            "gainers": [],
            "losers": [],
            "value_leaders": [],
            "count": 0,
            "source": "BRS API / TSETMC",
            "status": "NO_DATA",
            "summary_fa": f"فعلاً داده بازار ایران در دسترس نیست: {exc}",
        }


@router.get("/search")
async def iran_market_search(
    q: str = Query("", max_length=80),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    try:
        return {"items": await search_iran_symbols(query=q, limit=limit)}
    except Exception as exc:
        return {"items": [], "status": "NO_DATA", "summary_fa": f"جست‌وجوی نمادهای ایران فعلاً در دسترس نیست: {exc}"}


@router.get("/analyze/{symbol}")
async def iran_market_analyze(
    symbol: str,
    current_user: User = Depends(get_current_user),
):
    try:
        item = await find_iran_symbol(symbol)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Iran market data unavailable: {exc}") from exc
    if not item:
        raise HTTPException(status_code=404, detail="Iran market symbol not found")
    return {
        "market_type": "iran",
        "symbol": item["symbol"],
        "signal": item["signal"],
        "confidence": item["confidence"],
        "price": item["last_price"],
        "summary_fa": item["reason_fa"],
        "raw": item,
        "source": item["source"],
    }
