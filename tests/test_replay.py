import json
import shutil
import time
from datetime import UTC, datetime, timedelta

import pytest

from pitwall.openf1.errors import ReplayDataError
from pitwall.openf1.models import (
    IntervalPoint,
    Lap,
    PitStop,
    PositionUpdate,
    RaceControlMessage,
)
from pitwall.openf1.replay import (
    ReplayEngine,
    ReplayEvent,
    ReplaySession,
    load_session,
    merge_events,
)


def test_excerpt_contract(excerpt_dir):
    expected_files = {
        "drivers.json",
        "stints.json",
        "laps.json",
        "position.json",
        "intervals.json",
        "pit.json",
        "race_control.json",
        "location.json",
        "manifest.json",
        "location_all.json",
    }
    actual_files = {p.name for p in excerpt_dir.iterdir() if p.is_file()}
    assert actual_files == expected_files

    with open(excerpt_dir / "drivers.json", encoding="utf-8") as f:
        assert len(json.load(f)) == 22
    with open(excerpt_dir / "stints.json", encoding="utf-8") as f:
        assert len(json.load(f)) == 56
    with open(excerpt_dir / "laps.json", encoding="utf-8") as f:
        assert len(json.load(f)) == 38
    with open(excerpt_dir / "position.json", encoding="utf-8") as f:
        assert len(json.load(f)) == 30
    with open(excerpt_dir / "intervals.json", encoding="utf-8") as f:
        assert len(json.load(f)) == 272
    with open(excerpt_dir / "pit.json", encoding="utf-8") as f:
        assert len(json.load(f)) == 2
    with open(excerpt_dir / "race_control.json", encoding="utf-8") as f:
        assert len(json.load(f)) == 3
    with open(excerpt_dir / "location.json", encoding="utf-8") as f:
        assert len(json.load(f)) == 567

    assert (excerpt_dir / "location.json").stat().st_size == 72274

    with open(excerpt_dir / "manifest.json", encoding="utf-8") as f:
        manifest = json.load(f)
    assert isinstance(manifest, dict)
    assert manifest["replay_window"]["start"] == "2026-05-24T20:30:00+00:00"
    assert manifest["replay_window"]["end"] == "2026-05-24T20:31:00+00:00"
    assert manifest["session_key"] == 11291
    assert manifest["seeded_streams"] == ["laps", "location", "position"]
    assert manifest["record_counts"]["location"] == 567
    assert manifest["record_counts"]["location_all"] == 3300
    assert manifest["location_window"] == {
        "start": "2026-05-24T20:30:00+00:00",
        "end": "2026-05-24T20:32:30+00:00",
    }

    with open(excerpt_dir / "location_all.json", encoding="utf-8") as f:
        location_all_data = json.load(f)

    assert len(location_all_data) == 3300
    assert 1000 < len(location_all_data) < 3500

    distinct_drivers = {r["driver_number"] for r in location_all_data}
    assert len(distinct_drivers) >= 18

    with open(excerpt_dir / "drivers.json", encoding="utf-8") as f:
        drivers_data = json.load(f)
    session_driver_numbers = {d["driver_number"] for d in drivers_data}
    assert distinct_drivers.issubset(session_driver_numbers)

    # Sorted non-decreasing by (date, driver_number)
    keys = [(r["date"], r["driver_number"]) for r in location_all_data]
    assert all(keys[i] <= keys[i + 1] for i in range(len(keys) - 1))

    # Seed and 1Hz rules
    seed_limit = datetime.fromisoformat("2026-05-24T20:30:00+00:00")
    end_limit = datetime.fromisoformat("2026-05-24T20:32:30+00:00")

    driver_records = {}
    for r in location_all_data:
        d_num = r["driver_number"]
        dt = datetime.fromisoformat(r["date"])
        driver_records.setdefault(d_num, []).append(dt)

    for _d_num, dts in driver_records.items():
        seeds = [dt for dt in dts if dt < seed_limit]
        assert len(seeds) <= 1

        window_dts = [dt for dt in dts if dt >= seed_limit]
        assert all(dt < end_limit for dt in window_dts)

        # 1 Hz rule
        floored_seconds = {dt.replace(microsecond=0) for dt in window_dts}
        assert len(floored_seconds) == len(window_dts)

    total_bytes = sum(p.stat().st_size for p in excerpt_dir.glob("*.json"))
    assert total_bytes < 700000


