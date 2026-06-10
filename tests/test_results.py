import asyncio
import datetime as _dt

import httpx
from conftest import FIXED_NOW, SEASON, notifications
from textual.widgets import DataTable, Static

from pitwall.api.jolpica import JolpicaClient
from pitwall.app import PitwallApp
from pitwall.cache.store import SeasonStore
from pitwall.config import AppConfig
from pitwall.models import Constructor, Driver, RaceResult, parse_races
from pitwall.screens.results import (
    ResultsScreen,
    build_result_rows,
    build_round_rows,
    default_round_index,
)

# ---- Integration / TUI tests (AC-6, AC-7, AC-12 a/b/c) ----


async def test_loaded_rounds_list(injected_store):
    _conn, client, store, _requests = injected_store
    app = PitwallApp(config=AppConfig(season=2026), store=store, now=lambda: FIXED_NOW)
    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, ResultsScreen)

        status = screen.query_one("#results-status", Static)
        rounds_table = screen.query_one("#results-rounds-table", DataTable)

        assert status.display is False
        assert rounds_table.display is True

        labels = [str(col.label) for col in rounds_table.columns.values()]
        assert labels == ["Rnd", "Race"]
        assert rounds_table.row_count == 22

        # Row 0 cells equal exactly 1, Australian Grand Prix
        assert [str(c) for c in rounds_table.get_row_at(0)] == ["1", "Australian Grand Prix"]
        # row 5 equals 6, Monaco Grand Prix
        assert [str(c) for c in rounds_table.get_row_at(5)] == ["6", "Monaco Grand Prix"]
        # row 21 equals 22, Abu Dhabi Grand Prix
        assert [str(c) for c in rounds_table.get_row_at(21)] == ["22", "Abu Dhabi Grand Prix"]

        # The cursor row is 5
        assert rounds_table.cursor_row == 5

    await client.aclose()


async def test_default_round_results_and_url(injected_store):
    _conn, client, store, requests = injected_store
    app = PitwallApp(config=AppConfig(season=2026), store=store, now=lambda: FIXED_NOW)
    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("r")
        await app.workers.wait_for_complete()
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, ResultsScreen)

        detail_title = screen.query_one("#results-detail-title", Static)
        detail_status = screen.query_one("#results-detail-status", Static)
        results_table = screen.query_one("#results-table", DataTable)

        # #results-detail-title is displayed with exactly Round 6 — Monaco Grand Prix
        assert detail_title.display is True
        assert str(detail_title.content) == "Round 6 — Monaco Grand Prix"

        # #results-detail-status is hidden
        assert detail_status.display is False

        # #results-table is displayed with exactly the 8 column labels of D3 in order:
        # Pos, Driver, Team, Grid, Laps, Time, Status, Pts
        assert results_table.display is True
        labels = [str(col.label) for col in results_table.columns.values()]
        assert labels == ["Pos", "Driver", "Team", "Grid", "Laps", "Time", "Status", "Pts"]
        assert results_table.row_count == 22

        # Row 0 = 1, Andrea Kimi Antonelli, Mercedes, 1, 78, 2:23:31.243, Finished, 25
        assert [str(c) for c in results_table.get_row_at(0)] == [
            "1",
            "Andrea Kimi Antonelli",
            "Mercedes",
            "1",
            "78",
            "2:23:31.243",
            "Finished",
            "25",
        ]
        # row 1 = 2, Lewis Hamilton, Ferrari, 3, 78, +6.271, Finished, 18
        assert [str(c) for c in results_table.get_row_at(1)] == [
            "2",
            "Lewis Hamilton",
            "Ferrari",
            "3",
            "78",
            "+6.271",
            "Finished",
            "18",
        ]
        # row 15 = 16, Carlos Sainz, Williams, 12, 70, —, Retired, 0 (empty-string time → em dash)
        # Note: U+2014 is used for EM_DASH
        assert [str(c) for c in results_table.get_row_at(15)] == [
            "16",
            "Carlos Sainz",
            "Williams",
            "12",
            "70",
            "—",
            "Retired",
            "0",
        ]
        # row 16 = R, Charles Leclerc, Ferrari, 4, 64, —, Retired, 0 (absent Time block)
        assert [str(c) for c in results_table.get_row_at(16)] == [
            "R",
            "Charles Leclerc",
            "Ferrari",
            "4",
            "64",
            "—",
            "Retired",
            "0",
        ]
        # row 21 = R, Max Verstappen, Red Bull, 2, 0, —, Retired, 0
        assert [str(c) for c in results_table.get_row_at(21)] == [
            "R",
            "Max Verstappen",
            "Red Bull",
            "2",
            "0",
            "—",
            "Retired",
            "0",
        ]

        # The request recorder contains exactly one request whose URL path equals /ergast/f1/2026/6/results/
        results_requests = [r for r in requests if "/results" in r.url.path]
        assert len(results_requests) == 1
        assert results_requests[0].url.path == "/ergast/f1/2026/6/results/"

    await client.aclose()


