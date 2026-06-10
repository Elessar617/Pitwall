import random
from dataclasses import replace
from pathlib import Path

from pitwall.cache.db import (
    connect,
    get_constructor,
    get_driver,
    init_schema,
    select_constructor_standings,
    select_constructors,
    select_driver_standings,
    select_drivers,
    select_race_results,
    select_races,
    upsert_constructor_standings,
    upsert_constructors,
    upsert_driver_standings,
    upsert_drivers,
    upsert_race_results,
    upsert_races,
)
from pitwall.models import (
    parse_constructor_standings,
    parse_constructors,
    parse_driver_standings,
    parse_drivers,
    parse_races,
    parse_results,
)


def test_init_schema_idempotency(tmp_path: Path) -> None:
    """AC-10: Schema initialization is idempotent and maintains versioning invariants.

    Invariant: Repeated initialization on a single connection must not fail,
    raise tables-already-exist exceptions, or alter the target schema version (user_version = 1).
    """
    db_file = tmp_path / "pitwall.db"
    conn = connect(str(db_file))
    try:
        # Assert initial schema creation is successful
        init_schema(conn)

        # Assert repeated schema creation does not error
        init_schema(conn)

        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version;")
        version = cursor.fetchone()[0]
        cursor.close()

        assert version == 1
    finally:
        # Ownership & Lifetime: Explicitly close connection to prevent unclosed connection warnings.
        conn.close()


def test_entity_upsert_select_round_trip(db_conn, jolpica_payload) -> None:
    """AC-10: Per-entity upsert and select return identical model representation.

    Assumption: We parse real fixtures representing schedule (races), drivers, constructors,
    driver standings, constructor standings, and race results, and perform full serialization
    and deserialization cycles.
    Invariant: Re-upserting identical keys with modified fields performs in-place update,
    preserving total table row counts and returning modified data.
    """
    conn = db_conn

    # --- 1. Races ---
    races = parse_races(jolpica_payload("races"))
    upsert_races(conn, races)
    selected_races = select_races(conn, season=2026)
    assert len(selected_races) == len(races)
    assert selected_races == races

    # Modify FP1 time on the first race (frozen model, so replace is used)
    modified_race = replace(races[0], url="https://updated-race-url.com")
    upsert_races(conn, [modified_race, *races[1:]])
    selected_races_after = select_races(conn, season=2026)
    assert len(selected_races_after) == len(races)
    assert selected_races_after[0].url == "https://updated-race-url.com"

    # --- 2. Drivers ---
    drivers = parse_drivers(jolpica_payload("drivers"))
    upsert_drivers(conn, drivers)
    selected_drivers = select_drivers(conn)
    assert len(selected_drivers) == len(drivers)
    # Compare sorted by driver_id to avoid ordering issues
    assert sorted(selected_drivers, key=lambda d: d.driver_id) == sorted(drivers, key=lambda d: d.driver_id)

    modified_driver = replace(drivers[0], given_name="SurgicallyUpdatedName")
    upsert_drivers(conn, [modified_driver])
    selected_drivers_after = select_drivers(conn)
    assert len(selected_drivers_after) == len(drivers)
    retrieved_modified_driver = get_driver(conn, modified_driver.driver_id)
    assert retrieved_modified_driver is not None
    assert retrieved_modified_driver.given_name == "SurgicallyUpdatedName"

    # --- 3. Constructors ---
    constructors = parse_constructors(jolpica_payload("constructors"))
    upsert_constructors(conn, constructors)
    selected_constructors = select_constructors(conn)
    assert len(selected_constructors) == len(constructors)
    assert sorted(selected_constructors, key=lambda c: c.constructor_id) == sorted(
        constructors, key=lambda c: c.constructor_id
    )

    modified_constructor = replace(constructors[0], name="SurgicallyUpdatedConstructor")
    upsert_constructors(conn, [modified_constructor])
    selected_constructors_after = select_constructors(conn)
    assert len(selected_constructors_after) == len(constructors)
    retrieved_modified_constructor = get_constructor(conn, modified_constructor.constructor_id)
    assert retrieved_modified_constructor is not None
    assert retrieved_modified_constructor.name == "SurgicallyUpdatedConstructor"

    # --- 4. Driver Standings ---
    # Standings have foreign keys referencing drivers and constructors.
    # Because referential integrity is enabled (PRAGMA foreign_keys), upsert_drivers and
    # upsert_constructors must run first.
    standings = parse_driver_standings(jolpica_payload("driverstandings"))
    upsert_driver_standings(conn, season=2026, standings=standings)
    selected_standings = select_driver_standings(conn, season=2026)
    assert len(selected_standings) == len(standings)
    assert selected_standings == standings

    modified_standing = replace(standings[0], points=999.5)
    upsert_driver_standings(conn, season=2026, standings=[modified_standing, *standings[1:]])
    selected_standings_after = select_driver_standings(conn, season=2026)
    assert len(selected_standings_after) == len(standings)
    assert selected_standings_after[0].points == 999.5

    # --- 5. Constructor Standings ---
    c_standings = parse_constructor_standings(jolpica_payload("constructorstandings"))
    upsert_constructor_standings(conn, season=2026, standings=c_standings)
    selected_c_standings = select_constructor_standings(conn, season=2026)
    assert len(selected_c_standings) == len(c_standings)
    assert selected_c_standings == c_standings

    modified_c_standing = replace(c_standings[0], points=888.0)
    upsert_constructor_standings(conn, season=2026, standings=[modified_c_standing, *c_standings[1:]])
    selected_c_standings_after = select_constructor_standings(conn, season=2026)
    assert len(selected_c_standings_after) == len(c_standings)
    assert selected_c_standings_after[0].points == 888.0

    # --- 6. Race Results ---
    results = parse_results(jolpica_payload("results"))
    upsert_race_results(conn, season=2026, round=1, results=results)
    selected_results = select_race_results(conn, season=2026, round=1)
    assert len(selected_results) == len(results)
    assert selected_results == results

    modified_result = replace(results[0], grid=99)
    upsert_race_results(conn, season=2026, round=1, results=[modified_result, *results[1:]])
    selected_results_after = select_race_results(conn, season=2026, round=1)
    assert len(selected_results_after) == len(results)
    assert selected_results_after[0].grid == 99


