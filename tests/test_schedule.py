"""Schedule screen tests (SPEC-03 AC-6..13)."""

import asyncio
import copy
import datetime

import httpx
from conftest import FIXED_NOW, SEASON
from textual.widgets import DataTable, Static

from pitwall.api.jolpica import JolpicaClient
from pitwall.app import PitwallApp
from pitwall.cache.store import SeasonStore
from pitwall.config import AppConfig
from pitwall.models import Circuit, Race
from pitwall.screens.schedule import ScheduleScreen, build_rows, next_race_index

EM_DASH = "—"


def make_app(store):
    return PitwallApp(config=AppConfig(season=SEASON), store=store, now=lambda: FIXED_NOW)


def make_race(round_num, start, qualifying=None, sprint=None):
    circuit = Circuit(
        circuit_id=f"c{round_num}",
        url="https://example.invalid/c",
        circuit_name=f"Circuit {round_num}",
        lat=0.0,
        long=0.0,
        locality="Town",
        country="Land",
    )
    return Race(
        season=SEASON,
        round=round_num,
        url="https://example.invalid/r",
        race_name=f"Race {round_num}",
        circuit=circuit,
        start=start,
        fp1=None,
        fp2=None,
        fp3=None,
        qualifying=qualifying,
        sprint=sprint,
        sprint_qualifying=None,
    )


# ---- pure helpers (AC-8, AC-9) ----


def test_row_formatting_absent_and_present_sessions():
    start = datetime.datetime(2026, 3, 8, 4, 0, tzinfo=datetime.UTC)
    quali = datetime.datetime(2026, 3, 7, 5, 0, tzinfo=datetime.UTC)
    bare = make_race(1, start)
    sprinty = make_race(2, start, qualifying=quali, sprint=quali)

    rows = build_rows([sprinty, bare])

    assert rows[0][0] == "1"
    assert rows[0][5] == EM_DASH
    assert rows[0][6] == EM_DASH
    assert rows[1][5] == "03-07 05:00"
    assert rows[1][6] == "03-07 05:00"


def test_next_race_index_fixture(jolpica_payload):
    from pitwall.models import parse_races

    races = parse_races(jolpica_payload("races"))
    assert next_race_index(races, FIXED_NOW) == 6


def test_next_race_index_all_future_and_all_past_and_boundary():
    start = datetime.datetime(2026, 3, 8, 4, 0, tzinfo=datetime.UTC)
    races = [make_race(1, start), make_race(2, start + datetime.timedelta(days=7))]

    before = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    after = datetime.datetime(2027, 1, 1, tzinfo=datetime.UTC)

    assert next_race_index(races, before) == 0
    assert next_race_index(races, after) is None
    assert next_race_index(races, start) == 0  # equality counts as upcoming


# ---- Pilot tests ----


async def test_loading_state_before_gate_opens(db_conn, make_gated_transport):
    requests: list[httpx.Request] = []
    gate = asyncio.Event()
    client = JolpicaClient(transport=make_gated_transport(requests, gate))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = make_app(store)

    try:
        async with app.run_test() as pilot:
            await pilot.pause()
            status = app.screen.query_one("#schedule-status", Static)
            table = app.screen.query_one("#schedule-table", DataTable)
            assert str(status.content) == "Loading schedule…"
            assert status.display is True
            assert table.display is False

            gate.set()
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert status.display is False
            assert table.display is True
    finally:
        gate.set()
    await client.aclose()


async def test_loaded_table_columns_and_rows(injected_store):
    _conn, client, store, _requests = injected_store
    app = make_app(store)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        table = app.screen.query_one("#schedule-table", DataTable)
        labels = [str(col.label) for col in table.columns.values()]
        assert labels == ["Rnd", "Race", "Circuit", "Location", "Start (UTC)", "Quali (UTC)", "Sprint (UTC)"]
        assert table.row_count == 22
        row0 = [str(cell) for cell in table.get_row_at(0)]
        assert row0 == [
            "1",
            "Australian Grand Prix",
            "Albert Park Grand Prix Circuit",
            "Melbourne, Australia",
            "03-08 04:00",
            "03-07 05:00",
            EM_DASH,
        ]
        row1 = [str(cell) for cell in table.get_row_at(1)]
        assert row1 == [
            "2",
            "Chinese Grand Prix",
            "Shanghai International Circuit",
            "Shanghai, China",
            "03-15 07:00",
            "03-14 07:00",
            "03-14 03:00",
        ]
        last = [str(cell) for cell in table.get_row_at(21)]
        assert last[0] == "22"
    await client.aclose()


