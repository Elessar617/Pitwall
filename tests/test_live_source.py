import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from conftest import wrap_transport

from pitwall.openf1.client import OpenF1Client

# We import LiveSource and session_window from pitwall.openf1.live.
# Since the module/class do not exist yet, this will raise an ImportError/ModuleNotFoundError
# when running pytest, which is the correct RED phase result.
from pitwall.openf1.live import LiveSource, session_window
from pitwall.openf1.models import (
    Session,
)
from pitwall.openf1.replay import load_session, merge_events
from pitwall.screens.live_timing import fold_events


class MockSleepGate:
    """A gate-stepped sleep manager for deterministic testing."""

    def __init__(self):
        self.sleeps = []

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        # Yield control but do not block test execution
        await asyncio.sleep(0.001)


def get_mock_session() -> Session:
    """Return the mock session record as a Session object."""
    return Session(
        session_key=11291,
        meeting_key=1285,
        session_name="Race",
        date_start=datetime(2026, 5, 24, 19, 0, 0, tzinfo=UTC),
        date_end=datetime(2026, 5, 24, 21, 0, 0, tzinfo=UTC),
    )


def build_excerpt_handler(excerpt_dir: Path, recorded_requests: list[httpx.Request]):
    """Build a mock transport handler that serves excerpt files and records requests."""

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        url_str = str(request.url)

        if "sessions" in url_str:
            return httpx.Response(
                200,
                json=[
                    {
                        "session_key": 11291,
                        "meeting_key": 1285,
                        "session_name": "Race",
                        "session_type": "Race",
                        "date_start": "2026-05-24T19:00:00+00:00",
                        "date_end": "2026-05-24T21:00:00+00:00",
                        "circuit_short_name": "Montreal",
                    }
                ],
            )

        # Map query streams to file names
        mapping = {
            "drivers": "drivers.json",
            "stints": "stints.json",
            "position": "position.json",
            "intervals": "intervals.json",
            "laps": "laps.json",
            "pit": "pit.json",
            "race_control": "race_control.json",
            "location": "location.json",
        }

        for key, filename in mapping.items():
            if key in url_str:
                filepath = excerpt_dir / filename
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                return httpx.Response(200, json=data)

        return httpx.Response(404, json={"error": "not found"})

    return handler


@pytest.mark.asyncio
async def test_session_window_bounds() -> None:
    """Verify session_window boundary units at exactly start - 900s and end + 3600s."""
    session = get_mock_session()
    start = session.date_start
    end = session.date_end

    # Upcoming
    assert session_window(session, start - timedelta(seconds=901)) == "upcoming"
    # Open boundaries (inclusive)
    assert session_window(session, start - timedelta(seconds=900)) == "open"
    assert session_window(session, start) == "open"
    assert session_window(session, end) == "open"
    assert session_window(session, end + timedelta(seconds=3600)) == "open"
    # Ended boundary
    assert session_window(session, end + timedelta(seconds=3601)) == "ended"


@pytest.mark.asyncio
async def test_backfill_tick(excerpt_dir: Path) -> None:
    """AC-4: Backfill tick (tick 0) serves full excerpt, sorts events, matches fold equivalence."""
    recorded_requests = []
    transport_handler = build_excerpt_handler(excerpt_dir, recorded_requests)
    transport = wrap_transport(transport_handler)

    clock_time = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)
    clock = lambda: clock_time

    sleep_gate = MockSleepGate()

    async with OpenF1Client(transport=transport) as client:
        session = get_mock_session()
        source = LiveSource(
            client,
            session,
            poll_interval_s=10.0,
            sleep=sleep_gate.sleep,
            clock=clock,
        )

        # We take the first tick from the generator
        ticks = []
        async for tick in source.ticks():
            ticks.append(tick)
            break

        assert len(ticks) == 1
        tick0 = ticks[0]

        # Verify gate-stepped sleep called exactly once on tick 0
        assert sleep_gate.sleeps == [10.0]

        # Assert the eight request URLs in exact order
        expected_urls = [
            "https://api.openf1.org/v1/drivers?session_key=11291",
            "https://api.openf1.org/v1/stints?session_key=11291",
            "https://api.openf1.org/v1/position?session_key=11291",
            "https://api.openf1.org/v1/intervals?session_key=11291",
            "https://api.openf1.org/v1/laps?session_key=11291",
            "https://api.openf1.org/v1/pit?session_key=11291",
            "https://api.openf1.org/v1/race_control?session_key=11291",
            "https://api.openf1.org/v1/location?session_key=11291&date%3E2026-05-24T20:28:00",
        ]
        actual_urls = [str(r.url) for r in recorded_requests]
        assert actual_urls == expected_urls

        # Verify exposed state
        assert len(source.drivers) == 22
        assert len(source.stints) == 56

        # Fold equivalence
        replay_session = load_session(excerpt_dir)
        replay_events = merge_events(replay_session)
        expected_fold = fold_events(replay_events)
        actual_fold = fold_events(list(tick0.events))
        assert actual_fold == expected_fold

        # Verify playhead, data head, index, and event types
        expected_data_head = datetime(2026, 5, 24, 20, 32, 29, 886000, tzinfo=UTC)
        assert tick0.playhead == expected_data_head
        assert source.data_head == expected_data_head
        assert tick0.index == 0
        assert isinstance(tick0.events, tuple)

        # Verify sorting key: (ts, KIND_PRIORITY[kind], driver_number or -1, arrival_seq)
        for i in range(len(tick0.events) - 1):
            e1 = tick0.events[i]
            e2 = tick0.events[i + 1]
            assert e1.ts <= e2.ts