async def test_season_loading_state(db_conn, make_gated_transport):
    requests: list[httpx.Request] = []
    gate = asyncio.Event()
    client = JolpicaClient(transport=make_gated_transport(requests, gate))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store, now=lambda: FIXED_NOW)
    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("r")
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ResultsScreen)

            status = screen.query_one("#results-status", Static)
            rounds_table = screen.query_one("#results-rounds-table", DataTable)
            detail_title = screen.query_one("#results-detail-title", Static)
            detail_status = screen.query_one("#results-detail-status", Static)
            results_table = screen.query_one("#results-table", DataTable)

            assert status.display is True
            assert str(status.content) == "Loading results…"

            assert rounds_table.display is False
            assert detail_title.display is False
            assert detail_status.display is False
            assert results_table.display is False

            assert app.sub_title == "season 2026 · loading…"

            gate.set()
            await app.workers.wait_for_complete()
            await pilot.pause()
    finally:
        gate.set()
    await client.aclose()


async def test_season_error_state(db_conn, make_failing_transport):
    requests: list[httpx.Request] = []
    client = JolpicaClient(transport=make_failing_transport(requests))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store, now=lambda: FIXED_NOW)
    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, ResultsScreen)

        status = screen.query_one("#results-status", Static)
        rounds_table = screen.query_one("#results-rounds-table", DataTable)
        detail_title = screen.query_one("#results-detail-title", Static)
        detail_status = screen.query_one("#results-detail-status", Static)
        results_table = screen.query_one("#results-table", DataTable)

        assert status.display is True
        assert str(status.content) == "Results unavailable — season load failed."

        assert rounds_table.display is False
        assert detail_title.display is False
        assert detail_status.display is False
        assert results_table.display is False

        assert app.sub_title == "season 2026 · load failed"

    await client.aclose()


async def test_empty_schedule_state(db_conn, jolpica_payload, make_fixture_transport):
    requests: list[httpx.Request] = []
    overrides = {"races": {"MRData": {"total": "0", "RaceTable": {"Races": []}}}}
    client = JolpicaClient(transport=make_fixture_transport(requests, overrides=overrides))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store, now=lambda: FIXED_NOW)
    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, ResultsScreen)

        status = screen.query_one("#results-status", Static)
        rounds_table = screen.query_one("#results-rounds-table", DataTable)
        detail_title = screen.query_one("#results-detail-title", Static)
        detail_status = screen.query_one("#results-detail-status", Static)
        results_table = screen.query_one("#results-table", DataTable)

        assert status.display is True
        assert str(status.content) == "No rounds available for season 2026."

        assert rounds_table.display is False
        assert detail_title.display is False
        assert detail_status.display is False
        assert results_table.display is False

    await client.aclose()


# ---- Pure helpers tests (AC-2..4) ----


def _c(name):
    return Constructor(constructor_id=name.lower(), url="https://example.invalid", name=name, nationality="X")


def _d(given, family):
    return Driver(
        driver_id=family.lower(),
        permanent_number=1,
        code="DUM",
        url=None,
        given_name=given,
        family_name=family,
        date_of_birth=_dt.date(2000, 1, 1),
        nationality="X",
    )


def _rr(pos, pos_text, pts, grid, laps, status, time_str, driver=None, constructor=None):
    return RaceResult(
        number=44,
        position=pos,
        position_text=pos_text,
        points=pts,
        driver=driver or _d("John", "Doe"),
        constructor=constructor or _c("Ferrari"),
        grid=grid,
        laps=laps,
        status=status,
        time_millis=None,
        time_str=time_str,
        fastest_lap=None,
    )


