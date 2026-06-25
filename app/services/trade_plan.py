from typing import Any

from app.collectors.binance import fetch_binance_klines
from app.services.analyzer import analyze_market
from app.services.commodity_data import analyze_commodity_symbol, is_commodity_symbol, normalize_commodity_symbol
from app.services.exchange_standards import get_exchange_standard
from app.services.live_price import attach_live_price, fetch_live_price
from app.services.market_report import kline_to_candle, price_change_percent
from app.services.pair_data import analyze_pair_symbol, parse_pair


def _round_price(value: float) -> float:
    if value >= 1000:
        return round(value, 2)
    if value >= 1:
        return round(value, 4)
    return round(value, 8)


def _zone(price: float, side: str) -> dict[str, float]:
    if side == "LONG":
        return {"from": _round_price(price * 0.998), "to": _round_price(price * 1.002)}
    return {"from": _round_price(price * 1.002), "to": _round_price(price * 0.998)}


def _risk_reward_targets(price: float, stop_loss: float, side: str, resistance: float | None, support: float | None) -> list[dict]:
    risk = abs(price - stop_loss)
    if risk <= 0:
        risk = price * 0.01
    direction = 1 if side == "LONG" else -1
    targets = [
        {"name": "TP1", "price": _round_price(price + direction * risk), "rr": 1},
        {"name": "TP2", "price": _round_price(price + direction * risk * 2), "rr": 2},
        {"name": "TP3", "price": _round_price(price + direction * risk * 3), "rr": 3},
    ]
    if side == "LONG" and resistance:
        targets[0]["price"] = _round_price(max(targets[0]["price"], resistance))
    if side == "SHORT" and support:
        targets[0]["price"] = _round_price(min(targets[0]["price"], support))
    return targets


def _position_size(account_size: float, price: float, stop_loss: float, risk_percent: float) -> dict[str, float]:
    risk_amount = account_size * (risk_percent / 100)
    per_unit_risk = abs(price - stop_loss)
    quantity = risk_amount / per_unit_risk if per_unit_risk else 0
    notional = quantity * price
    return {
        "account_size": _round_price(account_size),
        "risk_percent": risk_percent,
        "risk_amount": _round_price(risk_amount),
        "suggested_quantity": _round_price(quantity),
        "notional_value": _round_price(notional),
    }


def build_management_rules(analysis: dict[str, Any], side: str, entry_price: float | None = None) -> dict[str, Any]:
    price = float(analysis.get("price") or entry_price or 0)
    levels = analysis.get("levels") or {}
    support = levels.get("support")
    resistance = levels.get("resistance")
    stop_loss = float(levels.get("stop_loss") or (price * 0.985 if side == "LONG" else price * 1.015))
    if side == "SHORT" and stop_loss < price:
        stop_loss = price * 1.015
    if side == "LONG" and stop_loss > price:
        stop_loss = price * 0.985

    adverse_trigger = price - abs(price - stop_loss) * 0.5 if side == "LONG" else price + abs(price - stop_loss) * 0.5
    invalidation = price - abs(price - stop_loss) * 0.85 if side == "LONG" else price + abs(price - stop_loss) * 0.85
    return {
        "entry_zone": _zone(price, side),
        "stop_loss": _round_price(stop_loss),
        "take_profits": _risk_reward_targets(price, stop_loss, side, resistance, support),
        "partial_close": [
            "در TP1 حدود 30٪ تا 50٪ حجم بسته شود و حد ضرر به نقطه ورود نزدیک شود.",
            "در TP2 بخشی دیگر بسته شود و باقی معامله با trailing stop مدیریت شود.",
        ],
        "if_price_goes_against": {
            "warning_price": _round_price(adverse_trigger),
            "invalidation_price": _round_price(invalidation),
            "close_rule": "اگر کندل تایم‌فریم انتخابی بعد از ورود پشت حد ضرر یا حد ابطال بسته شد، خروج اولویت دارد.",
            "dca_rule": "میانگین کم کردن فقط وقتی مجاز است که سیگنال هنوز معتبر باشد، RSI در محدوده خطر نباشد و ریسک کل از سقف مجاز بالاتر نرود.",
            "default_action": "برای کاربر معمولی: DCA نکن؛ حد ضرر را اجرا کن یا حجم را کم کن.",
        },
    }


async def _analysis_for_symbol(exchange: str, symbol: str, timeframe: str, limit: int) -> dict[str, Any]:
    pair = parse_pair(symbol)
    if pair:
        return await analyze_pair_symbol(symbol=symbol, timeframe=timeframe, limit=limit)
    if is_commodity_symbol(symbol):
        return await analyze_commodity_symbol(normalize_commodity_symbol(symbol) or symbol, timeframe=timeframe, limit=limit)

    normalized = symbol.upper().replace("/", "")
    klines = await fetch_binance_klines(symbol=normalized, interval=timeframe, limit=limit)
    candles = [kline_to_candle(kline) for kline in klines]
    result = analyze_market(candles=candles, symbol=normalized, timeframe=timeframe)
    try:
        attach_live_price(result, await fetch_live_price(symbol=normalized, exchange=exchange))
    except Exception as exc:
        result["live_price"] = {"exchange": exchange, "symbol": normalized, "status": "unavailable", "message": str(exc)}
    result["change_percent"] = price_change_percent(candles)
    return result