def test_load_session(excerpt_dir, tmp_path):
    session = load_session(excerpt_dir)
    assert isinstance(session, ReplaySession)
    assert len(session.drivers) == 22
    assert len(session.stints) == 56
    assert len(session.laps) == 38
    assert len(session.position) == 30
    assert len(session.intervals) == 272
    assert len(session.pit) == 2
    assert len(session.race_control) == 3
    assert session.replay_start == datetime(2026, 5, 24, 20, 30, tzinfo=UTC)

    # Missing laps.json raises ReplayDataError naming laps.json
    for p in excerpt_dir.iterdir():
        if p.is_file() and p.name != "laps.json":
            shutil.copy(p, tmp_path / p.name)
    with pytest.raises(ReplayDataError) as exc_info:
        load_session(tmp_path)
    assert "laps.json" in str(exc_info.value)

    # Invalid JSON loud - each stream file containing invalid JSON must raise ReplayDataError naming the file
    for name in ["drivers", "stints", "laps", "position", "intervals", "pit", "race_control"]:
        # Clear/reset tmpdir first
        for p in tmp_path.iterdir():
            if p.is_file():
                p.unlink()
        for p in excerpt_dir.iterdir():
            if p.is_file():
                shutil.copy(p, tmp_path / p.name)

        bad_json_path = tmp_path / f"{name}.json"
        with open(bad_json_path, "w", encoding="utf-8") as f:
            f.write("invalid json")

        with pytest.raises(ReplayDataError) as exc_info:
            load_session(tmp_path)
        assert f"{name}.json" in str(exc_info.value)

    # List-shaped manifest -> replay_start is None
    # Restore ALL streams: the loop's last iteration left race_control.json invalid.
    for p in excerpt_dir.iterdir():
        if p.is_file():
            shutil.copy(p, tmp_path / p.name)
    with open(tmp_path / "manifest.json", "w", encoding="utf-8") as f:
        f.write("[]")
    session_list_manifest = load_session(tmp_path)
    assert session_list_manifest.replay_start is None

    # Absent manifest -> replay_start is None
    (tmp_path / "manifest.json").unlink()
    session_no_manifest = load_session(tmp_path)
    assert session_no_manifest.replay_start is None

    # Extra location_driver1.json ignored
    with open(tmp_path / "location_driver1.json", "w", encoding="utf-8") as f:
        f.write('{"ignored": true}')
    session_extra_ignored = load_session(tmp_path)
    assert session_extra_ignored is not None


