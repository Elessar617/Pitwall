import asyncio
import datetime

import httpx
from conftest import notifications
from textual.widgets import DataTable, Static

from pitwall.api.jolpica import JolpicaClient
from pitwall.app import PitwallApp
from pitwall.cache.store import SeasonStore
from pitwall.config import AppConfig
from pitwall.models import Constructor, Driver, parse_constructors, parse_drivers
from pitwall.screens.cells import EM_DASH
from pitwall.screens.profiles import ProfilesScreen, build_constructor_rows, build_driver_rows
from pitwall.screens.schedule import ScheduleScreen
from pitwall.screens.standings import StandingsScreen


async def test_loaded_drivers_section(injected_store):
    _conn, _client, store, _requests = injected_store
    app = PitwallApp(config=AppConfig(season=2026), store=store)
    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("p")
        await app.workers.wait_for_complete()
        await pilot.pause()

        screen = app.screen
        assert isinstance(screen, ProfilesScreen)

        # Drivers title and table display states
        drivers_title = screen.query_one("#profiles-drivers-title", Static)
        assert drivers_title.display is True
        assert str(drivers_title.content) == "Drivers"

        drivers_status = screen.query_one("#profiles-drivers-status", Static)
        assert drivers_status.display is False

        profiles_status = screen.query_one("#profiles-status", Static)
        assert profiles_status.display is False

        drivers_table = screen.query_one("#profiles-drivers-table", DataTable)
        assert drivers_table.display is True

        labels = [str(col.label) for col in drivers_table.columns.values()]
        assert labels == ["No", "Driver", "Code", "Nationality", "Born"]
        assert drivers_table.row_count == 23

        # literal cell checks:
        # row 0 = 23, Alexander Albon, ALB, Thai, 1996-03-23
        assert [str(c) for c in drivers_table.get_row_at(0)] == ["23", "Alexander Albon", "ALB", "Thai", "1996-03-23"]
        # row 1 = 14, Fernando Alonso, ALO, Spanish, 1981-07-29
        assert [str(c) for c in drivers_table.get_row_at(1)] == [
            "14",
            "Fernando Alonso",
            "ALO",
            "Spanish",
            "1981-07-29",
        ]
        # row 7 = —, Jak Crawford, —, —, —
        assert [str(c) for c in drivers_table.get_row_at(7)] == [EM_DASH, "Jak Crawford", EM_DASH, EM_DASH, EM_DASH]
        # row 11 = 27, Nico Hülkenberg, HUL, German, 1987-08-19
        assert [str(c) for c in drivers_table.get_row_at(11)] == [
            "27",
            "Nico Hülkenberg",
            "HUL",
            "German",
            "1987-08-19",
        ]
        # row 17 = 81, Oscar Piastri, PIA, Australian, 2001-04-06
        assert [str(c) for c in drivers_table.get_row_at(17)] == [
            "81",
            "Oscar Piastri",
            "PIA",
            "Australian",
            "2001-04-06",
        ]
        # row 18 = 11, Sergio Pérez, PER, Mexican, 1990-01-26
        assert [str(c) for c in drivers_table.get_row_at(18)] == ["11", "Sergio Pérez", "PER", "Mexican", "1990-01-26"]
        # row 22 = 3, Max Verstappen, VER, Dutch, 1997-09-30
        assert [str(c) for c in drivers_table.get_row_at(22)] == ["3", "Max Verstappen", "VER", "Dutch", "1997-09-30"]


async def test_loaded_constructors_section(injected_store):
    _conn, _client, store, _requests = injected_store
    app = PitwallApp(config=AppConfig(season=2026), store=store)
    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press("p")
        await app.workers.wait_for_complete()
        await pilot.pause()

        screen = app.screen

        constructors_title = screen.query_one("#profiles-constructors-title", Static)
        assert constructors_title.display is True
        assert str(constructors_title.content) == "Constructors"

        constructors_status = screen.query_one("#profiles-constructors-status", Static)
        assert constructors_status.display is False

        constructors_table = screen.query_one("#profiles-constructors-table", DataTable)
        assert constructors_table.display is True

        labels = [str(col.label) for col in constructors_table.columns.values()]
        assert labels == ["Team", "Nationality"]
        assert constructors_table.row_count == 11

        # Row checks:
        assert [str(c) for c in constructors_table.get_row_at(0)] == ["Alpine F1 Team", "French"]
        assert [str(c) for c in constructors_table.get_row_at(1)] == ["Aston Martin", "British"]
        assert [str(c) for c in constructors_table.get_row_at(8)] == ["RB F1 Team", "Italian"]
        assert [str(c) for c in constructors_table.get_row_at(9)] == ["Red Bull", "Austrian"]
        assert [str(c) for c in constructors_table.get_row_at(10)] == ["Williams", "British"]


