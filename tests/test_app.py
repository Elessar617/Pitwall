"""App-shell tests via Textual's run_test harness (SPEC-02 AC-6, 7, 9, 10, 11, 12)."""

import datetime
import sqlite3

import httpx
import pytest
from conftest import notifications
from textual.widgets import Footer, Header

from pitwall.api.jolpica import JolpicaClient
from pitwall.app import PitwallApp
from pitwall.cache.db import select_races
from pitwall.cache.store import SeasonStore
from pitwall.config import AppConfig
from pitwall.screens import (
    LiveTimingScreen,
    ProfilesScreen,
    ResultsScreen,
    ScheduleScreen,
    StandingsScreen,
    StrategyScreen,
)

SEASON = 2026
FIXED_NOW = datetime.datetime(2026, 6, 9, 14, 30, tzinfo=datetime.UTC)


@pytest.fixture
def injected(injected_store):
    """Alias of the conftest-owned store fixture (SPEC-03 AC-3 consolidation)."""
    return injected_store


def notification_messages(app):
    """Severity/message pairs from the app's notification store."""
    return [(n.severity, n.message) for n in notifications(app)]


async def test_chassis_mounts(injected):
    _conn, client, store, _requests = injected
    app = PitwallApp(config=AppConfig(season=SEASON), store=store)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.screen.query_one(Header)
        assert app.screen.query_one(Footer)
        assert isinstance(app.screen, ScheduleScreen)
        bound_keys = {binding.key for binding in app.BINDINGS}
        assert {"s", "n", "r", "p", "q", "l"} <= bound_keys
    await client.aclose()


async def test_navigation_bindings(injected):
    _conn, client, store, _requests = injected
    app = PitwallApp(config=AppConfig(season=SEASON), store=store)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        for key, screen_type in (
            ("n", StandingsScreen),
            ("r", ResultsScreen),
            ("p", ProfilesScreen),
            ("s", ScheduleScreen),
            ("l", LiveTimingScreen),
        ):
            await pilot.press(key)
            await pilot.pause()
            assert isinstance(app.screen, screen_type)
    await client.aclose()


async def test_active_screen_keypress_noop(injected):
    _conn, client, store, _requests = injected
    app = PitwallApp(config=AppConfig(season=SEASON), store=store)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        first = app.screen
        assert isinstance(first, ScheduleScreen)
        await pilot.press("s")
        await pilot.pause()
        assert app.screen is first
    await client.aclose()


async def test_quit(injected):
    _conn, client, store, _requests = injected
    app = PitwallApp(config=AppConfig(season=SEASON), store=store)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.press("q")
    # Clean exit: the context manager completed without raising.
    await client.aclose()


async def test_season_load_happy_path(injected):
    conn, client, store, requests = injected
    app = PitwallApp(config=AppConfig(season=SEASON), store=store)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert len(requests) == 3
        assert app.sub_title == f"season {SEASON} · data as of 14:30 UTC"
        assert len(select_races(conn, SEASON)) > 0
    await client.aclose()


async def test_season_load_failure_notifies(db_conn, make_failing_transport):
    requests: list[httpx.Request] = []
    client = JolpicaClient(transport=make_failing_transport(requests))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=SEASON), store=store)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, ScheduleScreen)
        assert app.sub_title == f"season {SEASON} · load failed"
        errors = [msg for sev, msg in notification_messages(app) if sev == "error"]
        assert any("HTTP request failed with status: 500" in msg for msg in errors), errors
    await client.aclose()


async def test_stale_cache_served_with_warning(db_conn, jolpica_payload, make_failing_transport):
    from pitwall.cache.db import (
        set_refresh_log,
        upsert_constructor_standings,
        upsert_driver_standings,
        upsert_races,
    )
    from pitwall.models import (
        parse_constructor_standings,
        parse_driver_standings,
        parse_races,
    )

    old_fetched = datetime.datetime(2026, 6, 7, 8, 0, tzinfo=datetime.UTC)
    races = parse_races(jolpica_payload("races"))
    upsert_races(db_conn, races, season=SEASON)
    set_refresh_log(db_conn, f"schedule:{SEASON}", old_fetched, record_count=len(races))
    drivers = parse_driver_standings(jolpica_payload("driverstandings"))
    upsert_driver_standings(db_conn, SEASON, drivers)
    set_refresh_log(db_conn, f"driver_standings:{SEASON}", old_fetched, record_count=len(drivers))
    constructors = parse_constructor_standings(jolpica_payload("constructorstandings"))
    upsert_constructor_standings(db_conn, SEASON, constructors)
    set_refresh_log(db_conn, f"constructor_standings:{SEASON}", old_fetched, record_count=len(constructors))

    requests: list[httpx.Request] = []
    client = JolpicaClient(transport=make_failing_transport(requests))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=SEASON), store=store)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert app.sub_title == f"season {SEASON} · data as of 08:00 UTC · stale"
        warnings = [msg for sev, msg in notification_messages(app) if sev == "warning"]
        assert any("stale" in msg for msg in warnings)
    await client.aclose()