def test_merge_events(excerpt_dir):
    session = load_session(excerpt_dir)
    events = merge_events(session)
    assert len(events) == 381

    counts = {}
    for e in events:
        counts[e.kind] = counts.get(e.kind, 0) + 1
    assert counts.get("position") == 30
    assert counts.get("interval") == 272
    assert counts.get("lap_started") == 38
    assert counts.get("lap_completed") == 36
    assert counts.get("pit") == 2
    assert counts.get("race_control") == 3

    assert all(events[i].ts <= events[i + 1].ts for i in range(len(events) - 1))

    # lap_completed ts == date_start + lap_duration
    completed_events = [e for e in events if e.kind == "lap_completed"]
    for ce in completed_events:
        lap = next(
            lp
            for lp in session.laps
            if lp.driver_number == ce.payload.driver_number and lp.lap_number == ce.payload.lap_number
        )
        assert lap.date_start is not None
        assert lap.lap_duration is not None
        assert ce.ts == lap.date_start + timedelta(seconds=lap.lap_duration)

    # purity
    assert merge_events(session) == merge_events(session)

    # synthetic date_start=None lap contributes zero events
    from dataclasses import replace

    null_start_lap = Lap(driver_number=63, lap_number=99, date_start=None, lap_duration=75.0)
    session_with_null_lap = replace(session, laps=[*list(session.laps), null_start_lap])
    events_with_null = merge_events(session_with_null_lap)
    # Merged events should be identical as null start lap yields no events
    assert len(events_with_null) == len(events)

    # same-ts tie-break KIND_PRIORITY then driver_number then seq
    t0 = datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC)
    # KIND_PRIORITY order: position (0), interval (1), lap_started (2), lap_completed (3), pit (4), race_control (5)
    # We construct a session with events sharing t0
    test_session = ReplaySession(
        drivers=[],
        stints=[],
        position=[
            PositionUpdate(date=t0, driver_number=5, position=1),  # seq 0
            PositionUpdate(date=t0, driver_number=2, position=2),  # seq 1
        ],
        intervals=[
            IntervalPoint(date=t0, driver_number=2, gap_to_leader=1.0, interval=1.0),  # seq 0
        ],
        laps=[
            Lap(driver_number=2, lap_number=1, date_start=t0, lap_duration=None),  # seq 0 -> lap_started
        ],
        pit=[
            PitStop(date=t0, driver_number=2, lap_number=1, pit_duration=10.0),  # seq 0
        ],
        race_control=[
            RaceControlMessage(
                date=t0,
                message="test",
                category=None,
                flag=None,
                scope=None,
                lap_number=None,
                driver_number=None,
            ),  # seq 0
        ],
        replay_start=t0,
    )
    merged = merge_events(test_session)
    # Expected ordering:
    # 1. PositionUpdate (kind=position: priority 0), driver_number=2 (lower than 5)
    # 2. PositionUpdate (kind=position: priority 0), driver_number=5
    # 3. IntervalPoint (kind=interval: priority 1), driver_number=2
    # 4. Lap (kind=lap_started: priority 2), driver_number=2
    # 5. PitStop (kind=pit: priority 4), driver_number=2
    # 6. RaceControlMessage (kind=race_control: priority 5), driver_number=None (-1 tie-break)
    assert [m.kind for m in merged] == [
        "position",
        "position",
        "interval",
        "lap_started",
        "pit",
        "race_control",
    ]
    assert [m.payload.driver_number for m in merged] == [2, 5, 2, 2, 2, None]


