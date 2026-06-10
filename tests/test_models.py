import copy
import datetime
from dataclasses import FrozenInstanceError

import pytest

from pitwall.errors import DataParseError
from pitwall.models import (
    parse_constructor_standings,
    parse_constructors,
    parse_driver_standings,
    parse_drivers,
    parse_races,
    parse_results,
)


def test_each_domain_model_is_frozen_and_raises_error_on_attribute_assignment(jolpica_payload):
    """AC-02: Each of the eight domain models is frozen and raises FrozenInstanceError on attribute assignment."""
    # Arrange: Parse the real fixtures using the boundary functions to produce valid model instances.
    drivers = parse_drivers(jolpica_payload("drivers"))
    constructors = parse_constructors(jolpica_payload("constructors"))
    driver_standings = parse_driver_standings(jolpica_payload("driverstandings"))
    constructor_standings = parse_constructor_standings(jolpica_payload("constructorstandings"))
    races = parse_races(jolpica_payload("races"))
    results = parse_results(jolpica_payload("results"))

    driver = drivers[0]
    constructor = constructors[0]
    driver_standing = driver_standings[0]
    constructor_standing = constructor_standings[0]
    race = races[0]
    circuit = race.circuit
    result = results[0]
    fastest_lap = result.fastest_lap

    # Act & Assert: Mutating any attribute on any of the eight model instances must raise FrozenInstanceError.
    with pytest.raises(FrozenInstanceError):
        driver.driver_id = "mutated_driver_id"  # ty: ignore[invalid-assignment] - intentional frozen mutation check

    with pytest.raises(FrozenInstanceError):
        constructor.constructor_id = "mutated_constructor_id"  # ty: ignore[invalid-assignment] - intentional frozen mutation check

    with pytest.raises(FrozenInstanceError):
        driver_standing.points = 999.0  # ty: ignore[invalid-assignment] - intentional frozen mutation check

    with pytest.raises(FrozenInstanceError):
        constructor_standing.points = 999.0  # ty: ignore[invalid-assignment] - intentional frozen mutation check

    with pytest.raises(FrozenInstanceError):
        race.round = 99  # ty: ignore[invalid-assignment] - intentional frozen mutation check

    with pytest.raises(FrozenInstanceError):
        circuit.circuit_id = "mutated_circuit_id"  # ty: ignore[invalid-assignment] - intentional frozen mutation check

    with pytest.raises(FrozenInstanceError):
        result.grid = 99  # ty: ignore[invalid-assignment] - intentional frozen mutation check

    with pytest.raises(FrozenInstanceError):
        if fastest_lap is not None:
            fastest_lap.lap = 99  # ty: ignore[invalid-assignment] - intentional frozen mutation check


def test_parsing_real_fixtures_yields_exact_typed_values_and_correct_numeric_coercions(jolpica_payload):
    """AC-03: Parsing the real fixtures yields the exact typed values and correct numeric/date/datetime conversions."""
    # Arrange: Load the raw fixtures from the jolpica payload loader.
    driver_payload = jolpica_payload("drivers")
    driver_standings_payload = jolpica_payload("driverstandings")
    races_payload = jolpica_payload("races")
    results_payload = jolpica_payload("results")

    # Act: Parse them into domain model lists.
    drivers = parse_drivers(driver_payload)
    driver_standings = parse_driver_standings(driver_standings_payload)
    races = parse_races(races_payload)
    results = parse_results(results_payload)

    # Assert: Verify exact typing and value assertions.
    # (a) DriverStanding.points == 156.0 (float) and DriverStanding.wins == 5 (int)
    assert isinstance(driver_standings[0].points, float)
    assert driver_standings[0].points == 156.0
    assert isinstance(driver_standings[0].wins, int)
    assert driver_standings[0].wins == 5

    # (b) Circuit.lat == -37.8497 (float)
    assert isinstance(races[0].circuit.lat, float)
    assert races[0].circuit.lat == -37.8497

    # (c) Race.start is a tz-aware UTC datetime (2026-03-08 04:00 UTC)
    expected_start = datetime.datetime(2026, 3, 8, 4, 0, tzinfo=datetime.UTC)
    assert races[0].start == expected_start
    assert races[0].start.tzinfo is not None
    assert races[0].start.tzinfo.utcoffset(races[0].start) == datetime.timedelta(0)

    # (d) Driver.date_of_birth is a date (1996-03-23)
    assert isinstance(drivers[0].date_of_birth, datetime.date)
    assert drivers[0].date_of_birth == datetime.date(1996, 3, 23)

    # (e) RaceResult.time_millis == 8611243 (int)
    assert isinstance(results[0].time_millis, int)
    assert results[0].time_millis == 8611243


