import unicodedata


def sanitize_text(text: str) -> str:
    """Return ``text`` with control/unsupported characters removed and ``$`` escaped."""

    normalized = unicodedata.normalize("NFC", text)
    result_chars = []
    for ch in normalized:
        cat = unicodedata.category(ch)
        # Drop control characters entirely
        if cat.startswith("C"):
            continue
        # Remove various symbol characters (including most emoji) that are not
        # typically present in the default Matplotlib font and cause warnings
        if cat.startswith("S"):
            continue
        # Escape the dollar sign to prevent Matplotlib from interpreting it as
        # a math text delimiter
        if ch == "$":
            result_chars.append("\\$")
        else:
            result_chars.append(ch)
    return "".join(result_chars).strip()
