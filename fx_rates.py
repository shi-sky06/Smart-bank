"""
fx_rates.py

Shared currency conversion helper — used by the Currency Converter page
and the International Transfer page, so both use the same source of
exchange rates and the same offline fallback behavior.
"""

import requests

CURRENCIES = ["USD", "INR", "EUR", "GBP", "JPY", "AUD", "CAD", "CNY", "SGD", "AED"]

# Fallback rates (relative to 1 USD) — only used if the live API is unreachable,
# so features still work with no internet, just with a visible "offline" note.
FALLBACK_RATES_USD_BASE = {
    "USD": 1.0,
    "INR": 87.5,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 149.0,
    "AUD": 1.52,
    "CAD": 1.36,
    "CNY": 7.15,
    "SGD": 1.34,
    "AED": 3.67,
}

API_URL = "https://open.er-api.com/v6/latest/USD"


def get_rate(from_curr, to_curr):
    """Returns (rate, source_label_string). Tries the live API first,
    falls back to a static table if there's no internet or the API fails."""

    try:
        response = requests.get(API_URL, timeout=5)
        data = response.json()

        if data.get("result") == "success":
            rates = data["rates"]
            rate = rates[to_curr] / rates[from_curr]
            return rate, "Live rate"

    except Exception:
        pass

    usd_to_from = FALLBACK_RATES_USD_BASE[from_curr]
    usd_to_to = FALLBACK_RATES_USD_BASE[to_curr]
    rate = usd_to_to / usd_to_from
    return rate, "⚠️ Offline estimate — rates may be outdated"
