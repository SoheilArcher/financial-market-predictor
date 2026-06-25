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
    "XAUUSD": ["gold", "xau", "bullion"],
    "XAGUSD": ["silver", "xag"],
    "WTIUSD": ["oil", "crude", "wti"],
    "BRENTUSD": ["brent", "oil", "crude"],
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


def _summary_en(impact: str, symbols: list[str]) -> str:
    target = ", ".join(symbols) if symbols else "the market"
    if impact == "POSITIVE":
        return f"This news may be positive for {target}, but price and volume confirmation are still needed."
    if impact == "NEGATIVE":
        return f"This news may add downside risk for {target}; risk management is important."
    return f"The market impact on {target} is not clear yet and should be compared with price action."


def _display_title_fa(item: dict[str, Any], impact: str, symbols: list[str]) -> str:
    target = "، ".join(symbols) if symbols else "کل بازار"
    source = item.get("source", "منبع خبری")
    if impact == "POSITIVE":
        return f"خبر مثبت احتمالی از {source} درباره {target}"
    if impact == "NEGATIVE":
        return f"خبر هشداردهنده از {source} درباره {target}"
    return f"خبر قابل بررسی از {source} درباره {target}"


def _description_fa(impact: str, triggers: list[str], original_title: str) -> str:
    trigger_text = "، ".join(triggers) if triggers else "کلمات کلیدی مشخصی"
    if impact == "POSITIVE":
        return f"در متن خبر نشانه‌های مثبت مثل {trigger_text} دیده شده است. عنوان اصلی منبع: {original_title}"
    if impact == "NEGATIVE":
        return f"در متن خبر نشانه‌های ریسکی مثل {trigger_text} دیده شده است. عنوان اصلی منبع: {original_title}"
    return f"اثر خبر هنوز قطعی نیست و باید با قیمت و حجم مقایسه شود. عنوان اصلی منبع: {original_title}"


TOPIC_FA = [
    (["etf", "fund"], "موضوع خبر درباره صندوق‌های قابل معامله و ورود سرمایه نهادی است."),
    (["fed", "rate", "inflation"], "موضوع خبر به نرخ بهره، تورم یا سیاست پولی آمریکا مربوط است."),
    (["hack", "exploit", "fraud"], "خبر به رخداد امنیتی، هک یا ریسک اعتماد در بازار اشاره دارد."),
    (["lawsuit", "sec", "regulation", "ban", "crackdown"], "خبر به فشار حقوقی یا قانون‌گذاری مربوط است."),
    (["liquidation", "leverage"], "خبر درباره لیکویید شدن موقعیت‌ها و ریسک معاملات اهرمی است."),
    (["rally", "surge", "gain", "record"], "خبر از رشد قیمت یا افزایش تقاضا صحبت می‌کند."),
    (["drop", "fall", "decline", "slump"], "خبر از افت قیمت یا فشار فروش صحبت می‌کند."),
    (["gold", "bullion"], "خبر به بازار طلا و تقاضای دارایی امن مربوط است."),
    (["silver"], "خبر به بازار نقره و فلزات گران‌بها مربوط است."),
    (["oil", "crude", "brent", "wti"], "خبر به نفت، انرژی و انتظارات عرضه و تقاضا مربوط است."),
]

TRIGGER_FA = {
    "approve": "تایید",
    "approved": "تایید",
    "approval": "تایید",
    "adoption": "پذیرش",
    "bull": "روند صعودی",
    "bullish": "روند صعودی",
    "buy": "خرید",
    "gain": "رشد",
    "gains": "رشد",
    "growth": "رشد",
    "institutional": "ورود سرمایه نهادی",
    "launch": "راه‌اندازی",
    "rally": "رالی صعودی",
    "record": "رکورد جدید",
    "rise": "افزایش",
    "surge": "جهش قیمت",
    "ban": "ممنوعیت",
    "bear": "روند نزولی",
    "bearish": "روند نزولی",
    "crackdown": "برخورد نظارتی",
    "crash": "ریزش",
    "decline": "افت",
    "drop": "افت",
    "exploit": "رخداد امنیتی",
    "fall": "ریزش",
    "fraud": "تقلب",
    "hack": "هک",
    "lawsuit": "پرونده حقوقی",
    "limit": "محدودیت",
    "limits": "محدودیت",
    "liquidation": "لیکویید شدن",
    "regulation": "قانون‌گذاری",
    "restrictions": "محدودیت",
    "restrict": "محدودسازی",
    "restricted": "محدود شده",
    "risk": "ریسک",
    "sell": "فروش",
    "slump": "افت شدید",
}


def _topic_fa(text: str) -> str:
    lowered = text.lower()
    for keywords, topic in TOPIC_FA:
        if any(keyword in lowered for keyword in keywords):
            return topic
    return "خبر درباره یکی از عوامل اثرگذار روی بازار است، اما موضوع آن نیاز به بررسی کنار چارت دارد."


def _plain_news_fa(item: dict[str, Any], impact: str, symbols: list[str], triggers: list[str]) -> str:
    source = item.get("source", "منبع خبری")
    target = "، ".join(symbols) if symbols else "بازار"
    source_text = f"{item.get('title', '')}. {item.get('description', '')}"
    topic = _topic_fa(source_text)
    trigger_text = "، ".join(TRIGGER_FA.get(trigger, trigger) for trigger in triggers) if triggers else "نشانه قطعی مثبت یا منفی"
    if impact == "POSITIVE":
        effect = "برداشت اولیه سیستم این است که خبر می‌تواند کمی به نفع خریداران باشد."
    elif impact == "NEGATIVE":
        effect = "برداشت اولیه سیستم این است که خبر می‌تواند فشار فروش یا ریسک احتیاط ایجاد کند."
    else:
        effect = "برداشت اولیه سیستم خنثی است و هنوز جهت مشخصی از متن خبر دیده نمی‌شود."
    return f"{source} خبری منتشر کرده که به {target} مربوط است. {topic} {effect} دلیل تشخیص: {trigger_text}."


def _original_excerpt(item: dict[str, Any]) -> str:
    text = _strip_html(f"{item.get('title', '')}. {item.get('description', '')}")
    return text[:420]


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
                "summary_en": _summary_en(impact, related),
                "title_fa": _display_title_fa(item, impact, related),
                "description_fa": _description_fa(impact, triggers, item["title"]),
                "news_text_fa": _plain_news_fa(item, impact, related, triggers),
                "original_excerpt": _original_excerpt(item),
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
        summary_en = "Recent news is slightly positive, but it still needs confirmation from live price and volume."
    elif impact_counts["negative"] > impact_counts["positive"]:
        mood = "NEWS_NEGATIVE"
        summary = "اخبار اخیر ریسک منفی بیشتری نشان می‌دهد؛ ورود بدون حد ضرر مناسب نیست."
        summary_en = "Recent news shows more downside risk; entering without a stop loss is not appropriate."
    else:
        mood = "NEWS_MIXED"
        summary = "اخبار جهت یکدست ندارد؛ بهتر است هر نماد جداگانه با چارت بررسی شود."
        summary_en = "News is mixed; each symbol should be checked against its own chart."

    return {
        "generated_at": datetime.now(timezone.utc),
        "sources": [source["name"] for source in NEWS_SOURCES],
        "symbols": sorted(wanted - {"MARKET"}),
        "summary": {
            "mood": mood,
            "summary_fa": summary,
            "summary_en": summary_en,
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
