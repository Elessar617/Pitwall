import datetime

import httpx
import pytest
from conftest import wrap_transport

from pitwall.api.jolpica import JolpicaClient
from pitwall.cache.db import (
    get_refresh_log,
    set_refresh_log,
    upsert_constructors,
    upsert_drivers,
    upsert_race_results,
    upsert_races,
)
from pitwall.cache.store import SeasonStore, Source
from pitwall.errors import JolpicaHttpError, JolpicaNetworkError
from pitwall.models import Constructor, Driver, Race


@pytest.mark.asyncio
async def test_store_empty_cache_fetches_persists_and_returns_network(db_conn, jolpica_payload) -> None:
    """AC-11: Empty cache triggers network fetch, persists results, and returns Source.NETWORK.

    Invariant: An empty cache must call the HTTP transport exactly once.
    Invariant: The result returned carries Source.NETWORK with fetched_at matching the mock clock.
    Invariant: An immediate subsequent read must return cached data (Source.CACHE) without extra network calls.
    """

    recorded_requests = []
    races_payload = jolpica_payload("races")

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=races_payload)

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)

    mock_now = datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)
    store = SeasonStore(db_conn, client, now=lambda: mock_now)

    # Act - first call (Cache Miss)
    result = await store.get_schedule(season=2026)

    # Assert network status and metadata
    assert result.source == Source.NETWORK
    assert result.fetched_at == mock_now
    assert len(result.data) == 22
    assert all(isinstance(r, Race) for r in result.data)
    assert len(recorded_requests) == 1

    # Assert persistence in database
    db_refresh_time = get_refresh_log(db_conn, "schedule:2026")
    assert db_refresh_time == mock_now

    # Act - second call (Cache Hit)
    result_repeat = await store.get_schedule(season=2026)

    # Assert read-through from cache
    assert result_repeat.source == Source.CACHE
    assert result_repeat.fetched_at == mock_now
    assert result_repeat.data == result.data
    assert len(recorded_requests) == 1  # Verify request count remains unchanged


@pytest.mark.asyncio
async def test_store_pre_seeded_fresh_cache_skips_transport(db_conn, jolpica_payload) -> None:
    """AC-11: SeasonStore retrieves data from fresh cache without issuing transport requests.

    Invariant: If the cache contains data and the scope's last refresh timestamp is within
    the freshness duration (no intermediate sessions, age < 24h), no HTTP calls are issued.
    """

    races = jolpica_payload("races")
    from pitwall.models import parse_races as parser

    parsed_races = parser(races)
    upsert_races(db_conn, parsed_races)

    mock_now = datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)
    set_refresh_log(db_conn, "schedule:2026", mock_now, record_count=len(parsed_races))

    # Initialize store with a client configured with a failing mock transport to prove it is not called
    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("Network transport should not be invoked for a fresh cache read.")

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: mock_now)

    # Act
    result = await store.get_schedule(season=2026)

    # Assert
    assert result.source == Source.CACHE
    assert result.fetched_at == mock_now
    assert len(result.data) == 22