def test_build_result_rows_formats_per_subcases():
    # Arrange
    res_a = _rr(1, "1", 25.0, 1, 78, "Finished", "+6.271")  # normal
    res_b = _rr(17, "R", 0.0, 4, 64, "Retired", None)  # time_str is None, position_text is R
    res_c = _rr(18, "D", 0.0, 5, 60, "Disqualified", "")  # time_str is ""
    results = [res_a, res_b, res_c]

    # Act
    rows = build_result_rows(results)

    # Assert
    assert len(rows) == 3
    # Pos, Driver, Team, Grid, Laps, Time, Status, Pts
    assert rows[0] == ("1", "John Doe", "Ferrari", "1", "78", "+6.271", "Finished", "25")
    assert rows[1] == ("R", "John Doe", "Ferrari", "4", "64", "—", "Retired", "0")
    assert rows[2] == ("D", "John Doe", "Ferrari", "5", "60", "—", "Disqualified", "0")


def test_build_result_rows_sorts_by_position_with_none_last():
    # Arrange
    r1 = _rr(2, "2", 18.0, 2, 78, "Finished", "+10.0")
    r2 = _rr(None, "R", 0.0, 3, 50, "Accident", None)
    r3 = _rr(1, "1", 25.0, 1, 78, "Finished", "1:30:00")
    r4 = _rr(None, "W", 0.0, 4, 0, "Withdrawn", None)
    results = [r1, r2, r3, r4]

    # Act
    rows = build_result_rows(results)

    # Assert
    assert len(rows) == 4
    assert rows[0][0] == "1"
    assert rows[1][0] == "2"
    assert rows[2][0] in ("R", "W")
    assert rows[3][0] in ("R", "W")
    assert {rows[2][0], rows[3][0]} == {"R", "W"}


def _circuit(circuit_id="monaco"):
    from pitwall.models import Circuit

    return Circuit(
        circuit_id=circuit_id,
        url="https://example.invalid",
        circuit_name="Monaco",
        lat=43.7,
        long=7.4,
        locality="Monte Carlo",
        country="Monaco",
    )


def _race(round_val, race_name, start_dt=None):
    from pitwall.models import Race

    return Race(
        season=2026,
        round=round_val,
        url="https://example.invalid",
        race_name=race_name,
        circuit=_circuit(),
        start=start_dt or _dt.datetime(2026, 6, 7, 13, 0, tzinfo=_dt.UTC),
        fp1=None,
        fp2=None,
        fp3=None,
        qualifying=None,
        sprint=None,
        sprint_qualifying=None,
    )


def test_build_round_rows_sorts_by_round_ascending():
    # Arrange
    race_a = _race(6, "Monaco Grand Prix")
    race_b = _race(1, "Australian Grand Prix")
    race_c = _race(22, "Abu Dhabi Grand Prix")
    races = [race_a, race_b, race_c]

    # Act
    rows = build_round_rows(races)

    # Assert
    assert len(rows) == 3
    assert rows[0] == ("1", "Australian Grand Prix")
    assert rows[1] == ("6", "Monaco Grand Prix")
    assert rows[2] == ("22", "Abu Dhabi Grand Prix")


def test_default_round_index_under_fixed_now(jolpica_payload):
    # Arrange
    races_data = jolpica_payload("races")
    races = parse_races(races_data)

    # Act
    idx = default_round_index(races, FIXED_NOW)

    # Assert
    assert idx == 5


def test_default_round_index_before_season_starts(jolpica_payload):
    # Arrange
    races_data = jolpica_payload("races")
    races = parse_races(races_data)
    first_race_start = races[0].start
    now_before = first_race_start - _dt.timedelta(seconds=1)

    # Act
    idx = default_round_index(races, now_before)

    # Assert
    assert idx is None


def test_default_round_index_at_first_race_start_equality(jolpica_payload):
    # Arrange
    races_data = jolpica_payload("races")
    races = parse_races(races_data)
    first_race_start = races[0].start

    # Act
    idx = default_round_index(races, first_race_start)

    # Assert
    assert idx is None


def test_default_round_index_after_last_race_starts(jolpica_payload):
    # Arrange
    races_data = jolpica_payload("races")
    races = parse_races(races_data)
    last_race_start = races[-1].start
    now_after = last_race_start + _dt.timedelta(seconds=1)

    # Act
    idx = default_round_index(races, now_after)

    # Assert
    assert idx == 21


# ---- SPEC-05 cycle 2 RED part B: extended tests (AC-8, AC-9, AC-10, AC-11, AC-13) ----


