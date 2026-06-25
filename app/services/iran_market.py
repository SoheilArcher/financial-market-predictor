import os
import time
from typing import Any

import httpx

BRS_API_KEY = os.getenv("BRS_API_KEY", "FreeSV0E1LSgB9RDjuf0QorSLViX8pPG")
BRS_ALL_SYMBOLS_URL = "https://Api.BrsApi.ir/Tsetmc/AllSymbols.php"
BRS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}
DEFAULT_IRAN_WATCHLIST = ["خودرو", "فولاد", "شتران", "شستا", "وبملت", "وتجارت", "فملی", "خساپا", "اهرم", "طلا"]

_CACHE: dict[str, Any] = {"fetched_at": 0.0, "items": []}


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    number = _to_float(value)
    return int(number) if number is not None else None


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _normalize_symbol(value: str) -> str:
    return _clean(value).replace(" ", "").replace("\u200c", "").lower()


def _market_signal(item: dict[str, Any]) -> tuple[str, int, str]:
    last_change = _to_float(item.get("plp")) or 0
    close_change = _to_float(item.get("pcp")) or 0
    buy_volume = sum(_to_float(item.get(f"qd{i}")) or 0 for i in range(1, 6))
    sell_volume = sum(_to_float(item.get(f"qo{i}")) or 0 for i in range(1, 6))
    last_price = _to_float(item.get("pl"))
    upper = _to_float(item.get("tmax"))
    lower = _to_float(item.get("tmin"))

    score = 50
    reasons: list[str] = []
    if last_change > 1 and close_change > 0:
        score += 15
        reasons.append("آخرین قیمت و قیمت پایانی مثبت هستند.")
    if last_change < -1 and close_change < 0:
        score -= 15
        reasons.append("آخرین قیمت و قیمت پایانی منفی هستند.")
    if buy_volume > sell_volume * 1.3:
        score += 10
        reasons.append("حجم تقاضای پنج ردیف اول از عرضه بیشتر است.")
    if sell_volume > buy_volume * 1.3:
        score -= 10
        reasons.append("حجم عرضه پنج ردیف اول از تقاضا بیشتر است.")
    if last_price and upper and last_price >= upper * 0.995:
        score += 10
        reasons.append("قیمت نزدیک سقف مجاز روزانه است.")
    if last_price and lower and last_price <= lower * 1.005:
        score -= 10
        reasons.append("قیمت نزدیک کف مجاز روزانه است.")

    score = max(0, min(100, score))
    if score >= 65:
        return "BUY", score, " ".join(reasons) or "قدرت نسبی خریدار بهتر است."
    if score <= 35:
        return "SELL", 100 - score, " ".join(reasons) or "فشار فروش غالب است."
    return "WAIT", score, "فعلاً برتری واضحی بین عرضه و تقاضا دیده نمی‌شود."


def _serialize(item: dict[str, Any]) -> dict[str, Any]:
    signal, confidence, reason_fa = _market_signal(item)
    return {
        "symbol": _clean(item.get("l18")),
        "name": _clean(item.get("l30")),
        "isin": _clean(item.get("isin")),
        "industry": _clean(item.get("cs")),
        "time": _clean(item.get("time")),
        "last_price": _to_float(item.get("pl")),
        "last_change": _to_float(item.get("plc")),
        "last_change_percent": _to_float(item.get("plp")),
        "close_price": _to_float(item.get("pc")),
        "close_change": _to_float(item.get("pcc")),
        "close_change_percent": _to_float(item.get("pcp")),
        "open_price": _to_float(item.get("pf")),
        "low_price": _to_float(item.get("pmin")),
        "high_price": _to_float(item.get("pmax")),
        "yesterday_price": _to_float(item.get("py")),
        "min_allowed": _to_float(item.get("tmin")),
        "max_allowed": _to_float(item.get("tmax")),
        "trade_count": _to_int(item.get("tno")),
        "trade_volume": _to_int(item.get("tvol")),
        "trade_value": _to_int(item.get("tval")),
        "market_value": _to_int(item.get("mv")),
        "eps": _to_float(item.get("eps")),
        "pe": _to_float(item.get("pe")),
        "best_bid_price": _to_float(item.get("pd1")),
        "best_bid_volume": _to_int(item.get("qd1")),
        "best_ask_price": _to_float(item.get("po1")),
        "best_ask_volume": _to_int(item.get("qo1")),
        "signal": signal,
        "confidence": confidence,
        "reason_fa": reason_fa,
        "source": "BRS API / TSETMC",
    }


async def fetch_iran_symbols(type_value: int = 1, ttl_seconds: int = 60) -> list[dict[str, Any]]:
    now = time.time()
    if _CACHE["items"] and now - _CACHE["fetched_at"] < ttl_seconds:
        return _CACHE["items"]

    params = {"key": BRS_API_KEY, "type": type_value}
    async with httpx.AsyncClient(timeout=25, headers=BRS_HEADERS) as client:
        response = await client.get(BRS_ALL_SYMBOLS_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    if isinstance(payload, dict):
        raw_items = payload.get("data") or payload.get("items") or payload.get("symbols") or []
    else:
        raw_items = payload
    if not isinstance(raw_items, list):
        raise ValueError("Invalid Iran market provider response")

    items = [_serialize(item) for item in raw_items if isinstance(item, dict) and item.get("l18")]
    _CACHE.update({"fetched_at": now, "items": items})
    return items


async def search_iran_symbols(query: str = "", limit: int = 20) -> list[dict[str, Any]]:
    items = await fetch_iran_symbols()
    q = _normalize_symbol(query)
    if not q:
        return items[:limit]
    matches = [
        item
        for item in items
        if q in _normalize_symbol(item["symbol"])
        or q in _normalize_symbol(item["name"])
        or q in _normalize_symbol(item["industry"])
    ]
    return matches[:limit]


async def find_iran_symbol(symbol: str) -> dict[str, Any] | None:
    normalized = _normalize_symbol(symbol)
    for item in await fetch_iran_symbols():
        if _normalize_symbol(item["symbol"]) == normalized:
            return item
    matches = await search_iran_symbols(symbol, limit=1)
    return matches[0] if matches else None


async def build_iran_market_overview(symbols: str | None = None, limit: int = 12) -> dict[str, Any]:
    selected = [item.strip() for item in (symbols or "").split(",") if item.strip()] or DEFAULT_IRAN_WATCHLIST
    results = []
    for symbol in selected[: max(1, min(limit, 30))]:
        item = await find_iran_symbol(symbol)
        if item:
            results.append(item)

    all_items = await fetch_iran_symbols()
    gainers = sorted(all_items, key=lambda item: item.get("last_change_percent") or -999, reverse=True)[:5]
    losers = sorted(all_items, key=lambda item: item.get("last_change_percent") or 999)[:5]
    leaders = sorted(all_items, key=lambda item: item.get("trade_value") or 0, reverse=True)[:5]

    return {
        "market_type": "iran",
        "symbols": results,
        "gainers": gainers,
        "losers": losers,
        "value_leaders": leaders,
        "count": len(results),
        "source": "BRS API / TSETMC",
        "summary_fa": "بازار ایران بر اساس داده‌های لحظه‌ای/تابلوی TSETMC بررسی شد. این خروجی توصیه مالی قطعی نیست.",
    }
