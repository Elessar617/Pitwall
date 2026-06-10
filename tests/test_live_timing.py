# ruff: noqa: RUF001
import asyncio
import shutil
from datetime import UTC, datetime
from typing import Any

import pytest
from conftest import notifications
from textual.widgets import DataTable, Static

from pitwall.app import PitwallApp
from pitwall.config import AppConfig
from pitwall.screens.live_timing import (
    build_tower_rows,
    fold_events,
    format_interval,
    format_lap_time,
    format_speed,
)


# Helper gate class for stepping replay
class SleepGate:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.history = []

    async def sleep(self, seconds: float):
        self.history.append(seconds)
        await self.queue.get()
        self.queue.task_done()

    def release(self):
        self.queue.put_nowait(True)


@pytest.fixture
def injected(injected_store):
    """Alias of the conftest-owned store fixture."""
    return injected_store


def test_format_helpers():
    """AC-8 format helper literals."""
    assert format_interval(None) == "—"
    assert format_interval(0.0) == "—"
    assert format_interval(0.506) == "+0.506"
    assert format_interval("+1 LAP") == "+1 LAP"

    assert format_lap_time(None) == "—"
    assert format_lap_time(76.545) == "1:16.545"
    assert format_lap_time(66.068) == "1:06.068"
    assert format_lap_time(45.5) == "45.500"

    assert format_speed(60.0) == "×60"
    assert format_speed(1.5) == "×1.5"


def test_end_state_rows_full_table(excerpt_dir):
    """AC-7 full-table equality via the pure fold/row helpers."""
    from pitwall.openf1.replay import load_session, merge_events

    session = load_session(excerpt_dir)
    events = merge_events(session)

    # Fold all events
    state = fold_events(events)
    rows = build_tower_rows(state, session.drivers, session.stints)

    expected_rows = [
        ("1", "RUS", "—", "—", "1:16.545", "S"),
        ("2", "ANT", "+0.506", "+0.506", "1:16.531", "S"),
        ("3", "VER", "+5.048", "+5.491", "1:16.088", "S"),
        ("4", "HAM", "+0.826", "+6.317", "1:16.068", "S"),
        ("5", "LEC", "+6.480", "+12.792", "1:16.553", "S"),
        ("6", "HAD", "+0.645", "+13.437", "1:16.499", "S"),
        ("7", "COL", "—", "+32.599", "1:17.292", "M"),
        ("8", "LAW", "+4.920", "+37.318", "1:17.801", "M"),
        ("9", "GAS", "+8.545", "+45.310", "1:17.569", "M"),
        ("10", "BEA", "+1.860", "+47.152", "1:18.120", "S"),
        ("11", "SAI", "+12.608", "+59.528", "1:17.544", "M"),
        ("12", "ALO", "+2.315", "+61.828", "1:20.409", "S"),
        ("13", "OCO", "+0.409", "+62.237", "1:38.391", "M"),
        ("14", "NOR", "+2.521", "+64.706", "1:23.114", "M"),
        ("15", "HUL", "+0.364", "+65.070", "1:19.039", "S"),
        ("16", "BOR", "+5.412", "+70.038", "1:17.752", "S"),
        ("17", "PIA", "+13.730", "+1 LAP", "1:17.308", "M"),
        ("18", "PER", "+12.148", "+1 LAP", "1:24.198", "M"),
        ("19", "STR", "+7.365", "+1 LAP", "1:22.036", "S"),
        ("20", "BOT", "+28.684", "+1 LAP", "1:19.225", "M"),
        ("21", "ALB", "—", "—", "—", "S"),
        ("22", "LIN", "—", "—", "—", "M"),
    ]
    assert rows == expected_rows


def test_pure_helpers_edges():
    """Unit edges on synthetic events."""
    # A driver with no position sorts after all positioned drivers by driver_number;
    # two drivers with equal position order by driver_number;
    # events for a driver number absent from drivers produce no row;
    # the fold returns new state objects (input state unmutated).
    from pitwall.openf1.models import SessionDriver
    from pitwall.openf1.replay import ReplayEvent

    drivers = [
        SessionDriver(driver_number=1, name_acronym="NOR", full_name="Lando Norris", team_name="McLaren"),
        SessionDriver(driver_number=2, name_acronym="SAR", full_name="Logan Sargeant", team_name="Williams"),
        SessionDriver(driver_number=3, name_acronym="RIC", full_name="Daniel Ricciardo", team_name="RB"),
    ]

    class DummyPayload:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    # 1. the fold returns new state objects (input state unmutated).
    state0 = fold_events([])
    ev1 = ReplayEvent(
        ts=datetime(2026, 6, 10, tzinfo=UTC), kind="position", payload=DummyPayload(driver_number=1, position=2)
    )
    state1 = fold_events([ev1], state0)
    assert state0[0] == {}
    assert state1[0] == {1: 2}

    # 2. events for a driver number absent from drivers produce no row.
    ev2 = ReplayEvent(
        ts=datetime(2026, 6, 10, tzinfo=UTC), kind="position", payload=DummyPayload(driver_number=99, position=1)
    )
    state2 = fold_events([ev2], state1)
    rows2 = build_tower_rows(state2, drivers, [])
    assert len(rows2) == 3
    acronyms = [r[1] for r in rows2]
    assert "NOR" in acronyms
    assert "SAR" in acronyms
    assert "RIC" in acronyms

    # 3. A driver with no position sorts after all positioned drivers by driver_number.
    state3 = fold_events([], state1)
    rows3 = build_tower_rows(state3, drivers, [])
    assert rows3[0][1] == "NOR"
    assert rows3[1][1] == "SAR"
    assert rows3[2][1] == "RIC"

    # 4. two drivers with equal position order by driver_number.
    ev_equal = [
        ReplayEvent(
            ts=datetime(2026, 6, 10, tzinfo=UTC), kind="position", payload=DummyPayload(driver_number=1, position=2)
        ),
        ReplayEvent(
            ts=datetime(2026, 6, 10, tzinfo=UTC), kind="position", payload=DummyPayload(driver_number=2, position=2)
        ),
        ReplayEvent(
            ts=datetime(2026, 6, 10, tzinfo=UTC), kind="position", payload=DummyPayload(driver_number=3, position=1)
        ),
    ]
    state4 = fold_events(ev_equal)
    rows4 = build_tower_rows(state4, drivers, [])
    assert rows4[0][1] == "RIC"
    assert rows4[1][1] == "NOR"
    assert rows4[2][1] == "SAR"