@pytest.mark.asyncio
async def test_store_scope_wiring_staleness_isolation(db_conn, jolpica_payload) -> None:
    """AC-12: Staleness evaluations are isolated to their respective scopes.

    Assumption: Schedule/Races are configured. Round 1 has sessions completed in the past.
    Round 2 has a session start strictly between the cache's fetched_at and now.
    Invariant: Querying round 1's results cache should hit Source.CACHE (unaffected by round 2 session).
    Invariant: Querying season-wide schedule cache should hit Source.NETWORK (invalidated by round 2 session).
    """

    # Seed schedule with custom session starts
    # Round 1: sessions long in the past
    # Round 2: session starting inside the staleness window
    races = jolpica_payload("races")
    from pitwall.models import parse_races as parser_races

    parsed_races = parser_races(races)

    from dataclasses import replace

    # Round 1 (index 0) - past sessions
    r1 = replace(
        parsed_races[0],
        qualifying=datetime.datetime(2026, 3, 7, 12, 0, tzinfo=datetime.UTC),
        start=datetime.datetime(2026, 3, 8, 12, 0, tzinfo=datetime.UTC),
    )
    # Round 2 (index 1) - session in the middle of our window
    r2 = replace(
        parsed_races[1],
        qualifying=datetime.datetime(2026, 6, 9, 11, 0, tzinfo=datetime.UTC),  # Inside window (10:00 to 12:00)
    )

    upsert_races(db_conn, [r1, r2, *parsed_races[2:]])

    # Seed results for Round 1
    results_payload = jolpica_payload("results")
    from pitwall.models import parse_results as parser_results

    parsed_results = parser_results(results_payload)
    upsert_race_results(db_conn, season=2026, round=1, results=parsed_results)

    # Set cache refresh log for both scopes to fetched_at (10:00:00)
    fetched_at = datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)
    set_refresh_log(db_conn, "schedule:2026", fetched_at, record_count=len(parsed_races))
    set_refresh_log(db_conn, "results:2026:1", fetched_at, record_count=len(parsed_results))

    # Setup store with mock clock set to now (12:00:00)
    # Window: 10:00:00 to 12:00:00. Round 2 session starts at 11:00:00.
    now_clock = datetime.datetime(2026, 6, 9, 12, 0, tzinfo=datetime.UTC)

    recorded_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=jolpica_payload("races"))

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: now_clock)

    # Act: Request Round 1 results.
    # Because Round 1 has no sessions in the window, its cache must remain fresh.
    results_result = await store.get_race_results(season=2026, round=1)

    assert results_result.source == Source.CACHE
    assert results_result.fetched_at == fetched_at
    assert len(recorded_requests) == 0

    # Act: Request season schedule.
    # Because a session start for Round 2 is strictly in the window, the season schedule is stale.
    schedule_result = await store.get_schedule(season=2026)

    assert schedule_result.source == Source.NETWORK
    assert schedule_result.fetched_at == now_clock
    assert len(recorded_requests) == 1


@pytest.mark.asyncio
async def test_store_stale_cache_with_failing_transport_serves_degraded(db_conn, jolpica_payload) -> None:
    """AC-13: When cache is stale but network fails, store returns stale data with Source.STALE_CACHE.

    Invariant: Serve stale cache data rather than throwing an exception when a local cache exists.
    Invariant: The returned result's fetched_at must be the original, unmodified cache timestamp.
    """

    # Seed DB with parsed races
    from pitwall.models import parse_races as parser

    parsed_races = parser(jolpica_payload("races"))
    upsert_races(db_conn, parsed_races)

    # Seed cache as stale (age >= 24h)
    now_clock = datetime.datetime(2026, 6, 10, 10, 0, tzinfo=datetime.UTC)
    fetched_at = now_clock - datetime.timedelta(hours=25)
    set_refresh_log(db_conn, "schedule:2026", fetched_at, record_count=len(parsed_races))

    # Mock transport returning a 500 status code
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: now_clock)

    # Act
    result = await store.get_schedule(season=2026)

    # Assert
    assert result.source == Source.STALE_CACHE
    assert result.fetched_at == fetched_at
    assert len(result.data) == 22


@pytest.mark.asyncio
async def test_store_empty_cache_with_failing_transport_propagates_original_error(db_conn) -> None:
    """AC-13: Empty cache + network failure propagates the original error.

    Invariant: When no cache exists to serve degraded, the exception must propagate to the caller.
    """

    # Mock transport raising a connection exception
    def handler(request: httpx.Request) -> httpx.Response:
        exc = httpx.ConnectError("Connection failed")
        raise exc

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: datetime.datetime.now(datetime.UTC))

    # Act & Assert
    with pytest.raises(JolpicaNetworkError):
        await store.get_schedule(season=2026)


@pytest.mark.asyncio
async def test_store_coverage_for_remaining_methods(db_conn, jolpica_payload) -> None:
    """Exercise remaining store methods to verify coverage and function."""

    payloads = {
        "driverstandings": jolpica_payload("driverstandings"),
        "constructorstandings": jolpica_payload("constructorstandings"),
        "drivers": jolpica_payload("drivers"),
        "constructors": jolpica_payload("constructors"),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        url_path = request.url.path
        if "driverstandings" in url_path:
            return httpx.Response(200, json=payloads["driverstandings"])
        elif "constructorstandings" in url_path:
            return httpx.Response(200, json=payloads["constructorstandings"])
        elif "drivers" in url_path:
            return httpx.Response(200, json=payloads["drivers"])
        elif "constructors" in url_path:
            return httpx.Response(200, json=payloads["constructors"])
        return httpx.Response(404)

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)
    mock_now = datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)
    store = SeasonStore(db_conn, client, now=lambda: mock_now)

    # Call get_driver_standings
    res_ds = await store.get_driver_standings(season=2026)
    assert res_ds.source == Source.NETWORK
    assert len(res_ds.data) == 22

    # Call get_constructor_standings
    res_cs = await store.get_constructor_standings(season=2026)
    assert res_cs.source == Source.NETWORK
    assert len(res_cs.data) == 11

    # Call get_drivers
    res_d = await store.get_drivers(season=2026)
    assert res_d.source == Source.NETWORK
    assert len(res_d.data) == 23

    # Call get_constructors
    res_c = await store.get_constructors(season=2026)
    assert res_c.source == Source.NETWORK
    assert len(res_c.data) == 11


