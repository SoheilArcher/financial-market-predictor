from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from xml.etree import ElementTree

import httpx


NEWS_SOURCES = [
    {
        "name": "CoinDesk",
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "weight": 0.9,
    },
    {
        "name": "Cointelegraph",
        "url": "https://cointelegraph.com/rss",
        "weight": 0.85,
    },
]

SYMBOL_KEYWORDS = {
    "BTCUSDT": ["btc", "bitcoin"],
    "ETHUSDT": ["eth", "ether", "ethereum"],
    "BNBUSDT": ["bnb", "binance"],
    "SOLUSDT": ["sol", "solana"],
    "XRPUSDT": ["xrp", "ripple"],
    "ADAUSDT": ["ada", "cardano"],
    "DOGEUSDT": ["doge", "dogecoin"],
    "LINKUSDT": ["link", "chainlink"],
    "AVAXUSDT": ["avax", "avalanche"],
    "TONUSDT": ["ton", "toncoin"],
}

POSITIVE_WORDS = [
    "approve",
    "approved",
    "approval",
    "adoption",
    "bull",
    "bullish",
    "buy",
    "gain",
    "gains",
    "growth",
    "institutional",
    "launch",
    "rally",
    "record",
    "rise",
    "surge",
]

NEGATIVE_WORDS = [
    "ban",
    "bear",
    "bearish",
    "crackdown",
    "crash",
    "decline",
    "drop",
    "exploit",
    "fall",
    "fraud",
    "hack",
    "lawsuit",
    "limit",
    "limits",
    "liquidation",
    "regulation",
    "restrictions",
    "restrict",
    "restricted",
    "risk",
    "sell",
    "slump",
]


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def _text_of(item: ElementTree.Element, name: str) -> str:
    child = item.find(name)
    if child is not None and child.text:
        return child.text.strip()
    for element in item:
        if element.tag.endswith(name) and element.text:
            return element.text.strip()
    return ""


def _symbol_filter(symbols: str | None) -> set[str]:
    if not symbols:
        return set(SYMBOL_KEYWORDS)
    result = set()
    for symbol in symbols.split(","):
        normalized = symbol.strip().upper().replace("/", "")
        if normalized:
            result.add(normalized)
    return result or set(SYMBOL_KEYWORDS)


def _related_symbols(text: str, wanted: set[str]) -> list[str]:
    lowered = text.lower()
    related = []
    for symbol, keywords in SYMBOL_KEYWORDS.items():
        if symbol not in wanted:
            continue
        if any(re.search(rf"\b{re.escape(keyword)}\b", lowered) for keyword in keywords):
            related.append(symbol)
    if "MARKET" in wanted and not related:
        related.append("MARKET")
    return related


def _impact(text: str) -> tuple[str, int, list[str]]:
    lowered = text.lower()
    positives = [word for word in POSITIVE_WORDS if re.search(rf"\b{re.escape(word)}\b", lowered)]
    negatives = [word for word in NEGATIVE_WORDS if re.search(rf"\b{re.escape(word)}\b", lowered)]
    score = len(positives) - len(negatives)
    if score > 0:
        return "POSITIVE", min(85, 50 + score * 10), positives[:5]
    if score < 0:
        return "NEGATIVE", min(85, 50 + abs(score) * 10), negatives[:5]
    return "NEUTRAL", 45, []


def _summary_fa(impact: str, symbols: list[str]) -> str:
    target = "، ".join(symbols) if symbols else "کل بازار"
    if impact == "POSITIVE":
        return f"این خبر برای {target} اثر مثبت احتمالی دارد، اما نیاز به تایید قیمت و حجم دارد."
    if impact == "NEGATIVE":
        return f"این خبر می‌تواند برای {target} ریسک منفی ایجاد کند؛ مدیریت حد ضرر مهم است."
    return f"اثر خبر روی {target} هنوز واضح نیست و باید با رفتار قیمت مقایسه شود."