@pytest.mark.asyncio
async def test_replay_states_stepped(injected, excerpt_dir):
    """AC-9 gate-stepped screen states."""
    _conn, _client, store, _requests = injected
    gate = SleepGate()
    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=str(excerpt_dir), replay_speed=60.0),
        store=store,
        replay_sleep=gate.sleep,
    )

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            # Await initial season load
            await app.workers.wait_for_complete()
            await pilot.pause()

            # Press 'l' to mount LiveTimingScreen
            await pilot.press("l")
            await pilot.pause()

            # Poll until worker reaches the first sleep (gate.history has 1 item)
            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach first sleep gate")  # noqa: TRY003

            # 1. Loading state (gate closed)
            status_widget: Any = app.screen.query_one("#live-status", Static)
            assert str(status_widget.content) == "Loading replay…"
            table_widget = app.screen.query_one("#live-table", DataTable)
            assert table_widget.display is False

            # 2. Release tick 0 (catch-up tick)
            gate.release()

            # Poll until worker reaches second sleep (gate.history has 2 items)
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach second sleep gate")  # noqa: TRY003

            assert str(status_widget.content) == "Replay ×60 · 20:30:00 UTC"
            assert table_widget.display is True
            assert table_widget.row_count == 22

            # Check column labels (AC-9)
            labels = [str(col.label) for col in table_widget.columns.values()]
            assert labels == ["Pos", "Drv", "Int", "Gap", "Last", "Tyre"]

            # Check row 0 and row 21
            row0 = [str(c) for c in table_widget.get_row_at(0)]
            row21 = [str(c) for c in table_widget.get_row_at(21)]
            assert row0 == ["1", "RUS", "—", "—", "—", "S"]
            assert row21 == ["22", "LIN", "—", "—", "—", "M"]

            # 3. Release the remaining 5 sleeps to finish the replay
            for _ in range(5):
                gate.release()

            # Wait for the exclusive worker to finish
            await app.workers.wait_for_complete()
            await app.screen.workers.wait_for_complete()
            await pilot.pause()

            # Status is finished
            assert str(status_widget.content) == "Replay finished · 20:32:30 UTC"

            # Assert full-table equality with AC-7 expected rows
            expected_rows = [
                ("1", "RUS", "—", "—", "1:16.545", "S"),
                ("2", "ANT", "+0.506", "+0.506", "1:16.531", "S"),
                ("3", "VER", "+5.048", "+5.491", "1:16.088", "S"),
                ("4", "HAM", "+0.826", "+6.317", "1:16.068", "S"),
                ("5", "LEC", "+6.480", "+12.792", "1:16.553", "S"),
                ("6", "HAD", "+0.645", "+13.437", "1:16.499", "S"),
                ("7", "COL", "—", "+32.599", "1:17.292", "M"),
                ("8", "LAW", "+4.920", "+37.318", "1:17.801", "M"),
                ("9", "GAS", "+8.545", "+45.310", "1:17.569", "M"),
                ("10", "BEA", "+1.860", "+47.152", "1:18.120", "S"),
                ("11", "SAI", "+12.608", "+59.528", "1:17.544", "M"),
                ("12", "ALO", "+2.315", "+61.828", "1:20.409", "S"),
                ("13", "OCO", "+0.409", "+62.237", "1:38.391", "M"),
                ("14", "NOR", "+2.521", "+64.706", "1:23.114", "M"),
                ("15", "HUL", "+0.364", "+65.070", "1:19.039", "S"),
                ("16", "BOR", "+5.412", "+70.038", "1:17.752", "S"),
                ("17", "PIA", "+13.730", "+1 LAP", "1:17.308", "M"),
                ("18", "PER", "+12.148", "+1 LAP", "1:24.198", "M"),
                ("19", "STR", "+7.365", "+1 LAP", "1:22.036", "S"),
                ("20", "BOT", "+28.684", "+1 LAP", "1:19.225", "M"),
                ("21", "ALB", "—", "—", "—", "S"),
                ("22", "LIN", "—", "—", "—", "M"),
            ]
            actual_rows = [[str(c) for c in table_widget.get_row_at(i)] for i in range(22)]
            assert actual_rows == [list(r) for r in expected_rows]
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_no_session_state(injected):
    """AC-10(a) replay_dir=None."""
    _conn, _client, store, _requests = injected
    sleep_calls: list[float] = []

    async def recording_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=None),
        store=store,
        replay_sleep=recording_sleep,
    )
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.press("l")
        await pilot.pause()

        status_widget = app.screen.query_one("#live-status", Static)
        assert str(status_widget.content) == "No live session — start pitwall with --live or --replay <fixtures-dir>."
        table_widget = app.screen.query_one("#live-table", DataTable)
        assert table_widget.display is False
        map_widget = app.screen.query_one("#live-map", Static)
        assert map_widget.display is False

        # AC-9f: press v in no-replay state -> no-op: status text unchanged, view stays all
        assert getattr(app.screen, "view_index") == 0  # noqa: B009
        await pilot.press("v")
        await pilot.pause()
        assert str(status_widget.content) == "No live session — start pitwall with --live or --replay <fixtures-dir>."
        assert getattr(app.screen, "view_index") == 0  # noqa: B009

        # No live-replay worker ran: no worker carries the group, and the
        # injected sleep recorder never fired (public-API proof, no patching).
        await app.workers.wait_for_complete()
        assert not [w for w in app.workers if w.group == "live-replay"]
        assert sleep_calls == []