@pytest.mark.asyncio
async def test_steady_state_cursors(excerpt_dir: Path) -> None:
    """AC-5: Cursors query with proper overlap, return 404 as quiet window, deduplicate overlap."""
    recorded_requests = []
    backfill_handler = build_excerpt_handler(excerpt_dir, recorded_requests)

    # State manager for mock server responses
    is_backfill = True

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal is_backfill
        if is_backfill:
            res = backfill_handler(request)
            # Once location is requested, backfill of tick 0 is complete
            if "location" in str(request.url):
                is_backfill = False
            return res
        # After backfill, all streams return 404
        recorded_requests.append(request)
        return httpx.Response(404, json={"error": "no new data"})

    transport = wrap_transport(handler)
    clock_time = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)
    clock = lambda: clock_time
    sleep_gate = MockSleepGate()

    async with OpenF1Client(transport=transport) as client:
        session = get_mock_session()
        source = LiveSource(
            client,
            session,
            poll_interval_s=10.0,
            sleep=sleep_gate.sleep,
            clock=clock,
        )

        iterator = source.ticks()
        tick0 = await anext(iterator)
        recorded_requests.clear()  # Clear backfill requests

        tick1 = await anext(iterator)

        # Assert the six pinned cursor URLs in order (cursor = stream max - 1s, laps - 240s)
        expected_cursors = [
            "https://api.openf1.org/v1/position?session_key=11291&date%3E2026-05-24T20:30:34",
            "https://api.openf1.org/v1/intervals?session_key=11291&date%3E2026-05-24T20:30:58",
            "https://api.openf1.org/v1/laps?session_key=11291&date%3E2026-05-24T20:26:52",
            "https://api.openf1.org/v1/pit?session_key=11291&date%3E2026-05-24T20:30:46",
            "https://api.openf1.org/v1/race_control?session_key=11291&date%3E2026-05-24T20:30:45",
            "https://api.openf1.org/v1/location?session_key=11291&date%3E2026-05-24T20:32:28",
        ]
        actual_cursors = [str(r.url) for r in recorded_requests]
        assert actual_cursors == expected_cursors

        # Verify empty tick with playhead unchanged
        assert tick1.events == ()
        assert tick1.playhead == tick0.playhead


