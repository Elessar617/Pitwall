import asyncio
import copy
import datetime as _dt

import httpx
from conftest import FIXED_NOW, SEASON
from textual.widgets import DataTable, Static

from pitwall.api.jolpica import JolpicaClient
from pitwall.app import PitwallApp
from pitwall.cache.store import SeasonStore
from pitwall.config import AppConfig
from pitwall.models import Constructor, ConstructorStanding, Driver, DriverStanding
from pitwall.screens.standings import (
    StandingsScreen,
    build_constructor_rows,
    build_driver_rows,
)

# ---- SPEC-04 cycle 1: pure helpers (AC-2..4) ----
EM = "—"


def _constructor(name):
    return Constructor(constructor_id=name.lower(), url="https://example.invalid", name=name, nationality="X")


def _driver(given, family, code):
    return Driver(
        driver_id=family.lower(),
        permanent_number=1,
        code=code,
        url=None,
        given_name=given,
        family_name=family,
        date_of_birth=_dt.date(2000, 1, 1),
        nationality="X",
    )


def _ds(pos, pos_text, points, wins, driver, constructors):
    return DriverStanding(
        position=pos, position_text=pos_text, points=points, wins=wins, driver=driver, constructors=constructors
    )


# format_points tests relocated to tests/test_cells.py


def test_build_driver_rows_contracts():
    alpha, beta = _constructor("Alpha"), _constructor("Beta")
    rows = build_driver_rows(
        [
            _ds(2, "2", 7.5, 0, _driver("Two", "Second", None), [alpha]),
            _ds(1, "-", 156.0, 5, _driver("One", "First", "ONE"), [alpha, beta]),
            _ds(3, "3", 0.0, 0, _driver("Three", "Third", "THR"), []),
        ]
    )

    assert rows[0] == ("-", "One First", "ONE", "Alpha / Beta", "156", "5")
    assert rows[1] == ("2", "Two Second", EM, "Alpha", "7.5", "0")
    assert rows[2] == ("3", "Three Third", "THR", EM, "0", "0")


def test_build_constructor_rows_contracts():
    rows = build_constructor_rows(
        [
            ConstructorStanding(
                position=2, position_text="2", points=165.0, wins=0, constructor=_constructor("Ferrari")
            ),
            ConstructorStanding(
                position=1, position_text="1", points=244.0, wins=6, constructor=_constructor("Mercedes")
            ),
        ]
    )

    assert rows[0] == ("1", "Mercedes", "244", "6")
    assert rows[1] == ("2", "Ferrari", "165", "0")


# ---- SPEC-04 cycle 2: the standings screen (AC-5..12) ----


DRIVER_COLS = ["Pos", "Driver", "Code", "Team", "Pts", "Wins"]
CONSTRUCTOR_COLS = ["Pos", "Team", "Pts", "Wins"]


def make_app(store):
    return PitwallApp(config=AppConfig(season=SEASON), store=store, now=lambda: FIXED_NOW)


def section_widgets(screen):
    return {
        "status": screen.query_one("#standings-status", Static),
        "d_title": screen.query_one("#standings-drivers-title", Static),
        "d_table": screen.query_one("#standings-drivers-table", DataTable),
        "c_title": screen.query_one("#standings-constructors-title", Static),
        "c_table": screen.query_one("#standings-constructors-table", DataTable),
    }


async def goto_standings(app, pilot):
    await app.workers.wait_for_complete()
    await pilot.pause()
    await pilot.press("n")
    await pilot.pause()


async def test_loaded_drivers_table(injected_store):
    _conn, client, store, _requests = injected_store
    app = make_app(store)
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_standings(app, pilot)
        w = section_widgets(app.screen)
        labels = [str(col.label) for col in w["d_table"].columns.values()]
        assert labels == DRIVER_COLS
        assert w["d_table"].row_count == 22
        assert [str(c) for c in w["d_table"].get_row_at(0)] == [
            "1",
            "Andrea Kimi Antonelli",
            "ANT",
            "Mercedes",
            "156",
            "5",
        ]
        assert [str(c) for c in w["d_table"].get_row_at(1)] == ["2", "Lewis Hamilton", "HAM", "Ferrari", "90", "0"]
        assert [str(c) for c in w["d_table"].get_row_at(21)] == ["22", "Lance Stroll", "STR", "Aston Martin", "0", "0"]
        assert str(w["d_title"].content) == "Driver standings"
        assert w["d_title"].display is True
    await client.aclose()