def test_parsing_malformed_driver_standings_raises_data_parse_error(jolpica_payload):
    """AC-03: A payload with a malformed numeric (e.g. points = "abc") raises DataParseError matching 'points'."""
    # Arrange: Load the malformed driver standings payload.
    malformed_payload = jolpica_payload("driverstandings_malformed")

    # Act & Assert: Parsing must fail with DataParseError indicating 'points' is malformed.
    with pytest.raises(DataParseError, match="points"):
        parse_driver_standings(malformed_payload)


def test_parsing_conventional_race_weekend_sets_standard_practice_and_qualifying_sessions(jolpica_payload):
    """AC-04: races.json round 1 parses with standard sessions set and sprint sessions None."""
    # Arrange: Load the schedule fixture.
    races_payload = jolpica_payload("races")

    # Act: Parse the schedule.
    races = parse_races(races_payload)
    race = races[0]  # Round 1 is conventional

    # Assert: Verify practice/qualifying sessions are set and sprint sessions are None.
    assert race.fp1 == datetime.datetime(2026, 3, 6, 1, 30, tzinfo=datetime.UTC)
    assert race.fp2 == datetime.datetime(2026, 3, 6, 5, 0, tzinfo=datetime.UTC)
    assert race.fp3 == datetime.datetime(2026, 3, 7, 1, 30, tzinfo=datetime.UTC)
    assert race.qualifying == datetime.datetime(2026, 3, 7, 5, 0, tzinfo=datetime.UTC)
    assert race.sprint is None
    assert race.sprint_qualifying is None


def test_parsing_sprint_race_weekend_sets_sprint_sessions_and_omits_unneeded_practices(jolpica_payload):
    """AC-04: races_sprint_weekend.json parses with sprint and sprint_qualifying set and fp2/fp3 None."""
    # Arrange: Load the sprint weekend schedule fixture.
    sprint_payload = jolpica_payload("races_sprint_weekend")

    # Act: Parse the schedule.
    races = parse_races(sprint_payload)
    race = races[0]

    # Assert: Verify sprint/sprint_qualifying sessions are set and fp2/fp3 are None.
    assert race.fp1 == datetime.datetime(2026, 3, 13, 3, 30, tzinfo=datetime.UTC)
    assert race.fp2 is None
    assert race.fp3 is None
    assert race.qualifying == datetime.datetime(2026, 3, 14, 7, 0, tzinfo=datetime.UTC)
    assert race.sprint == datetime.datetime(2026, 3, 14, 3, 0, tzinfo=datetime.UTC)
    assert race.sprint_qualifying == datetime.datetime(2026, 3, 13, 7, 30, tzinfo=datetime.UTC)


def test_parsing_sprint_shootout_alias_sets_sprint_qualifying_session(jolpica_payload):
    """AC-04: A SprintShootout-keyed variant in the race schedule is accepted as sprint_qualifying."""
    # Arrange: Load the sprint weekend schedule fixture and rename SprintQualifying to SprintShootout.
    sprint_payload = jolpica_payload("races_sprint_weekend")
    race_dict = sprint_payload["MRData"]["RaceTable"]["Races"][0]
    if "SprintQualifying" in race_dict:
        race_dict["SprintShootout"] = race_dict.pop("SprintQualifying")

    # Act: Parse the modified schedule payload.
    races = parse_races(sprint_payload)
    race = races[0]

    # Assert: Verify sprint_qualifying is mapped correctly from SprintShootout and fp2/fp3 are None.
    assert race.sprint_qualifying == datetime.datetime(2026, 3, 13, 7, 30, tzinfo=datetime.UTC)
    assert race.fp2 is None
    assert race.fp3 is None