@pytest.mark.asyncio
async def test_store_drivers_and_constructors_only_return_entities_for_requested_season(db_conn) -> None:
    """Adversary Finding 1: Season-scoped driver/constructor cache reads return cross-season data.

    Cache reads for drivers:{season} and constructors:{season} must return only entities
    fetched for that specific season, even if other entities exist globally.
    """
    driver_2026 = Driver(
        driver_id="alpha",
        permanent_number=1,
        code="ALP",
        url="http://alpha.com",
        given_name="Alpha",
        family_name="Driver",
        date_of_birth=datetime.date(1990, 1, 1),
        nationality="British",
    )
    driver_2025 = Driver(
        driver_id="beta",
        permanent_number=2,
        code="BET",
        url="http://beta.com",
        given_name="Beta",
        family_name="Driver",
        date_of_birth=datetime.date(1991, 2, 2),
        nationality="French",
    )

    constructor_2026 = Constructor(
        constructor_id="team_a",
        url="http://team_a.com",
        name="Team A",
        nationality="British",
    )
    constructor_2025 = Constructor(
        constructor_id="team_b",
        url="http://team_b.com",
        name="Team B",
        nationality="French",
    )

    mock_now = datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)

    # Pre-populate drivers/constructors in database
    upsert_drivers(db_conn, [driver_2026], season=2026)
    set_refresh_log(db_conn, "drivers:2026", mock_now, record_count=1)

    upsert_drivers(db_conn, [driver_2025], season=2025)
    set_refresh_log(db_conn, "drivers:2025", mock_now, record_count=1)

    upsert_constructors(db_conn, [constructor_2026], season=2026)
    set_refresh_log(db_conn, "constructors:2026", mock_now, record_count=1)

    upsert_constructors(db_conn, [constructor_2025], season=2025)
    set_refresh_log(db_conn, "constructors:2025", mock_now, record_count=1)

    # Initialize store with a client configured with a failing mock transport to prove it is not called
    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("Network transport should not be invoked for a fresh cache read.")

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: mock_now)

    # Act
    drivers_result = await store.get_drivers(season=2026)
    constructors_result = await store.get_constructors(season=2026)

    # Assert
    assert [d.driver_id for d in drivers_result.data] == ["alpha"]
    assert [c.constructor_id for c in constructors_result.data] == ["team_a"]


@pytest.mark.asyncio
async def test_store_empty_table_with_fresh_log_triggers_fetch(db_conn, jolpica_payload) -> None:
    """Adversary Finding 2: A refresh log entry without table rows must not count as cache presence.

    If the schedule table is empty, even with a fresh refresh_log entry, the store must trigger
    a network fetch.
    """
    recorded_requests = []
    races_payload = jolpica_payload("races")

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=races_payload)

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)

    mock_now = datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)
    set_refresh_log(db_conn, "schedule:2026", mock_now)

    store = SeasonStore(db_conn, client, now=lambda: mock_now)

    # Act
    result = await store.get_schedule(season=2026)

    # Assert
    assert result.source == Source.NETWORK
    assert len(recorded_requests) == 1


