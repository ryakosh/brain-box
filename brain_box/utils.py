from datetime import datetime, timezone
import re

_REGEX_ALNUM = re.compile(r"\w+", re.UNICODE)


def now():
    """Generate current date and time."""

    return datetime.now(timezone.utc)


def sanitize_alnum(text: str) -> str:
    """
    Sanitize a string as only containing alpha numeric characters.

    Args:
        text: The raw user input string.

    Returns:
        str: A sanitized alnum string.
    """

    tokens = _REGEX_ALNUM.findall(text)

    return " ".join(tokens)