def test_ac05_asymmetry_and_insertion_order_independence(tmp_path: Path, jolpica_payload) -> None:
    """AC-05: Id-keyed entity retrieval operates independently of list positions and asymmetry.

    Invariant: A driver present in drivers but absent from standings must be retrievable by profile query.
    Invariant: Standings lookups must be keyed on driver_id/constructor_id, not order index.
    Invariant: Shuffling the input insertion order produces identical retrieved collections.
    """
    db_file_1 = tmp_path / "pitwall_order_1.db"
    db_file_2 = tmp_path / "pitwall_order_2.db"

    # Ownership & Lifetime: Open both connections and guarantee teardown closing.
    conn_1 = connect(str(db_file_1))
    try:
        init_schema(conn_1)

        conn_2 = connect(str(db_file_2))
        try:
            init_schema(conn_2)

            drivers = parse_drivers(jolpica_payload("drivers"))
            standings = parse_driver_standings(jolpica_payload("driverstandings"))
            constructors = parse_constructors(jolpica_payload("constructors"))

            # 23 drivers but 22 standings rows in the F1 fixtures
            assert len(drivers) == 23
            assert len(standings) == 22

            # Pre-seed dependencies
            upsert_constructors(conn_1, constructors)
            upsert_drivers(conn_1, drivers)
            upsert_driver_standings(conn_1, season=2026, standings=standings)

            # Identify the standings-absent driver using python set arithmetic
            driver_ids_in_standings = {s.driver.driver_id for s in standings}
            driver_ids_in_drivers = {d.driver_id for d in drivers}
            absent_driver_ids = driver_ids_in_drivers - driver_ids_in_standings
            assert len(absent_driver_ids) == 1
            absent_driver_id = next(iter(absent_driver_ids))

            # Assert profile retrieval succeeds for the driver absent from standings
            absent_driver = get_driver(conn_1, absent_driver_id)
            assert absent_driver is not None
            assert absent_driver.driver_id == absent_driver_id

            shuffled_drivers = list(drivers)
            shuffled_standings = list(standings)

            # Seed local random generator for deterministic shuffling in tests
            rng = random.Random(42)  # noqa: S311
            rng.shuffle(shuffled_drivers)
            rng.shuffle(shuffled_standings)

            # Seed dependencies and shuffled lists
            upsert_constructors(conn_2, constructors)
            upsert_drivers(conn_2, shuffled_drivers)
            upsert_driver_standings(conn_2, season=2026, standings=shuffled_standings)

            # Select from both databases and verify identity representation
            selected_drivers_1 = select_drivers(conn_1)
            selected_drivers_2 = select_drivers(conn_2)

            selected_standings_1 = select_driver_standings(conn_1, season=2026)
            selected_standings_2 = select_driver_standings(conn_2, season=2026)

            # Lists must contain exactly the same objects, ordered identically (by PK)
            assert selected_drivers_1 == selected_drivers_2
            assert selected_standings_1 == selected_standings_2
        finally:
            conn_2.close()
    finally:
        conn_1.close()