@pytest.mark.asyncio
async def test_load_error_state(injected, tmp_path):
    """AC-10(b) invalid drivers.json."""
    _conn, _client, store, _requests = injected

    with open(tmp_path / "drivers.json", "w", encoding="utf-8") as f:
        f.write("invalid json")
    for filename in ["laps.json", "intervals.json", "position.json", "stints.json", "pit.json", "race_control.json"]:
        with open(tmp_path / filename, "w", encoding="utf-8") as f:
            f.write("[]")

    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=str(tmp_path)),
        store=store,
    )
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.press("l")
        await app.screen.workers.wait_for_complete()
        await pilot.pause()

        status_widget: Any = app.screen.query_one("#live-status", Static)
        assert str(status_widget.content) == "Replay unavailable — failed to load replay data."
        table_widget = app.screen.query_one("#live-table", DataTable)
        assert table_widget.display is False
        map_widget = app.screen.query_one("#live-map", Static)
        assert map_widget.display is False

        # Exactly one error notification
        errors = [n.message for n in notifications(app) if n.severity == "error"]
        assert len(errors) == 1


@pytest.mark.asyncio
async def test_no_events_state(injected, excerpt_dir, tmp_path):
    """AC-10(c) empty stream arrays."""
    _conn, _client, store, _requests = injected
    shutil.copy(excerpt_dir / "drivers.json", tmp_path / "drivers.json")
    shutil.copy(excerpt_dir / "stints.json", tmp_path / "stints.json")
    for filename in ["laps.json", "intervals.json", "position.json", "pit.json", "race_control.json"]:
        with open(tmp_path / filename, "w", encoding="utf-8") as f:
            f.write("[]")

    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=str(tmp_path)),
        store=store,
    )
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.press("l")
        await app.screen.workers.wait_for_complete()
        await pilot.pause()

        status_widget: Any = app.screen.query_one("#live-status", Static)
        assert str(status_widget.content) == "Replay unavailable — replay data contains no events."
        table_widget = app.screen.query_one("#live-table", DataTable)
        assert table_widget.display is False
        map_widget = app.screen.query_one("#live-map", Static)
        assert map_widget.display is False


@pytest.mark.asyncio
async def test_chassis_isolation_and_quit(injected, excerpt_dir):
    """AC-12 nav, subtitle, Jolpica recorder requests, q mid-replay clean exit."""
    _conn, client, store, requests = injected
    gate = SleepGate()
    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=str(excerpt_dir), replay_speed=60.0),
        store=store,
        replay_sleep=gate.sleep,
    )

    try:
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            # Season load requests == 3
            assert len(requests) == 3

            # Footer Live label
            assert any(b.key == "l" and b.description == "Live" for b in app.BINDINGS)

            # Activates LiveTimingScreen
            await pilot.press("l")
            await pilot.pause()
            live_screen = app.screen
            assert live_screen.__class__.__name__ == "LiveTimingScreen"

            # Re-press no-op
            await pilot.press("l")
            await pilot.pause()
            assert app.screen is live_screen

            status_widget: Any = live_screen.query_one("#live-status", Static)
            assert str(status_widget.content) == "Loading replay…"

            # Wait until worker reaches first sleep
            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach first sleep gate")  # noqa: TRY003

            # Release tick 0
            gate.release()

            # Wait until worker reaches second sleep
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach second sleep gate")  # noqa: TRY003

            assert str(status_widget.content) == "Replay ×60 · 20:30:00 UTC"

            # Wander s -> l preserves state
            await pilot.press("s")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "ScheduleScreen"

            await pilot.press("l")
            await pilot.pause()
            assert app.screen is live_screen
            assert str(status_widget.content) == "Replay ×60 · 20:30:00 UTC"

            # Subtitle still season 2026 · data as of 14:30 UTC
            assert app.sub_title == "season 2026 · data as of 14:30 UTC"

            # Jolpica requests still 3
            assert len(requests) == 3

            # Rotation intact (n, r, p, s)
            for key, name in [
                ("n", "StandingsScreen"),
                ("r", "ResultsScreen"),
                ("p", "ProfilesScreen"),
                ("s", "ScheduleScreen"),
            ]:
                await pilot.press(key)
                await pilot.pause()
                assert app.screen.__class__.__name__ == name

            # Switch back to live
            await pilot.press("l")
            await pilot.pause()

            # Press q mid-replay (with sleep gate closed/waiting)
            await pilot.press("q")
    finally:
        for _ in range(10):
            gate.release()

    # Outside block is clean exit
    await client.aclose()