@pytest.mark.asyncio
async def test_store_empty_table_on_network_failure_propagates_error(db_conn) -> None:
    """Adversary Finding 2: On network failure with an empty table, the error propagates.

    Even if a refresh_log entry exists, if the data table is empty and the network fetch fails,
    we must propagate the network error instead of returning Source.STALE_CACHE with [].
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)

    mock_now = datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)
    set_refresh_log(db_conn, "schedule:2026", mock_now)

    store = SeasonStore(db_conn, client, now=lambda: mock_now)

    # Act & Assert
    with pytest.raises(JolpicaHttpError):
        await store.get_schedule(season=2026)


@pytest.mark.asyncio
async def test_successful_empty_fetch_becomes_cache_hit_and_stale_serves(db_conn) -> None:
    """Verify that a successful empty fetch becomes a cache hit on the second call, stale-serves on outage, and triggers fetch if bogus."""
    # Invariant: A successful fetch returning [] must be stored as a cache hit so that
    # the second call returns Source.CACHE with [] and does not hit the network.
    # Invariant: During an outage, a known-empty scope must serve stale data [] instead of erroring.
    # Invariant: A refresh_log row without a recorded fetch (bogus log) must still trigger a fetch.

    recorded_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        empty_payload = {
            "MRData": {
                "total": "0",
                "limit": "30",
                "offset": "0",
                "RaceTable": {"season": "2026", "round": "99", "Races": []},
            }
        }
        return httpx.Response(200, json=empty_payload)

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)

    mock_now = datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)
    store = SeasonStore(db_conn, client, now=lambda: mock_now)

    # 1. First call: Cache Miss, successful fetch returning []
    result = await store.get_race_results(season=2026, round=99)
    assert result.source == Source.NETWORK
    assert result.data == []
    assert len(recorded_requests) == 1

    # 2. Second call: Cache Hit, returns Source.CACHE with []
    result_repeat = await store.get_race_results(season=2026, round=99)
    assert result_repeat.source == Source.CACHE
    assert result_repeat.data == []
    assert len(recorded_requests) == 1  # No additional network requests

    # 3. Cache is stale (outage scenario)
    # We set clock to 25 hours later, making the cache stale.
    stale_time = mock_now + datetime.timedelta(hours=25)

    # Configure transport to fail
    def failing_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection failed")  # noqa: TRY003

    failing_client = JolpicaClient(transport=wrap_transport(failing_handler))
    store_stale = SeasonStore(db_conn, failing_client, now=lambda: stale_time)

    # Stale read should serve stale cache with [] instead of erroring
    result_stale = await store_stale.get_race_results(season=2026, round=99)
    assert result_stale.source == Source.STALE_CACHE
    assert result_stale.data == []

    # 4. Bogus log case: refresh_log has row but no recorded fetch
    # We clear the database connection or use a new one to simulate bogus state
    # Actually, we can just seed the refresh log with a bogus entry for a different round,
    # e.g., results:2026:98, but the results table has no rows.
    # No fetch was ever recorded for round 98 on this store instance.
    set_refresh_log(db_conn, "results:2026:98", mock_now)

    # Try fetching round 98 (with the original client, which returns empty payload)
    recorded_requests.clear()
    store_bogus = SeasonStore(db_conn, client, now=lambda: mock_now)
    result_bogus = await store_bogus.get_race_results(season=2026, round=98)
    # Since there was no recorded fetch for round 98 on this run/state, it must trigger a network fetch
    assert result_bogus.source == Source.NETWORK
    assert len(recorded_requests) == 1


@pytest.mark.asyncio
async def test_store_empty_schedule_refresh_replace_semantics(db_conn) -> None:
    """Verify that a successful empty schedule refresh replaces the schedule scope in the store."""
    import datetime

    from pitwall.api.jolpica import JolpicaClient
    from pitwall.cache.store import SeasonStore, Source
    from pitwall.models import Circuit, Race

    circuit = Circuit(
        circuit_id="melbourne",
        url="http://m.com",
        circuit_name="Melbourne",
        lat=-37.8497,
        long=144.968,
        locality="Melbourne",
        country="Australia",
    )
    round_1 = Race(
        season=2026,
        round=1,
        url="http://r.com",
        race_name="GP 1",
        circuit=circuit,
        start=datetime.datetime(2026, 3, 8, 4, 0, tzinfo=datetime.UTC),
        fp1=None,
        fp2=None,
        fp3=None,
        qualifying=None,
        sprint=None,
        sprint_qualifying=None,
    )

    # 1. Seed round_1 in races
    upsert_races(db_conn, [round_1])

    # 2. Set refresh log as stale (25h ago)
    mock_now = datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)
    stale_time = mock_now - datetime.timedelta(hours=25)
    set_refresh_log(db_conn, "schedule:2026", stale_time, record_count=1)

    # Mock transport returning empty schedule
    recorded_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        empty_payload = {
            "MRData": {
                "total": "0",
                "limit": "30",
                "offset": "0",
                "RaceTable": {"season": "2026", "Races": []},
            }
        }
        return httpx.Response(200, json=empty_payload)

    transport = wrap_transport(handler)
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: mock_now)

    # First call: triggers network fetch (Source.NETWORK) and returns []
    res1 = await store.get_schedule(season=2026)
    assert res1.source == Source.NETWORK
    assert res1.data == []
    assert len(recorded_requests) == 1

    # Second call: returns CACHE []
    res2 = await store.get_schedule(season=2026)
    assert res2.source == Source.CACHE
    assert res2.data == []
    assert len(recorded_requests) == 1

    # Outage 25 hours later serves STALE_CACHE with []
    outage_time = mock_now + datetime.timedelta(hours=25)

    def failing_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Outage")

    failing_client = JolpicaClient(transport=wrap_transport(failing_handler))
    store_outage = SeasonStore(db_conn, failing_client, now=lambda: outage_time)

    res3 = await store_outage.get_schedule(season=2026)
    assert res3.source == Source.STALE_CACHE
    assert res3.data == []


@pytest.mark.asyncio
async def test_store_cross_helper_atomicity(db_conn, jolpica_payload) -> None:
    """Verify that a SeasonStore refresh failure leaves global profiles and logs untouched.

    iter15 re-pin (CARRY-POSITION-TEXT): present-but-null required strings now fail
    the PARSE boundary (DataParseError -> stale-serve) instead of reaching SQLite,
    so the store degrades to STALE_CACHE while all cached state stays untouched.
    DB-level rollback atomicity remains covered by the transactional tests in
    tests/test_db.py.
    """
    import copy
    import datetime

    from pitwall.cache.db import (
        get_constructor,
        get_driver,
        select_driver_standings,
        select_race_results,
    )
    from pitwall.models import Circuit, Constructor, Driver, DriverStanding, Race, RaceResult

    # --- 1. Driver Standings Store Atomicity ---
    # Setup: Seed baseline profiles and standings.
    old_driver = Driver(
        driver_id="shared",
        permanent_number=10,
        code="SHD",
        url="http://shared.com",
        given_name="OldName",
        family_name="OldFamily",
        date_of_birth=datetime.date(1990, 1, 1),
        nationality="British",
    )
    old_constructor = Constructor(
        constructor_id="shared_team",
        url="http://shared-c.com",
        name="OldTeam",
        nationality="British",
    )
    upsert_drivers(db_conn, [old_driver])
    upsert_constructors(db_conn, [old_constructor])

    ds_old = DriverStanding(
        position=1,
        position_text="1",
        points=10.0,
        wins=1,
        driver=old_driver,
        constructors=[old_constructor],
    )
    from pitwall.cache.db import upsert_driver_standings

    upsert_driver_standings(db_conn, season=2026, standings=[ds_old])

    stale_time = datetime.datetime(2026, 6, 8, 10, 0, tzinfo=datetime.UTC)
    set_refresh_log(db_conn, "driver_standings:2026", stale_time, record_count=1)

    # Configure mock transport to return standings payload with new profile info,
    # but a bad standing entry with positionText=null (None) to trigger DB constraint failure.
    standings_payload = copy.deepcopy(jolpica_payload("driverstandings"))
    standing_list = standings_payload["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"]
    # Clear other entries to keep it simple, leaving only 2 entries
    standing_list[0]["Driver"]["driverId"] = "shared"
    standing_list[0]["Driver"]["givenName"] = "NewNameFromFailedRefresh"
    standing_list[0]["Driver"]["familyName"] = "NewFamily"
    standing_list[0]["Constructors"][0]["constructorId"] = "shared_team"
    standing_list[0]["Constructors"][0]["name"] = "NewTeam"
    # Make it fail by setting positionText to null (None)
    standing_list[0]["positionText"] = None

    def standings_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=standings_payload)

    mock_now = datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)
    client1 = JolpicaClient(transport=wrap_transport(standings_handler))
    store1 = SeasonStore(db_conn, client1, now=lambda: mock_now)

    # The fetch happens (mock_now is 24h+ past stale_time) but the parse
    # boundary rejects the null positionText -> the store serves stale cache.
    result1 = await store1.get_driver_standings(season=2026)
    assert result1.source is Source.STALE_CACHE

    # Assert: Check that global profiles, standings, and refresh log are untouched and no transaction is left open.
    assert db_conn.in_transaction is False
    driver = get_driver(db_conn, "shared")
    assert driver is not None
    assert driver.given_name == "OldName"
    constructor = get_constructor(db_conn, "shared_team")
    assert constructor is not None
    assert constructor.name == "OldTeam"
    assert select_driver_standings(db_conn, season=2026) == [ds_old]
    assert get_refresh_log(db_conn, "driver_standings:2026") == stale_time

    # --- 2. Race Results Store Atomicity ---
    # Setup: Seed circuit, race, and baseline results.
    circuit = Circuit(
        circuit_id="melbourne",
        url="http://m.com",
        circuit_name="Melbourne",
        lat=-37.8497,
        long=144.968,
        locality="Melbourne",
        country="Australia",
    )
    race = Race(
        season=2026,
        round=1,
        url="http://r.com",
        race_name="Melbourne GP",
        circuit=circuit,
        start=datetime.datetime(2026, 3, 8, 12, 0, tzinfo=datetime.UTC),
        fp1=None,
        fp2=None,
        fp3=None,
        qualifying=None,
        sprint=None,
        sprint_qualifying=None,
    )
    upsert_races(db_conn, [race])

    res_old = RaceResult(
        number=1,
        position=1,
        position_text="1",
        points=25.0,
        driver=old_driver,
        constructor=old_constructor,
        grid=1,
        laps=58,
        status="Finished",
        time_millis=None,
        time_str=None,
        fastest_lap=None,
    )
    upsert_race_results(db_conn, season=2026, round=1, results=[res_old])
    set_refresh_log(db_conn, "results:2026:1", stale_time, record_count=1)

    # Configure mock transport to return results payload with new profile info,
    # but a bad result entry with positionText=null (None) to trigger DB constraint failure.
    results_payload = copy.deepcopy(jolpica_payload("results"))
    results_list = results_payload["MRData"]["RaceTable"]["Races"][0]["Results"]
    results_list[0]["Driver"]["driverId"] = "shared"
    results_list[0]["Driver"]["givenName"] = "NewNameFromFailedRefreshResults"
    results_list[0]["Driver"]["familyName"] = "NewFamilyResults"
    results_list[0]["Constructor"]["constructorId"] = "shared_team"
    results_list[0]["Constructor"]["name"] = "NewTeamResults"
    results_list[0]["positionText"] = None

    def results_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=results_payload)

    client2 = JolpicaClient(transport=wrap_transport(results_handler))
    store2 = SeasonStore(db_conn, client2, now=lambda: mock_now)

    # iter15 re-pin: the parse boundary rejects the null field -> stale-serve.
    result2 = await store2.get_race_results(season=2026, round=1)
    assert result2.source is Source.STALE_CACHE

    # Assert: Check that global profiles, race results, and refresh log are untouched and no transaction is left open.
    assert db_conn.in_transaction is False
    driver2 = get_driver(db_conn, "shared")
    assert driver2 is not None
    assert driver2.given_name == "OldName"
    constructor2 = get_constructor(db_conn, "shared_team")
    assert constructor2 is not None
    assert constructor2.name == "OldTeam"
    assert select_race_results(db_conn, season=2026, round=1) == [res_old]
    assert get_refresh_log(db_conn, "results:2026:1") == stale_time


async def test_null_position_text_degrades_to_stale_serve(db_conn, jolpica_payload):
    """iter15 CARRY-POSITION-TEXT: present-but-null strings hit the parse boundary,
    so the store degrades to stale-serve instead of raising sqlite3.IntegrityError."""
    import copy
    import datetime

    from pitwall.api.jolpica import JolpicaClient
    from pitwall.cache.db import set_refresh_log, upsert_driver_standings
    from pitwall.cache.store import Source
    from pitwall.models import parse_driver_standings

    good = jolpica_payload("driverstandings")
    # Seed the cache with good data marked stale.
    drivers = parse_driver_standings(good)
    upsert_driver_standings(db_conn, 2026, drivers)
    set_refresh_log(
        db_conn,
        "driver_standings:2026",
        datetime.datetime(2026, 6, 7, 8, 0, tzinfo=datetime.UTC),
        record_count=len(drivers),
    )

    evil = copy.deepcopy(good)
    evil["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0]["positionText"] = None

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=evil)

    from conftest import wrap_transport

    client = JolpicaClient(transport=wrap_transport(handler))
    from pitwall.cache.store import SeasonStore

    store = SeasonStore(db_conn, client, now=lambda: datetime.datetime(2026, 6, 9, 14, 30, tzinfo=datetime.UTC))
    result = await store.get_driver_standings(2026)
    assert result.source is Source.STALE_CACHE
    await client.aclose()
