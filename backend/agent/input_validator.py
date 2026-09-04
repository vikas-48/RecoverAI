import re

SUSPICIOUS_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"system\s+prompt",
    r"developer\s+message",
    r"reveal\s+your\s+instructions",
    r"override\s+(the\s+)?policy",
    r"bypass\s+(the\s+)?policy",
    r"execute\s+without\s+approval",
]


def validate_untrusted_text(value: str) -> bool:
    text = (value or "").lower()
    return not any(re.search(pattern, text) for pattern in SUSPICIOUS_PATTERNS)