@pytest.mark.asyncio
async def test_deduplication_and_lap_policy() -> None:
    """AC-5: Verify same-second deduplication and lap started->completed policy."""
    poll_count = 0

    # We construct a sequence of server responses
    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal poll_count
        url = str(request.url)

        if "sessions" in url:
            return httpx.Response(
                200,
                json=[
                    {
                        "session_key": 11291,
                        "meeting_key": 1285,
                        "session_name": "Race",
                        "session_type": "Race",
                        "date_start": "2026-05-24T19:00:00+00:00",
                        "date_end": "2026-05-24T21:00:00+00:00",
                        "circuit_short_name": "Montreal",
                    }
                ],
            )

        if "drivers" in url or "stints" in url:
            return httpx.Response(200, json=[])

        if poll_count == 0:
            # Backfill (poll 0)
            if "race_control" in url:
                return httpx.Response(
                    200,
                    json=[
                        {
                            "date": "2026-05-24T20:30:45+00:00",
                            "message": "First Message",
                            "category": None,
                            "flag": None,
                            "scope": None,
                            "lap_number": None,
                            "driver_number": None,
                        }
                    ],
                )
            if "laps" in url:
                return httpx.Response(
                    200,
                    json=[
                        {
                            "driver_number": 1,
                            "lap_number": 5,
                            "date_start": "2026-05-24T20:30:00+00:00",
                            "lap_duration": None,
                        }
                    ],
                )
            return httpx.Response(200, json=[])

        elif poll_count == 1:
            # Steady state poll 1 (tick 1)
            if "race_control" in url:
                # Returns the already seen message (deduped) and a new message with the same timestamp
                return httpx.Response(
                    200,
                    json=[
                        {
                            "date": "2026-05-24T20:30:45+00:00",
                            "message": "First Message",
                            "category": None,
                            "flag": None,
                            "scope": None,
                            "lap_number": None,
                            "driver_number": None,
                        },
                        {
                            "date": "2026-05-24T20:30:45+00:00",
                            "message": "Second Message",
                            "category": None,
                            "flag": None,
                            "scope": None,
                            "lap_number": None,
                            "driver_number": None,
                        },
                    ],
                )
            if "laps" in url:
                # Re-serves the lap with lap_duration filled in
                return httpx.Response(
                    200,
                    json=[
                        {
                            "driver_number": 1,
                            "lap_number": 5,
                            "date_start": "2026-05-24T20:30:00+00:00",
                            "lap_duration": 76.5,
                        }
                    ],
                )
            return httpx.Response(200, json=[])

        return httpx.Response(404, json=[])

    transport = wrap_transport(handler)
    clock_time = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)
    clock = lambda: clock_time
    sleep_gate = MockSleepGate()

    async with OpenF1Client(transport=transport) as client:
        session = get_mock_session()
        source = LiveSource(
            client,
            session,
            poll_interval_s=10.0,
            sleep=sleep_gate.sleep,
            clock=clock,
        )

        iterator = source.ticks()

        # Tick 0
        tick0 = await anext(iterator)
        # Should have exactly one lap_started event for lap 5
        lap_started_events = [e for e in tick0.events if e.kind == "lap_started"]
        assert len(lap_started_events) == 1
        assert lap_started_events[0].payload.lap_number == 5

        # Should have exactly one race control message
        rc_events = [e for e in tick0.events if e.kind == "race_control"]
        assert len(rc_events) == 1
        assert rc_events[0].payload.message == "First Message"

        # Advance poll count for steady state
        poll_count = 1

        # Tick 1
        tick1 = await anext(iterator)

        # Deduplication edge check:
        # "First Message" should be deduped, only "Second Message" emitted
        rc1_events = [e for e in tick1.events if e.kind == "race_control"]
        assert len(rc1_events) == 1
        assert rc1_events[0].payload.message == "Second Message"

        # Lap started->completed policy:
        # lap_started must not be re-emitted, and lap_completed is emitted with correct duration-based timestamp
        lap_started_tick1 = [e for e in tick1.events if e.kind == "lap_started"]
        assert len(lap_started_tick1) == 0

        lap_completed_tick1 = [e for e in tick1.events if e.kind == "lap_completed"]
        assert len(lap_completed_tick1) == 1
        assert lap_completed_tick1[0].payload.lap_number == 5
        assert lap_completed_tick1[0].ts == datetime(2026, 5, 24, 20, 31, 16, 500000, tzinfo=UTC)


@pytest.mark.asyncio
async def test_stints_refresh(excerpt_dir: Path) -> None:
    """AC-5: Verify stints are refetched on tick 6 only."""
    recorded_requests = []
    excerpt_handler = build_excerpt_handler(excerpt_dir, recorded_requests)

    def handler(request: httpx.Request) -> httpx.Response:
        return excerpt_handler(request)

    transport = wrap_transport(handler)
    clock_time = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)
    clock = lambda: clock_time
    sleep_gate = MockSleepGate()

    async with OpenF1Client(transport=transport) as client:
        session = get_mock_session()
        source = LiveSource(
            client,
            session,
            poll_interval_s=10.0,
            sleep=sleep_gate.sleep,
            clock=clock,
        )

        iterator = source.ticks()

        # Tick 0: Backfill, fetches stints
        await anext(iterator)
        stints_requests_t0 = [r for r in recorded_requests if "stints" in str(r.url)]
        assert len(stints_requests_t0) == 1
        recorded_requests.clear()

        # Ticks 1 to 5: steady state, stints should not be fetched
        for _ in range(1, 6):
            await anext(iterator)
            stints_requests = [r for r in recorded_requests if "stints" in str(r.url)]
            assert len(stints_requests) == 0
            recorded_requests.clear()

        # Tick 6: stints should be refetched
        await anext(iterator)
        stints_requests_t6 = [r for r in recorded_requests if "stints" in str(r.url)]
        assert len(stints_requests_t6) == 1