async def test_owned_resources_closed(tmp_path, make_fixture_transport):
    requests: list[httpx.Request] = []
    config = AppConfig(season=SEASON, db_path=str(tmp_path / "owned.db"))
    app = PitwallApp(
        config=config,
        transport=make_fixture_transport(requests),
        now=lambda: FIXED_NOW,
    )

    async with app.run_test():
        await app.workers.wait_for_complete()
        assert app.owned_connection is not None
        assert app.owned_client is not None
        conn = app.owned_connection
        client = app.owned_client

    assert client._client.is_closed
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


async def test_injected_store_not_closed(injected):
    conn, client, store, _requests = injected
    app = PitwallApp(config=AppConfig(season=SEASON), store=store)

    async with app.run_test():
        await app.workers.wait_for_complete()

    assert app.owned_connection is None
    assert app.owned_client is None
    assert not client._client.is_closed
    assert conn.execute("SELECT 1").fetchone() == (1,)
    await client.aclose()


async def test_second_launch_same_db(tmp_path, make_fixture_transport):
    db_path = str(tmp_path / "relaunch.db")
    for _ in range(2):
        requests: list[httpx.Request] = []
        config = AppConfig(season=SEASON, db_path=db_path)
        app = PitwallApp(
            config=config,
            transport=make_fixture_transport(requests),
            now=lambda: FIXED_NOW,
        )
        async with app.run_test():
            await app.workers.wait_for_complete()
        assert app.sub_title == f"season {SEASON} · data as of 14:30 UTC"


def test_loading_subtitle_constant():
    """The loading-state string is part of the AC-9..11 status contract."""
    app = PitwallApp(config=AppConfig(season=SEASON))
    assert app.loading_subtitle == f"season {SEASON} · loading…"


def test_transport_annotation():
    """AC-2 (SPEC-03): transport seam matches JolpicaClient's async transport type."""
    import inspect

    sig = inspect.signature(PitwallApp.__init__)
    assert sig.parameters["transport"].annotation == (httpx.AsyncBaseTransport | None)


async def test_snapshot_reactive_happy(injected):
    _conn, client, store, _requests = injected
    app = PitwallApp(config=AppConfig(season=SEASON), store=store)
    assert app.snapshot is None
    assert app.load_error is None

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert app.snapshot is not None
        assert app.snapshot.schedule.data
        assert app.load_error is None
    await client.aclose()


async def test_load_error_reactive_failure(db_conn, make_failing_transport):
    requests: list[httpx.Request] = []
    client = JolpicaClient(transport=make_failing_transport(requests))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=SEASON), store=store)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert app.snapshot is None
        assert app.load_error is not None
        assert "HTTP request failed with status: 500" in app.load_error
    await client.aclose()


async def test_watch_observes_snapshot(injected):
    _conn, client, store, _requests = injected
    app = PitwallApp(config=AppConfig(season=SEASON), store=store)
    seen = []

    async with app.run_test() as pilot:
        app.watch(app, "snapshot", lambda value: seen.append(value), init=True)
        await app.workers.wait_for_complete()
        await pilot.pause()

    assert seen and seen[-1] is not None
    await client.aclose()


async def test_strategy_binding_and_nav(injected_store):
    """SPEC-12 AC-7a: the g binding lands on StrategyScreen (additive)."""
    _conn, client, store, _requests = injected_store
    app = PitwallApp(config=AppConfig(season=2026), store=store)
    bindings = {b.key: (b.action, b.description) for b in PitwallApp.BINDINGS}
    assert bindings["g"] == ("show_screen('strategy')", "Game")
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.press("g")
        await pilot.pause()
        assert isinstance(app.screen, StrategyScreen)
        assert PitwallApp.SCREENS["strategy"] is StrategyScreen
    await client.aclose()
