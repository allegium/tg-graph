import unicodedata


def sanitize_text(text: str) -> str:
    """Normalize text and remove control characters while keeping Unicode."""
    normalized = unicodedata.normalize("NFC", text)
    return "".join(
        ch for ch in normalized if not unicodedata.category(ch).startswith("C")
    ).strip()
