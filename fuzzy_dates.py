import math
from argparse import ArgumentTypeError
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


def fuzzy_utc(d: Any) -> datetime | None:
    """Normalizes a datetime, date, or string representation into an aware UTC datetime."""
    if not d:
        return None

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
    utc1 = fuzzy_utc(d)
    utc2 = fuzzy_utc(d2)

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


def parse_interval(value: str) -> timedelta | None:
    """Parses "90", "1.5s", "250ms", "10m", "2h" or "3d" into a timedelta. Plain numbers are seconds"""
    if not value:
        return None
    s = str(value).strip().lower()
    try:
        # Plain seconds
        seconds = int(s)
        return timedelta(seconds=seconds)
    except ValueError:
        pass
    # Suffixed formats
    if s.endswith("ms"):
        num = float(s[:-2])
        return timedelta(milliseconds=num)
    if s.endswith("s"):
        num = float(s[:-1])
        return timedelta(seconds=num)
    if s.endswith("m"):
        num = float(s[:-1])
        return timedelta(minutes=num)
    if s.endswith("h"):
        num = float(s[:-1])
        return timedelta(hours=num)
    if s.endswith("d"):
        num = float(s[:-1])
        return timedelta(days=num)
    # Fallback: try float seconds
    try:
        return timedelta(seconds=float(s))
    except Exception:
        raise ArgumentTypeError(f"Unrecognized interval format: {value}")


def as_duration_str(interval: timedelta) -> str:
    """A wait or length of time in its largest units, rounded up so it's never understated:
    45s -> "45 seconds", 61s -> "2 minutes", 90m -> "1 hour 30 minutes", 26h -> "1 day 2 hours".
    Seconds are only used under a minute; at most two units are shown"""
    total_seconds: int = max(0, math.ceil(interval.total_seconds()))
    if total_seconds < 60:
        return f"{total_seconds} second" if total_seconds == 1 else f"{total_seconds} seconds"

    total_minutes: int = math.ceil(total_seconds / 60)
    if total_minutes < 60:
        return f"{total_minutes} minute" if total_minutes == 1 else f"{total_minutes} minutes"

    if total_minutes < 24 * 60:
        hours, minutes = divmod(total_minutes, 60)
        larger: str = f"{hours} hour" if hours == 1 else f"{hours} hours"
        smaller: str = f"{minutes} minute" if minutes == 1 else f"{minutes} minutes"
    else:
        total_hours: int = math.ceil(total_minutes / 60)
        days, hours = divmod(total_hours, 24)
        larger: str = f"{days} day" if days == 1 else f"{days} days"
        smaller: str = f"{hours} hour" if hours == 1 else f"{hours} hours"
    return f"{larger} {smaller}" if not smaller.startswith("0 ") else larger


def to_days(interval: timedelta) -> float:
    """You can get just the int of days using the .days property, this returns fractional days too"""
    return interval.total_seconds() / (24 * 60 * 60)


def to_utc_iso_8601(d: datetime) -> str:
    # Convert to UTC if it has timezone info
    if d.tzinfo is not None:
        d = d.astimezone(timezone.utc).replace(tzinfo=None)

    # Format as ISO 8601 string with Z suffix to indicate UTC
    return d.isoformat() + 'Z'


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

    # as_duration_str examples
    for seconds in [1, 45, 60, 61, 3599, 3600, 5400, 86400, 93600]:
        print(seconds, as_duration_str(timedelta(seconds=seconds)))

    # fuzzy_same examples
    aware = datetime.now(tz=timezone.utc)
    naive = datetime.utcnow()
    print("same?", fuzzy_same(aware, naive))
