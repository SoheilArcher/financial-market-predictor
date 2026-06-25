from app.services.commodity_data import commodity_suggestions

POPULAR_ASSETS = [
    "BTC",
    "ETH",
    "BNB",
    "SOL",
    "XRP",
    "ADA",
    "DOGE",
    "LINK",
    "AVAX",
    "TON",
    "TRX",
    "DOT",
    "MATIC",
    "LTC",
    "BCH",
    "ATOM",
    "NEAR",
    "APT",
    "ARB",
    "OP",
    "UNI",
    "AAVE",
    "FIL",
    "ETC",
    "ICP",
    "INJ",
    "SUI",
    "PEPE",
    "SHIB",
]

POPULAR_QUOTES = ["USDT", "USDC", "BTC", "ETH"]


def _clean_symbol(value: str) -> str:
    return (value or "").strip().upper().replace(" ", "")


def _description(symbol: str, kind: str) -> str:
    if kind == "commodity":
        return f"کالای جهانی {symbol}"
    if kind == "pair":
        return f"جفت ارز {symbol} برای مقایسه نسبی دو دارایی"
    return f"نماد معاملاتی {symbol} در بازار اسپات"


def _item(symbol: str, kind: str) -> dict:
    return {
        "symbol": symbol,
        "label": symbol,
        "type": kind,
        "description": _description(symbol, kind),
    }


def build_symbol_suggestions(query: str, limit: int = 12) -> list[dict]:
    q = _clean_symbol(query)
    max_items = max(1, min(limit, 30))
    suggestions: list[dict] = []
    seen: set[str] = set()

    def add(symbol: str, kind: str) -> None:
        if len(suggestions) >= max_items:
            return
        if symbol in seen:
            return
        seen.add(symbol)
        suggestions.append(_item(symbol, kind))

    for item in commodity_suggestions(query):
        if len(suggestions) >= max_items:
            break
        if item["symbol"] not in seen:
            seen.add(item["symbol"])
            suggestions.append(item)

    if "/" in q:
        base_query, quote_query = (q.split("/", 1) + [""])[:2]
        bases = [asset for asset in POPULAR_ASSETS if not base_query or asset.startswith(base_query)]
        quotes = [asset for asset in POPULAR_ASSETS if asset != base_query and (not quote_query or asset.startswith(quote_query))]
        if base_query and base_query not in bases and len(base_query) >= 2:
            bases.insert(0, base_query)
        for base in bases:
            for quote in quotes:
                if base != quote:
                    add(f"{base}/{quote}", "pair")
        return suggestions

    compact_matches = [
        f"{asset}{quote}"
        for asset in POPULAR_ASSETS
        for quote in POPULAR_QUOTES
        if asset != quote and not (asset == "BTC" and quote == "ETH") and f"{asset}{quote}".startswith(q)
    ]
    for symbol in compact_matches:
        add(symbol, "spot")

    asset_matches = [asset for asset in POPULAR_ASSETS if asset.startswith(q)]
    for asset in asset_matches:
        add(f"{asset}USDT", "spot")
        if asset != "ETH":
            add(f"{asset}/ETH", "pair")
        if asset != "BTC":
            add(f"{asset}/BTC", "pair")

    if len(q) >= 2:
        for asset in POPULAR_ASSETS:
            if q in asset:
                add(f"{asset}USDT", "spot")

    return suggestions
