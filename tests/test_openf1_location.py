import json
import time
from datetime import UTC, datetime, timedelta

import pytest

from pitwall.errors import DataParseError
from pitwall.openf1.errors import ReplayDataError
from pitwall.openf1.location import LocationFeed, load_location
from pitwall.openf1.models import LocationPoint, parse_location
from pitwall.openf1.replay import load_session


def test_parse_location_excerpt(excerpt_dir):
    location_path = excerpt_dir / "location.json"
    with open(location_path, encoding="utf-8") as f:
        location_data = json.load(f)
    locations = parse_location(location_data)
    assert len(locations) == 567
    assert all(isinstance(loc, LocationPoint) for loc in locations)
    assert all(loc.driver_number == 1 for loc in locations)

    # record 0 (the seed)
    loc_0 = locations[0]
    assert loc_0.date == datetime(2026, 5, 24, 20, 29, 59, 746000, tzinfo=UTC)
    assert loc_0.x == 3231.0
    assert loc_0.y == 1807.0

    # record 566
    loc_566 = locations[566]
    assert loc_566.date == datetime(2026, 5, 24, 20, 32, 29, 886000, tzinfo=UTC)


def test_parse_location_rejections():
    # boolean x raises DataParseError
    with pytest.raises(DataParseError):
        parse_location([{"date": "2026-05-24T20:29:59.746000+00:00", "driver_number": 1, "x": True, "y": 1807.0}])

    # non-finite x rejected
    with pytest.raises(DataParseError):
        parse_location(
            [{"date": "2026-05-24T20:29:59.746000+00:00", "driver_number": 1, "x": float("nan"), "y": 1807.0}]
        )
    with pytest.raises(DataParseError):
        parse_location(
            [{"date": "2026-05-24T20:29:59.746000+00:00", "driver_number": 1, "x": float("inf"), "y": 1807.0}]
        )

    # missing driver_number raises naming the field
    with pytest.raises(DataParseError) as exc_info:
        parse_location([{"date": "2026-05-24T20:29:59.746000+00:00", "x": 3231.0, "y": 1807.0}])
    assert "driver_number" in str(exc_info.value)

    # naive date parses as UTC
    locations = parse_location([{"date": "2026-05-24T20:29:59.746000", "driver_number": 1, "x": 3231.0, "y": 1807.0}])
    assert locations[0].date == datetime(2026, 5, 24, 20, 29, 59, 746000, tzinfo=UTC)

    # non-list payload rejected
    with pytest.raises(DataParseError):
        parse_location("not a list")
    with pytest.raises(DataParseError):
        parse_location({"not": "a list"})


def test_location_point_fields():
    # Extra keys ignored during parsing
    locations = parse_location(
        [
            {
                "date": "2026-05-24T20:29:59.746000+00:00",
                "driver_number": 1,
                "x": 3231.0,
                "y": 1807.0,
                "z": 100.0,
                "session_key": 11291,
                "meeting_key": 1285,
            }
        ]
    )
    assert len(locations) == 1
    loc = locations[0]
    assert loc.date == datetime(2026, 5, 24, 20, 29, 59, 746000, tzinfo=UTC)
    assert loc.driver_number == 1
    assert loc.x == 3231.0
    assert loc.y == 1807.0
    # LocationPoint has exactly the four D4 fields (z/session_key/meeting_key ignored)
    assert not hasattr(loc, "z")
    assert not hasattr(loc, "session_key")
    assert not hasattr(loc, "meeting_key")


def test_load_location_excerpt(excerpt_dir):
    points = load_location(excerpt_dir)
    assert len(points) == 567
    assert all(isinstance(p, LocationPoint) for p in points)
    with open(excerpt_dir / "location.json", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 567
    for p, record in zip(points, data, strict=True):
        expected_dt = datetime.fromisoformat(record["date"])
        if expected_dt.tzinfo is None:
            expected_dt = expected_dt.replace(tzinfo=UTC)
        assert p.date == expected_dt
        assert p.driver_number == record["driver_number"]
        assert p.x == record["x"]
        assert p.y == record["y"]


def test_missing_file_empty(tmp_path):
    points = load_location(tmp_path)
    assert points == []


def test_invalid_json(tmp_path):
    bad_json_path = tmp_path / "location.json"
    with open(bad_json_path, "w", encoding="utf-8") as f:
        f.write("{invalid json")

    with pytest.raises(ReplayDataError) as exc_info:
        load_location(tmp_path)
    assert "location.json" in str(exc_info.value)


def test_malformed_record(tmp_path):
    bad_record_path = tmp_path / "location.json"
    with open(bad_record_path, "w", encoding="utf-8") as f:
        json.dump([{"date": "2026-05-24T20:29:59.746000+00:00", "x": 3231.0, "y": 1807.0}], f)

    with pytest.raises(DataParseError):
        load_location(tmp_path)


def test_load_session_coexistence(excerpt_dir):
    session = load_session(excerpt_dir)
    assert len(session.drivers) == 22
    assert len(session.stints) == 56
    assert len(session.laps) == 38
    assert len(session.position) == 30
    assert len(session.intervals) == 272
    assert len(session.pit) == 2
    assert len(session.race_control) == 3
    assert session.replay_start == datetime(2026, 5, 24, 20, 30, tzinfo=UTC)


def test_feed_pinned_ticks(excerpt_dir):
    points = load_location(excerpt_dir)
    feed = LocationFeed(points)

    playheads = [
        datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 30, 30, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 31, 0, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 31, 30, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 32, 0, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 32, 30, tzinfo=UTC),
    ]
    expected_ts = [
        datetime(2026, 5, 24, 20, 29, 59, 746000, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 30, 29, 825000, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 30, 59, 846000, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 31, 29, 965000, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 31, 59, 306000, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 32, 29, 886000, tzinfo=UTC),
    ]

    for ph, exp in zip(playheads, expected_ts, strict=True):
        res = feed.advance(ph)
        assert 1 in res
        assert res[1].date == exp


