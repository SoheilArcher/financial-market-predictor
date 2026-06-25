from typing import Any


DEFAULT_ANNUAL_RETURN_PERCENT = 35.0
DEFAULT_PLATFORM_FEE_PERCENT = 5.0


def build_iran_fixed_income_quote(
    *,
    capital_amount: float,
    annual_return_percent: float = DEFAULT_ANNUAL_RETURN_PERCENT,
    platform_fee_percent: float = DEFAULT_PLATFORM_FEE_PERCENT,
    tax_percent: float = 0.0,
) -> dict[str, Any]:
    if capital_amount <= 0:
        raise ValueError("capital_amount must be greater than zero")
    gross_yearly_profit = capital_amount * (annual_return_percent / 100)
    gross_monthly_profit = gross_yearly_profit / 12
    fee_amount = max(0.0, gross_yearly_profit) * (platform_fee_percent / 100)
    tax_amount = max(0.0, gross_yearly_profit) * (tax_percent / 100)
    net_yearly_profit = gross_yearly_profit - fee_amount - tax_amount
    return {
        "market": "iran_fixed_income",
        "capital_amount": round(capital_amount, 4),
        "annual_return_percent": round(annual_return_percent, 4),
        "gross_yearly_profit": round(gross_yearly_profit, 4),
        "gross_monthly_profit": round(gross_monthly_profit, 4),
        "platform_fee_percent": round(platform_fee_percent, 4),
        "platform_fee_amount": round(fee_amount, 4),
        "tax_percent": round(tax_percent, 4),
        "tax_amount": round(tax_amount, 4),
        "net_yearly_profit": round(net_yearly_profit, 4),
        "net_monthly_profit": round(net_yearly_profit / 12, 4),
        "net_return_percent": round((net_yearly_profit / capital_amount) * 100, 4),
        "summary_fa": (
            "این محاسبه سناریوی هدف برای صندوق‌ها/ابزارهای درآمد ثابت بازار سرمایه ایران است "
            "و وعده سود قطعی یا تضمین عملکرد آینده محسوب نمی‌شود."
        ),
    }
