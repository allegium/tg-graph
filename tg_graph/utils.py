import unicodedata


def sanitize_text(text: str) -> str:
    """Normalize text and strip characters unsupported by common fonts."""
    normalized = unicodedata.normalize("NFKD", text)
    ascii_bytes = normalized.encode("ascii", "ignore")
    return ascii_bytes.decode("ascii")
