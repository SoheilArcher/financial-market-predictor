from typing import Any, Dict, List


def calculate_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0

    gains = []
    losses = []

    for i in range(1, period + 1):
        diff = closes[-i] - closes[-i - 1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calculate_ema(values: List[float], period: int) -> float:
    if not values:
        return 0.0

    if len(values) < period:
        return round(values[-1], 2)

    multiplier = 2 / (period + 1)
    ema = values[0]

    for price in values[1:]:
        ema = (price - ema) * multiplier + ema

    return round(ema, 2)


def analyze_market(
    candles: List[Dict[str, Any]],
    symbol: str,
    timeframe: str
) -> Dict[str, Any]:
    if not candles or len(candles) < 20:
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": "NO_DATA",
            "message": "داده کافی برای تحلیل وجود ندارد.",
        }

    closes = [float(c["close"]) for c in candles]
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]

    current_price = closes[-1]

    rsi = calculate_rsi(closes)
    ema_20 = calculate_ema(closes, 20)
    ema_50 = calculate_ema(closes, 50)

    support = round(min(lows[-20:]), 2)
    resistance = round(max(highs[-20:]), 2)

    reasons = []
    signal = "WAIT"
    confidence = 50
    risk = "MEDIUM"

    if current_price > ema_20 > ema_50 and rsi < 70:
        signal = "LONG"
        confidence = 68
        risk = "MEDIUM"
        reasons.append("قیمت بالای EMA20 و EMA50 قرار دارد.")
        reasons.append("روند کوتاه‌مدت صعودی دیده می‌شود.")
    elif current_price < ema_20 < ema_50 and rsi > 30:
        signal = "SHORT"
        confidence = 66
        risk = "MEDIUM"
        reasons.append("قیمت پایین EMA20 و EMA50 قرار دارد.")
        reasons.append("روند کوتاه‌مدت نزولی دیده می‌شود.")
    else:
        reasons.append("روند واضح و قدرتمندی دیده نمی‌شود.")
        reasons.append("ورود عجولانه ریسک دارد.")

    if rsi >= 70:
        reasons.append("RSI وارد محدوده اشباع خرید شده است.")
        risk = "HIGH"
    elif rsi <= 30:
        reasons.append("RSI وارد محدوده اشباع فروش شده است.")
        risk = "HIGH"
    else:
        reasons.append("RSI در محدوده خنثی قرار دارد.")

    if ema_20 > ema_50:
        trend = "UP"
    elif ema_20 < ema_50:
        trend = "DOWN"
    else:
        trend = "SIDEWAY"

    stop_loss = round(support * 0.995, 2)
    take_profit = round(resistance * 1.005, 2)

    if signal == "WAIT":
        summary = "فعلاً ورود قطعی پیشنهاد نمی‌شود. بازار نیاز به تأیید بیشتر دارد."
    elif signal == "LONG":
        summary = "شرایط برای موقعیت خرید بهتر از فروش است، اما ورود باید با حد ضرر انجام شود."
    else:
        summary = "شرایط برای موقعیت فروش بهتر از خرید است، اما ریسک برگشت قیمت وجود دارد."

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "signal": signal,
        "confidence": confidence,
        "risk": risk,
        "price": round(current_price, 2),
        "summary_fa": summary,
        "levels": {
            "support": support,
            "resistance": resistance,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        },
        "indicators": {
            "rsi": rsi,
            "ema_20": ema_20,
            "ema_50": ema_50,
            "trend": trend,
        },
        "reasons": reasons,
        "disclaimer": "این خروجی پیشنهاد تحلیلی است و تضمین سود نیست.",
    }