async def _fetch_source(client: httpx.AsyncClient, source: dict[str, Any]) -> list[dict[str, Any]]:
    response = await client.get(source["url"])
    response.raise_for_status()
    root = ElementTree.fromstring(response.text)
    items = []
    for item in root.findall(".//item")[:30]:
        title = _strip_html(_text_of(item, "title"))
        link = _text_of(item, "link")
        description = _strip_html(_text_of(item, "description"))
        published_at = _parse_date(_text_of(item, "pubDate"))
        if title:
            items.append(
                {
                    "source": source["name"],
                    "source_weight": source["weight"],
                    "title": title,
                    "url": link,
                    "description": description[:280],
                    "published_at": published_at,
                }
            )
    return items


def _verify_items(items: list[dict[str, Any]]) -> None:
    by_symbol: dict[str, set[str]] = {}
    for item in items:
        for symbol in item["symbols"]:
            if symbol == "MARKET":
                continue
            by_symbol.setdefault(symbol, set()).add(item["source"])
    for item in items:
        source_count = max([len(by_symbol.get(symbol, set())) for symbol in item["symbols"] if symbol != "MARKET"] or [1])
        item["source_count_for_symbol"] = source_count
        item["verification"] = "cross_source" if source_count >= 2 else "single_source"
        if source_count >= 2:
            item["confidence"] = min(95, item["confidence"] + 10)


async def build_news_report(symbols: str | None = None, limit: int = 20) -> dict[str, Any]:
    wanted = _symbol_filter(symbols)
    wanted.add("MARKET")
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        results = await asyncio_gather_sources(client)

    raw_items = [item for group in results for item in group]
    items = []
    seen_urls = set()
    for item in raw_items:
        if item["url"] in seen_urls:
            continue
        seen_urls.add(item["url"])
        text = f"{item['title']} {item['description']}"
        related = _related_symbols(text, wanted)
        if not related:
            continue
        impact, confidence, triggers = _impact(text)
        item.update(
            {
                "symbols": related,
                "impact": impact,
                "confidence": round(confidence * item.pop("source_weight"), 1),
                "triggers": triggers,
                "summary_fa": _summary_fa(impact, related),
            }
        )
        items.append(item)

    _verify_items(items)
    items.sort(key=lambda item: item["published_at"], reverse=True)
    selected = items[: max(1, min(limit, 50))]
    impact_counts = {
        "positive": sum(1 for item in selected if item["impact"] == "POSITIVE"),
        "negative": sum(1 for item in selected if item["impact"] == "NEGATIVE"),
        "neutral": sum(1 for item in selected if item["impact"] == "NEUTRAL"),
    }
    if impact_counts["positive"] > impact_counts["negative"]:
        mood = "NEWS_POSITIVE"
        summary = "اخبار اخیر کمی به نفع بازار است، اما باید با قیمت زنده و حجم تایید شود."
    elif impact_counts["negative"] > impact_counts["positive"]:
        mood = "NEWS_NEGATIVE"
        summary = "اخبار اخیر ریسک منفی بیشتری نشان می‌دهد؛ ورود بدون حد ضرر مناسب نیست."
    else:
        mood = "NEWS_MIXED"
        summary = "اخبار جهت یکدست ندارد؛ بهتر است هر نماد جداگانه با چارت بررسی شود."

    return {
        "generated_at": datetime.now(timezone.utc),
        "sources": [source["name"] for source in NEWS_SOURCES],
        "symbols": sorted(wanted - {"MARKET"}),
        "summary": {
            "mood": mood,
            "summary_fa": summary,
            **impact_counts,
        },
        "items": selected,
        "disclaimer": "این تحلیل خبر، اعتبارسنجی حقوقی خبر نیست و فقط اثر احتمالی خبر روی بازار را تخمین می‌زند.",
    }


async def asyncio_gather_sources(client: httpx.AsyncClient) -> list[list[dict[str, Any]]]:
    import asyncio

    tasks = [_fetch_source(client, source) for source in NEWS_SOURCES]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [result for result in results if isinstance(result, list)]