async def test_on_demand_request_contract(injected_store):
    _conn, _client, store, requests = injected_store
    app = PitwallApp(config=AppConfig(season=2026), store=store)
    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()

        # the recorder holds exactly 3 requests (no rosters)
        assert len(requests) == 3
        for req in requests:
            path = req.url.path
            assert "/drivers/" not in path
            assert "/constructors/" not in path

        # press "p"
        await pilot.press("p")
        await app.workers.wait_for_complete()
        await pilot.pause()

        # after p + wait: exactly 5 requests
        assert len(requests) == 5
        roster_reqs = [r for r in requests if "/drivers/" in r.url.path or "/constructors/" in r.url.path]
        assert len(roster_reqs) == 2
        assert roster_reqs[0].url.path == "/ergast/f1/2026/drivers/"
        assert roster_reqs[1].url.path == "/ergast/f1/2026/constructors/"

        # press "s", then "p", + wait: still exactly 5 requests
        await pilot.press("s")
        await pilot.pause()
        await pilot.press("p")
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert len(requests) == 5


async def test_season_loading_state(db_conn, jolpica_payload, make_gated_transport):
    from conftest import FIXED_NOW

    gate = asyncio.Event()
    requests = []
    transport = make_gated_transport(requests, gate)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store)

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press("p")
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ProfilesScreen)

            status = screen.query_one("#profiles-status", Static)
            assert status.display is True
            assert str(status.content) == "Loading profiles…"

            widgets = [
                "#profiles-drivers-title",
                "#profiles-drivers-status",
                "#profiles-drivers-table",
                "#profiles-constructors-title",
                "#profiles-constructors-status",
                "#profiles-constructors-table",
            ]
            for w_id in widgets:
                widget = screen.query_one(w_id)
                assert widget.display is False

            assert app.sub_title == "season 2026 · loading…"

            gate.set()
            await app.workers.wait_for_complete()
    finally:
        gate.set()
        await client.aclose()


async def test_season_error_state(db_conn, make_failing_transport):
    from conftest import FIXED_NOW

    requests = []
    transport = make_failing_transport(requests)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store)

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("p")
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ProfilesScreen)

            status = screen.query_one("#profiles-status", Static)
            assert status.display is True
            assert str(status.content) == "Profiles unavailable — season load failed."

            widgets = [
                "#profiles-drivers-title",
                "#profiles-drivers-status",
                "#profiles-drivers-table",
                "#profiles-constructors-title",
                "#profiles-constructors-status",
                "#profiles-constructors-table",
            ]
            for w_id in widgets:
                widget = screen.query_one(w_id)
                assert widget.display is False

            for req in requests:
                path = req.url.path
                assert "/drivers/" not in path
                assert "/constructors/" not in path

            assert app.screen is screen
            assert app.sub_title == "season 2026 · load failed"
    finally:
        await client.aclose()


