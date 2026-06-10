import datetime

FALLBACK_TTL = datetime.timedelta(hours=24)


def is_stale(
    fetched_at: datetime.datetime,
    now: datetime.datetime,
    session_starts: list[datetime.datetime],
) -> bool:
    """Determine cache staleness based on calendar-keyed events and fallback age.

    This function does not read the system clock directly, ensuring it remains
    side-effect free and deterministic for verification (PoT #1).

    Examples:
        >>> import datetime
        >>> fetched = datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)
        >>> current = datetime.datetime(2026, 6, 9, 12, 0, tzinfo=datetime.UTC)
        >>> is_stale(fetched, current, [datetime.datetime(2026, 6, 9, 11, 0, tzinfo=datetime.UTC)])
        True
        >>> is_stale(fetched, current, [])
        False
    """
    # Invariant: comparison operations must be performed using timezone-aware datetimes.
    # Failure Mode: if the age meets or exceeds FALLBACK_TTL, the cache is immediately invalid.
    if now - fetched_at >= FALLBACK_TTL:
        return True

    # Invariant: a session start strictly within (fetched_at, now) invalidates the cache.
    return any(fetched_at < start < now for start in session_starts)
