from datetime import datetime, timezone
from typing import Any

import httpx


BINANCE_TICKER_PRICE_URL = "https://api.binance.com/api/v3/ticker/price"


def _asset_parts(symbol: str) -> tuple[str, str]:
    normalized = symbol.upper().replace("/", "")
    for quote in ("USDT", "USDC", "BUSD", "BTC", "ETH", "TRY", "EUR"):
        if normalized.endswith(quote) and len(normalized) > len(quote):
            return normalized[: -len(quote)], quote
    return normalized, ""


async def fetch_live_price(symbol: str, exchange: str = "Binance") -> dict[str, Any]:
    normalized_symbol = symbol.upper().replace("/", "")
    if exchange.lower() != "binance":
        raise ValueError(f"Live price is not supported for exchange: {exchange}")

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(BINANCE_TICKER_PRICE_URL, params={"symbol": normalized_symbol})
        response.raise_for_status()
        payload = response.json()

    base_asset, quote_asset = _asset_parts(normalized_symbol)
    return {
        "exchange": "Binance",
        "source": "Binance ticker price",
        "symbol": normalized_symbol,
        "base_asset": base_asset,
        "quote_asset": quote_asset,
        "price": round(float(payload["price"]), 8),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def attach_live_price(
    payload: dict[str, Any],
    live_price: dict[str, Any] | None,
    analysis_price_key: str = "price",
) -> dict[str, Any]:
    if not live_price:
        return payload

    analysis_price = payload.get(analysis_price_key)
    payload["candle_price"] = analysis_price
    payload["price"] = live_price["price"]
    payload["live_price"] = live_price

    if analysis_price:
        delta = ((live_price["price"] - float(analysis_price)) / float(analysis_price)) * 100
        payload["live_price"]["delta_from_candle_percent"] = round(delta, 4)
    return payload