async def test_roster_loading_state_and_chassis_isolation(db_conn, jolpica_payload):
    from conftest import FIXED_NOW, _season_payloads, wrap_transport

    gate = asyncio.Event()
    requests = []
    payloads = _season_payloads(jolpica_payload)

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if "/drivers/" in path or "/constructors/" in path:
            await gate.wait()
        for key, payload in payloads.items():
            if key in path:
                return httpx.Response(200, json=payload)
        return httpx.Response(404, json={"error": "not found"})

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store)

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("p")
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ProfilesScreen)

            assert screen.query_one("#profiles-status", Static).display is False
            assert screen.query_one("#profiles-drivers-title", Static).display is True
            assert screen.query_one("#profiles-constructors-title", Static).display is True

            drivers_status = screen.query_one("#profiles-drivers-status", Static)
            assert drivers_status.display is True
            assert str(drivers_status.content) == "Loading drivers…"

            constructors_status = screen.query_one("#profiles-constructors-status", Static)
            assert constructors_status.display is True
            assert str(constructors_status.content) == "Loading constructors…"

            assert screen.query_one("#profiles-drivers-table", DataTable).display is False
            assert screen.query_one("#profiles-constructors-table", DataTable).display is False

            assert app.sub_title == "season 2026 · data as of 14:30 UTC"

            gate.set()
            await app.workers.wait_for_complete()
            await pilot.pause()

            assert screen.query_one("#profiles-drivers-status", Static).display is False
            assert screen.query_one("#profiles-constructors-status", Static).display is False

            drivers_table = screen.query_one("#profiles-drivers-table", DataTable)
            constructors_table = screen.query_one("#profiles-constructors-table", DataTable)
            assert drivers_table.display is True
            assert drivers_table.row_count == 23
            assert constructors_table.display is True
            assert constructors_table.row_count == 11
            assert app.sub_title == "season 2026 · data as of 14:30 UTC"
    finally:
        gate.set()
        await client.aclose()


async def test_drivers_fail_constructors_render(db_conn, jolpica_payload):
    from conftest import FIXED_NOW, _season_payloads, wrap_transport

    requests = []
    payloads = _season_payloads(jolpica_payload)

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if "/drivers/" in path:
            return httpx.Response(500, json={"error": "failed"})
        for key, payload in payloads.items():
            if key in path:
                return httpx.Response(200, json=payload)
        return httpx.Response(404, json={"error": "not found"})

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store)

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("p")
            await app.workers.wait_for_complete()
            await pilot.pause()

            screen = app.screen

            drivers_status = screen.query_one("#profiles-drivers-status", Static)
            assert drivers_status.display is True
            assert str(drivers_status.content) == "Drivers unavailable — fetch failed."

            assert screen.query_one("#profiles-drivers-table", DataTable).display is False

            c_table = screen.query_one("#profiles-constructors-table", DataTable)
            assert c_table.display is True
            assert c_table.row_count == 11

            assert app.focused is c_table
            assert not any(n.severity == "error" for n in notifications(app))
            assert app.sub_title == "season 2026 · data as of 14:30 UTC"
    finally:
        await client.aclose()


async def test_constructors_fail_drivers_render(db_conn, jolpica_payload):
    from conftest import FIXED_NOW, _season_payloads, wrap_transport

    requests = []
    payloads = _season_payloads(jolpica_payload)

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if "/constructors/" in path:
            return httpx.Response(500, json={"error": "failed"})
        for key, payload in payloads.items():
            if key in path:
                return httpx.Response(200, json=payload)
        return httpx.Response(404, json={"error": "not found"})

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store)

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("p")
            await app.workers.wait_for_complete()
            await pilot.pause()

            screen = app.screen

            d_table = screen.query_one("#profiles-drivers-table", DataTable)
            assert d_table.display is True
            assert d_table.row_count == 23
            assert app.focused is d_table

            c_status = screen.query_one("#profiles-constructors-status", Static)
            assert c_status.display is True
            assert str(c_status.content) == "Constructors unavailable — fetch failed."

            assert screen.query_one("#profiles-constructors-table", DataTable).display is False
            assert not any(n.severity == "error" for n in notifications(app))
    finally:
        await client.aclose()


async def test_empty_rosters(make_fixture_transport, db_conn):
    from conftest import FIXED_NOW

    requests = []
    overrides = {
        "/drivers/": {"MRData": {"total": "0", "DriverTable": {"Drivers": []}}},
        "/constructors/": {"MRData": {"total": "0", "ConstructorTable": {"Constructors": []}}},
    }
    transport = make_fixture_transport(requests, overrides)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store)

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("p")
            await app.workers.wait_for_complete()
            await pilot.pause()

            screen = app.screen

            drivers_status = screen.query_one("#profiles-drivers-status", Static)
            assert drivers_status.display is True
            assert str(drivers_status.content) == "No drivers listed for season 2026."

            constructors_status = screen.query_one("#profiles-constructors-status", Static)
            assert constructors_status.display is True
            assert str(constructors_status.content) == "No constructors listed for season 2026."

            assert screen.query_one("#profiles-drivers-table", DataTable).display is False
            assert screen.query_one("#profiles-constructors-table", DataTable).display is False
            assert screen.query_one("#profiles-drivers-title", Static).display is True
            assert screen.query_one("#profiles-constructors-title", Static).display is True
    finally:
        await client.aclose()


