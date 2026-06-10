import datetime

import pytest

from pitwall.cache.freshness import FALLBACK_TTL, is_stale


def test_fallback_ttl_value_invariant() -> None:
    """AC-12: Verify that the fallback time-to-live is exactly 24 hours.

    Invariant: FALLBACK_TTL must be a datetime.timedelta equal to exactly 24 hours
    to act as the maximum duration for cache freshness when session timings are absent.
    """
    assert datetime.timedelta(hours=24) == FALLBACK_TTL


@pytest.mark.parametrize(
    "fetched_at, now, session_starts, expected",
    [
        # --- (a) Session start strictly between fetched_at and now -> True ---
        # Case 1: Single session start precisely in the middle of the window.
        (
            datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC),
            datetime.datetime(2026, 6, 9, 12, 0, tzinfo=datetime.UTC),
            [datetime.datetime(2026, 6, 9, 11, 0, tzinfo=datetime.UTC)],
            True,
        ),
        # Case 2: Boundary check - session start equals fetched_at (strictly between: fetched_at < session_start < now).
        (
            datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC),
            datetime.datetime(2026, 6, 9, 12, 0, tzinfo=datetime.UTC),
            [datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)],
            False,
        ),
        # Case 3: Boundary check - session start equals now (strictly between: fetched_at < session_start < now).
        (
            datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC),
            datetime.datetime(2026, 6, 9, 12, 0, tzinfo=datetime.UTC),
            [datetime.datetime(2026, 6, 9, 12, 0, tzinfo=datetime.UTC)],
            False,
        ),
        # --- (b) No session start in window and age < FALLBACK_TTL -> False ---
        # Case 4: Sessions exist, but all are either prior to fetched_at or after now.
        (
            datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC),
            datetime.datetime(2026, 6, 9, 18, 0, tzinfo=datetime.UTC),
            [
                datetime.datetime(2026, 6, 9, 9, 0, tzinfo=datetime.UTC),
                datetime.datetime(2026, 6, 9, 19, 0, tzinfo=datetime.UTC),
            ],
            False,
        ),
        # --- (c) Age >= FALLBACK_TTL (24 h) -> True regardless of session starts ---
        # Case 5: Exactly 24 hours old, no sessions.
        (
            datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC),
            datetime.datetime(2026, 6, 10, 10, 0, tzinfo=datetime.UTC),
            [],
            True,
        ),
        # Case 6: 25 hours old, sessions exist but outside the window.
        (
            datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC),
            datetime.datetime(2026, 6, 10, 11, 0, tzinfo=datetime.UTC),
            [datetime.datetime(2026, 6, 9, 9, 0, tzinfo=datetime.UTC)],
            True,
        ),
        # --- (d) Empty session_starts within TTL -> False ---
        # Case 7: Age is less than 24 hours and there are no scheduled sessions.
        (
            datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC),
            datetime.datetime(2026, 6, 9, 23, 59, tzinfo=datetime.UTC),
            [],
            False,
        ),
    ],
)
def test_is_stale_truth_table(
    fetched_at: datetime.datetime,
    now: datetime.datetime,
    session_starts: list[datetime.datetime],
    expected: bool,
) -> None:
    """AC-12: Verify that is_stale returns correct boolean values across all boundary conditions.

    Assumption: Time inputs are always timezone-aware (UTC).
    Invariant: is_stale is a pure function and does not query system clocks internally.
    """
    assert is_stale(fetched_at, now, session_starts) is expected
