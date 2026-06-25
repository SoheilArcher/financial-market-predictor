from datetime import datetime, timezone
from typing import Any

from app.collectors.binance import fetch_binance_klines
from app.services.analyzer import analyze_market, calculate_ema, calculate_rsi
from app.services.chart_data import ema_series, rsi_series


def parse_pair(symbol: str) -> tuple[str, str] | None:
    normalized = symbol.upper().replace(" ", "")
    if "/" not in normalized:
        return None
    base, quote = [part.strip() for part in normalized.split("/", 1)]
    if not base or not quote or base == quote:
        return None
    return base, quote


def pair_symbol(base: str, quote: str) -> str:
    return f"{base.upper()}/{quote.upper()}"


def _usdt_symbol(asset: str) -> str:
    return f"{asset.upper()}USDT"


def _ratio_candle(base_kline: list[Any], quote_kline: list[Any]) -> dict[str, Any]:
    quote_open = float(quote_kline[1])
    quote_high = float(quote_kline[2])
    quote_low = float(quote_kline[3])
    quote_close = float(quote_kline[4])
    base_open = float(base_kline[1])
    base_high = float(base_kline[2])
    base_low = float(base_kline[3])
    base_close = float(base_kline[4])
    ratio_open = base_open / quote_open if quote_open else 0
    ratio_high = base_high / quote_low if quote_low else 0
    ratio_low = base_low / quote_high if quote_high else 0
    ratio_close = base_close / quote_close if quote_close else 0
    return {
        "time": int(base_kline[0] / 1000),
        "timestamp": datetime.fromtimestamp(base_kline[0] / 1000, tz=timezone.utc).isoformat(),
        "open": round(ratio_open, 8),
        "high": round(max(ratio_open, ratio_high, ratio_low, ratio_close), 8),
        "low": round(min(ratio_open, ratio_high, ratio_low, ratio_close), 8),
        "close": round(ratio_close, 8),
        "volume": float(base_kline[5]),
    }


async def build_pair_candles(base: str, quote: str, timeframe: str = "5m", limit: int = 150) -> list[dict[str, Any]]:
    base_klines = await fetch_binance_klines(symbol=_usdt_symbol(base), interval=timeframe, limit=limit)
    quote_klines = await fetch_binance_klines(symbol=_usdt_symbol(quote), interval=timeframe, limit=limit)
    by_time = {item[0]: item for item in quote_klines}
    candles = []
    for base_item in base_klines:
        quote_item = by_time.get(base_item[0])
        if quote_item:
            candles.append(_ratio_candle(base_item, quote_item))
    return candles


async def fetch_pair_live_price(base: str, quote: str) -> dict[str, Any]:
    from app.services.live_price import fetch_live_price

    base_price = await fetch_live_price(_usdt_symbol(base), exchange="Binance")
    quote_price = await fetch_live_price(_usdt_symbol(quote), exchange="Binance")
    price = base_price["price"] / quote_price["price"] if quote_price["price"] else 0
    return {
        "exchange": "Synthetic",
        "source": f"Binance ratio {base.upper()}USDT / {quote.upper()}USDT",
        "symbol": pair_symbol(base, quote),
        "base_asset": base.upper(),
        "quote_asset": quote.upper(),
        "price": round(price, 8),
        "base_usdt_price": base_price["price"],
        "quote_usdt_price": quote_price["price"],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


async def build_pair_chart_data(base: str, quote: str, timeframe: str = "5m", limit: int = 150) -> dict[str, Any]:
    candles = await build_pair_candles(base=base, quote=quote, timeframe=timeframe, limit=limit)
    closes = [item["close"] for item in candles]
    live_price = await fetch_pair_live_price(base, quote)
    return {
        "exchange": "Synthetic",
        "symbol": pair_symbol(base, quote),
        "timeframe": timeframe,
        "pair_mode": True,
        "candles": candles,
        "indicators": {
            "ema20": ema_series(closes, 20),
            "ema50": ema_series(closes, 50),
            "rsi14": rsi_series(closes, 14),
        },
        "last": candles[-1] if candles else None,
        "live_price": live_price,
        "disclaimer": "Pair data is synthetic, calculated from Binance USDT markets.",
    }


async def analyze_pair_symbol(symbol: str, timeframe: str = "5m", limit: int = 100) -> dict[str, Any]:
    pair = parse_pair(symbol)
    if not pair:
        raise ValueError("Pair symbol must look like BTC/ETH")
    base, quote = pair
    candles = await build_pair_candles(base=base, quote=quote, timeframe=timeframe, limit=limit)
    result = analyze_market(candles=candles, symbol=pair_symbol(base, quote), timeframe=timeframe)
    result["pair_mode"] = True
    result["pair_explanation_fa"] = f"این تحلیل نسبت قیمت {base.upper()} به {quote.upper()} است؛ یعنی هر 1 {base.upper()} چند {quote.upper()} ارزش دارد."
    try:
        live_price = await fetch_pair_live_price(base, quote)
        from app.services.live_price import attach_live_price

        attach_live_price(result, live_price)
    except Exception as exc:
        result["live_price"] = {
            "exchange": "Synthetic",
            "symbol": pair_symbol(base, quote),
            "status": "unavailable",
            "message": str(exc),
        }
    return result