async def test_loaded_constructors_table(injected_store):
    _conn, client, store, _requests = injected_store
    app = make_app(store)
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_standings(app, pilot)
        w = section_widgets(app.screen)
        labels = [str(col.label) for col in w["c_table"].columns.values()]
        assert labels == CONSTRUCTOR_COLS
        assert w["c_table"].row_count == 11
        assert [str(c) for c in w["c_table"].get_row_at(0)] == ["1", "Mercedes", "244", "6"]
        assert [str(c) for c in w["c_table"].get_row_at(1)] == ["2", "Ferrari", "165", "0"]
        assert [str(c) for c in w["c_table"].get_row_at(10)] == ["11", "Cadillac F1 Team", "0", "0"]
        assert str(w["c_title"].content) == "Constructor standings"
        assert w["status"].display is False
    await client.aclose()


async def test_both_tables_fit_80x24(injected_store):
    _conn, client, store, _requests = injected_store
    app = make_app(store)
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_standings(app, pilot)
        w = section_widgets(app.screen)
        screen_height = app.screen.region.height
        assert w["c_table"].region.bottom <= screen_height
        assert w["d_table"].region.height >= 5
        assert w["c_table"].region.height >= 5
    await client.aclose()


async def test_loading_state(db_conn, make_gated_transport):
    requests: list[httpx.Request] = []
    gate = asyncio.Event()
    client = JolpicaClient(transport=make_gated_transport(requests, gate))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = make_app(store)
    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("n")
            await pilot.pause()
            w = section_widgets(app.screen)
            assert str(w["status"].content) == "Loading standings…"
            assert w["status"].display is True
            for key in ("d_title", "d_table", "c_title", "c_table"):
                assert w[key].display is False
            assert app.sub_title == f"season {SEASON} · loading…"

            gate.set()
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert w["status"].display is False
            assert w["d_table"].display is True
            assert w["c_table"].display is True
    finally:
        gate.set()
    await client.aclose()


def _empty_standings(payload):
    empty = copy.deepcopy(payload)
    empty["MRData"]["StandingsTable"]["StandingsLists"] = []
    empty["MRData"]["total"] = "0"
    return empty


async def test_empty_states(db_conn, jolpica_payload, make_fixture_transport):
    requests: list[httpx.Request] = []
    overrides = {
        "driverstandings": _empty_standings(jolpica_payload("driverstandings")),
        "constructorstandings": _empty_standings(jolpica_payload("constructorstandings")),
    }
    client = JolpicaClient(transport=make_fixture_transport(requests, overrides=overrides))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = make_app(store)
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_standings(app, pilot)
        w = section_widgets(app.screen)
        assert app.sub_title == f"season {SEASON} · data as of 14:30 UTC"
        assert str(w["status"].content) == f"No standings available for season {SEASON}."
        assert w["status"].display is True
        for key in ("d_title", "d_table", "c_title", "c_table"):
            assert w[key].display is False
    await client.aclose()


async def test_asymmetric_empty_drivers_only_focuses_constructors_table_and_navigates(
    db_conn, jolpica_payload, make_fixture_transport
):
    # Arrange
    requests: list[httpx.Request] = []
    overrides = {"driverstandings": _empty_standings(jolpica_payload("driverstandings"))}
    client = JolpicaClient(transport=make_fixture_transport(requests, overrides=overrides))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = make_app(store)

    # Act
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_standings(app, pilot)
        w = section_widgets(app.screen)

        # Assert
        assert w["d_title"].display is False
        assert w["d_table"].display is False
        assert w["c_table"].display is True
        assert w["c_table"].row_count == 11
        assert w["status"].display is False

        # AC-5 additions:
        # Assert initial focus is constructors table
        assert app.focused is w["c_table"]
        assert w["c_table"].cursor_row == 0

        # Press down arrow
        await pilot.press("down")
        await pilot.pause()

        # Assert cursor moves without tab
        assert w["c_table"].cursor_row == 1

    await client.aclose()