async def test_stale_rosters_notify_once(db_conn, jolpica_payload, make_failing_transport):
    from conftest import FIXED_NOW

    from pitwall.cache.db import (
        set_refresh_log,
        upsert_constructor_standings,
        upsert_constructors,
        upsert_driver_standings,
        upsert_drivers,
        upsert_races,
    )
    from pitwall.models import (
        parse_constructor_standings,
        parse_constructors,
        parse_driver_standings,
        parse_drivers,
        parse_races,
    )

    old_fetched = datetime.datetime(2026, 6, 7, 8, 0, tzinfo=datetime.UTC)

    races = parse_races(jolpica_payload("races"))
    upsert_races(db_conn, races, season=2026)
    set_refresh_log(db_conn, "schedule:2026", old_fetched, record_count=len(races))

    drivers_std = parse_driver_standings(jolpica_payload("driverstandings"))
    upsert_driver_standings(db_conn, 2026, drivers_std)
    set_refresh_log(db_conn, "driver_standings:2026", old_fetched, record_count=len(drivers_std))

    constructors_std = parse_constructor_standings(jolpica_payload("constructorstandings"))
    upsert_constructor_standings(db_conn, 2026, constructors_std)
    set_refresh_log(db_conn, "constructor_standings:2026", old_fetched, record_count=len(constructors_std))

    drivers = parse_drivers(jolpica_payload("drivers"))
    upsert_drivers(db_conn, drivers, season=2026)
    set_refresh_log(db_conn, "drivers:2026", old_fetched, record_count=len(drivers))

    constructors = parse_constructors(jolpica_payload("constructors"))
    upsert_constructors(db_conn, constructors, season=2026)
    set_refresh_log(db_conn, "constructors:2026", old_fetched, record_count=len(constructors))

    requests = []
    transport = make_failing_transport(requests)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store)

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("p")
            await app.workers.wait_for_complete()
            await pilot.pause()

            screen = app.screen
            drivers_table = screen.query_one("#profiles-drivers-table", DataTable)
            constructors_table = screen.query_one("#profiles-constructors-table", DataTable)

            assert drivers_table.row_count == 23
            assert constructors_table.row_count == 11

            assert screen.query_one("#profiles-drivers-status", Static).display is False
            assert screen.query_one("#profiles-constructors-status", Static).display is False

            assert app.sub_title == "season 2026 · data as of 08:00 UTC · stale"

            warning_drivers_msgs = [
                n
                for n in notifications(app)
                if n.severity == "warning" and "Serving stale cached drivers (as of 08:00 UTC)." in n.message
            ]
            warning_constructors_msgs = [
                n
                for n in notifications(app)
                if n.severity == "warning" and "Serving stale cached constructors (as of 08:00 UTC)." in n.message
            ]
            assert len(warning_drivers_msgs) == 1
            assert len(warning_constructors_msgs) == 1

            await pilot.press("s")
            await pilot.pause()
            await pilot.press("p")
            await app.workers.wait_for_complete()
            await pilot.pause()

            warning_drivers_msgs_2 = [
                n
                for n in notifications(app)
                if n.severity == "warning" and "Serving stale cached drivers (as of 08:00 UTC)." in n.message
            ]
            warning_constructors_msgs_2 = [
                n
                for n in notifications(app)
                if n.severity == "warning" and "Serving stale cached constructors (as of 08:00 UTC)." in n.message
            ]
            assert len(warning_drivers_msgs_2) == 1
            assert len(warning_constructors_msgs_2) == 1
    finally:
        await client.aclose()


async def test_renders_with_empty_schedule(make_fixture_transport, db_conn):
    from conftest import FIXED_NOW

    requests = []
    overrides = {"races": {"MRData": {"total": "0", "RaceTable": {"Races": []}}}}
    transport = make_fixture_transport(requests, overrides)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store)

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("p")
            await app.workers.wait_for_complete()
            await pilot.pause()

            screen = app.screen
            assert screen.query_one("#profiles-drivers-table", DataTable).row_count == 23
            assert screen.query_one("#profiles-constructors-table", DataTable).row_count == 11
    finally:
        await client.aclose()


