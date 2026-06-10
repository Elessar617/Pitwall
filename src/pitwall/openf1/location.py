import json
from datetime import datetime
from pathlib import Path

from pitwall.openf1.errors import ReplayDataError
from pitwall.openf1.models import LocationPoint, parse_location


def load_location(path: Path) -> list[LocationPoint]:
    """Load and parse location points from location.json in the directory."""
    # Safety / Failure Modes:
    # 1. Absent file returns [] to support backward compatibility.
    # 2. Invalid JSON raises ReplayDataError naming location.json.
    # 3. Malformed records raise DataParseError via parse_location.
    location_path = path / "location.json"
    if not location_path.exists():
        return []
    try:
        with open(location_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ReplayDataError(f"Invalid JSON in location.json: {e}") from e  # noqa: TRY003
    return parse_location(data)


def load_location_all(path: Path) -> list[LocationPoint]:
    """Load and parse location points from location_all.json if present, falling back to location.json."""
    location_all_path = path / "location_all.json"
    if location_all_path.exists():
        try:
            with open(location_all_path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ReplayDataError(f"Invalid JSON in location_all.json: {e}") from e  # noqa: TRY003
        return parse_location(data)
    return load_location(path)


class LocationFeed:
    """Monotonic feed over timestamp-sorted location points."""

    def __init__(self, points: list[LocationPoint]) -> None:
        # Loop Bound: bounded by len(points) - 1.
        # Invariant: points must be sorted non-decreasingly by date.
        # Failure Mode: raises ValueError if points are unsorted.
        for i in range(len(points) - 1):
            if points[i].date > points[i + 1].date:
                raise ValueError("Points must be sorted non-decreasingly by timestamp")  # noqa: TRY003
        self._points = points
        self._cursor_idx = 0
        self._last_playhead: datetime | None = None
        self._latest: dict[int, LocationPoint] = {}

    def advance(self, playhead: datetime) -> dict[int, LocationPoint]:
        """Advance cursor to playhead, returning latest LocationPoint per driver."""
        # Loop Bound: cursor advances at most len(self._points) times across all calls.
        # Invariants: playhead must be non-decreasing across calls.
        # Failure Mode: raises ValueError if playhead is strictly smaller than the previous one.
        if self._last_playhead is not None and playhead < self._last_playhead:
            raise ValueError("Playhead cannot regress")  # noqa: TRY003
        self._last_playhead = playhead

        num_points = len(self._points)
        while self._cursor_idx < num_points and self._points[self._cursor_idx].date <= playhead:
            pt = self._points[self._cursor_idx]
            self._latest[pt.driver_number] = pt
            self._cursor_idx += 1

        return dict(self._latest)
