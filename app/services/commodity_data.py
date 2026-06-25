from datetime import datetime, timezone
from typing import Any

import httpx

from app.services.analyzer import analyze_market
from app.services.live_price import attach_live_price

YAHOO_CHART_URL = "https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
YAHOO_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

COMMODITY_SYMBOLS = {
    "XAUUSD": {
        "provider_symbol": "GC=F",
        "name_fa": "طلا",
        "name_en": "Gold",
        "aliases": ["GOLD", "XAU", "طلا"],
        "unit": "USD per troy ounce",
    },
    "XAGUSD": {
        "provider_symbol": "SI=F",
        "name_fa": "نقره",
        "name_en": "Silver",
        "aliases": ["SILVER", "XAG", "نقره"],
        "unit": "USD per troy ounce",
    },
    "WTIUSD": {
        "provider_symbol": "CL=F",
        "name_fa": "نفت خام WTI",
        "name_en": "WTI Crude Oil",
        "aliases": ["USOIL", "OIL", "WTI", "نفت"],
        "unit": "USD per barrel",
    },
    "BRENTUSD": {
        "provider_symbol": "BZ=F",
        "name_fa": "نفت برنت",
        "name_en": "Brent Crude Oil",
        "aliases": ["UKOIL", "BRENT", "برنت"],
        "unit": "USD per barrel",
    },
    "NGAS": {
        "provider_symbol": "NG=F",
        "name_fa": "گاز طبیعی",
        "name_en": "Natural Gas",
        "aliases": ["NATGAS", "NATURALGAS", "GAS", "گاز"],
        "unit": "USD per MMBtu",
    },
    "COPPER": {
        "provider_symbol": "HG=F",
        "name_fa": "مس",
        "name_en": "Copper",
        "aliases": ["HG", "COPPERUSD", "مس"],
        "unit": "USD per pound",
    },
}

ALIAS_TO_SYMBOL = {
    alias.upper(): symbol
    for symbol, item in COMMODITY_SYMBOLS.items()
    for alias in [symbol, *item["aliases"]]
}

INTERVALS = {
    "1m": ("1m", "1d"),
    "5m": ("5m", "5d"),
    "15m": ("15m", "5d"),
    "1h": ("1h", "1mo"),
    "4h": ("1h", "3mo"),
    "1d": ("1d", "1y"),
}


def normalize_commodity_symbol(symbol: str) -> str | None:
    normalized = (symbol or "").strip().upper().replace("/", "").replace(" ", "")
    return ALIAS_TO_SYMBOL.get(normalized)


def is_commodity_symbol(symbol: str) -> bool:
    return normalize_commodity_symbol(symbol) is not None


def commodity_suggestions(query: str) -> list[dict[str, Any]]:
    q = (query or "").strip().upper()
    if not q:
        return []
    items = []
    for symbol, meta in COMMODITY_SYMBOLS.items():
        haystack = [symbol, meta["name_en"].upper(), meta["name_fa"], *meta["aliases"]]
        if any(q in value.upper() for value in haystack):
            items.append(
                {
                    "symbol": symbol,
                    "label": f"{symbol} - {meta['name_fa']}",
                    "type": "commodity",
                    "description": f"{meta['name_fa']} / {meta['name_en']} - {meta['unit']}",
                }
            )
    return items


def _timestamp_to_iso(value: int) -> str:
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


async def fetch_commodity_candles(symbol: str, timeframe: str = "5m", limit: int = 150) -> list[dict[str, Any]]:
    normalized = normalize_commodity_symbol(symbol)
    if not normalized:
        raise ValueError(f"Unsupported commodity symbol: {symbol}")

    interval, range_value = INTERVALS.get(timeframe, INTERVALS["5m"])
    provider_symbol = COMMODITY_SYMBOLS[normalized]["provider_symbol"]
    params = {
        "interval": interval,
        "range": range_value,
        "includePrePost": "false",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            YAHOO_CHART_URL.format(symbol=provider_symbol),
            params=params,
            headers=YAHOO_HEADERS,
        )
        response.raise_for_status()
        payload = response.json()

    result = payload["chart"]["result"][0]
    timestamps = result.get("timestamp") or []
    quote = result["indicators"]["quote"][0]
    candles = []
    for index, timestamp in enumerate(timestamps):
        values = {
            "open": quote.get("open", [])[index],
            "high": quote.get("high", [])[index],
            "low": quote.get("low", [])[index],
            "close": quote.get("close", [])[index],
            "volume": quote.get("volume", [0])[index] or 0,
        }
        if any(values[key] is None for key in ("open", "high", "low", "close")):
            continue
        candles.append(
            {
                "time": int(timestamp),
                "timestamp": _timestamp_to_iso(int(timestamp)),
                "open": float(values["open"]),
                "high": float(values["high"]),
                "low": float(values["low"]),
                "close": float(values["close"]),
                "volume": float(values["volume"]),
            }
        )
    return candles[-limit:]


async def fetch_commodity_live_price(symbol: str) -> dict[str, Any]:
    normalized = normalize_commodity_symbol(symbol)
    candles = await fetch_commodity_candles(normalized or symbol, timeframe="1m", limit=1)
    if not candles:
        raise ValueError(f"No live price for commodity: {symbol}")
    meta = COMMODITY_SYMBOLS[normalized]
    return {
        "exchange": "Yahoo Finance",
        "source": f"Yahoo Finance {meta['provider_symbol']}",
        "symbol": normalized,
        "base_asset": normalized,
        "quote_asset": "USD",
        "price": round(float(candles[-1]["close"]), 6),
        "name_fa": meta["name_fa"],
        "name_en": meta["name_en"],
        "unit": meta["unit"],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


async def build_commodity_chart_data(symbol: str, timeframe: str = "5m", limit: int = 150) -> dict[str, Any]:
    from app.services.chart_data import ema_series, rsi_series

    normalized = normalize_commodity_symbol(symbol)
    candles = await fetch_commodity_candles(normalized or symbol, timeframe=timeframe, limit=limit)
    closes = [item["close"] for item in candles]
    live_price = await fetch_commodity_live_price(normalized or symbol)
    meta = COMMODITY_SYMBOLS[normalized]
    return {
        "exchange": "Yahoo Finance",
        "symbol": normalized,
        "display_name": meta["name_fa"],
        "timeframe": timeframe,
        "market_type": "commodity",
        "candles": candles,
        "indicators": {
            "ema20": ema_series(closes, 20),
            "ema50": ema_series(closes, 50),
            "rsi14": rsi_series(closes, 14),
        },
        "last": candles[-1] if candles else None,
        "live_price": live_price,
        "disclaimer": "Commodity data is sourced from Yahoo Finance futures feeds and is for analysis only.",
    }


async def analyze_commodity_symbol(symbol: str, timeframe: str = "5m", limit: int = 100) -> dict[str, Any]:
    normalized = normalize_commodity_symbol(symbol)
    candles = await fetch_commodity_candles(normalized or symbol, timeframe=timeframe, limit=limit)
    result = analyze_market(candles=candles, symbol=normalized, timeframe=timeframe)
    result["market_type"] = "commodity"
    result["exchange"] = "Yahoo Finance"
    result["summary_fa"] = f"{COMMODITY_SYMBOLS[normalized]['name_fa']}: {result.get('summary_fa', '')}"
    try:
        attach_live_price(result, await fetch_commodity_live_price(normalized or symbol))
    except Exception as exc:
        result["live_price"] = {
            "exchange": "Yahoo Finance",
            "symbol": normalized,
            "status": "unavailable",
            "message": str(exc),
        }
    return result