def test_season_roster_shared_ids_do_not_leak_or_delete_cross_season(db_conn) -> None:
    """Verify upserting same driver/constructor IDs in a newer season does not delete older season memberships."""
    # Invariant: Roster memberships are season-specific. Upserting a driver in season 2026
    # must not delete the driver's membership in season 2025, even if they share the same ID.
    import datetime

    from pitwall.models import Constructor, Driver

    conn = db_conn

    driver_2025 = Driver(
        driver_id="shared_driver",
        permanent_number=1,
        code="SHA",
        url="http://shared.com",
        given_name="Season2025",
        family_name="Driver",
        date_of_birth=datetime.date(1990, 1, 1),
        nationality="British",
    )
    driver_2026 = Driver(
        driver_id="shared_driver",
        permanent_number=1,
        code="SHA",
        url="http://shared.com",
        given_name="Season2026",
        family_name="Driver",
        date_of_birth=datetime.date(1990, 1, 1),
        nationality="British",
    )

    constructor_2025 = Constructor(
        constructor_id="shared_constructor",
        url="http://shared.com",
        name="Season2025 Team",
        nationality="British",
    )
    constructor_2026 = Constructor(
        constructor_id="shared_constructor",
        url="http://shared.com",
        name="Season2026 Team",
        nationality="British",
    )

    # 1. Upsert season 2025 rosters
    upsert_drivers(conn, [driver_2025], season=2025)
    upsert_constructors(conn, [constructor_2025], season=2025)

    # Verify 2025 memberships are present
    assert [d.driver_id for d in select_drivers(conn, season=2025)] == ["shared_driver"]
    assert [c.constructor_id for c in select_constructors(conn, season=2025)] == ["shared_constructor"]

    # 2. Upsert season 2026 rosters
    upsert_drivers(conn, [driver_2026], season=2026)
    upsert_constructors(conn, [constructor_2026], season=2026)

    # Verify 2026 memberships are present
    assert [d.driver_id for d in select_drivers(conn, season=2026)] == ["shared_driver"]
    assert [c.constructor_id for c in select_constructors(conn, season=2026)] == ["shared_constructor"]

    # Invariant check: Verify 2025 memberships were NOT deleted or cascade deleted
    assert [d.driver_id for d in select_drivers(conn, season=2025)] == ["shared_driver"]
    assert [c.constructor_id for c in select_constructors(conn, season=2025)] == ["shared_constructor"]


