import re
from datetime import datetime, timezone
from typing import Any

from app.services.market_report import DEFAULT_MARKET_SYMBOLS, build_market_report


SYMBOL_ALIASES = {
    "طلا": "XAUUSD",
    "gold": "XAUUSD",
    "xau": "XAUUSD",
    "xauusd": "XAUUSD",
    "نقره": "XAGUSD",
    "silver": "XAGUSD",
    "xag": "XAGUSD",
    "xagusd": "XAGUSD",
    "نفت": "WTIUSD",
    "oil": "WTIUSD",
    "wti": "WTIUSD",
    "wtiusd": "WTIUSD",
    "بیت کوین": "BTCUSDT",
    "بیت‌کوین": "BTCUSDT",
    "بیت": "BTCUSDT",
    "btc": "BTCUSDT",
    "bitcoin": "BTCUSDT",
    "اتریوم": "ETHUSDT",
    "اتر": "ETHUSDT",
    "eth": "ETHUSDT",
    "ethereum": "ETHUSDT",
    "سولانا": "SOLUSDT",
    "sol": "SOLUSDT",
    "solana": "SOLUSDT",
    "bnb": "BNBUSDT",
    "ریپل": "XRPUSDT",
    "xrp": "XRPUSDT",
}

TIMEFRAME_ALIASES = {
    "یک دقیقه": "1m",
    "۱ دقیقه": "1m",
    "پنج دقیقه": "5m",
    "۵ دقیقه": "5m",
    "پانزده دقیقه": "15m",
    "۱۵ دقیقه": "15m",
    "یک ساعت": "1h",
    "۱ ساعت": "1h",
    "چهار ساعت": "4h",
    "۴ ساعت": "4h",
    "روزانه": "1d",
    "daily": "1d",
}

RISK_PENALTY = {
    "LOW": 4,
    "MEDIUM": 12,
    "HIGH": 24,
    "UNKNOWN": 18,
}


def normalize_query_text(question: str) -> str:
    return question.strip().lower().replace("ي", "ی").replace("ك", "ک")


def extract_timeframe(question: str, default: str = "5m") -> str:
    normalized = normalize_query_text(question)
    explicit = re.search(r"\b(1m|5m|15m|1h|4h|1d)\b", normalized)
    if explicit:
        return explicit.group(1)
    for phrase, timeframe in TIMEFRAME_ALIASES.items():
        if phrase in normalized:
            return timeframe
    return default


def extract_top_n(question: str, default: int = 3) -> int:
    normalized = normalize_query_text(question)
    if "دو معامله" in normalized or "۲ معامله" in normalized or "2 معامله" in normalized:
        return 2
    if "یک معامله" in normalized or "۱ معامله" in normalized or "1 معامله" in normalized:
        return 1
    match = re.search(r"(\d+)\s*(?:معامله|موقعیت|فرصت)", normalized)
    if match:
        return max(1, min(int(match.group(1)), 5))
    return default