@pytest.mark.asyncio
async def test_engine(excerpt_dir):
    session = load_session(excerpt_dir)
    events = merge_events(session)

    sleep_calls = []

    async def record_sleep(seconds: float):
        sleep_calls.append(seconds)

    engine = ReplayEngine(
        events,
        speed=60,
        tick_interval_s=0.5,
        sleep=record_sleep,
        start_at=session.replay_start,
    )

    ticks = []
    async for tick in engine.ticks():
        ticks.append(tick)

    # exactly 6 ticks
    assert len(ticks) == 6

    # playheads 20:30:00..20:32:30 step 30s
    expected_playheads = [
        datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 30, 30, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 31, 0, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 31, 30, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 32, 0, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 32, 30, tzinfo=UTC),
    ]
    assert [t.playhead for t in ticks] == expected_playheads

    # per-tick counts [44,165,152,6,12,2]
    assert [len(t.events) for t in ticks] == [44, 165, 152, 6, 12, 2]

    # 6 sleep calls each 0.5
    assert sleep_calls == [0.5] * 6

    # re-iteration identical
    ticks2 = []
    async for tick in engine.ticks():
        ticks2.append(tick)
    assert ticks2 == ticks
    assert sleep_calls == [0.5] * 12

    # start_at=None defaults to first ts
    engine_none_start = ReplayEngine(
        events,
        speed=60,
        tick_interval_s=0.5,
        sleep=record_sleep,
        start_at=None,
    )
    ticks_none = []
    async for tick in engine_none_start.ticks():
        ticks_none.append(tick)
    assert ticks_none[0].playhead == events[0].ts

    # far-future start_at -> one catch-up tick
    far_future = datetime(2026, 5, 24, 21, 0, tzinfo=UTC)
    engine_future = ReplayEngine(
        events,
        speed=60,
        tick_interval_s=0.5,
        sleep=record_sleep,
        start_at=far_future,
    )
    ticks_future = []
    async for tick in engine_future.ticks():
        ticks_future.append(tick)
    assert len(ticks_future) == 1
    assert ticks_future[0].playhead == far_future
    assert len(ticks_future[0].events) == len(events)

    # empty events -> zero ticks
    engine_empty = ReplayEngine(
        [],
        speed=60,
        tick_interval_s=0.5,
        sleep=record_sleep,
        start_at=session.replay_start,
    )
    ticks_empty = []
    async for tick in engine_empty.ticks():
        ticks_empty.append(tick)
    assert len(ticks_empty) == 0

    # empty-span tick still yielded
    t0 = datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC)
    synthetic_events = [
        ReplayEvent(ts=t0, kind="position", payload=PositionUpdate(date=t0, driver_number=1, position=1)),
        ReplayEvent(
            ts=t0 + timedelta(seconds=95),
            kind="position",
            payload=PositionUpdate(date=t0 + timedelta(seconds=95), driver_number=1, position=1),
        ),
    ]
    engine_span = ReplayEngine(
        synthetic_events,
        speed=60,
        tick_interval_s=0.5,
        sleep=record_sleep,
        start_at=t0,
    )
    ticks_span = []
    async for tick in engine_span.ticks():
        ticks_span.append(tick)
    # Ticks at: t0, t0+30, t0+60, t0+90, t0+120
    assert len(ticks_span) == 5
    assert [len(t.events) for t in ticks_span] == [1, 0, 0, 0, 1]

    # speed=0 and tick_interval_s=0 raise ValueError
    with pytest.raises(ValueError):
        ReplayEngine(events, speed=0)
    with pytest.raises(ValueError):
        ReplayEngine(events, speed=60, tick_interval_s=0)
    with pytest.raises(ValueError):
        ReplayEngine(events, speed=-1)
    with pytest.raises(ValueError):
        ReplayEngine(events, speed=60, tick_interval_s=-0.5)


def test_merge_events_benchmark():
    # AC-13: merge_events over ~23,000 synthetic interval-scale records completes < 2.0 s
    t0 = datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC)
    intervals = [
        IntervalPoint(date=t0 + timedelta(milliseconds=i), driver_number=1, gap_to_leader=1.0, interval=1.0)
        for i in range(23000)
    ]
    session = ReplaySession(
        drivers=[],
        stints=[],
        position=[],
        intervals=intervals,
        laps=[],
        pit=[],
        race_control=[],
        replay_start=t0,
    )
    start_time = time.perf_counter()
    events = merge_events(session)
    duration = time.perf_counter() - start_time
    assert len(events) == 23000
    assert duration < 2.0


def test_worker_catch_implication():
    import inspect

    from pitwall.screens.live_timing import LiveTimingScreen

    source = inspect.getsource(LiveTimingScreen._replay_worker)
    assert (
        "except (ReplayDataError, DataParseError, OSError):" in source
        or "except (ReplayDataError, DataParseError, OSError) as" in source
    )


def test_spec_constants():
    # AC-7: TICK_INTERVAL_S and KIND_PRIORITY exported
    import inspect

    import pitwall.openf1.replay as replay
    from pitwall.openf1.replay import KIND_PRIORITY, TICK_INTERVAL_S, ReplayEngine

    assert TICK_INTERVAL_S == 0.5
    assert KIND_PRIORITY == {
        "position": 0,
        "interval": 1,
        "lap_started": 2,
        "lap_completed": 3,
        "pit": 4,
        "race_control": 5,
    }

    # ReplayEngine's default tick_interval_s is TICK_INTERVAL_S
    sig = inspect.signature(ReplayEngine.__init__)
    assert sig.parameters["tick_interval_s"].default == TICK_INTERVAL_S

    # grep -c "KIND_PRIORITY" src/pitwall/openf1/replay.py >= 2
    replay_src = inspect.getsource(replay)
    assert replay_src.count("KIND_PRIORITY") >= 2

    # grep -rn "except Exception" src/pitwall/openf1/ and noqa: S110 are empty
    # We can inspect files directly in the test to prevent regression
    import pathlib

    openf1_dir = pathlib.Path("src/pitwall/openf1")
    for p in openf1_dir.glob("*.py"):
        src_code = p.read_text(encoding="utf-8")
        assert "except Exception" not in src_code
        if p.name == "replay.py":
            assert "noqa: S110" not in src_code


