from datetime import datetime, timedelta, timezone, date
from typing import Any


def _to_aware(dt: datetime) -> datetime:
    """Converts a datetime object to an aware UTC datetime.

    Naive datetimes are treated as local time first before converting to UTC.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        # Assume local system timezone for naive datetimes, then convert to UTC
        dt = dt.astimezone()

    return dt.astimezone(timezone.utc)


def parse_date(d: str) -> datetime:
    """Parses relative time keywords or string formatted dates into a datetime object."""
    if not d or not isinstance(d, str):
        raise ValueError(f"Expected a non-empty date string, got {d!r}")

    d_clean = d.lower().strip()
    if d_clean == "yesterday":
        return datetime.now() - timedelta(days=1)
    elif d_clean == "today":
        return datetime.now()
    elif d_clean == "tomorrow":
        return datetime.now() + timedelta(days=1)

    # Standard ISO 8601 parsing (Python 3.7+)
    # Handles ISO formats like '2027-01-09T19:15:00', '2027-01-09', '2027-01-09T19:15:00Z', etc.
    try:
        return datetime.fromisoformat(d_clean.replace("z", "+00:00"))
    except ValueError:
        pass

    # Fallback common formats
    formats = (
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y-%m-%d",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
    )
    for fmt in formats:
        try:
            return datetime.strptime(d_clean, fmt)
        except ValueError:
            continue

    raise ValueError(f"Could not parse date string '{d}' using supported formats")


def fuzz_utc(d: Any) -> datetime:
    """Normalizes a datetime, date, or string representation into an aware UTC datetime."""
    if d is None:
        raise ValueError("Cannot convert None to UTC datetime")

    val = d

    # Convert pure date objects (excluding datetime subclasses) to start-of-day datetime
    if type(val) is date:
        val = datetime.combine(val, datetime.min.time())

    # Parse string input
    if isinstance(val, str):
        val = parse_date(val)

    # Verify we ended up with a datetime
    if not isinstance(val, datetime):
        raise TypeError(f"Expected datetime, date, or date string; got {type(d).__name__}")

    return _to_aware(val)


def fuzzy_same(d: Any, d2: Any, tolerance_seconds: float = 0.0) -> bool:
    """Compares two date/datetime objects or strings for temporal equality in UTC.

    Returns False safely if input strings are unparseable or types are invalid.
    """
    utc1 = fuzz_utc(d)
    utc2 = fuzz_utc(d2)

    if tolerance_seconds > 0:
        return abs((utc1 - utc2).total_seconds()) <= tolerance_seconds

    return utc1 == utc2


def as_casual_str(d: datetime) -> str:
    today = datetime.now()
    diff = d.date() - today.date()
    days = diff.days

    if -30 < days < 30:
        s = {
            0: 'today',
            1: 'tomorrow',
            -1: 'yesterday',
            -7: '1 week ago',
            7: 'in 1 week',
        }.get(days)
        if s:
            return s
        if days < 0:
            return f"{abs(days)} days ago"
        return f"in {days} days"
    return d.strftime("%m/%d/%Y")


if __name__ == '__main__':
    now = datetime.now()
    today = now - timedelta(hours=1)
    tomorrow = now + timedelta(days=1)
    yesterday = now - timedelta(days=1)
    next_week = now + timedelta(weeks=1)
    days_ago = now - timedelta(weeks=2)
    months_ago = now - timedelta(days=65)

    print("today", as_casual_str(today))
    print("tomorrow", as_casual_str(tomorrow))
    print("yesterday", as_casual_str(yesterday))
    print("next_week", as_casual_str(next_week))
    print("days ago", as_casual_str(days_ago))
    print("months ago", as_casual_str(months_ago))

    # are_the_same examples
    aware = datetime.now(tz=timezone.utc)
    naive = datetime.utcnow()
    print("same?", are_the_same(aware, naive))