@pytest.mark.asyncio
async def test_map_render_stepped(injected, excerpt_dir):  # noqa: C901
    """AC-9 split layout (gate-stepped)."""
    _conn, _client, store, _requests = injected
    gate = SleepGate()
    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=str(excerpt_dir), replay_speed=60.0),
        store=store,
        replay_sleep=gate.sleep,
    )

    expected_grid = [
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠙⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡄⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢧⠹⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⢳⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⢳⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠈⢧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠈⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠃⠀⠀⠀⠀⠸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡸⠀⠀⠀⠀⠀⠀⢳⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠇⠀⠀⠀⠀⠀⠀⠘⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠚⠁⠀⠀⠀⠀⠀⠀⠀⠀⢣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠡⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠓⠒⠲⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣹⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢳⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠢⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢦⠀⠀⠀⠀⠀⠀⠀⠀⢸⡃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⢸⢁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠳⣄⠀⠀⠀⠀⠀⠀⢸⠈⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠳⢄⡀⠀⠀⠀⠸⣄⡢⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠒⠤⢄⣀⣀⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    ]

    cells_t0 = {
        (0, 22): 11,
        (1, 24): 23,
        (2, 23): 63,
        (3, 23): 12,
        (7, 22): 81,
        (8, 22): 3,
        (8, 29): 27,
        (9, 22): 44,
        (13, 17): 16,
        (13, 32): 31,
        (14, 17): 6,
        (14, 32): 55,
        (21, 20): 18,
        (21, 34): 41,
        (23, 35): 77,
        (25, 36): 1,
        (27, 36): 87,
        (28, 36): 10,
        (29, 28): 43,
        (31, 33): 30,
    }
    styles_t0 = {
        1: "#F47600",
        3: "#4781D7",
        6: "#4781D7",
        10: "#00A1E8",
        11: "#909090",
        12: "#00D7B6",
        16: "#ED1131",
        18: "#229971",
        23: "#1868DB",
        27: "#F50537",
        30: "#6C98FF",
        31: "#9C9FA2",
        41: "#6C98FF",
        43: "#00A1E8",
        44: "#ED1131",
        55: "#1868DB",
        63: "#00D7B6",
        77: "#909090",
        81: "#F47600",
        87: "#9C9FA2",
    }

    cells_end = {
        (0, 22): 5,
        (0, 23): 1,
        (0, 24): 27,
        (1, 24): 23,
        (5, 23): 63,
        (6, 23): 12,
        (7, 28): 55,
        (10, 19): 44,
        (10, 20): 3,
        (12, 18): 81,
        (15, 32): 77,
        (16, 17): 31,
        (18, 17): 16,
        (19, 17): 6,
        (20, 33): 87,
        (21, 34): 41,
        (22, 34): 10,
        (27, 26): 11,
        (30, 30): 18,
        (30, 38): 30,
        (31, 34): 43,
    }
    styles_end = {
        1: "#F47600",
        3: "#4781D7",
        5: "#F50537",
        6: "#4781D7",
        10: "#00A1E8",
        11: "#909090",
        12: "#00D7B6",
        16: "#ED1131",
        18: "#229971",
        23: "#1868DB",
        27: "#F50537",
        30: "#6C98FF",
        31: "#9C9FA2",
        41: "#6C98FF",
        43: "#00A1E8",
        44: "#ED1131",
        55: "#1868DB",
        63: "#00D7B6",
        77: "#909090",
        81: "#F47600",
        87: "#9C9FA2",
    }

    def embed_markers(base_grid, cells_map):
        grid_copy = [list(row) for row in base_grid]
        for r, c in cells_map:
            grid_copy[r][c] = "●"
        return "\n".join("".join(row) for row in grid_copy)

    def assert_spans(text_obj, cells_map, styles_map):
        plain_text = text_obj.plain
        for (r, c), drv in cells_map.items():
            offset = r * 57 + c
            assert plain_text[offset] == "●"
            found = False
            for span in text_obj.spans:
                if span.start <= offset < span.end:
                    expected = styles_map[drv]
                    assert expected in str(span.style) or str(span.style) == expected
                    found = True
                    break
            assert found, f"No span for marker at ({r}, {c})"

    try:
        # Run at size=(120, 40) for split rendering (terminal width >= 100)
        async with app.run_test(size=(120, 40)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("l")
            await pilot.pause()

            # Poll until worker reaches first sleep
            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach first sleep gate")  # noqa: TRY003

            # 1. Loading state (gate closed)
            status_widget: Any = app.screen.query_one("#live-status", Static)
            assert str(status_widget.content) == "Loading replay…"
            table_widget = app.screen.query_one("#live-table", DataTable)
            map_widget = app.screen.query_one("#live-map", Static)
            assert table_widget.display is False
            assert map_widget.display is False
            assert map_widget.border_subtitle == ""  # absent in loading state

            # 2. Release tick 0 (catch-up tick)
            gate.release()

            # Poll until worker reaches second sleep
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach second sleep gate")  # noqa: TRY003

            assert str(status_widget.content) == "Replay ×60 · 20:30:00 UTC"
            assert table_widget.display is True
            assert map_widget.display is True

            # Verify map content string
            expected_str_tick0 = embed_markers(expected_grid, cells_t0)
            assert str(map_widget.content) == expected_str_tick0
            # Verify styled spans for markers
            assert_spans(map_widget.content, cells_t0, styles_t0)

            # Verify dimensions and caption
            assert map_widget.region.width == 58
            assert map_widget.region.height == 34
            assert table_widget.region.width == 48
            assert map_widget.border_subtitle == "Montreal · 20:30:00 UTC"

            # 3. Release the remaining 5 sleeps to finish the replay
            for _ in range(5):
                gate.release()

            await app.workers.wait_for_complete()
            await app.screen.workers.wait_for_complete()
            await pilot.pause()

            assert str(status_widget.content) == "Replay finished · 20:32:30 UTC"
            assert map_widget.display is True
            assert map_widget.border_subtitle == "Montreal · 20:32:30 UTC"

            # Verify final map content string
            expected_str_final = embed_markers(expected_grid, cells_end)
            assert str(map_widget.content) == expected_str_final
            # Verify styled spans for markers
            assert_spans(map_widget.content, cells_end, styles_end)

            # Verify end-state rows in the table
            assert table_widget.row_count == 22
    finally:
        for _ in range(10):
            gate.release()

    # Now verify the tower-only mode under size=(80, 24)
    gate.history.clear()
    gate.queue = asyncio.Queue()
    app_tower = PitwallApp(
        config=AppConfig(season=2026, replay_dir=excerpt_dir),
        store=store,
        replay_sleep=gate.sleep,
    )
    try:
        async with app_tower.run_test(size=(80, 24)) as pilot:
            await app_tower.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("l")
            await pilot.pause()

            # Poll until worker reaches first sleep
            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach first sleep gate")  # noqa: TRY003 - test gate-loop guard

            # Release tick 0
            gate.release()

            # Poll until worker reaches second sleep
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach second sleep gate")  # noqa: TRY003 - test gate-loop guard

            status_widget = app_tower.screen.query_one("#live-status", Static)
            table_widget = app_tower.screen.query_one("#live-table", DataTable)
            map_widget = app_tower.screen.query_one("#live-map", Static)

            assert str(status_widget.content) == "Replay ×60 · 20:30:00 UTC"
            assert table_widget.display is True
            assert map_widget.display is False  # hidden because width 80 < 100
            assert table_widget.has_class("tower-only") is True
            assert table_widget.region.width == 80
            assert map_widget.border_subtitle == ""  # absent when map hidden
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_map_single_driver_fallback(injected, excerpt_dir, tmp_path):
    """Fallback path reproduces the old single-driver literals when location_all.json is absent."""
    _conn, _client, store, _requests = injected
    gate = SleepGate()

    # Copy all excerpt files except location_all.json
    for p in excerpt_dir.iterdir():
        if p.is_file() and p.name != "location_all.json":
            import shutil

            shutil.copy(p, tmp_path / p.name)

    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=str(tmp_path), replay_speed=60.0),
        store=store,
        replay_sleep=gate.sleep,
    )

    old_expected_grid = [
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠙⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡄⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢃⠸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠓⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⢠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⢁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠈⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠃⠀⠀⠀⠀⠈⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡼⠀⠀⠀⠀⠀⠀⢃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠇⠀⠀⠀⠀⠀⠀⠐⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡴⠒⠁⠀⠀⠀⠀⠀⠀⠀⠀⠣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢨⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢨⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢘⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠓⠒⠲⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⡅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡱⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠢⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢦⠀⠀⠀⠀⠀⠀⠀⠀⢐⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠰⢡⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⣀⠀⠀⠀⠀⠀⠀⢸⠐⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠲⢄⡀⠀⠀⠀⠸⣄⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠒⠤⢄⣀⣀⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    ]

    try:
        async with app.run_test(size=(120, 40)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("l")
            await pilot.pause()

            # Poll until worker reaches first sleep
            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach first sleep gate")  # noqa: TRY003

            map_widget = app.screen.query_one("#live-map", Static)

            # Release tick 0
            gate.release()

            # Poll until worker reaches second sleep
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach second sleep gate")  # noqa: TRY003

            # Verify tick 0 single-driver marker at cell (25, 36)
            grid_tick0 = list(old_expected_grid)
            row_25 = grid_tick0[25]
            grid_tick0[25] = row_25[:36] + "●" + row_25[37:]
            expected_str_tick0 = "\n".join(grid_tick0)
            assert str(map_widget.content) == expected_str_tick0
            assert map_widget.border_subtitle == "Montreal · 20:30:00 UTC"

            # Release the remaining 5 sleeps to finish the replay
            for _ in range(5):
                gate.release()

            await app.workers.wait_for_complete()
            await app.screen.workers.wait_for_complete()
            await pilot.pause()

            # Verify final map content at cell (0, 24)
            grid_final = list(old_expected_grid)
            row_0 = grid_final[0]
            grid_final[0] = row_0[:24] + "●" + row_0[25:]
            expected_str_final = "\n".join(grid_final)
            assert str(map_widget.content) == expected_str_final
            assert map_widget.border_subtitle == "Montreal · 20:32:30 UTC"
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_tower_only_no_location(injected, excerpt_dir, tmp_path):
    """AC-10(a) tower-only back-compat (no location.json)."""
    _conn, _client, store, _requests = injected
    gate = SleepGate()

    for p in excerpt_dir.iterdir():
        if p.is_file() and p.name not in ("location.json", "location_all.json"):
            shutil.copy(p, tmp_path / p.name)

    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=str(tmp_path), replay_speed=60.0),
        store=store,
        replay_sleep=gate.sleep,
    )
    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.press("l")
            await pilot.pause()

            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach first sleep")  # noqa: TRY003

            status_widget = app.screen.query_one("#live-status", Static)
            table_widget = app.screen.query_one("#live-table", DataTable)
            map_widget = app.screen.query_one("#live-map", Static)

            assert table_widget.display is False
            assert map_widget.display is False

            gate.release()

            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()

            assert str(status_widget.content) == "Replay ×60 · 20:30:00 UTC"
            assert table_widget.display is True
            assert map_widget.display is False
            assert table_widget.region.width == 80

            for _ in range(5):
                gate.release()

            await app.workers.wait_for_complete()
            await app.screen.workers.wait_for_complete()
            await pilot.pause()

            assert str(status_widget.content) == "Replay finished · 20:32:30 UTC"
            assert map_widget.display is False
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_corrupt_location_error(injected, excerpt_dir, tmp_path):
    """AC-10(b) invalid location.json."""
    _conn, _client, store, _requests = injected

    for p in excerpt_dir.iterdir():
        if p.is_file():
            shutil.copy(p, tmp_path / p.name)
    with open(tmp_path / "location_all.json", "w", encoding="utf-8") as f:
        f.write("{invalid json")

    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=str(tmp_path)),
        store=store,
    )
    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.press("l")
        await app.screen.workers.wait_for_complete()
        await pilot.pause()

        status_widget = app.screen.query_one("#live-status", Static)
        assert str(status_widget.content) == "Replay unavailable — failed to load replay data."
        table_widget = app.screen.query_one("#live-table", DataTable)
        map_widget = app.screen.query_one("#live-map", Static)
        assert table_widget.display is False
        assert map_widget.display is False

        # Exactly one error notification
        errors = [n.message for n in notifications(app) if n.severity == "error"]
        assert len(errors) == 1