async def test_focus_and_nav_keys(injected_store):
    _conn, _client, store, requests = injected_store
    app = PitwallApp(config=AppConfig(season=2026), store=store)
    async with app.run_test(size=(80, 24)) as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()

        await pilot.press("p")
        await app.workers.wait_for_complete()
        await pilot.pause()

        drivers_table = app.screen.query_one("#profiles-drivers-table", DataTable)
        constructors_table = app.screen.query_one("#profiles-constructors-table", DataTable)
        assert app.focused is drivers_table

        await pilot.press("p")
        await pilot.pause()
        assert isinstance(app.screen, ProfilesScreen)

        await pilot.press("tab")
        await pilot.pause()
        assert app.focused is constructors_table

        assert constructors_table.cursor_row == 0
        await pilot.press("down")
        await pilot.pause()
        assert constructors_table.cursor_row == 1

        await pilot.press("shift+tab")
        await pilot.pause()
        assert app.focused is drivers_table

        assert drivers_table.cursor_row == 0
        await pilot.press("down")
        await pilot.pause()
        assert drivers_table.cursor_row == 1

        assert len(requests) == 5

        await pilot.press("n")
        await pilot.pause()
        assert isinstance(app.screen, StandingsScreen)

        await pilot.press("p")
        await pilot.pause()
        assert isinstance(app.screen, ProfilesScreen)
        assert app.screen.query_one("#profiles-drivers-table", DataTable).row_count == 23
        assert app.screen.query_one("#profiles-constructors-table", DataTable).row_count == 11
        assert len(requests) == 5

        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, ScheduleScreen)

        await pilot.press("p")
        await pilot.pause()
        assert isinstance(app.screen, ProfilesScreen)

        await pilot.press("q")
        await pilot.pause()


async def test_midload_wander_away(db_conn, make_gated_transport):
    from conftest import FIXED_NOW

    gate = asyncio.Event()
    requests = []
    transport = make_gated_transport(requests, gate)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store)

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            # (e) press p during load (season-loading state)
            await pilot.press("p")
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ProfilesScreen)
            status = screen.query_one("#profiles-status", Static)
            assert status.display is True
            assert str(status.content) == "Loading profiles…"

            # press s (back to schedule)
            await pilot.press("s")
            await pilot.pause()
            assert isinstance(app.screen, ScheduleScreen)

            # open the gate, await completion
            gate.set()
            await app.workers.wait_for_complete()
            await pilot.pause()

            # app.focused is the schedule screen's #schedule-table (inactive profiles screen did not steal focus)
            schedule_table = app.screen.query_one("#schedule-table", DataTable)
            assert app.focused is schedule_table

            # pressing p then shows the tables populated
            await pilot.press("p")
            await pilot.pause()
            assert app.screen is screen

            assert screen.query_one("#profiles-drivers-table", DataTable).row_count == 23
            assert screen.query_one("#profiles-constructors-table", DataTable).row_count == 11
    finally:
        gate.set()
        await client.aclose()


async def test_load_completes_on_profiles_screen(db_conn, make_gated_transport):
    from conftest import FIXED_NOW

    gate = asyncio.Event()
    requests = []
    transport = make_gated_transport(requests, gate)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    app = PitwallApp(config=AppConfig(season=2026), store=store)

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            # (f) press p during load and stay
            await pilot.press("p")
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ProfilesScreen)
            status = screen.query_one("#profiles-status", Static)
            assert status.display is True
            assert str(status.content) == "Loading profiles…"

            # open the gate, await completion
            gate.set()
            await app.workers.wait_for_complete()
            await pilot.pause()

            # app.focused is #profiles-drivers-table
            drivers_table = screen.query_one("#profiles-drivers-table", DataTable)
            assert app.focused is drivers_table
    finally:
        gate.set()
        await client.aclose()