def test_unwrap_envelope_malformed(jolpica_payload) -> None:
    """Verify various unwrap envelope validation failures."""
    # Invariant: Malformed top-level structure must raise DataParseError.

    # MRData missing
    payload = copy.deepcopy(jolpica_payload("drivers"))
    del payload["MRData"]
    with pytest.raises(DataParseError, match="Missing 'MRData' envelope"):
        parse_drivers(payload)

    # table_key missing
    payload = copy.deepcopy(jolpica_payload("drivers"))
    del payload["MRData"]["DriverTable"]
    with pytest.raises(DataParseError, match="Missing 'DriverTable'"):
        parse_drivers(payload)

    # list_key missing
    payload = copy.deepcopy(jolpica_payload("drivers"))
    del payload["MRData"]["DriverTable"]["Drivers"]
    with pytest.raises(DataParseError, match="Missing 'Drivers'"):
        parse_drivers(payload)

    # list_key not a list
    payload = copy.deepcopy(jolpica_payload("drivers"))
    payload["MRData"]["DriverTable"]["Drivers"] = "not a list"
    with pytest.raises(DataParseError, match="Expected list for 'Drivers'"):
        parse_drivers(payload)


def test_parse_driver_failures(jolpica_payload) -> None:
    """Verify driver parsing validation checks."""
    # Invariant: Driver dict must conform to schema and types.

    # Driver not a dict
    payload = copy.deepcopy(jolpica_payload("drivers"))
    payload["MRData"]["DriverTable"]["Drivers"][0] = "not a dict"
    with pytest.raises(DataParseError, match="Expected dictionary for Driver"):
        parse_drivers(payload)

    # Driver missing key
    payload = copy.deepcopy(jolpica_payload("drivers"))
    del payload["MRData"]["DriverTable"]["Drivers"][0]["driverId"]
    with pytest.raises(DataParseError, match="Missing required Driver field"):
        parse_drivers(payload)

    # Coerce optional int failure (permanentNumber)
    payload = copy.deepcopy(jolpica_payload("drivers"))
    payload["MRData"]["DriverTable"]["Drivers"][0]["permanentNumber"] = "invalid_int"
    with pytest.raises(DataParseError, match="Malformed integer value for field 'permanentNumber'"):
        parse_drivers(payload)

    # Coerce optional int empty
    payload = copy.deepcopy(jolpica_payload("drivers"))
    payload["MRData"]["DriverTable"]["Drivers"][0]["permanentNumber"] = ""
    drivers = parse_drivers(payload)
    assert drivers[0].permanent_number is None

    # Date of birth malformed
    payload = copy.deepcopy(jolpica_payload("drivers"))
    payload["MRData"]["DriverTable"]["Drivers"][0]["dateOfBirth"] = "invalid_date"
    with pytest.raises(DataParseError, match="Malformed dateOfBirth"):
        parse_drivers(payload)


def test_parse_constructor_failures(jolpica_payload) -> None:
    """Verify constructor parsing validation checks."""
    # Invariant: Constructor dict must conform to schema and types.

    # Constructor not a dict
    payload = copy.deepcopy(jolpica_payload("constructors"))
    payload["MRData"]["ConstructorTable"]["Constructors"][0] = "not a dict"
    with pytest.raises(DataParseError, match="Expected dictionary for Constructor"):
        parse_constructors(payload)

    # Constructor missing key
    payload = copy.deepcopy(jolpica_payload("constructors"))
    del payload["MRData"]["ConstructorTable"]["Constructors"][0]["constructorId"]
    with pytest.raises(DataParseError, match="Missing required Constructor field"):
        parse_constructors(payload)