@pytest.mark.asyncio
async def test_degradation_containment_and_cadence() -> None:
    """AC-6: Verify per-request containment of OpenF1Errors, consecutive_failures, and cadence bounds."""
    recorded_requests = []
    should_fail = False

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        if should_fail:
            # Raise connection/network errors which OpenF1Client wraps to OpenF1NetworkError
            raise httpx.ConnectError("Connection failed")  # noqa: TRY003

        url = str(request.url)
        if "sessions" in url:
            return httpx.Response(200, json=[])
        return httpx.Response(200, json=[])

    transport = wrap_transport(handler)
    clock_time = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)
    clock = lambda: clock_time
    sleep_gate = MockSleepGate()

    async with OpenF1Client(transport=transport) as client:
        session = get_mock_session()
        source = LiveSource(
            client,
            session,
            poll_interval_s=10.0,
            sleep=sleep_gate.sleep,
            clock=clock,
        )

        iterator = source.ticks()

        # Tick 0 (Healthy)
        tick0 = await anext(iterator)
        assert tick0.events == ()
        assert source.consecutive_failures == 0
        recorded_requests.clear()

        # Tick 1 (Failing)
        should_fail = True
        tick1 = await anext(iterator)
        # Verify tick is still yielded with empty events and failures == 1
        assert tick1.events == ()
        assert source.consecutive_failures == 1
        # Assert cadence: exactly one sleep and <= 8 requests
        assert len(recorded_requests) <= 8
        recorded_requests.clear()

        # Tick 2 (Failing)
        tick2 = await anext(iterator)
        assert tick2.events == ()
        assert source.consecutive_failures == 2
        recorded_requests.clear()

        # Tick 3 (Clean)
        should_fail = False
        tick3 = await anext(iterator)
        assert tick3.events == ()
        assert source.consecutive_failures == 0


@pytest.mark.asyncio
async def test_termination_and_small_loop_bound() -> None:
    """AC-6: Clock steps past date_end + 3600 breaks loop, and clock near end honors small loop bound."""
    recorded_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=[])

    transport = wrap_transport(handler)
    sleep_gate = MockSleepGate()

    # Case A: Termination past date_end + 3600 (22:00:00 UTC) via clock step
    # Start clock at 21:59:50 (within overrun window)
    clock_time = datetime(2026, 5, 24, 21, 59, 50, tzinfo=UTC)

    def clock_step():
        nonlocal clock_time
        # Step clock by 15 seconds on each call
        clock_time += timedelta(seconds=15)
        return clock_time

    async with OpenF1Client(transport=transport) as client:
        session = get_mock_session()
        source = LiveSource(
            client,
            session,
            poll_interval_s=10.0,
            sleep=sleep_gate.sleep,
            clock=clock_step,
        )

        ticks = []
        async for tick in source.ticks():
            ticks.append(tick)

        # Loop should terminate because clock steps past 22:00:00 (end + 3600)
        # Tick 0 clock() will be 22:00:05 (first step during/before tick 0), which breaks the loop immediately
        assert len(ticks) == 0

    # Case B: Small computed loop bound is honored exactly
    # session date_end + 3600 is 22:00:00. Clock starts at 21:59:45.
    # computed tick count limit: 1 + ceil((22:00:00 - 21:59:45) / 10) = 1 + ceil(15 / 10) = 1 + 2 = 3 ticks.
    # Set clock to be static so it doesn't step beyond overrun window
    static_clock = lambda: datetime(2026, 5, 24, 21, 59, 45, tzinfo=UTC)

    async with OpenF1Client(transport=transport) as client:
        session = get_mock_session()
        source = LiveSource(
            client,
            session,
            poll_interval_s=10.0,
            sleep=sleep_gate.sleep,
            clock=static_clock,
        )

        ticks = []
        async for tick in source.ticks():
            ticks.append(tick)

        assert len(ticks) == 3