def test_feed_purity_and_monotonic(excerpt_dir):
    points = load_location(excerpt_dir)
    feed = LocationFeed(points)

    ph = datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC)
    res1 = feed.advance(ph)
    assert 1 in res1

    res1[1] = LocationPoint(
        date=datetime(2026, 5, 24, 20, 29, 0, tzinfo=UTC),
        driver_number=1,
        x=0.0,
        y=0.0,
    )

    res2 = feed.advance(ph)
    assert res2[1] is not None
    assert res1 != res2

    # equal playheads ok
    res3 = feed.advance(ph)
    assert res3[1].date == datetime(2026, 5, 24, 20, 29, 59, 746000, tzinfo=UTC)

    # strictly smaller playhead raises ValueError
    ph_smaller = datetime(2026, 5, 24, 20, 29, 59, tzinfo=UTC)
    with pytest.raises(ValueError):
        feed.advance(ph_smaller)


def test_feed_validation():
    p1 = LocationPoint(date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC), driver_number=1, x=1.0, y=2.0)
    p2 = LocationPoint(date=datetime(2026, 5, 24, 20, 29, 0, tzinfo=UTC), driver_number=1, x=1.0, y=2.0)
    with pytest.raises(ValueError):
        LocationFeed([p1, p2])

    empty_feed = LocationFeed([])
    assert empty_feed.advance(datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC)) == {}


def test_feed_benchmark():
    points = [
        LocationPoint(
            date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC) + timedelta(seconds=i),
            driver_number=1,
            x=1.0,
            y=2.0,
        )
        for i in range(25000)
    ]
    feed = LocationFeed(points)
    start = time.perf_counter()
    for j in range(300):
        feed.advance(datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC) + timedelta(seconds=j * 80))
    duration = time.perf_counter() - start
    assert duration < 2.0


def test_load_location_all_precedence(excerpt_dir, tmp_path):
    from pitwall.openf1.location import load_location_all

    # (a) load_location_all(EXCERPT) returns exactly the location_all count, sorted, multi-driver.
    points_all = load_location_all(excerpt_dir)
    assert len(points_all) == 3300

    # sorted by (date, driver_number)
    assert all(points_all[i].date <= points_all[i + 1].date for i in range(len(points_all) - 1))

    # multi-driver
    distinct_drivers = {p.driver_number for p in points_all}
    assert len(distinct_drivers) >= 18

    # (b) A tmpdir copy of the excerpt without location_all.json -> load_location_all returns
    # the same 567 points as load_location (fallback path, list-equality)
    import shutil

    for p in excerpt_dir.iterdir():
        if p.is_file() and p.name != "location_all.json":
            shutil.copy(p, tmp_path / p.name)

    points_fallback = load_location_all(tmp_path)
    points_single = load_location(tmp_path)
    assert len(points_fallback) == 567
    assert points_fallback == points_single

    # (c) location_all.json containing [] -> returns [] (no fallback; present governs)
    with open(tmp_path / "location_all.json", "w", encoding="utf-8") as f:
        f.write("[]")
    assert load_location_all(tmp_path) == []

    # (d) Invalid JSON in location_all.json -> ReplayDataError whose message names location_all.json
    # (even when a valid location.json sits beside it)
    with open(tmp_path / "location_all.json", "w", encoding="utf-8") as f:
        f.write("invalid json")
    with pytest.raises(ReplayDataError) as exc_info:
        load_location_all(tmp_path)
    assert "location_all.json" in str(exc_info.value)