def evaluate_open_position(analysis: dict[str, Any], side: str, entry_price: float, stop_loss: float | None = None) -> dict[str, Any]:
    current_price = float(analysis.get("price") or 0)
    signal = analysis.get("signal")
    levels = analysis.get("levels") or {}
    active_stop = stop_loss or levels.get("stop_loss")
    pnl_percent = 0.0
    if entry_price:
        pnl_percent = ((current_price - entry_price) / entry_price) * 100
        if side == "SHORT":
            pnl_percent *= -1

    action = "HOLD"
    message = "موقعیت را نگه دار، اما حد ضرر و شرایط ابطال را رعایت کن."
    severity = "info"
    if active_stop and ((side == "LONG" and current_price <= float(active_stop)) or (side == "SHORT" and current_price >= float(active_stop))):
        action = "CLOSE"
        severity = "danger"
        message = "قیمت به محدوده حد ضرر رسیده است؛ بستن معامله اولویت دارد."
    elif signal in {"LONG", "SHORT"} and signal != side:
        action = "REDUCE_OR_CLOSE"
        severity = "warning"
        message = "سیگنال فعلی خلاف معامله باز است؛ کاهش حجم یا خروج را بررسی کن."
    elif pnl_percent < -1.5:
        action = "NO_DCA"
        severity = "warning"
        message = "معامله وارد ضرر قابل توجه شده؛ میانگین کم کردن بدون تایید جدید پیشنهاد نمی‌شود."

    return {
        "action": action,
        "severity": severity,
        "current_price": _round_price(current_price),
        "entry_price": _round_price(entry_price),
        "pnl_percent": round(pnl_percent, 2),
        "message_fa": message,
    }


async def build_trade_plan(
    exchange: str,
    symbol: str,
    timeframe: str = "5m",
    limit: int = 150,
    account_size: float = 1000,
    risk_percent: float = 1.0,
    entry_price: float | None = None,
    side: str | None = None,
) -> dict[str, Any]:
    analysis = await _analysis_for_symbol(exchange, symbol, timeframe, limit)
    signal = analysis.get("signal", "WAIT")
    selected_side = (side or signal).upper()
    exchange_standard = get_exchange_standard(exchange if not is_commodity_symbol(symbol) else analysis.get("exchange", exchange))

    if signal not in {"LONG", "SHORT"} and not side:
        return {
            "symbol": analysis.get("symbol", symbol.upper()),
            "timeframe": timeframe,
            "trade_status": "NO_TRADE",
            "summary_fa": "فعلاً ورود جدید پیشنهاد نمی‌شود. برای ورود باید سیگنال جهت‌دار و نسبت ریسک به ریوارد مناسب شکل بگیرد.",
            "analysis": analysis,
            "exchange_standard": exchange_standard,
            "alerts": [
                "وقتی سیگنال LONG یا SHORT شد دوباره بررسی کن.",
                "بدون حد ضرر معامله باز نکن.",
            ],
            "disclaimer": "این پلن آموزشی/تحلیلی است و توصیه مالی قطعی محسوب نمی‌شود.",
        }

    if selected_side not in {"LONG", "SHORT"}:
        selected_side = "LONG" if signal == "LONG" else "SHORT"
    rules = build_management_rules(analysis, selected_side, entry_price=entry_price)
    price = float(analysis.get("price") or entry_price or 0)
    position = _position_size(account_size, price, float(rules["stop_loss"]), min(risk_percent, exchange_standard["max_risk_per_trade_percent"]))
    monitor = None
    if entry_price:
        monitor = evaluate_open_position(analysis, selected_side, entry_price, float(rules["stop_loss"]))

    return {
        "symbol": analysis.get("symbol", symbol.upper()),
        "timeframe": timeframe,
        "trade_status": "READY" if signal == selected_side else "MANAGE_EXISTING",
        "side": selected_side,
        "current_signal": signal,
        "confidence": analysis.get("confidence", 0),
        "risk": analysis.get("risk", "UNKNOWN"),
        "price": analysis.get("price"),
        "plan": rules,
        "position_sizing": position,
        "monitor": monitor,
        "analysis": analysis,
        "exchange_standard": exchange_standard,
        "alerts": [
            "ورود فقط داخل entry zone و با حد ضرر فعال انجام شود.",
            "اگر قیمت به invalidation رسید، خروج مقدم بر میانگین کم کردن است.",
            "هر 60 ثانیه یا با بسته شدن کندل تایم‌فریم، وضعیت معامله دوباره بررسی شود.",
        ],
        "disclaimer": "این پلن آموزشی/تحلیلی است و توصیه مالی قطعی محسوب نمی‌شود.",
    }
