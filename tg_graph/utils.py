import unicodedata


def sanitize_text(text: str) -> str:
    """Normalize fancy Unicode characters to improve font compatibility."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(
        ch for ch in normalized if unicodedata.category(ch)[0] != "S"
    )