async def test_error_state(db_conn, make_failing_transport):
    requests: list[httpx.Request] = []
    client = JolpicaClient(transport=make_failing_transport(requests))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = make_app(store)
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_standings(app, pilot)
        w = section_widgets(app.screen)
        assert str(w["status"].content) == "Standings unavailable — season load failed."
        assert w["status"].display is True
        for key in ("d_title", "d_table", "c_title", "c_table"):
            assert w[key].display is False
        assert isinstance(app.screen, StandingsScreen)
        assert app.sub_title == f"season {SEASON} · load failed"
    await client.aclose()


def _seed_stale(db_conn, jolpica_payload):
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

    old_fetched = _dt.datetime(2026, 6, 7, 8, 0, tzinfo=_dt.UTC)
    races = parse_races(jolpica_payload("races"))
    upsert_races(db_conn, races, season=SEASON)
    set_refresh_log(db_conn, f"schedule:{SEASON}", old_fetched, record_count=len(races))
    drivers = parse_driver_standings(jolpica_payload("driverstandings"))
    upsert_driver_standings(db_conn, SEASON, drivers)
    set_refresh_log(db_conn, f"driver_standings:{SEASON}", old_fetched, record_count=len(drivers))
    constructors = parse_constructor_standings(jolpica_payload("constructorstandings"))
    upsert_constructor_standings(db_conn, SEASON, constructors)
    set_refresh_log(db_conn, f"constructor_standings:{SEASON}", old_fetched, record_count=len(constructors))


async def test_stale_state_renders_data(db_conn, jolpica_payload, make_failing_transport):
    _seed_stale(db_conn, jolpica_payload)
    requests: list[httpx.Request] = []
    client = JolpicaClient(transport=make_failing_transport(requests))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = make_app(store)
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_standings(app, pilot)
        w = section_widgets(app.screen)
        assert w["d_table"].row_count == 22
        assert w["c_table"].row_count == 11
        assert w["status"].display is False
        assert app.sub_title == f"season {SEASON} · data as of 08:00 UTC · stale"
    await client.aclose()


async def test_focus_and_nav_with_two_tables(injected_store):
    from pitwall.screens import ResultsScreen, ScheduleScreen

    _conn, client, store, _requests = injected_store
    app = make_app(store)
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_standings(app, pilot)
        w = section_widgets(app.screen)
        first = app.screen

        assert app.focused is w["d_table"]
        await pilot.press("n")
        await pilot.pause()
        assert app.screen is first

        assert w["d_table"].cursor_row == 0
        await pilot.press("down")
        await pilot.pause()
        assert w["d_table"].cursor_row == 1

        await pilot.press("tab")
        await pilot.pause()
        assert app.focused is w["c_table"]

        await pilot.press("r")
        await pilot.pause()
        assert isinstance(app.screen, ResultsScreen)
        await pilot.press("n")
        await pilot.pause()
        assert app.screen is first
        assert section_widgets(app.screen)["d_table"].row_count == 22
        assert section_widgets(app.screen)["c_table"].row_count == 11

        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, ScheduleScreen)
        await pilot.press("n")
        await pilot.pause()
        assert app.screen is first

        await pilot.press("q")
    await client.aclose()


async def test_midload_wander(db_conn, make_gated_transport):
    from pitwall.screens import ScheduleScreen

    requests: list[httpx.Request] = []
    gate = asyncio.Event()
    client = JolpicaClient(transport=make_gated_transport(requests, gate))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = make_app(store)
    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("n")
            await pilot.pause()
            assert str(app.screen.query_one("#standings-status", Static).content) == "Loading standings…"
            await pilot.press("s")
            await pilot.pause()
            assert isinstance(app.screen, ScheduleScreen)

            gate.set()
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.focused is app.screen.query_one("#schedule-table", DataTable)

            await pilot.press("n")
            await pilot.pause()
            w = section_widgets(app.screen)
            assert w["d_table"].row_count == 22
            assert w["c_table"].row_count == 11
            assert w["status"].display is False
    finally:
        gate.set()
    await client.aclose()