def test_shrunken_scope_refresh_replaces_entire_scope(db_conn) -> None:
    """Verify that whole-scope refreshes remove rows absent from the latest payload, while leaving other scopes untouched."""
    # Invariant: Refreshing a scope (e.g. drivers, constructors, race results, standings)
    # must replace all entries for that specific scope in the database with the new payload,
    # ensuring no stale records remain, while preserving entries in other scopes (e.g. other seasons/rounds).
    import datetime

    from pitwall.models import Circuit, Constructor, ConstructorStanding, Driver, DriverStanding, Race, RaceResult

    conn = db_conn

    # Setup drivers and constructors globally
    alpha = Driver(
        driver_id="alpha",
        permanent_number=1,
        code="ALP",
        url="http://a.com",
        given_name="Alpha",
        family_name="Driver",
        date_of_birth=datetime.date(1990, 1, 1),
        nationality="British",
    )
    beta = Driver(
        driver_id="beta",
        permanent_number=2,
        code="BET",
        url="http://b.com",
        given_name="Beta",
        family_name="Driver",
        date_of_birth=datetime.date(1990, 1, 1),
        nationality="French",
    )
    gamma = Driver(
        driver_id="gamma",
        permanent_number=3,
        code="GAM",
        url="http://g.com",
        given_name="Gamma",
        family_name="Driver",
        date_of_birth=datetime.date(1990, 1, 1),
        nationality="German",
    )
    upsert_drivers(conn, [alpha, beta, gamma])

    team_a = Constructor(constructor_id="team_a", url="http://a.com", name="Team A", nationality="British")
    team_b = Constructor(constructor_id="team_b", url="http://b.com", name="Team B", nationality="French")
    team_c = Constructor(constructor_id="team_c", url="http://c.com", name="Team C", nationality="German")
    upsert_constructors(conn, [team_a, team_b, team_c])

    # We need races in database to associate results/standings referential integrity
    circuit = Circuit(
        circuit_id="melbourne",
        url="http://m.com",
        circuit_name="Melbourne",
        lat=-37.8497,
        long=144.968,
        locality="Melbourne",
        country="Australia",
    )
    race_2026_1 = Race(
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
    race_2026_2 = Race(
        season=2026,
        round=2,
        url="http://r.com",
        race_name="GP 2",
        circuit=circuit,
        start=datetime.datetime(2026, 3, 15, 4, 0, tzinfo=datetime.UTC),
        fp1=None,
        fp2=None,
        fp3=None,
        qualifying=None,
        sprint=None,
        sprint_qualifying=None,
    )
    upsert_races(conn, [race_2026_1, race_2026_2])

    # 1. DRIVERS SCOPE
    upsert_drivers(conn, [gamma], season=2025)
    upsert_drivers(conn, [alpha, beta], season=2026)
    assert sorted([d.driver_id for d in select_drivers(conn, season=2026)]) == ["alpha", "beta"]
    upsert_drivers(conn, [alpha], season=2026)
    assert [d.driver_id for d in select_drivers(conn, season=2026)] == ["alpha"]
    assert [d.driver_id for d in select_drivers(conn, season=2025)] == ["gamma"]

    # 2. CONSTRUCTORS SCOPE
    upsert_constructors(conn, [team_c], season=2025)
    upsert_constructors(conn, [team_a, team_b], season=2026)
    assert sorted([c.constructor_id for c in select_constructors(conn, season=2026)]) == ["team_a", "team_b"]
    upsert_constructors(conn, [team_a], season=2026)
    assert [c.constructor_id for c in select_constructors(conn, season=2026)] == ["team_a"]
    assert [c.constructor_id for c in select_constructors(conn, season=2025)] == ["team_c"]

    # 3. RACE RESULTS SCOPE
    res_alpha = RaceResult(
        number=1,
        position=1,
        position_text="1",
        points=25.0,
        driver=alpha,
        constructor=team_a,
        grid=1,
        laps=58,
        status="Finished",
        time_millis=None,
        time_str=None,
        fastest_lap=None,
    )
    res_beta = RaceResult(
        number=2,
        position=2,
        position_text="2",
        points=18.0,
        driver=beta,
        constructor=team_b,
        grid=2,
        laps=58,
        status="Finished",
        time_millis=None,
        time_str=None,
        fastest_lap=None,
    )
    res_gamma = RaceResult(
        number=3,
        position=3,
        position_text="3",
        points=15.0,
        driver=gamma,
        constructor=team_c,
        grid=3,
        laps=58,
        status="Finished",
        time_millis=None,
        time_str=None,
        fastest_lap=None,
    )

    upsert_race_results(conn, season=2026, round=2, results=[res_gamma])
    upsert_race_results(conn, season=2026, round=1, results=[res_alpha, res_beta])
    assert sorted([r.driver.driver_id for r in select_race_results(conn, season=2026, round=1)]) == ["alpha", "beta"]
    upsert_race_results(conn, season=2026, round=1, results=[res_alpha])
    assert [r.driver.driver_id for r in select_race_results(conn, season=2026, round=1)] == ["alpha"]
    assert [r.driver.driver_id for r in select_race_results(conn, season=2026, round=2)] == ["gamma"]

    # 4. DRIVER STANDINGS SCOPE
    ds_alpha = DriverStanding(position=1, position_text="1", points=25.0, wins=1, driver=alpha, constructors=[team_a])
    ds_beta = DriverStanding(position=2, position_text="2", points=18.0, wins=0, driver=beta, constructors=[team_b])
    ds_gamma = DriverStanding(position=3, position_text="3", points=15.0, wins=0, driver=gamma, constructors=[team_c])

    upsert_driver_standings(conn, season=2025, standings=[ds_gamma])
    upsert_driver_standings(conn, season=2026, standings=[ds_alpha, ds_beta])
    assert sorted([s.driver.driver_id for s in select_driver_standings(conn, season=2026)]) == ["alpha", "beta"]
    upsert_driver_standings(conn, season=2026, standings=[ds_alpha])
    assert [s.driver.driver_id for s in select_driver_standings(conn, season=2026)] == ["alpha"]
    assert [s.driver.driver_id for s in select_driver_standings(conn, season=2025)] == ["gamma"]

    # 5. CONSTRUCTOR STANDINGS SCOPE
    cs_team_a = ConstructorStanding(position=1, position_text="1", points=25.0, wins=1, constructor=team_a)
    cs_team_b = ConstructorStanding(position=2, position_text="2", points=18.0, wins=0, constructor=team_b)
    cs_team_c = ConstructorStanding(position=3, position_text="3", points=15.0, wins=0, constructor=team_c)

    upsert_constructor_standings(conn, season=2025, standings=[cs_team_c])
    upsert_constructor_standings(conn, season=2026, standings=[cs_team_a, cs_team_b])
    assert sorted([s.constructor.constructor_id for s in select_constructor_standings(conn, season=2026)]) == [
        "team_a",
        "team_b",
    ]
    upsert_constructor_standings(conn, season=2026, standings=[cs_team_a])
    assert [s.constructor.constructor_id for s in select_constructor_standings(conn, season=2026)] == ["team_a"]
    assert [s.constructor.constructor_id for s in select_constructor_standings(conn, season=2025)] == ["team_c"]


def test_upsert_races_replace_semantics(db_conn) -> None:
    """Verify that upsert_races replaces the schedule scope for the season."""
    import datetime

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
    round1 = Race(
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
    round2 = Race(
        season=2026,
        round=2,
        url="http://r.com",
        race_name="GP 2",
        circuit=circuit,
        start=datetime.datetime(2026, 3, 15, 4, 0, tzinfo=datetime.UTC),
        fp1=None,
        fp2=None,
        fp3=None,
        qualifying=None,
        sprint=None,
        sprint_qualifying=None,
    )

    # 1. Refresh [round1, round2]
    upsert_races(db_conn, [round1, round2])
    assert select_races(db_conn, season=2026) == [round1, round2]

    # 2. then [round1] leaves exactly [round1]
    upsert_races(db_conn, [round1])
    assert select_races(db_conn, season=2026) == [round1]

    # 3. an empty schedule refresh leaves zero race rows
    upsert_races(db_conn, [], season=2026)
    assert select_races(db_conn, season=2026) == []


def test_mid_refresh_atomicity_all_scopes(db_conn) -> None:
    """Verify atomicity of all scope-refresh helpers upon mid-refresh failure."""
    import datetime
    import sqlite3
    from dataclasses import replace

    import pytest

    from pitwall.models import Circuit, Constructor, ConstructorStanding, Driver, DriverStanding, Race, RaceResult

    # Setup baseline entities
    circuit = Circuit(
        circuit_id="melbourne",
        url="http://m.com",
        circuit_name="Melbourne",
        lat=-37.8497,
        long=144.968,
        locality="Melbourne",
        country="Australia",
    )
    driver_1 = Driver(
        driver_id="driver1",
        permanent_number=1,
        code="DR1",
        url="http://d1.com",
        given_name="Driver",
        family_name="One",
        date_of_birth=datetime.date(1990, 1, 1),
        nationality="British",
    )
    driver_2 = Driver(
        driver_id="driver2",
        permanent_number=2,
        code="DR2",
        url="http://d2.com",
        given_name="Driver",
        family_name="Two",
        date_of_birth=datetime.date(1990, 1, 2),
        nationality="French",
    )
    upsert_drivers(db_conn, [driver_1, driver_2])

    team_1 = Constructor(constructor_id="team1", url="http://t1.com", name="Team One", nationality="British")
    team_2 = Constructor(constructor_id="team2", url="http://t2.com", name="Team Two", nationality="French")
    upsert_constructors(db_conn, [team_1, team_2])

    race_1 = Race(
        season=2026,
        round=1,
        url="http://r1.com",
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
    race_2 = Race(
        season=2026,
        round=2,
        url="http://r2.com",
        race_name="GP 2",
        circuit=circuit,
        start=datetime.datetime(2026, 3, 15, 4, 0, tzinfo=datetime.UTC),
        fp1=None,
        fp2=None,
        fp3=None,
        qualifying=None,
        sprint=None,
        sprint_qualifying=None,
    )

    # --- 1. Races ---
    upsert_races(db_conn, [race_1])
    assert select_races(db_conn, season=2026) == [race_1]

    bad_race = replace(race_2, race_name=None)
    with pytest.raises(sqlite3.Error):
        upsert_races(db_conn, [race_1, bad_race], season=2026)

    assert db_conn.in_transaction is False
    assert select_races(db_conn, season=2026) == [race_1]
    db_conn.commit()
    assert select_races(db_conn, season=2026) == [race_1]

    # --- 2. Drivers ---
    upsert_drivers(db_conn, [driver_1], season=2026)
    assert select_drivers(db_conn, season=2026) == [driver_1]

    bad_driver = replace(driver_2, given_name=None)
    with pytest.raises(sqlite3.Error):
        upsert_drivers(db_conn, [driver_1, bad_driver], season=2026)

    assert db_conn.in_transaction is False
    assert select_drivers(db_conn, season=2026) == [driver_1]
    db_conn.commit()
    assert select_drivers(db_conn, season=2026) == [driver_1]

    # --- 3. Constructors ---
    upsert_constructors(db_conn, [team_1], season=2026)
    assert select_constructors(db_conn, season=2026) == [team_1]

    bad_constructor = replace(team_2, name=None)
    with pytest.raises(sqlite3.Error):
        upsert_constructors(db_conn, [team_1, bad_constructor], season=2026)

    assert db_conn.in_transaction is False
    assert select_constructors(db_conn, season=2026) == [team_1]
    db_conn.commit()
    assert select_constructors(db_conn, season=2026) == [team_1]

    # --- 4. Race Results ---
    upsert_races(db_conn, [race_1])
    res_1 = RaceResult(
        number=1,
        position=1,
        position_text="1",
        points=25.0,
        driver=driver_1,
        constructor=team_1,
        grid=1,
        laps=58,
        status="Finished",
        time_millis=None,
        time_str=None,
        fastest_lap=None,
    )
    res_2 = RaceResult(
        number=2,
        position=2,
        position_text="2",
        points=18.0,
        driver=driver_2,
        constructor=team_2,
        grid=2,
        laps=58,
        status="Finished",
        time_millis=None,
        time_str=None,
        fastest_lap=None,
    )
    upsert_race_results(db_conn, season=2026, round=1, results=[res_1])
    assert select_race_results(db_conn, season=2026, round=1) == [res_1]

    bad_res = replace(res_2, position_text=None)
    with pytest.raises(sqlite3.Error):
        upsert_race_results(db_conn, season=2026, round=1, results=[res_1, bad_res])

    assert db_conn.in_transaction is False
    assert select_race_results(db_conn, season=2026, round=1) == [res_1]
    db_conn.commit()
    assert select_race_results(db_conn, season=2026, round=1) == [res_1]

    # --- 5. Driver Standings ---
    ds_1 = DriverStanding(position=1, position_text="1", points=25.0, wins=1, driver=driver_1, constructors=[team_1])
    ds_2 = DriverStanding(position=2, position_text="2", points=18.0, wins=0, driver=driver_2, constructors=[team_2])
    upsert_driver_standings(db_conn, season=2026, standings=[ds_1])
    assert select_driver_standings(db_conn, season=2026) == [ds_1]

    bad_ds = replace(ds_2, position_text=None)
    with pytest.raises(sqlite3.Error):
        upsert_driver_standings(db_conn, season=2026, standings=[ds_1, bad_ds])

    assert db_conn.in_transaction is False
    assert select_driver_standings(db_conn, season=2026) == [ds_1]
    db_conn.commit()
    assert select_driver_standings(db_conn, season=2026) == [ds_1]

    # --- 6. Constructor Standings ---
    cs_1 = ConstructorStanding(position=1, position_text="1", points=25.0, wins=1, constructor=team_1)
    cs_2 = ConstructorStanding(position=2, position_text="2", points=18.0, wins=0, constructor=team_2)
    upsert_constructor_standings(db_conn, season=2026, standings=[cs_1])
    assert select_constructor_standings(db_conn, season=2026) == [cs_1]

    bad_cs = replace(cs_2, position_text=None)
    with pytest.raises(sqlite3.Error):
        upsert_constructor_standings(db_conn, season=2026, standings=[cs_1, bad_cs])

    assert db_conn.in_transaction is False
    assert select_constructor_standings(db_conn, season=2026) == [cs_1]
    assert select_constructor_standings(db_conn, season=2026) == [cs_1]
    db_conn.commit()
    assert select_constructor_standings(db_conn, season=2026) == [cs_1]


def test_cross_helper_atomicity(db_conn) -> None:
    """Verify that a driver-standings or race-results refresh failure leaves global profiles and logs untouched.

    Assumption: The driver/constructor tables are shared globally across seasons/rounds, while
    standings and results are scoped. If a scoped refresh fails (e.g. database NOT NULL constraint),
    any modifications to the global profile tables within that refresh must be rolled back.
    Failure Mode: IntegrityError (sqlite3.Error) is raised and connection has no open transaction.
    """
    import datetime
    import sqlite3
    from dataclasses import replace
    from typing import cast

    import pytest

    from pitwall.cache.db import get_refresh_log, set_refresh_log
    from pitwall.models import Circuit, Constructor, Driver, DriverStanding, Race, RaceResult

    # --- 1. Driver Standings Atomicity ---
    # Invariant: Seeding initial shared profiles (OldName, OldTeam) and a driver standing entry.
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
    upsert_driver_standings(db_conn, season=2026, standings=[ds_old])
    set_refresh_log(
        db_conn, "driver_standings:2026", datetime.datetime(2026, 6, 8, 10, 0, tzinfo=datetime.UTC), record_count=1
    )

    # Act: Refresh payload carries new profile names but fails inside target scope due to violating NOT NULL.
    new_driver = replace(old_driver, given_name="NewNameFromFailedRefresh")
    new_constructor = replace(old_constructor, name="NewTeam")

    ds_bad = DriverStanding(
        position=2,
        position_text=cast(str, None),  # Violates NOT NULL constraint in driver_standings
        points=20.0,
        wins=2,
        driver=new_driver,
        constructors=[new_constructor],
    )

    with pytest.raises(sqlite3.Error):
        upsert_driver_standings(db_conn, season=2026, standings=[ds_bad])

    # Assert: Check that global profiles, standings, and refresh log are untouched and no transaction remains open.
    assert db_conn.in_transaction is False
    driver = get_driver(db_conn, "shared")
    assert driver is not None
    assert driver.given_name == "OldName"
    constructor = get_constructor(db_conn, "shared_team")
    assert constructor is not None
    assert constructor.name == "OldTeam"
    assert select_driver_standings(db_conn, season=2026) == [ds_old]
    assert get_refresh_log(db_conn, "driver_standings:2026") == datetime.datetime(
        2026, 6, 8, 10, 0, tzinfo=datetime.UTC
    )

    # --- 2. Race Results Atomicity ---
    # Setup: Seed circuit, race, and baseline race result.
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
    set_refresh_log(
        db_conn, "results:2026:1", datetime.datetime(2026, 6, 8, 10, 0, tzinfo=datetime.UTC), record_count=1
    )

    # Act: Refresh payload carries new profile names but fails inside target scope due to violating NOT NULL.
    new_driver2 = replace(old_driver, given_name="NewNameFromFailedRefreshResults")
    new_constructor2 = replace(old_constructor, name="NewTeamResults")

    res_bad = RaceResult(
        number=2,
        position=2,
        position_text=cast(str, None),  # Violates NOT NULL constraint in race_results
        points=18.0,
        driver=new_driver2,
        constructor=new_constructor2,
        grid=2,
        laps=58,
        status="Finished",
        time_millis=None,
        time_str=None,
        fastest_lap=None,
    )

    with pytest.raises(sqlite3.Error):
        upsert_race_results(db_conn, season=2026, round=1, results=[res_bad])

    # Assert: Check that global profiles, race results, and refresh log are untouched and no transaction remains open.
    assert db_conn.in_transaction is False
    driver2 = get_driver(db_conn, "shared")
    assert driver2 is not None
    assert driver2.given_name == "OldName"
    constructor2 = get_constructor(db_conn, "shared_team")
    assert constructor2 is not None
    assert constructor2.name == "OldTeam"
    assert select_race_results(db_conn, season=2026, round=1) == [res_old]
    assert get_refresh_log(db_conn, "results:2026:1") == datetime.datetime(2026, 6, 8, 10, 0, tzinfo=datetime.UTC)