@pytest.mark.asyncio
async def test_location_accumulation_and_outline_readiness(excerpt_dir: Path) -> None:
    """AC-7: Verify outline readiness thresholds, take_outline_points clears, latest_location out-of-order replacement."""
    recorded_requests = []
    transport_handler = build_excerpt_handler(excerpt_dir, recorded_requests)
    transport = wrap_transport(transport_handler)

    clock_time = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)
    clock = lambda: clock_time
    sleep_gate = MockSleepGate()

    async with OpenF1Client(transport=transport) as client:
        session = get_mock_session()
        source = LiveSource(
            client,
            session,
            poll_interval_s=10.0,
            sleep=sleep_gate.sleep,
            clock=clock,
        )

        iterator = source.ticks()
        await anext(iterator)

        # After AC-4 backfill tick:
        # 1. outline_ready is True (span 150.14 s >= 150.0, count 567 >= 500)
        assert source.outline_ready is True

        # 2. take_outline_points() returns the 567 points and clears the buffer
        points = source.take_outline_points()
        assert len(points) == 567
        assert isinstance(points, tuple)

        # Second call returns empty tuple
        assert source.take_outline_points() == ()

        # 3. latest_location() returns fresh dict and contains correct driver latest point
        loc_dict = source.latest_location()
        assert isinstance(loc_dict, dict)
        # Should be a fresh dict per call
        assert loc_dict is not source.latest_location()

        driver_1_point = loc_dict[1]
        assert driver_1_point.driver_number == 1
        assert driver_1_point.date == datetime(2026, 5, 24, 20, 32, 29, 886000, tzinfo=UTC)
        assert driver_1_point.x == -472.0
        assert driver_1_point.y == 16521.0


@pytest.mark.asyncio
async def test_location_out_of_order_tolerance() -> None:
    """AC-7: Verify out-of-order tolerance and equal-ts later-fetch wins policy."""
    recorded_requests = []
    points_to_serve = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        if "location" in str(request.url):
            return httpx.Response(200, json=points_to_serve)
        return httpx.Response(200, json=[])

    transport = wrap_transport(handler)
    clock_time = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)
    clock = lambda: clock_time
    sleep_gate = MockSleepGate()

    async with OpenF1Client(transport=transport) as client:
        session = get_mock_session()
        source = LiveSource(
            client,
            session,
            poll_interval_s=10.0,
            sleep=sleep_gate.sleep,
            clock=clock,
        )

        iterator = source.ticks()

        # Poll 1: Serve a new point
        points_to_serve = [{"date": "2026-05-24T20:30:00.000000+00:00", "driver_number": 1, "x": 10.0, "y": 20.0}]
        await anext(iterator)
        loc = source.latest_location()
        assert loc[1].x == 10.0

        # Poll 2: Older point arrives (out-of-order). Date is 20:29:50 (older).
        # Newer point (20:30:00) should be kept.
        points_to_serve = [{"date": "2026-05-24T20:29:50.000000+00:00", "driver_number": 1, "x": 5.0, "y": 5.0}]
        await anext(iterator)
        loc = source.latest_location()
        assert loc[1].x == 10.0  # Kept newer point

        # Poll 3: Equal timestamp, new coordinates.
        # Equal-ts later-fetch wins.
        points_to_serve = [{"date": "2026-05-24T20:30:00.000000+00:00", "driver_number": 1, "x": 15.0, "y": 25.0}]
        await anext(iterator)
        loc = source.latest_location()
        assert loc[1].x == 15.0  # Replaced because date >= held date


@pytest.mark.asyncio
async def test_location_buffer_cap_readiness() -> None:
    """AC-7: Verify location_buffer_cap readiness on count alone and not-ready paths."""
    recorded_requests = []
    points_to_serve = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        if "location" in str(request.url):
            return httpx.Response(200, json=points_to_serve)
        return httpx.Response(200, json=[])

    transport = wrap_transport(handler)
    clock_time = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)
    clock = lambda: clock_time
    sleep_gate = MockSleepGate()

    async with OpenF1Client(transport=transport) as client:
        session = get_mock_session()

        # Test Case A: location_buffer_cap=10 readiness on count alone
        source_cap = LiveSource(
            client,
            session,
            poll_interval_s=10.0,
            sleep=sleep_gate.sleep,
            clock=clock,
            location_buffer_cap=10,
        )

        iterator = source_cap.ticks()

        # Serve 10 points with small span (e.g. 5 seconds span)
        points_to_serve = [
            {"date": f"2026-05-24T20:30:0{i}.000000+00:00", "driver_number": 1, "x": float(i), "y": float(i)}
            for i in range(10)
        ]
        await anext(iterator)

        # Should be ready because count (10) >= location_buffer_cap (10)
        assert source_cap.outline_ready is True
        assert len(source_cap.take_outline_points()) == 10

    async with OpenF1Client(transport=transport) as client:
        # Test Case B: Not ready when both span and count thresholds are not met
        source_not_ready = LiveSource(
            client,
            session,
            poll_interval_s=10.0,
            sleep=sleep_gate.sleep,
            clock=clock,
        )
        iterator = source_not_ready.ticks()

        # Serve 5 points with 5 seconds span (span 5 < 150, count 5 < 500)
        points_to_serve = [
            {"date": f"2026-05-24T20:30:0{i}.000000+00:00", "driver_number": 1, "x": float(i), "y": float(i)}
            for i in range(5)
        ]
        await anext(iterator)
        assert source_not_ready.outline_ready is False

        # Test Case C: Not ready when location 404s (empty list)
        points_to_serve = []
        await anext(iterator)
        assert source_not_ready.outline_ready is False


