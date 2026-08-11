# Patoshi Radar keyword set, adapted for Robinhood Radar.
KEYWORDS = [
    "patoshi",
    "pat",
    "turan",
    "pato",
    "patos",
    "enes",
    "parad",
    "paradot",
    "paradotor",
    "patosh",
]

def find_keyword_matches(name: str, symbol: str):
    text = f"{name or ''} {symbol or ''}".lower()
    return [keyword for keyword in KEYWORDS if keyword.lower() in text]

def is_match(name: str, symbol: str) -> bool:
    return bool(find_keyword_matches(name, symbol))
