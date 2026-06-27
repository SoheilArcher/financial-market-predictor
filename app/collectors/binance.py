from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.database import AsyncSessionLocal
from app.models.market import Exchange, Symbol, Candle


BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"


async def get_or_create_exchange(session, name: str):
    result = await session.execute(
        select(Exchange).where(Exchange.name == name)
    )
    exchange = result.scalar_one_or_none()

    if exchange:
        return exchange

    exchange = Exchange(name=name, type="crypto", status="active")
    session.add(exchange)
    await session.flush()
    return exchange


async def get_or_create_symbol(session, exchange_id: int, symbol: str):
    base_asset = symbol.replace("USDT", "")
    quote_asset = "USDT"

    result = await session.execute(
        select(Symbol).where(
            Symbol.exchange_id == exchange_id,
            Symbol.symbol == symbol
        )
    )
    db_symbol = result.scalar_one_or_none()

    if db_symbol:
        return db_symbol

    db_symbol = Symbol(
        exchange_id=exchange_id,
        symbol=symbol,
        base_asset=base_asset,
        quote_asset=quote_asset,
    )
    session.add(db_symbol)
    await session.flush()
    return db_symbol


_KLINES_CACHE = {}
_KLINES_CACHE_TTL = 10.0


async def fetch_binance_klines(symbol="BTCUSDT", interval="5m", limit=100):
    import time
    key = (symbol, interval, limit)
    now = time.monotonic()
    cached = _KLINES_CACHE.get(key)
    if cached and (now - cached[0]) < _KLINES_CACHE_TTL:
        return cached[1]
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(BINANCE_KLINES_URL, params=params)
        response.raise_for_status()
        data = response.json()
    _KLINES_CACHE[key] = (now, data)
    if len(_KLINES_CACHE) > 500:
        oldest = min(_KLINES_CACHE, key=lambda k: _KLINES_CACHE[k][0])
        _KLINES_CACHE.pop(oldest, None)
    return data


async def save_binance_candles(symbol: str = "BTCUSDT", interval: str = "5m", limit: int = 100):
    klines = await fetch_binance_klines(symbol=symbol, interval=interval, limit=limit)

    async with AsyncSessionLocal() as session:
        exchange = await get_or_create_exchange(session, "Binance")
        db_symbol = await get_or_create_symbol(session, exchange.id, symbol)

        rows = []

        for k in klines:
            rows.append({
                "symbol_id": db_symbol.id,
                "timeframe": interval,
                "timestamp": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc),
                "open": k[1],
                "high": k[2],
                "low": k[3],
                "close": k[4],
                "volume": k[5],
            })

        stmt = insert(Candle).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["symbol_id", "timeframe", "timestamp"]
        )

        await session.execute(stmt)
        await session.commit()

    return {
        "exchange": "Binance",
        "symbol": symbol,
        "interval": interval,
        "saved": len(rows),
    }


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(save_binance_candles())
    print(result)