@pytest.mark.asyncio
async def test_empty_location_tower_only(injected, excerpt_dir, tmp_path):
    """AC-10(c) empty [] location.json -> tower-only."""
    _conn, _client, store, _requests = injected
    gate = SleepGate()

    for p in excerpt_dir.iterdir():
        if p.is_file():
            shutil.copy(p, tmp_path / p.name)
    with open(tmp_path / "location.json", "w", encoding="utf-8") as f:
        f.write("[]")
    with open(tmp_path / "location_all.json", "w", encoding="utf-8") as f:
        f.write("[]")

    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=str(tmp_path), replay_speed=60.0),
        store=store,
        replay_sleep=gate.sleep,
    )
    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.press("l")
            await pilot.pause()

            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach first sleep")  # noqa: TRY003

            status_widget = app.screen.query_one("#live-status", Static)
            table_widget = app.screen.query_one("#live-table", DataTable)
            map_widget = app.screen.query_one("#live-map", Static)

            assert table_widget.display is False
            assert map_widget.display is False

            gate.release()

            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()

            assert str(status_widget.content) == "Replay ×60 · 20:30:00 UTC"
            assert table_widget.display is True
            assert map_widget.display is False
            assert table_widget.region.width == 80

            for _ in range(5):
                gate.release()

            await app.workers.wait_for_complete()
            await app.screen.workers.wait_for_complete()
            await pilot.pause()

            assert str(status_widget.content) == "Replay finished · 20:32:30 UTC"
            assert map_widget.display is False

            errors = [n.message for n in notifications(app) if n.severity == "error"]
            assert len(errors) == 0
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_tower_colours_stepped(injected, excerpt_dir):
    """AC-8 coloured tower asserts for view all at tick 0 and end state."""
    _conn, _client, store, _requests = injected
    gate = SleepGate()
    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=str(excerpt_dir), replay_speed=60.0),
        store=store,
        replay_sleep=gate.sleep,
    )
    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            await pilot.press("l")
            await pilot.pause()

            # Poll until worker reaches first sleep
            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()

            # Release tick 0
            gate.release()

            # Poll until worker reaches second sleep
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()

            table_widget = app.screen.query_one("#live-table", DataTable)

            # Check row 0 and 21 Drv styles at tick 0
            row0_drv = table_widget.get_row_at(0)[1]
            row21_drv = table_widget.get_row_at(21)[1]
            assert str(row0_drv.style) == "#00D7B6"
            assert str(row21_drv.style) == "#6C98FF"

            # Check all 22 styles at tick 0
            expected_styles_t0 = [
                "#00D7B6",
                "#00D7B6",
                "#4781D7",
                "#ED1131",
                "#ED1131",
                "#4781D7",
                "#00A1E8",
                "#6C98FF",
                "#00A1E8",
                "#9C9FA2",
                "#F47600",
                "#1868DB",
                "#229971",
                "#9C9FA2",
                "#F50537",
                "#F50537",
                "#909090",
                "#F47600",
                "#229971",
                "#909090",
                "#1868DB",
                "#6C98FF",
            ]
            actual_styles_t0 = [str(table_widget.get_row_at(i)[1].style) for i in range(22)]
            assert actual_styles_t0 == expected_styles_t0

            # Release the remaining 5 sleeps to finish the replay
            for _ in range(5):
                gate.release()

            await app.workers.wait_for_complete()
            await app.screen.workers.wait_for_complete()
            await pilot.pause()

            # Check all 22 styles at end state
            expected_styles_end = [
                "#00D7B6",
                "#00D7B6",
                "#4781D7",
                "#ED1131",
                "#ED1131",
                "#4781D7",
                "#00A1E8",
                "#6C98FF",
                "#00A1E8",
                "#9C9FA2",
                "#1868DB",
                "#229971",
                "#9C9FA2",
                "#F47600",
                "#F50537",
                "#F50537",
                "#F47600",
                "#909090",
                "#229971",
                "#909090",
                "#1868DB",
                "#6C98FF",
            ]
            actual_styles_end = [str(table_widget.get_row_at(i)[1].style) for i in range(22)]
            assert actual_styles_end == expected_styles_end
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_view_cycling_ux(injected, excerpt_dir):
    """AC-9 View cycling UX (a)-(h) and chassis isolation."""
    _conn, _client, store, requests = injected
    gate = SleepGate()
    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=str(excerpt_dir), replay_speed=60.0),
        store=store,
        replay_sleep=gate.sleep,
    )
    try:
        async with app.run_test(size=(120, 40)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            # (h) Binding surface: LiveTimingScreen.BINDINGS check
            from pitwall.screens.live_timing import LiveTimingScreen

            binding_v = next((b for b in LiveTimingScreen.BINDINGS if b.key == "v"), None)
            assert binding_v is not None
            assert binding_v.action == "cycle_view"
            assert binding_v.description == "View"

            await pilot.press("l")
            await pilot.pause()

            # Poll until worker reaches first sleep (loading state)
            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach first sleep gate")  # noqa: TRY003

            status_widget = app.screen.query_one("#live-status", Static)
            table_widget = app.screen.query_one("#live-table", DataTable)
            map_widget = app.screen.query_one("#live-map", Static)

            assert str(status_widget.content) == "Loading replay…"
            assert table_widget.display is False

            # (f) Pressing v while table is hidden (loading state) -> no-op
            await pilot.press("v")
            await pilot.pause()
            assert str(status_widget.content) == "Loading replay…"

            # Release tick 0
            gate.release()

            # Poll until worker reaches second sleep
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach second sleep gate")  # noqa: TRY003

            assert str(status_widget.content) == "Replay ×60 · 20:30:00 UTC"
            assert table_widget.display is True
            assert map_widget.display is True
            initial_gate_count = len(gate.history)

            # (a) press v -> lead fight
            await pilot.press("v")
            await pilot.pause()
            assert str(status_widget.content) == "Replay ×60 · 20:30:00 UTC · view: lead fight"
            assert table_widget.row_count == 5

            expected_acronyms_lead = ["RUS", "ANT", "VER", "HAM", "LEC"]
            expected_styles_lead = ["#00D7B6", "#00D7B6", "#4781D7", "#ED1131", "#ED1131"]
            actual_acronyms_lead = [str(table_widget.get_row_at(i)[1]) for i in range(5)]
            actual_styles_lead = [str(table_widget.get_row_at(i)[1].style) for i in range(5)]
            assert actual_acronyms_lead == expected_acronyms_lead
            assert actual_styles_lead == expected_styles_lead

            # Map shows only admitted drivers' markers
            # Locate all ● in the map_widget content and assert equality with the derived lead-view cells
            plain_map = map_widget.content.plain
            actual_marker_cells = set()
            for idx, char in enumerate(plain_map):
                if char == "●":
                    row = idx // 57
                    col = idx % 57
                    actual_marker_cells.add((row, col))
            assert actual_marker_cells == {(2, 23), (3, 23), (8, 22), (9, 22), (13, 17)}

            # Sleep gate acquired zero additional times (still same history length)
            assert len(gate.history) == initial_gate_count

            # (b) v again -> podium fight
            await pilot.press("v")
            await pilot.pause()
            assert str(status_widget.content) == "Replay ×60 · 20:30:00 UTC · view: podium fight"
            assert table_widget.row_count == 4
            expected_acronyms_podium = ["RUS", "ANT", "VER", "HAM"]
            actual_acronyms_podium = [str(table_widget.get_row_at(i)[1]) for i in range(4)]
            assert actual_acronyms_podium == expected_acronyms_podium

            # (c) v again -> points fight
            await pilot.press("v")
            await pilot.pause()
            assert str(status_widget.content) == "Replay ×60 · 20:30:00 UTC · view: points fight"
            assert table_widget.row_count == 5
            expected_acronyms_points = ["LAW", "GAS", "BEA", "NOR", "SAI"]
            actual_acronyms_points = [str(table_widget.get_row_at(i)[1]) for i in range(5)]
            assert actual_acronyms_points == expected_acronyms_points
            # NOR style is present
            nor_drv = table_widget.get_row_at(3)[1]
            assert str(nor_drv.style) == "#F47600"

            # (d) v again -> wraps to all
            await pilot.press("v")
            await pilot.pause()
            assert str(status_widget.content) == "Replay ×60 · 20:30:00 UTC"
            assert table_widget.row_count == 22

            # Set view to lead fight before advancing
            await pilot.press("v")
            await pilot.pause()
            assert str(status_widget.content) == "Replay ×60 · 20:30:00 UTC · view: lead fight"

            # (e) Release remaining steps with lead view active
            for _ in range(5):
                gate.release()

            await app.workers.wait_for_complete()
            await app.screen.workers.wait_for_complete()
            await pilot.pause()

            assert str(status_widget.content) == "Replay finished · 20:32:30 UTC · view: lead fight"
            assert table_widget.row_count == 5
            expected_acronyms_end_lead = ["RUS", "ANT", "VER", "HAM", "LEC"]
            expected_styles_end_lead = ["#00D7B6", "#00D7B6", "#4781D7", "#ED1131", "#ED1131"]
            actual_acronyms_end_lead = [str(table_widget.get_row_at(i)[1]) for i in range(5)]
            actual_styles_end_lead = [str(table_widget.get_row_at(i)[1].style) for i in range(5)]
            assert actual_acronyms_end_lead == expected_acronyms_end_lead
            assert actual_styles_end_lead == expected_styles_end_lead

            # Pressing v after finish still cycles
            await pilot.press("v")
            await pilot.pause()
            assert str(status_widget.content) == "Replay finished · 20:32:30 UTC · view: podium fight"
            assert table_widget.row_count == 4

            # (g) View persists across navigation
            # Set to lead fight
            await pilot.press("v")  # podium -> points
            await pilot.pause()
            await pilot.press("v")  # points -> all
            await pilot.pause()
            await pilot.press("v")  # all -> lead fight
            await pilot.pause()
            assert str(status_widget.content) == "Replay finished · 20:32:30 UTC · view: lead fight"

            # Press 's' (Schedule) then 'l' (Live)
            await pilot.press("s")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "ScheduleScreen"

            await pilot.press("l")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "LiveTimingScreen"
            assert str(status_widget.content) == "Replay finished · 20:32:30 UTC · view: lead fight"
            assert table_widget.row_count == 5

            # (d) Chassis isolation checks
            assert app.sub_title == "season 2026 · data as of 14:30 UTC"
            assert len(requests) == 3
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_post_replay_isolation(injected, excerpt_dir):
    """AC-11a post-replay chassis isolation (subtitle + exactly 3 requests after finished)."""
    _conn, _client, store, requests = injected
    gate = SleepGate()
    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=str(excerpt_dir), replay_speed=60.0),
        store=store,
        replay_sleep=gate.sleep,
    )
    try:
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("l")
            await pilot.pause()

            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()

            for _ in range(6):
                gate.release()

            await app.workers.wait_for_complete()
            await app.screen.workers.wait_for_complete()
            await pilot.pause()

            status_widget = app.screen.query_one("#live-status", Static)
            assert str(status_widget.content) == "Replay finished · 20:32:30 UTC"

            assert app.sub_title == "season 2026 · data as of 14:30 UTC"
            assert len(requests) == 3
    finally:
        for _ in range(10):
            gate.release()


