"""Currency detection and budget extraction from unstructured text."""

import re

# ---------------------------------------------------------------------------
# Currency Symbol → Code Mapping
# ---------------------------------------------------------------------------

SYMBOL_TO_CURRENCY: dict[str, str] = {
    "$": "USD", "₹": "INR", "€": "EUR", "£": "GBP", "¥": "JPY",
    "元": "CNY", "₽": "RUB", "₩": "KRW", "₨": "NPR", "₺": "TRY", "₱": "PHP",
}

CURRENCY_TO_SYMBOL: dict[str, str] = {v: k for k, v in SYMBOL_TO_CURRENCY.items()}

# Word/abbreviation → (code, symbol)
WORD_TO_CURRENCY: dict[str, tuple[str, str]] = {
    "rs": ("INR", "₹"),
    "rupee": ("INR", "₹"),
    "rupees": ("INR", "₹"),
    "inr": ("INR", "₹"),
    "lakh": ("INR", "₹"),
    "crore": ("INR", "₹"),
    "dollar": ("USD", "$"),
    "dollars": ("USD", "$"),
    "usd": ("USD", "$"),
    "euro": ("EUR", "€"),
    "euros": ("EUR", "€"),
    "eur": ("EUR", "€"),
    "pound": ("GBP", "£"),
    "pounds": ("GBP", "£"),
    "gbp": ("GBP", "£"),
}

# Location → (code, symbol)
LOCATION_TO_CURRENCY: dict[str, tuple[str, str]] = {
    "mumbai": ("INR", "₹"),
    "delhi": ("INR", "₹"),
    "bangalore": ("INR", "₹"),
    "bengaluru": ("INR", "₹"),
    "chennai": ("INR", "₹"),
    "kolkata": ("INR", "₹"),
    "hyderabad": ("INR", "₹"),
    "india": ("INR", "₹"),
    "london": ("GBP", "£"),
    "uk": ("GBP", "£"),
    "new york": ("USD", "$"),
    "usa": ("USD", "$"),
}


def detect_currency(text: str) -> tuple[str, str]:
    """Detects currency from unstructured text using symbols, words, and locations.

    Priority: symbol match > word/abbreviation match > location match > default INR.

    Args:
        text: The unstructured input text to analyze.

    Returns:
        Tuple of (currency_code, currency_symbol), e.g. ("INR", "₹").
    """
    # 1. Check for currency symbols in text
    for symbol, code in SYMBOL_TO_CURRENCY.items():
        if symbol in text:
            return code, symbol

    text_lower = text.lower()

    # 2. Check for currency words / abbreviations
    for word, (code, symbol) in WORD_TO_CURRENCY.items():
        if re.search(rf"\b{re.escape(word)}\b", text_lower):
            return code, symbol

    # 3. Check for location-based hints
    for location, (code, symbol) in LOCATION_TO_CURRENCY.items():
        if re.search(rf"\b{re.escape(location)}\b", text_lower):
            return code, symbol

    # Default to INR for Indian-focused grants
    return "INR", "₹"


# Regex pattern for extracting monetary amounts
_AMOUNT_PATTERN = re.compile(
    r"(?:[\$₹€£¥元₽₩₨₺₱]|inr|usd|eur|gbp|jpy|rupees?|dollars?|euros?|pounds?|rs\.?)"
    r"\s*([\d,]+(?:\.\d+)?)"
    r"|"
    r"([\d,]+(?:\.\d+)?)\s*"
    r"(?:[\$₹€£¥元₽₩₨₺₱]|inr|usd|eur|gbp|jpy|rupees?|dollars?|euros?|pounds?|rs\.?)",
    re.IGNORECASE,
)

# Multiplier words for Indian number system
_MULTIPLIER_PATTERN = re.compile(
    r"([\d,.]+)\s*(lakh|lakhs|crore|crores)",
    re.IGNORECASE,
)

_MULTIPLIERS = {
    "lakh": 100_000,
    "lakhs": 100_000,
    "crore": 10_000_000,
    "crores": 10_000_000,
}


def extract_budget(text: str) -> float | None:
    """Extracts a monetary budget amount from unstructured text.

    Handles:
    - Prefix notation: $10,000 / ₹50,000
    - Suffix notation: 10,000 USD
    - Indian multipliers: 15 lakh, 2.5 crore

    Args:
        text: The input text to parse.

    Returns:
        The extracted budget as a float, or None if no amount found.
    """
    # First check for lakh/crore notation
    mult_match = _MULTIPLIER_PATTERN.search(text)
    if mult_match:
        try:
            base = float(mult_match.group(1).replace(",", ""))
            multiplier = _MULTIPLIERS.get(mult_match.group(2).lower(), 1)
            return base * multiplier
        except ValueError:
            pass

    # Then check for standard currency+number patterns
    match = _AMOUNT_PATTERN.search(text)
    if match:
        val_str = match.group(1) or match.group(2)
        try:
            return float(val_str.replace(",", ""))
        except ValueError:
            pass

    return None