def _seed_stale(db_conn, jolpica_payload):
    from pitwall.cache.db import (
        set_refresh_log,
        upsert_constructor_standings,
        upsert_driver_standings,
        upsert_race_results,
        upsert_races,
    )
    from pitwall.models import (
        parse_constructor_standings,
        parse_driver_standings,
        parse_races,
        parse_results,
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

    results = parse_results(jolpica_payload("results"))
    upsert_race_results(db_conn, season=SEASON, round=6, results=results)
    set_refresh_log(db_conn, f"results:{SEASON}:6", old_fetched, record_count=len(results))


async def test_round_switching_empty_and_cache_reuse(db_conn, jolpica_payload):
    from conftest import wrap_transport

    requests = []

    races_data = jolpica_payload("races")
    drivers_data = jolpica_payload("driverstandings")
    constructors_data = jolpica_payload("constructorstandings")
    results_data = jolpica_payload("results")
    empty_results = {"MRData": {"total": "0", "RaceTable": {"Races": []}}}

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if "races" in path:
            return httpx.Response(200, json=races_data)
        elif "driverstandings" in path:
            return httpx.Response(200, json=drivers_data)
        elif "constructorstandings" in path:
            return httpx.Response(200, json=constructors_data)
        elif "/2026/6/results" in path:
            return httpx.Response(200, json=results_data)
        elif "/2026/7/results" in path:
            return httpx.Response(200, json=empty_results)
        return httpx.Response(404, json={"error": "unexpected path"})

    client = JolpicaClient(transport=wrap_transport(handler))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store, now=lambda: FIXED_NOW)

    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("r")
        await app.workers.wait_for_complete()
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, ResultsScreen)

        detail_title = screen.query_one("#results-detail-title", Static)
        detail_status = screen.query_one("#results-detail-status", Static)
        results_table = screen.query_one("#results-table", DataTable)
        rounds_table = screen.query_one("#results-rounds-table", DataTable)

        assert rounds_table.cursor_row == 5

        # Exact request-path counts
        r6_requests = [r for r in requests if "/2026/6/results" in r.url.path]
        assert len(r6_requests) == 1

        # Press down (rounds table focused, cursor 5 -> 6)
        await pilot.press("down")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert rounds_table.cursor_row == 6

        r7_requests = [r for r in requests if "/2026/7/results" in r.url.path]
        assert len(r7_requests) == 1

        # 'Round 7 — Barcelona Grand Prix' title
        assert detail_title.display is True
        assert str(detail_title.content) == "Round 7 — Barcelona Grand Prix"

        # 'No results available for round 7.' status
        assert detail_status.display is True
        assert str(detail_status.content) == "No results available for round 7."
        assert results_table.display is False

        # Press up (back to round 6)
        await pilot.press("up")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert rounds_table.cursor_row == 5

        r6_requests_after = [r for r in requests if "/2026/6/results" in r.url.path]
        assert len(r6_requests_after) == 1  # cache reuse

        assert results_table.display is True
        assert results_table.row_count == 22

    await client.aclose()


async def test_round_loading_state_and_chassis_isolation(db_conn, jolpica_payload):
    from conftest import wrap_transport

    requests = []
    gate = asyncio.Event()

    races_data = jolpica_payload("races")
    drivers_data = jolpica_payload("driverstandings")
    constructors_data = jolpica_payload("constructorstandings")
    results_data = jolpica_payload("results")

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if "races" in path:
            return httpx.Response(200, json=races_data)
        elif "driverstandings" in path:
            return httpx.Response(200, json=drivers_data)
        elif "constructorstandings" in path:
            return httpx.Response(200, json=constructors_data)
        elif "/2026/6/results" in path:
            await gate.wait()
            return httpx.Response(200, json=results_data)
        return httpx.Response(404, json={"error": "unexpected path"})

    client = JolpicaClient(transport=wrap_transport(handler))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store, now=lambda: FIXED_NOW)

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("r")
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ResultsScreen)

            detail_title = screen.query_one("#results-detail-title", Static)
            detail_status = screen.query_one("#results-detail-status", Static)
            results_table = screen.query_one("#results-table", DataTable)
            rounds_table = screen.query_one("#results-rounds-table", DataTable)

            # 'Loading results for round 6…'
            assert detail_status.display is True
            assert str(detail_status.content) == "Loading results for round 6…"
            assert results_table.display is False

            # rounds table focused
            assert rounds_table.display is True
            assert app.focused is rounds_table

            # subtitle untouched by round fetches
            assert app.sub_title == "season 2026 · data as of 14:30 UTC"
            assert detail_title.display is True
            assert str(detail_title.content) == "Round 6 — Monaco Grand Prix"

            gate.set()
            await app.workers.wait_for_complete()
            await pilot.pause()

            assert detail_status.display is False
            assert results_table.display is True
            assert results_table.row_count == 22
    finally:
        gate.set()
        await client.aclose()