async def test_map_panel_border_and_title(injected, excerpt_dir):
    """AC-6: the map pane is a centered, round-bordered panel titled 'Track';
    the border/title are chrome — the braille content carries no border glyphs."""
    _conn, _client, store, _requests = injected
    gate = SleepGate()
    app = PitwallApp(
        config=AppConfig(season=2026, replay_dir=str(excerpt_dir), replay_speed=60.0),
        store=store,
        replay_sleep=gate.sleep,
    )
    async with app.run_test(size=(120, 40)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("l")
        await pilot.pause()
        for _ in range(100):
            if len(gate.history) >= 1:
                break
            await pilot.pause()
        else:
            raise AssertionError("worker did not reach first sleep gate")  # noqa: TRY003 - test gate-loop guard
        gate.release()
        for _ in range(100):
            if len(gate.history) >= 2:
                break
            await pilot.pause()
        else:
            raise AssertionError("worker did not reach second sleep gate")  # noqa: TRY003 - test gate-loop guard
        await pilot.pause()

        map_widget = app.screen.query_one("#live-map", Static)
        assert map_widget.display is True
        # Title is widget chrome (border_title), not part of the content.
        assert map_widget.border_title == "Track"
        # The round border is declared in CSS; the content string is the pure
        # braille grid with no border glyphs (R5).
        styles = map_widget.styles
        assert styles.border_top[0] == "round"
        assert styles.align_horizontal == "center"
        assert styles.align_vertical == "middle"
        content = map_widget.content
        plain = str(content.plain) if hasattr(content, "plain") else str(content)
        assert "╭" not in plain and "│" not in plain and "╰" not in plain
        assert "Track" not in plain
