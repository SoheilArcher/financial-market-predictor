DEFAULT_STANDARDS = {
    "max_risk_per_trade_percent": 1.0,
    "max_leverage": 3,
    "margin_mode": "isolated",
    "position_sizing": "Risk only the amount between entry and stop loss.",
    "dca_policy": "Do not average down unless the original signal is still valid and the new size keeps total risk under the limit.",
    "stop_loss_required": True,
    "notes_fa": [
        "قبل از ورود، حد ضرر باید مشخص باشد.",
        "اگر قیمت به حد ابطال رسید، معامله باید بسته شود؛ میانگین کم کردن جایگزین استاپ نیست.",
        "برای کاربران تازه‌کار، ریسک هر معامله بهتر است 0.5 تا 1 درصد سرمایه باشد.",
    ],
}

EXCHANGE_STANDARDS = {
    "binance": {
        **DEFAULT_STANDARDS,
        "name": "Binance",
        "order_types": ["market", "limit", "stop_market", "take_profit_market", "oco_spot"],
        "supports_futures": True,
        "supports_oco": True,
        "max_leverage": 5,
    },
    "coinex": {
        **DEFAULT_STANDARDS,
        "name": "CoinEx",
        "order_types": ["market", "limit", "stop_limit", "take_profit"],
        "supports_futures": True,
        "supports_oco": False,
        "max_leverage": 3,
    },
    "xt": {
        **DEFAULT_STANDARDS,
        "name": "XT",
        "order_types": ["market", "limit", "trigger_order"],
        "supports_futures": True,
        "supports_oco": False,
        "max_leverage": 3,
    },
    "bybit": {
        **DEFAULT_STANDARDS,
        "name": "Bybit",
        "order_types": ["market", "limit", "stop_market", "take_profit"],
        "supports_futures": True,
        "supports_oco": False,
        "max_leverage": 5,
    },
    "okx": {
        **DEFAULT_STANDARDS,
        "name": "OKX",
        "order_types": ["market", "limit", "stop", "oco"],
        "supports_futures": True,
        "supports_oco": True,
        "max_leverage": 5,
    },
    "yahoo finance": {
        **DEFAULT_STANDARDS,
        "name": "Yahoo Finance",
        "order_types": ["analysis_only"],
        "supports_futures": False,
        "supports_oco": False,
        "max_leverage": 1,
    },
}


def normalize_exchange_name(exchange: str | None) -> str:
    return (exchange or "Binance").strip().lower()


def get_exchange_standard(exchange: str | None) -> dict:
    key = normalize_exchange_name(exchange)
    if key in EXCHANGE_STANDARDS:
        return {"known": True, **EXCHANGE_STANDARDS[key]}
    return {
        "known": False,
        "name": exchange or "Unknown",
        **DEFAULT_STANDARDS,
        "needs_review": True,
        "message_fa": "این صرافی هنوز در استانداردهای سیستم ثبت نشده است. نام، آدرس سایت، بازارهای فعال و قوانین سفارش‌گذاری آن باید بررسی و اضافه شود.",
        "required_info": [
            "exchange_name",
            "website_url",
            "spot_or_futures",
            "supported_order_types",
            "min_order_size",
            "tick_size",
            "leverage_limits",
            "api_docs_url",
        ],
    }


def list_exchange_standards() -> dict:
    return {item["name"]: get_exchange_standard(item["name"]) for item in EXCHANGE_STANDARDS.values()}