def test_build_driver_rows_sorting():
    d1 = Driver(
        driver_id="alonso",
        permanent_number=14,
        code="ALO",
        url="http://...",
        given_name="Fernando",
        family_name="Alonso",
        date_of_birth=datetime.date(1981, 7, 29),
        nationality="Spanish",
    )
    d2 = Driver(
        driver_id="albon",
        permanent_number=23,
        code="ALB",
        url="http://...",
        given_name="Alexander",
        family_name="Albon",
        date_of_birth=datetime.date(1996, 3, 23),
        nationality="Thai",
    )
    d3 = Driver(
        driver_id="hamilton",
        permanent_number=44,
        code="HAM",
        url="http://...",
        given_name="Lewis",
        family_name="Hamilton",
        date_of_birth=datetime.date(1985, 1, 7),
        nationality="British",
    )
    d4 = Driver(
        driver_id="hulkenberg",
        permanent_number=27,
        code="HUL",
        url="http://...",
        given_name="Nico",
        family_name="Hülkenberg",
        date_of_birth=datetime.date(1987, 8, 19),
        nationality="German",
    )
    d5 = Driver(
        driver_id="piastri",
        permanent_number=81,
        code="PIA",
        url="http://...",
        given_name="Oscar",
        family_name="Piastri",
        date_of_birth=datetime.date(2001, 4, 6),
        nationality="Australian",
    )
    d6 = Driver(
        driver_id="perez",
        permanent_number=11,
        code="PER",
        url="http://...",
        given_name="Sergio",
        family_name="Pérez",
        date_of_birth=datetime.date(1990, 1, 26),
        nationality="Mexican",
    )
    # Shuffled input
    drivers = [d6, d4, d1, d5, d3, d2]
    rows = build_driver_rows(drivers)
    # Expected sorting by (family_name, given_name) code-point:
    # Albon, Alonso, Hamilton, Hülkenberg, Piastri, Pérez
    expected = [
        ("23", "Alexander Albon", "ALB", "Thai", "1996-03-23"),
        ("14", "Fernando Alonso", "ALO", "Spanish", "1981-07-29"),
        ("44", "Lewis Hamilton", "HAM", "British", "1985-01-07"),
        ("27", "Nico Hülkenberg", "HUL", "German", "1987-08-19"),
        ("81", "Oscar Piastri", "PIA", "Australian", "2001-04-06"),
        ("11", "Sergio Pérez", "PER", "Mexican", "1990-01-26"),
    ]
    assert rows == expected


def test_build_driver_rows_optionals():
    # A driver with all optional fields None
    d = Driver(
        driver_id="crawford",
        permanent_number=None,
        code=None,
        url=None,
        given_name="Jak",
        family_name="Crawford",
        date_of_birth=None,
        nationality=None,
    )
    rows = build_driver_rows([d])
    assert rows == [(EM_DASH, "Jak Crawford", EM_DASH, EM_DASH, EM_DASH)]


def test_build_driver_rows_fixtures(jolpica_payload):
    payload = jolpica_payload("drivers")
    drivers = parse_drivers(payload)
    rows = build_driver_rows(drivers)
    assert len(rows) == 23
    # index 7 Crawford row (all em-dashes for optional fields)
    assert rows[7] == (EM_DASH, "Jak Crawford", EM_DASH, EM_DASH, EM_DASH)
    # index 22 Verstappen
    assert rows[22] == ("3", "Max Verstappen", "VER", "Dutch", "1997-09-30")


def test_build_constructor_rows_sorting():
    c1 = Constructor(
        constructor_id="red_bull",
        url="http://...",
        name="Red Bull",
        nationality="Austrian",
    )
    c2 = Constructor(
        constructor_id="rb",
        url="http://...",
        name="RB F1 Team",
        nationality="Italian",
    )
    c3 = Constructor(
        constructor_id="alpine",
        url="http://...",
        name="Alpine F1 Team",
        nationality="French",
    )
    constructors = [c1, c3, c2]
    rows = build_constructor_rows(constructors)
    expected = [
        ("Alpine F1 Team", "French"),
        ("RB F1 Team", "Italian"),
        ("Red Bull", "Austrian"),
    ]
    assert rows == expected


def test_build_constructor_rows_fixtures(jolpica_payload):
    payload = jolpica_payload("constructors")
    constructors = parse_constructors(payload)
    rows = build_constructor_rows(constructors)
    assert len(rows) == 11
    # Check sorting order: RB F1 Team sorts before Red Bull
    names = [row[0] for row in rows]
    rb_idx = names.index("RB F1 Team")
    redbull_idx = names.index("Red Bull")
    assert rb_idx < redbull_idx
