import re
from typing import Any


def clean_text(value: Any) -> str:
    """
    Clean text before storing in DB / checkpoint / prompt.
    Removes null bytes and other problematic control chars.
    """

    if value is None:
        return ""

    if not isinstance(value, str):
        value = str(value)

    # remove null byte explicitly
    value = value.replace("\x00", "")

    # remove other problematic control characters
    value = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", value)

    return value.strip()


def clean_string_list(values: list[Any] | None) -> list[str]:
    """
    Clean a list of strings safely.
    Used for memories, summaries, documents, etc.
    """
    if not values:
        return []

    cleaned = []

    for item in values:
        text = clean_text(item)
        if text:
            cleaned.append(text)

    return cleaned