async def test_round_fetch_error_state(db_conn, jolpica_payload):
    from conftest import wrap_transport

    requests = []

    races_data = jolpica_payload("races")
    drivers_data = jolpica_payload("driverstandings")
    constructors_data = jolpica_payload("constructorstandings")

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if "races" in path:
            return httpx.Response(200, json=races_data)
        elif "driverstandings" in path:
            return httpx.Response(200, json=drivers_data)
        elif "constructorstandings" in path:
            return httpx.Response(200, json=constructors_data)
        elif "/results" in path:
            return httpx.Response(500, json={"error": "failed"})
        return httpx.Response(404, json={"error": "unexpected path"})

    client = JolpicaClient(transport=wrap_transport(handler))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store, now=lambda: FIXED_NOW)

    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("r")
        await app.workers.wait_for_complete()
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, ResultsScreen)

        detail_status = screen.query_one("#results-detail-status", Static)
        results_table = screen.query_one("#results-table", DataTable)
        rounds_table = screen.query_one("#results-rounds-table", DataTable)

        # 'Results unavailable — fetch failed for round 6.'
        assert detail_status.display is True
        assert str(detail_status.content) == "Results unavailable — fetch failed for round 6."
        assert results_table.display is False

        assert rounds_table.display is True
        assert app.focused is rounds_table
        assert app.screen is screen

        # subtitle unchanged
        assert app.sub_title == "season 2026 · data as of 14:30 UTC"

        # no new notifications
        assert len(notifications(app)) == 0

    await client.aclose()


async def test_stale_round_results_notify(db_conn, jolpica_payload, make_failing_transport):
    _seed_stale(db_conn, jolpica_payload)
    requests = []

    client = JolpicaClient(transport=make_failing_transport(requests))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store, now=lambda: FIXED_NOW)

    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("r")
        await app.workers.wait_for_complete()
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, ResultsScreen)

        rounds_table = screen.query_one("#results-rounds-table", DataTable)
        results_table = screen.query_one("#results-table", DataTable)
        detail_status = screen.query_one("#results-detail-status", Static)

        # both tables render
        assert rounds_table.row_count == 22
        assert results_table.row_count == 22
        assert detail_status.display is False

        # subtitle stale
        assert app.sub_title == "season 2026 · data as of 08:00 UTC · stale"

        # warning notification containing 'Serving stale cached results for round 6 (as of 08:00 UTC).'
        assert len(notifications(app)) > 0
        warning_notifs = [
            n
            for n in notifications(app)
            if n.severity == "warning" and "Serving stale cached results for round 6 (as of 08:00 UTC)." in n.message
        ]
        assert len(warning_notifs) == 1

    await client.aclose()


async def test_focus_and_nav_keys(injected_store):
    from pitwall.screens import ScheduleScreen, StandingsScreen

    _conn, client, store, requests = injected_store
    app = PitwallApp(config=AppConfig(season=2026), store=store, now=lambda: FIXED_NOW)

    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("r")
        await app.workers.wait_for_complete()
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, ResultsScreen)

        rounds_table = screen.query_one("#results-rounds-table", DataTable)
        results_table = screen.query_one("#results-table", DataTable)

        # (a) rounds-table focus retention
        assert app.focused is rounds_table

        # pressing r again is a no-op (same ResultsScreen instance)
        await pilot.press("r")
        await pilot.pause()
        assert app.screen is screen

        results_requests_before = [r for r in requests if "/results/" in r.url.path]
        assert len(results_requests_before) == 1

        # (b) tab to results table
        await pilot.press("tab")
        await pilot.pause()
        assert app.focused is results_table

        # no-fetch cursor moves in results table
        assert results_table.cursor_row == 0
        await pilot.press("down")
        await pilot.pause()
        assert results_table.cursor_row == 1

        results_requests_after = [r for r in requests if "/results/" in r.url.path]
        assert len(results_requests_after) == 1

        # (c) cross-screen round-trips: n activates StandingsScreen
        await pilot.press("n")
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, StandingsScreen)

        # pressing r returns to the same ResultsScreen instance
        await pilot.press("r")
        await pilot.pause()
        assert app.screen is screen
        assert rounds_table.row_count == 22
        assert results_table.row_count == 22

        # (d) pressing s activates ScheduleScreen
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, ScheduleScreen)

        # r returns to the same instance again
        await pilot.press("r")
        await pilot.pause()
        assert app.screen is screen

        # pressing q exits cleanly
        await pilot.press("q")
        await pilot.pause()

    await client.aclose()