def extract_symbols(question: str) -> list[str]:
    normalized = normalize_query_text(question)
    symbols: list[str] = []
    for phrase, symbol in sorted(SYMBOL_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if phrase in normalized and symbol not in symbols:
            symbols.append(symbol)

    for raw in re.findall(r"\b[A-Z]{2,6}(?:/[A-Z]{2,6}|USDT|USD)?\b", question.upper()):
        symbol = raw.replace("/", "")
        if len(symbol) <= 5 and symbol not in {"XAU", "XAG", "WTI"}:
            symbol = f"{symbol}USDT"
        if symbol not in symbols:
            symbols.append(symbol)

    return symbols[:8] or DEFAULT_MARKET_SYMBOLS[:8]


def risk_label_fa(risk: str) -> str:
    return {
        "LOW": "کم",
        "MEDIUM": "متوسط",
        "HIGH": "زیاد",
        "UNKNOWN": "نامشخص",
    }.get(risk, risk)


def score_candidate(item: dict[str, Any]) -> dict[str, Any]:
    signal = item.get("signal", "WAIT")
    confidence = float(item.get("confidence") or 0)
    change = float(item.get("change_percent") or 0)
    risk = item.get("risk", "UNKNOWN")
    risk_penalty = RISK_PENALTY.get(risk, RISK_PENALTY["UNKNOWN"])

    direction_bonus = 0
    if signal == "LONG" and change > 0:
        direction_bonus = min(abs(change) * 3, 12)
    elif signal == "SHORT" and change < 0:
        direction_bonus = min(abs(change) * 3, 12)
    elif signal in {"WAIT", "NO_DATA"}:
        direction_bonus = -14
    elif signal == "ERROR":
        direction_bonus = -45

    score = round(max(0, min(100, confidence + direction_bonus - risk_penalty)), 1)
    expected_quality = "HIGH" if score >= 72 else "MEDIUM" if score >= 52 else "LOW"
    action = "بررسی برای ورود" if signal in {"LONG", "SHORT"} and score >= 52 else "صبر"

    reasons = []
    reasons.append(f"سیگنال {signal} با اعتماد {confidence:g}")
    reasons.append(f"ریسک {risk_label_fa(risk)}")
    reasons.append(f"تغییر قیمت {change:g}%")
    if signal in {"WAIT", "NO_DATA"}:
        reasons.append("تایید کافی برای ورود ندارد")
    elif score < 52:
        reasons.append("نسبت اعتماد به ریسک هنوز جذاب نیست")
    else:
        reasons.append("نسبت اعتماد به ریسک قابل بررسی است")

    return {
        "symbol": item.get("symbol"),
        "signal": signal,
        "action": action,
        "score": score,
        "expected_quality": expected_quality,
        "confidence": confidence,
        "risk": risk,
        "change_percent": change,
        "price": item.get("live_price", {}).get("price") if isinstance(item.get("live_price"), dict) else item.get("price"),
        "source": item.get("source"),
        "reasons": reasons,
    }


def build_answer(question: str, ranked: list[dict[str, Any]], top_n: int, timeframe: str) -> str:
    tradable = [item for item in ranked if item["action"] == "بررسی برای ورود"]
    picks = tradable[:top_n]
    if not picks:
        best = ranked[0] if ranked else None
        if not best:
            return "فعلاً داده کافی برای پاسخ وجود ندارد."
        return (
            f"در تایم‌فریم {timeframe} فعلاً ورود قوی پیشنهاد نمی‌شود. "
            f"بهترین گزینه نسبی {best['symbol']} است، اما امتیاز آن {best['score']} است و بهتر است صبر کنید."
        )

    pick_text = "، ".join(f"{item['symbol']} ({item['signal']}، امتیاز {item['score']})" for item in picks)
    if top_n == 1:
        return f"در تایم‌فریم {timeframe} بهترین گزینه فعلی {pick_text} است. قبل از ورود، حد ضرر و حجم معامله را محدود نگه دارید."
    return f"در تایم‌فریم {timeframe} اگر فقط {top_n} معامله بخواهید، اولویت فعلی من این‌هاست: {pick_text}."


async def answer_trading_question(question: str, timeframe: str | None = None, limit: int = 120) -> dict[str, Any]:
    selected_timeframe = timeframe or extract_timeframe(question)
    symbols = extract_symbols(question)
    top_n = extract_top_n(question)
    report = await build_market_report(symbols=symbols, timeframe=selected_timeframe, limit=max(80, min(limit, 250)))
    ranked = sorted(
        [score_candidate(item) for item in report["items"]],
        key=lambda item: item["score"],
        reverse=True,
    )
    return {
        "question": question,
        "timeframe": selected_timeframe,
        "symbols": symbols,
        "top_n": top_n,
        "answer_fa": build_answer(question, ranked, top_n, selected_timeframe),
        "ranked_opportunities": ranked,
        "market_summary": report["summary"],
        "generated_at": datetime.now(timezone.utc),
        "disclaimer": "این خروجی دستیار تصمیم‌یار است و توصیه مالی قطعی محسوب نمی‌شود.",
    }