def test_parse_race_and_circuit_failures(jolpica_payload) -> None:
    """Verify race and circuit parsing validation checks."""
    # Invariant: Race and Circuit dicts must conform to schema and types.

    # Race not a dict
    payload = copy.deepcopy(jolpica_payload("races"))
    payload["MRData"]["RaceTable"]["Races"][0] = "not a dict"
    with pytest.raises(DataParseError, match="Expected dictionary for Race"):
        parse_races(payload)

    # Race missing key
    payload = copy.deepcopy(jolpica_payload("races"))
    del payload["MRData"]["RaceTable"]["Races"][0]["season"]
    with pytest.raises(DataParseError, match="Missing required Race field"):
        parse_races(payload)

    # Circuit not a dict
    payload = copy.deepcopy(jolpica_payload("races"))
    payload["MRData"]["RaceTable"]["Races"][0]["Circuit"] = "not a dict"
    with pytest.raises(DataParseError, match="Expected dictionary for Circuit"):
        parse_races(payload)

    # Circuit missing key
    payload = copy.deepcopy(jolpica_payload("races"))
    del payload["MRData"]["RaceTable"]["Races"][0]["Circuit"]["circuitId"]
    with pytest.raises(DataParseError, match="Missing required Circuit field"):
        parse_races(payload)

    # Location not a dict
    payload = copy.deepcopy(jolpica_payload("races"))
    payload["MRData"]["RaceTable"]["Races"][0]["Circuit"]["Location"] = "not a dict"
    with pytest.raises(DataParseError, match="Expected dictionary for Circuit Location"):
        parse_races(payload)

    # Location missing key
    payload = copy.deepcopy(jolpica_payload("races"))
    del payload["MRData"]["RaceTable"]["Races"][0]["Circuit"]["Location"]["lat"]
    with pytest.raises(DataParseError, match="Missing required Circuit Location field"):
        parse_races(payload)

    # Float coercion failure
    payload = copy.deepcopy(jolpica_payload("races"))
    payload["MRData"]["RaceTable"]["Races"][0]["Circuit"]["Location"]["lat"] = "invalid_float"
    with pytest.raises(DataParseError, match="Malformed float value for field 'lat'"):
        parse_races(payload)

    # Int coercion failure
    payload = copy.deepcopy(jolpica_payload("races"))
    payload["MRData"]["RaceTable"]["Races"][0]["season"] = "invalid_int"
    with pytest.raises(DataParseError, match="Malformed integer value for field 'season'"):
        parse_races(payload)

    # Datetime coercion failure
    payload = copy.deepcopy(jolpica_payload("races"))
    payload["MRData"]["RaceTable"]["Races"][0]["time"] = "invalid_time"
    with pytest.raises(DataParseError, match="Malformed datetime for field 'start'"):
        parse_races(payload)

    # tzinfo is None path
    payload = copy.deepcopy(jolpica_payload("races"))
    payload["MRData"]["RaceTable"]["Races"][0]["time"] = "04:00:00"
    races = parse_races(payload)
    assert races[0].start.tzinfo == datetime.UTC

    # Missing session time
    payload = copy.deepcopy(jolpica_payload("races"))
    payload["MRData"]["RaceTable"]["Races"][0]["FirstPractice"] = {"date": "2026-03-06"}
    with pytest.raises(DataParseError, match="time"):
        parse_races(payload)