def test_manifest_containment(excerpt_dir, tmp_path):
    # F13 _read_replay_start containment tests
    # Copy excerpt stream files
    for p in excerpt_dir.iterdir():
        if p.is_file() and p.name != "manifest.json":
            shutil.copy(p, tmp_path / p.name)

    # 1. invalid-JSON manifest -> replay_start is None
    with open(tmp_path / "manifest.json", "w", encoding="utf-8") as f:
        f.write("{invalid-json}")
    session = load_session(tmp_path)
    assert session.replay_start is None

    # 2. start 12345 -> None
    with open(tmp_path / "manifest.json", "w", encoding="utf-8") as f:
        json.dump({"replay_window": {"start": 12345}}, f)
    session = load_session(tmp_path)
    assert session.replay_start is None

    # 3. start not-a-date -> None
    with open(tmp_path / "manifest.json", "w", encoding="utf-8") as f:
        json.dump({"replay_window": {"start": "not-a-date"}}, f)
    session = load_session(tmp_path)
    assert session.replay_start is None


@pytest.mark.asyncio
async def test_tick_source_protocol_isinstance() -> None:
    # AC-3: TickSource runtime_checkable protocol; isinstance checks for ReplayEngine.
    # Use conftest wrap_transport + recorders.
    from pitwall.openf1.client import OpenF1Client
    from pitwall.openf1.replay import ReplayEngine, TickSource

    # isinstance check for ReplayEngine
    engine = ReplayEngine(events=[], speed=60.0)
    assert isinstance(engine, TickSource)

    # isinstance check for LiveSource
    from datetime import UTC, datetime

    import httpx
    from conftest import wrap_transport

    from pitwall.openf1.live import LiveSource
    from pitwall.openf1.models import Session

    recorded = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        return httpx.Response(200, json=[])

    transport = wrap_transport(handler)
    async with OpenF1Client(transport=transport) as client:
        session = Session(
            session_key=11291,
            meeting_key=1285,
            session_name="Race",
            date_start=datetime(2026, 5, 24, 19, 0, tzinfo=UTC),
            date_end=datetime(2026, 5, 24, 21, 0, tzinfo=UTC),
        )
        source = LiveSource(client, session)
        assert isinstance(source, TickSource)


def test_merge_none_driver_sentinel_orders_first():
    """iter15 mutation killer: same-ts tie-break places driver-less events before driver 1."""
    import datetime as _dt

    from pitwall.openf1.models import RaceControlMessage
    from pitwall.openf1.replay import ReplaySession, merge_events

    rc_none = RaceControlMessage(
        date=_dt.datetime(2026, 5, 24, 20, 30, tzinfo=_dt.UTC),
        message="FLAG",
        category="Flag",
        flag=None,
        scope=None,
        lap_number=None,
        driver_number=None,
    )
    rc_one = RaceControlMessage(
        date=_dt.datetime(2026, 5, 24, 20, 30, tzinfo=_dt.UTC),
        message="CAR 1",
        category="Other",
        flag=None,
        scope=None,
        lap_number=None,
        driver_number=1,
    )
    session = ReplaySession(
        drivers=[],
        stints=[],
        laps=[],
        position=[],
        intervals=[],
        pit=[],
        race_control=[rc_one, rc_none],
        replay_start=None,
    )
    events = merge_events(session)
    # The None-driver sentinel (-1) sorts BEFORE driver 1 at equal ts/kind.
    assert [getattr(e.payload, "driver_number", None) for e in events] == [None, 1]