async def test_midload_wander_away(db_conn, make_gated_transport):
    from pitwall.screens import ScheduleScreen

    requests = []
    gate = asyncio.Event()
    client = JolpicaClient(transport=make_gated_transport(requests, gate))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store, now=lambda: FIXED_NOW)

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            # (e) press r during load (season-loading state)
            await pilot.press("r")
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ResultsScreen)
            status = screen.query_one("#results-status", Static)
            assert status.display is True
            assert str(status.content) == "Loading results…"

            # press s (back to schedule)
            await pilot.press("s")
            await pilot.pause()
            assert isinstance(app.screen, ScheduleScreen)

            # open the gate, await completion
            gate.set()
            await app.workers.wait_for_complete()
            await pilot.pause()

            # app.focused is the schedule screen's #schedule-table (inactive results screen did not steal focus)
            schedule_table = app.screen.query_one("#schedule-table", DataTable)
            assert app.focused is schedule_table

            # pressing r then shows the rounds table populated (22 rows, cursor row 5)
            await pilot.press("r")
            await pilot.pause()
            assert app.screen is screen

            rounds_table = screen.query_one("#results-rounds-table", DataTable)
            assert rounds_table.display is True
            assert rounds_table.row_count == 22
            assert rounds_table.cursor_row == 5

            # and, after awaiting workers, the results table populated (22 rows)
            await app.workers.wait_for_complete()
            await pilot.pause()

            results_table = screen.query_one("#results-table", DataTable)
            assert results_table.display is True
            assert results_table.row_count == 22

    finally:
        gate.set()
        await client.aclose()


async def test_load_completes_on_results_screen(db_conn, make_gated_transport):
    requests = []
    gate = asyncio.Event()
    client = JolpicaClient(transport=make_gated_transport(requests, gate))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store, now=lambda: FIXED_NOW)

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            # (f) press r during load and stay
            await pilot.press("r")
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ResultsScreen)

            # open the gate, await completion
            gate.set()
            await app.workers.wait_for_complete()
            await pilot.pause()

            # app.focused is #results-rounds-table — guarded schedule screen did not pull focus
            rounds_table = screen.query_one("#results-rounds-table", DataTable)
            assert app.focused is rounds_table

    finally:
        gate.set()
        await client.aclose()


async def test_preseason_regression(db_conn, jolpica_payload):
    from conftest import wrap_transport

    requests = []

    races_data = jolpica_payload("races")
    drivers_data = jolpica_payload("driverstandings")
    constructors_data = jolpica_payload("constructorstandings")
    results_data = jolpica_payload("results")

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if "races" in path:
            return httpx.Response(200, json=races_data)
        elif "driverstandings" in path:
            return httpx.Response(200, json=drivers_data)
        elif "constructorstandings" in path:
            return httpx.Response(200, json=constructors_data)
        elif "/results" in path:
            return httpx.Response(200, json=results_data)
        return httpx.Response(404, json={"error": "unexpected path"})

    pre_season_now = _dt.datetime(2026, 1, 1, 0, 0, tzinfo=_dt.UTC)
    client = JolpicaClient(transport=wrap_transport(handler))
    store = SeasonStore(db_conn, client, now=lambda: pre_season_now)
    app = PitwallApp(config=AppConfig(season=2026), store=store, now=lambda: pre_season_now)

    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("r")
        await app.workers.wait_for_complete()
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, ResultsScreen)

        results_requests = [r for r in requests if "/results/" in r.url.path]
        assert len(results_requests) == 0

        detail_title = screen.query_one("#results-detail-title", Static)
        detail_status = screen.query_one("#results-detail-status", Static)
        results_table = screen.query_one("#results-table", DataTable)
        rounds_table = screen.query_one("#results-rounds-table", DataTable)

        assert detail_title.display is False
        assert results_table.display is False
        assert detail_status.display is False

        assert rounds_table.display is True
        assert rounds_table.row_count == 22
        assert rounds_table.cursor_row == 0

    await client.aclose()