async def test_cursor_on_next_race(injected_store):
    _conn, client, store, _requests = injected_store
    app = make_app(store)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        table = app.screen.query_one("#schedule-table", DataTable)
        assert table.cursor_row == 6
    await client.aclose()


async def test_cursor_row_zero_when_season_over(db_conn, make_fixture_transport):
    requests: list[httpx.Request] = []
    client = JolpicaClient(transport=make_fixture_transport(requests))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    season_over = datetime.datetime(2027, 1, 1, tzinfo=datetime.UTC)
    app = PitwallApp(config=AppConfig(season=SEASON), store=store, now=lambda: season_over)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        table = app.screen.query_one("#schedule-table", DataTable)
        assert table.cursor_row == 0
    await client.aclose()


async def test_empty_schedule_message(db_conn, jolpica_payload, make_fixture_transport):
    empty = copy.deepcopy(jolpica_payload("races"))
    empty["MRData"]["RaceTable"]["Races"] = []
    empty["MRData"]["total"] = "0"
    requests: list[httpx.Request] = []
    client = JolpicaClient(transport=make_fixture_transport(requests, overrides={"races": empty}))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = make_app(store)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        status = app.screen.query_one("#schedule-status", Static)
        table = app.screen.query_one("#schedule-table", DataTable)
        assert str(status.content) == f"No races scheduled for season {SEASON}."
        assert status.display is True
        assert table.display is False
    await client.aclose()


async def test_error_state_body_and_subtitle(db_conn, make_failing_transport):
    requests: list[httpx.Request] = []
    client = JolpicaClient(transport=make_failing_transport(requests))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = make_app(store)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        status = app.screen.query_one("#schedule-status", Static)
        table = app.screen.query_one("#schedule-table", DataTable)
        assert str(status.content) == "Schedule unavailable — season load failed."
        assert status.display is True
        assert table.display is False
        assert isinstance(app.screen, ScheduleScreen)
        assert app.sub_title == f"season {SEASON} · load failed"
    await client.aclose()


async def test_stale_snapshot_renders_table(db_conn, jolpica_payload, make_failing_transport):
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
    app = make_app(store)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        status = app.screen.query_one("#schedule-status", Static)
        table = app.screen.query_one("#schedule-table", DataTable)
        assert status.display is False
        assert table.display is True
        assert table.row_count == 22
        assert app.sub_title == f"season {SEASON} · data as of 08:00 UTC · stale"
    await client.aclose()


async def test_table_focused_after_load_and_nav_keys(injected_store):
    from pitwall.screens import StandingsScreen

    _conn, client, store, _requests = injected_store
    app = make_app(store)

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        table = app.screen.query_one("#schedule-table", DataTable)
        assert app.focused is table

        first_schedule = app.screen
        await pilot.press("n")
        await pilot.pause()
        assert isinstance(app.screen, StandingsScreen)

        await pilot.press("s")
        await pilot.pause()
        assert app.screen is first_schedule
        assert app.screen.query_one("#schedule-table", DataTable).row_count == 22

        await pilot.press("q")
    await client.aclose()


def test_no_priority_bindings():
    assert all(not binding.priority for binding in PitwallApp.BINDINGS)


def test_api_strings_render_markup_safe(db_conn, jolpica_payload, make_fixture_transport):
    """iter15 SEC-1: bracketed API data must not parse as Rich markup or crash."""
    import copy

    evil = copy.deepcopy(jolpica_payload("races"))
    evil["MRData"]["RaceTable"]["Races"][0]["raceName"] = "bad [/] name [@click=app.bell]X[/]"
    requests: list[httpx.Request] = []
    client = JolpicaClient(transport=make_fixture_transport(requests, overrides={"races": evil}))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = make_app(store)

    async def run() -> None:
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            table = app.screen.query_one("#schedule-table", DataTable)
            # The cell's plain text carries the brackets verbatim (no markup parse).
            assert str(table.get_row_at(0)[1]) == "bad [/] name [@click=app.bell]X[/]"

    import asyncio

    asyncio.run(run())
    asyncio.run(client.aclose())
