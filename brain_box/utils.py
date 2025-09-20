from datetime import datetime, timezone


def now():
    """Generate current date and time."""

    return datetime.now(timezone.utc)