def test_parse_standing_failures(jolpica_payload) -> None:
    """Verify driver and constructor standing parsing validation checks."""
    # Invariant: Standings dicts must conform to schema and types.

    # DriverStanding not a dict
    payload = copy.deepcopy(jolpica_payload("driverstandings"))
    payload["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0] = "not a dict"
    with pytest.raises(DataParseError, match="Expected dictionary for DriverStanding"):
        parse_driver_standings(payload)

    # DriverStanding missing key
    payload = copy.deepcopy(jolpica_payload("driverstandings"))
    del payload["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0]["position"]
    with pytest.raises(DataParseError, match="Missing required DriverStanding field"):
        parse_driver_standings(payload)

    # Constructors in DriverStanding not a list
    payload = copy.deepcopy(jolpica_payload("driverstandings"))
    payload["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0]["Constructors"] = "not a list"
    with pytest.raises(DataParseError, match="Expected list for Constructors in DriverStanding"):
        parse_driver_standings(payload)

    # ConstructorStanding not a dict
    payload = copy.deepcopy(jolpica_payload("constructorstandings"))
    payload["MRData"]["StandingsTable"]["StandingsLists"][0]["ConstructorStandings"][0] = "not a dict"
    with pytest.raises(DataParseError, match="Expected dictionary for ConstructorStanding"):
        parse_constructor_standings(payload)

    # ConstructorStanding missing key
    payload = copy.deepcopy(jolpica_payload("constructorstandings"))
    del payload["MRData"]["StandingsTable"]["StandingsLists"][0]["ConstructorStandings"][0]["position"]
    with pytest.raises(DataParseError, match="Missing required ConstructorStanding field"):
        parse_constructor_standings(payload)

    # parse_driver_standings s_list not dict / missing DriverStandings
    payload = copy.deepcopy(jolpica_payload("driverstandings"))
    payload["MRData"]["StandingsTable"]["StandingsLists"][0] = "not a dict"
    with pytest.raises(DataParseError):
        parse_driver_standings(payload)

    # parse_driver_standings driver_standings not list
    payload = copy.deepcopy(jolpica_payload("driverstandings"))
    payload["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"] = "not a list"
    with pytest.raises(DataParseError):
        parse_driver_standings(payload)

    # parse_constructor_standings s_list not dict / missing ConstructorStandings
    payload = copy.deepcopy(jolpica_payload("constructorstandings"))
    payload["MRData"]["StandingsTable"]["StandingsLists"][0] = "not a dict"
    with pytest.raises(DataParseError):
        parse_constructor_standings(payload)

    # parse_constructor_standings constructor_standings not list
    payload = copy.deepcopy(jolpica_payload("constructorstandings"))
    payload["MRData"]["StandingsTable"]["StandingsLists"][0]["ConstructorStandings"] = "not a list"
    with pytest.raises(DataParseError):
        parse_constructor_standings(payload)


def test_parse_results_failures(jolpica_payload) -> None:
    """Verify race results parsing validation checks."""
    # Invariant: RaceResult dicts must conform to schema and types.

    # RaceResult not a dict
    payload = copy.deepcopy(jolpica_payload("results"))
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0] = "not a dict"
    with pytest.raises(DataParseError, match="Expected dictionary for RaceResult"):
        parse_results(payload)

    # RaceResult missing key
    payload = copy.deepcopy(jolpica_payload("results"))
    del payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["number"]
    with pytest.raises(DataParseError, match="Missing required RaceResult field"):
        parse_results(payload)

    # coerce_position handling None/empty or non-numeric
    payload = copy.deepcopy(jolpica_payload("results"))
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["position"] = ""
    results = parse_results(payload)
    assert results[0].position is None

    payload = copy.deepcopy(jolpica_payload("results"))
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["position"] = "R"
    results = parse_results(payload)
    assert results[0].position is None

    # Time in RaceResult not a dict
    payload = copy.deepcopy(jolpica_payload("results"))
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["Time"] = "not a dict"
    with pytest.raises(DataParseError, match="Expected dictionary for RaceResult Time"):
        parse_results(payload)

    # FastestLap not a dict
    payload = copy.deepcopy(jolpica_payload("results"))
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["FastestLap"] = "not a dict"
    with pytest.raises(DataParseError, match="Expected dictionary for FastestLap"):
        parse_results(payload)

    # FastestLap missing required field
    payload = copy.deepcopy(jolpica_payload("results"))
    del payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["FastestLap"]["lap"]
    with pytest.raises(DataParseError, match="Missing required FastestLap field"):
        parse_results(payload)

    # FastestLap Time not a dict or missing time
    payload = copy.deepcopy(jolpica_payload("results"))
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["FastestLap"]["Time"] = "not a dict"
    with pytest.raises(DataParseError, match="Expected dictionary with 'time' for FastestLap Time"):
        parse_results(payload)

    # parse_results race not dict / missing Results
    payload = copy.deepcopy(jolpica_payload("results"))
    payload["MRData"]["RaceTable"]["Races"][0] = "not a dict"
    with pytest.raises(DataParseError):
        parse_results(payload)

    # parse_results results_list not list
    payload = copy.deepcopy(jolpica_payload("results"))
    payload["MRData"]["RaceTable"]["Races"][0]["Results"] = "not a list"
    with pytest.raises(DataParseError):
        parse_results(payload)


def test_present_session_block_missing_date_or_time_raises_error(jolpica_payload) -> None:
    """A present session block missing date or time raises DataParseError naming the field."""
    # Present FirstPractice but missing time
    payload = copy.deepcopy(jolpica_payload("races"))
    payload["MRData"]["RaceTable"]["Races"][0]["FirstPractice"] = {"date": "2026-03-06"}
    with pytest.raises(DataParseError, match="time"):
        parse_races(payload)

    # Present FirstPractice but missing date
    payload = copy.deepcopy(jolpica_payload("races"))
    payload["MRData"]["RaceTable"]["Races"][0]["FirstPractice"] = {"time": "12:00:00Z"}
    with pytest.raises(DataParseError, match="date"):
        parse_races(payload)


def test_parse_results_missing_results_container_raises_error(jolpica_payload) -> None:
    """A race entry missing its Results container raises DataParseError."""
    payload = copy.deepcopy(jolpica_payload("results"))
    del payload["MRData"]["RaceTable"]["Races"][0]["Results"]
    with pytest.raises(DataParseError, match="Results"):
        parse_results(payload)


def test_points_nan_and_infinity_raise_data_parse_error(jolpica_payload) -> None:
    """Points as 'NaN' or 'Infinity' must raise DataParseError."""
    # NaN points
    payload_nan = copy.deepcopy(jolpica_payload("driverstandings"))
    payload_nan["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0]["points"] = "NaN"
    with pytest.raises(DataParseError, match="points"):
        parse_driver_standings(payload_nan)

    # Infinity points
    payload_inf = copy.deepcopy(jolpica_payload("driverstandings"))
    payload_inf["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0]["points"] = "Infinity"
    with pytest.raises(DataParseError, match="points"):
        parse_driver_standings(payload_inf)


def test_wins_boolean_raises_data_parse_error(jolpica_payload) -> None:
    """Wins as a boolean (True/False) must raise DataParseError."""
    payload = copy.deepcopy(jolpica_payload("driverstandings"))
    payload["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0]["wins"] = True
    with pytest.raises(DataParseError, match="wins"):
        parse_driver_standings(payload)


def test_parse_race_with_timezone_offset_parses_to_utc(jolpica_payload) -> None:
    """A race entry with timezone-offset time parsed should yield a tz-aware UTC datetime."""
    payload = copy.deepcopy(jolpica_payload("races"))
    payload["MRData"]["RaceTable"]["Races"][0]["time"] = "04:00:00+02:00"
    payload["MRData"]["RaceTable"]["Races"][0]["date"] = "2026-03-08"

    races = parse_races(payload)
    race = races[0]

    # Expected UTC datetime is 2026-03-08 02:00:00 UTC
    expected = datetime.datetime(2026, 3, 8, 2, 0, 0, tzinfo=datetime.UTC)
    assert race.start == expected
    assert race.start.tzinfo == datetime.UTC


def test_present_but_falsey_session_raises_data_parse_error(jolpica_payload) -> None:
    """A present-but-falsey session block raises DataParseError naming the session key (absent key parses as None)."""
    # Invariant: A session block, if present in the races payload, must not be a falsey value (e.g. {}, [], "", 0, False).
    # If it is, it must raise a DataParseError naming the key. An absent key is still valid.
    for val in [{}, [], "", 0, False]:
        for key in ["FirstPractice", "SecondPractice", "ThirdPractice", "Qualifying", "Sprint", "SprintQualifying"]:
            payload = copy.deepcopy(jolpica_payload("races"))
            payload["MRData"]["RaceTable"]["Races"][0][key] = val
            with pytest.raises(DataParseError, match=key):
                parse_races(payload)

        # Invariant: SprintShootout is also a valid alias for SprintQualifying, so its falsey values must be validated similarly.
        payload = copy.deepcopy(jolpica_payload("races"))
        payload["MRData"]["RaceTable"]["Races"][0].pop("SprintQualifying", None)
        payload["MRData"]["RaceTable"]["Races"][0]["SprintShootout"] = val
        with pytest.raises(DataParseError, match="SprintShootout"):
            parse_races(payload)

    # Invariant: Verify that an absent session block parses as None (no exception raised).
    payload = copy.deepcopy(jolpica_payload("races"))
    if "FirstPractice" in payload["MRData"]["RaceTable"]["Races"][0]:
        del payload["MRData"]["RaceTable"]["Races"][0]["FirstPractice"]
    races = parse_races(payload)
    assert races[0].fp1 is None


def test_int_boundary_rejects_fractional_numbers_and_bool_positions(jolpica_payload) -> None:
    """Verify that fractional JSON numbers for integer fields and bool race positions raise DataParseError."""
    # Invariant: Integer boundaries must reject floats or bool values with DataParseError.

    # wins = 1.5 in driver standings
    payload = copy.deepcopy(jolpica_payload("driverstandings"))
    payload["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0]["wins"] = 1.5
    with pytest.raises(DataParseError, match="wins"):
        parse_driver_standings(payload)

    # wins = 1.5 in constructor standings
    payload = copy.deepcopy(jolpica_payload("constructorstandings"))
    payload["MRData"]["StandingsTable"]["StandingsLists"][0]["ConstructorStandings"][0]["wins"] = 1.5
    with pytest.raises(DataParseError, match="wins"):
        parse_constructor_standings(payload)

    # position = 1.5 in driver standings
    payload = copy.deepcopy(jolpica_payload("driverstandings"))
    payload["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0]["position"] = 1.5
    with pytest.raises(DataParseError, match="position"):
        parse_driver_standings(payload)

    # position = 1.5 in constructor standings
    payload = copy.deepcopy(jolpica_payload("constructorstandings"))
    payload["MRData"]["StandingsTable"]["StandingsLists"][0]["ConstructorStandings"][0]["position"] = 1.5
    with pytest.raises(DataParseError, match="position"):
        parse_constructor_standings(payload)

    # grid = 1.5 in race results
    payload = copy.deepcopy(jolpica_payload("results"))
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["grid"] = 1.5
    with pytest.raises(DataParseError, match="grid"):
        parse_results(payload)

    # permanentNumber = 1.5 in drivers
    payload = copy.deepcopy(jolpica_payload("drivers"))
    payload["MRData"]["DriverTable"]["Drivers"][0]["permanentNumber"] = 1.5
    with pytest.raises(DataParseError, match="permanentNumber"):
        parse_drivers(payload)

    # position = True in race results
    payload = copy.deepcopy(jolpica_payload("results"))
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["position"] = True
    with pytest.raises(DataParseError, match="position"):
        parse_results(payload)

    # position = 1.5 in race results
    payload = copy.deepcopy(jolpica_payload("results"))
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["position"] = 1.5
    with pytest.raises(DataParseError, match="position"):
        parse_results(payload)


def test_position_whole_number_float_string_raises_data_parse_error(jolpica_payload) -> None:
    """RaceResult position '1.0' (or other whole-number-float strings) raises DataParseError."""
    payload = copy.deepcopy(jolpica_payload("results"))

    # 1. Genuine status text like 'R' or 'DSQ' should still map to position=None
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["position"] = "R"
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["positionText"] = "R"
    results_r = parse_results(payload)
    assert results_r[0].position is None
    assert results_r[0].position_text == "R"

    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["position"] = "DSQ"
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["positionText"] = "DSQ"
    results_dsq = parse_results(payload)
    assert results_dsq[0].position is None
    assert results_dsq[0].position_text == "DSQ"

    # 2. Malformed position string '1.0' must raise DataParseError
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["position"] = "1.0"
    with pytest.raises(DataParseError, match="position"):
        parse_results(payload)

    # 3. Another whole-number-float string '2.0' must raise DataParseError
    payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["position"] = "2.0"
    with pytest.raises(DataParseError, match="position"):
        parse_results(payload)


def test_int_fields_nan_and_inf_raise_data_parse_error(jolpica_payload) -> None:
    """float('nan') and float('inf') on INT fields raise DataParseError, never raw ValueError/OverflowError."""
    nan_val = float("nan")
    inf_val = float("inf")

    # Test wins on driver standings
    for val in [nan_val, inf_val]:
        # wins
        payload = copy.deepcopy(jolpica_payload("driverstandings"))
        payload["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0]["wins"] = val
        with pytest.raises(DataParseError, match="wins"):
            parse_driver_standings(payload)

        # position
        payload = copy.deepcopy(jolpica_payload("driverstandings"))
        payload["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0]["position"] = val
        with pytest.raises(DataParseError, match="position"):
            parse_driver_standings(payload)

        # Test wins on constructor standings
        payload = copy.deepcopy(jolpica_payload("constructorstandings"))
        payload["MRData"]["StandingsTable"]["StandingsLists"][0]["ConstructorStandings"][0]["wins"] = val
        with pytest.raises(DataParseError, match="wins"):
            parse_constructor_standings(payload)

        # Test position on constructor standings
        payload = copy.deepcopy(jolpica_payload("constructorstandings"))
        payload["MRData"]["StandingsTable"]["StandingsLists"][0]["ConstructorStandings"][0]["position"] = val
        with pytest.raises(DataParseError, match="position"):
            parse_constructor_standings(payload)

        # Test grid on race results
        payload = copy.deepcopy(jolpica_payload("results"))
        payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["grid"] = val
        with pytest.raises(DataParseError, match="grid"):
            parse_results(payload)

        # Test position on race results
        payload = copy.deepcopy(jolpica_payload("results"))
        payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["position"] = val
        with pytest.raises(DataParseError, match="position"):
            parse_results(payload)


def test_drivers_validation(jolpica_payload) -> None:
    """Verify parse_drivers validates driver identity and display strings."""
    # Invariant: Driver identity and display strings must be non-empty strings.
    # Assumption: invalid_values contains non-string, empty, or None values.
    invalid_values = [None, "", 123, True, [], {}]
    for field in ["driverId", "givenName", "familyName"]:
        for val in invalid_values:
            payload = copy.deepcopy(jolpica_payload("drivers"))
            payload["MRData"]["DriverTable"]["Drivers"][0][field] = val
            with pytest.raises(DataParseError, match=field):
                parse_drivers(payload)


def test_constructors_validation(jolpica_payload) -> None:
    """Verify parse_constructors validates constructor identity and display strings."""
    # Invariant: Constructor identity and display strings must be non-empty strings.
    # Assumption: invalid_values contains non-string, empty, or None values.
    invalid_values = [None, "", 123, True, [], {}]
    for field in ["constructorId", "name"]:
        for val in invalid_values:
            payload = copy.deepcopy(jolpica_payload("constructors"))
            payload["MRData"]["ConstructorTable"]["Constructors"][0][field] = val
            with pytest.raises(DataParseError, match=field):
                parse_constructors(payload)


def test_driver_standings_validation(jolpica_payload) -> None:
    """Verify parse_driver_standings validates driver/constructor identity and display strings."""
    # Invariant: Nested driver and constructor strings must be non-empty strings.
    # Assumption: invalid_values contains non-string, empty, or None values.
    invalid_values = [None, "", 123, True, [], {}]
    for field in ["driverId", "givenName", "familyName"]:
        for val in invalid_values:
            payload = copy.deepcopy(jolpica_payload("driverstandings"))
            payload["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0]["Driver"][field] = val
            with pytest.raises(DataParseError, match=field):
                parse_driver_standings(payload)
    for field in ["constructorId", "name"]:
        for val in invalid_values:
            payload = copy.deepcopy(jolpica_payload("driverstandings"))
            payload["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][0]["Constructors"][0][field] = (
                val
            )
            with pytest.raises(DataParseError, match=field):
                parse_driver_standings(payload)


def test_constructor_standings_validation(jolpica_payload) -> None:
    """Verify parse_constructor_standings validates constructor identity and display strings."""
    # Invariant: Constructor identity and name must be non-empty strings.
    # Assumption: invalid_values contains non-string, empty, or None values.
    invalid_values = [None, "", 123, True, [], {}]
    for field in ["constructorId", "name"]:
        for val in invalid_values:
            payload = copy.deepcopy(jolpica_payload("constructorstandings"))
            payload["MRData"]["StandingsTable"]["StandingsLists"][0]["ConstructorStandings"][0]["Constructor"][
                field
            ] = val
            with pytest.raises(DataParseError, match=field):
                parse_constructor_standings(payload)


def test_races_validation(jolpica_payload) -> None:
    """Verify parse_races validates race/circuit identity and display strings."""
    # Invariant: Race name, circuit ID, and circuit name must be non-empty strings.
    # Assumption: invalid_values contains non-string, empty, or None values.
    invalid_values = [None, "", 123, True, [], {}]
    for val in invalid_values:
        payload = copy.deepcopy(jolpica_payload("races"))
        payload["MRData"]["RaceTable"]["Races"][0]["raceName"] = val
        with pytest.raises(DataParseError, match="raceName"):
            parse_races(payload)
    for field in ["circuitId", "circuitName"]:
        for val in invalid_values:
            payload = copy.deepcopy(jolpica_payload("races"))
            payload["MRData"]["RaceTable"]["Races"][0]["Circuit"][field] = val
            with pytest.raises(DataParseError, match=field):
                parse_races(payload)


def test_results_validation(jolpica_payload) -> None:
    """Verify parse_results validates driver/constructor identity and display strings."""
    # Invariant: Driver and constructor IDs and display names must be non-empty strings.
    # Assumption: invalid_values contains non-string, empty, or None values.
    invalid_values = [None, "", 123, True, [], {}]
    for field in ["driverId", "givenName", "familyName"]:
        for val in invalid_values:
            payload = copy.deepcopy(jolpica_payload("results"))
            payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["Driver"][field] = val
            with pytest.raises(DataParseError, match=field):
                parse_results(payload)
    for field in ["constructorId", "name"]:
        for val in invalid_values:
            payload = copy.deepcopy(jolpica_payload("results"))
            payload["MRData"]["RaceTable"]["Races"][0]["Results"][0]["Constructor"][field] = val
            with pytest.raises(DataParseError, match=field):
                parse_results(payload)