# ---- iter15 AC-1: malformed records degrade per-stream, never escape ----


async def test_malformed_record_contained_per_stream(make_session_transport_factory=None):
    import json as _json
    from datetime import UTC, datetime

    from conftest import wrap_transport

    from pitwall.openf1 import OpenF1Client
    from pitwall.openf1.live import LiveSource
    from pitwall.openf1.models import Session

    session = Session(
        session_key=11291,
        meeting_key=1285,
        session_name="Race",
        date_start=datetime(2026, 5, 24, 19, 0, tzinfo=UTC),
        date_end=datetime(2026, 5, 24, 21, 0, tzinfo=UTC),
    )
    clock_time = datetime(2026, 5, 24, 20, 35, 0, tzinfo=UTC)

    async def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "position" in url:
            return httpx.Response(
                200,
                text=_json.dumps([{"driver_number": 1, "date": "2026-05-24T20:30:00+00:00", "position": "banana"}]),
            )
        return httpx.Response(404, json=[])

    sleeps: list[float] = []

    async def fast_sleep(s: float) -> None:
        sleeps.append(s)

    async with OpenF1Client(transport=wrap_transport(handler)) as client:
        source = LiveSource(client, session, sleep=fast_sleep, clock=lambda: clock_time)
        iterator = source.ticks().__aiter__()
        tick = await iterator.__anext__()
        # The malformed position stream is contained: the tick yields, the
        # failure registers, and nothing escapes the OpenF1 taxonomy.
        assert tick.events == ()
        assert source.consecutive_failures >= 1


async def test_location_buffer_stops_after_outline_taken(db_conn, make_gated_transport):
    """iter15 PERF-1: once the outline is consumed, the buffer stays empty
    while latest_location keeps updating (markers unaffected)."""
    import json as _json
    from datetime import UTC, datetime, timedelta

    from conftest import wrap_transport

    from pitwall.openf1 import OpenF1Client
    from pitwall.openf1.live import LiveSource
    from pitwall.openf1.models import Session

    session = Session(
        session_key=11291,
        meeting_key=1285,
        session_name="Race",
        date_start=datetime(2026, 5, 24, 19, 0, tzinfo=UTC),
        date_end=datetime(2026, 5, 24, 21, 0, tzinfo=UTC),
    )
    base = datetime(2026, 5, 24, 20, 0, tzinfo=UTC)
    poll_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal poll_count
        url = str(request.url)
        if "location" in url:
            poll_count += 1
            pts = [
                {
                    "driver_number": 1,
                    "date": (base + timedelta(seconds=poll_count * 200 + i)).isoformat(),
                    "x": float(i),
                    "y": float(i),
                }
                for i in range(600)
            ]
            return httpx.Response(200, text=_json.dumps(pts))
        return httpx.Response(404, json=[])

    clock_now = base + timedelta(minutes=40)

    async def fast_sleep(s: float) -> None:
        pass

    async with OpenF1Client(transport=wrap_transport(handler)) as client:
        source = LiveSource(client, session, sleep=fast_sleep, clock=lambda: clock_now, location_buffer_cap=1200)
        iterator = source.ticks().__aiter__()
        await iterator.__anext__()
        await iterator.__anext__()
        assert source.outline_ready is True
        taken = source.take_outline_points()
        assert len(taken) > 0

        # Subsequent polls must NOT refill the buffer...
        await iterator.__anext__()
        await iterator.__anext__()
        assert source.take_outline_points() == ()
        # ...while the marker feed keeps tracking the newest point.
        latest = source.latest_location()
        assert 1 in latest
