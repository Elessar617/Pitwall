import json
from datetime import UTC, datetime

import pytest

from pitwall.errors import DataParseError
from pitwall.openf1.models import (
    IntervalPoint,
    Lap,
    PitStop,
    PositionUpdate,
    RaceControlMessage,
    SessionDriver,
    Stint,
    parse_drivers,
    parse_intervals,
    parse_laps,
    parse_pit,
    parse_position,
    parse_race_control,
    parse_stints,
)


def test_parse_excerpt_counts_and_values(excerpt_dir):
    # 1. Parse drivers
    drivers_path = excerpt_dir / "drivers.json"
    with open(drivers_path, encoding="utf-8") as f:
        drivers_data = json.load(f)
    drivers = parse_drivers(drivers_data)
    assert len(drivers) == 22
    assert all(isinstance(d, SessionDriver) for d in drivers)

    # acronym map 63->RUS 12->ANT 1->NOR
    acronym_map = {d.driver_number: d.name_acronym for d in drivers}
    assert acronym_map[63] == "RUS"
    assert acronym_map[12] == "ANT"
    assert acronym_map[1] == "NOR"

    # 2. Parse stints
    stints_path = excerpt_dir / "stints.json"
    with open(stints_path, encoding="utf-8") as f:
        stints_data = json.load(f)
    stints = parse_stints(stints_data)
    assert len(stints) == 56
    assert all(isinstance(s, Stint) for s in stints)

    # 3. Parse laps
    laps_path = excerpt_dir / "laps.json"
    with open(laps_path, encoding="utf-8") as f:
        laps_data = json.load(f)
    laps = parse_laps(laps_data)
    assert len(laps) == 38
    assert all(isinstance(lp, Lap) for lp in laps)

    # 4. Parse position
    position_path = excerpt_dir / "position.json"
    with open(position_path, encoding="utf-8") as f:
        position_data = json.load(f)
    positions = parse_position(position_data)
    assert len(positions) == 30
    assert all(isinstance(p, PositionUpdate) for p in positions)

    # 5. Parse intervals
    intervals_path = excerpt_dir / "intervals.json"
    with open(intervals_path, encoding="utf-8") as f:
        intervals_data = json.load(f)
    intervals = parse_intervals(intervals_data)
    assert len(intervals) == 272
    assert all(isinstance(i, IntervalPoint) for i in intervals)

    # interval union float / '+1 LAP' / None preserved
    # excerpt yields at least one record each where gap_to_leader is a float, the exact string '+1 LAP', and where interval is None.
    has_float_gap = False
    has_plus_one_lap_gap = False
    has_none_interval = False

    for item in intervals:
        if isinstance(item.gap_to_leader, float):
            has_float_gap = True
        if item.gap_to_leader == "+1 LAP":
            has_plus_one_lap_gap = True
        if item.interval is None:
            has_none_interval = True

    assert has_float_gap, "Should have at least one gap_to_leader float"
    assert has_plus_one_lap_gap, "Should have at least one gap_to_leader '+1 LAP' string"
    assert has_none_interval, "Should have at least one interval None"

    # 6. Parse pit
    pit_path = excerpt_dir / "pit.json"
    with open(pit_path, encoding="utf-8") as f:
        pit_data = json.load(f)
    pit_stops = parse_pit(pit_data)
    assert len(pit_stops) == 2
    assert all(isinstance(p, PitStop) for p in pit_stops)

    # 7. Parse race_control
    rc_path = excerpt_dir / "race_control.json"
    with open(rc_path, encoding="utf-8") as f:
        rc_data = json.load(f)
    rc_messages = parse_race_control(rc_data)
    assert len(rc_messages) == 3
    assert all(isinstance(m, RaceControlMessage) for m in rc_messages)


def test_loud_rejections():
    # boolean-where-number raises DataParseError
    with pytest.raises(DataParseError):
        parse_drivers(
            [{"driver_number": True, "name_acronym": "RUS", "full_name": "George Russell", "team_name": "Mercedes"}]
        )

    with pytest.raises(DataParseError):
        parse_laps(
            [
                {
                    "driver_number": 63,
                    "lap_number": False,
                    "date_start": "2026-05-24T20:30:00+00:00",
                    "lap_duration": 76.5,
                }
            ]
        )

    # non-finite float rejected
    with pytest.raises(DataParseError):
        parse_laps(
            [
                {
                    "driver_number": 63,
                    "lap_number": 1,
                    "date_start": "2026-05-24T20:30:00+00:00",
                    "lap_duration": float("nan"),
                }
            ]
        )

    with pytest.raises(DataParseError):
        parse_laps(
            [
                {
                    "driver_number": 63,
                    "lap_number": 1,
                    "date_start": "2026-05-24T20:30:00+00:00",
                    "lap_duration": float("inf"),
                }
            ]
        )

    # missing driver_number naming field raises DataParseError with driver_number in msg
    with pytest.raises(DataParseError) as exc_info:
        parse_drivers([{"name_acronym": "RUS", "full_name": "George Russell", "team_name": "Mercedes"}])
    assert "driver_number" in str(exc_info.value)

    # extra keys ignored
    drivers = parse_drivers(
        [
            {
                "driver_number": 63,
                "name_acronym": "RUS",
                "full_name": "George Russell",
                "team_name": "Mercedes",
                "extra_key": "some_value",
            }
        ]
    )
    assert len(drivers) == 1
    assert drivers[0].driver_number == 63
    assert not hasattr(drivers[0], "extra_key")


def test_naive_ts_to_utc():
    # naive timestamp parses as UTC
    laps = parse_laps(
        [{"driver_number": 63, "lap_number": 1, "date_start": "2026-05-24T20:30:00", "lap_duration": 76.5}]
    )
    assert len(laps) == 1
    assert laps[0].date_start == datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC)


def test_invalid_types_for_parsers():
    parsers = [
        parse_drivers,
        parse_stints,
        parse_laps,
        parse_position,
        parse_intervals,
        parse_pit,
        parse_race_control,
    ]
    for p in parsers:
        with pytest.raises(DataParseError):
            p("not a list")
        with pytest.raises(DataParseError):
            p(["not a dict"])


def test_internal_helpers_edge_cases():
    from pitwall.openf1.models import (
        _gap_value,
        _optional_string,
        parse_optional_timestamp,
        parse_timestamp,
    )

    # parse_timestamp edge cases
    with pytest.raises(DataParseError):
        parse_timestamp(123, "test_field")
    with pytest.raises(DataParseError):
        parse_timestamp("not-a-datetime", "test_field")

    # parse_optional_timestamp edge cases
    assert parse_optional_timestamp(None, "test") is None
    assert parse_optional_timestamp("", "test") is None

    # _optional_string edge cases
    with pytest.raises(DataParseError):
        _optional_string(123, "test")

    # _gap_value edge cases
    with pytest.raises(DataParseError):
        _gap_value(True, "test")
    with pytest.raises(DataParseError):
        _gap_value(float("nan"), "test")
    with pytest.raises(DataParseError):
        _gap_value([], "test")


def test_team_colour_parsing(excerpt_dir):
    # Load drivers from fixture
    drivers_path = excerpt_dir / "drivers.json"
    with open(drivers_path, encoding="utf-8") as f:
        drivers_data = json.load(f)

    # parse_drivers over EXCERPT/drivers.json yields 22 drivers
    drivers = parse_drivers(drivers_data)
    assert len(drivers) == 22

    parsed_colours = {d.driver_number: d.team_colour for d in drivers}

    # Spot pins
    assert parsed_colours[1] == "F47600"
    assert parsed_colours[3] == "4781D7"
    assert parsed_colours[63] == "00D7B6"

    # Full-dict equality vs the fixture-derived table
    derived_table = {d["driver_number"]: d.get("team_colour") for d in drivers_data}
    assert parsed_colours == derived_table

    # Check that it matches the Context table literals exactly
    expected_context_table = {
        1: "F47600",
        3: "4781D7",
        5: "F50537",
        6: "4781D7",
        10: "00A1E8",
        11: "909090",
        12: "00D7B6",
        14: "229971",
        16: "ED1131",
        18: "229971",
        23: "1868DB",
        27: "F50537",
        30: "6C98FF",
        31: "9C9FA2",
        41: "6C98FF",
        43: "00A1E8",
        44: "ED1131",
        55: "1868DB",
        63: "00D7B6",
        77: "909090",
        81: "F47600",
        87: "9C9FA2",
    }
    assert parsed_colours == expected_context_table

    # A record without team_colour, with team_colour: null, or "" parses to None
    test_cases = [
        {"driver_number": 99, "name_acronym": "TST", "full_name": "Test Driver", "team_name": "Test Team"},
        {
            "driver_number": 99,
            "name_acronym": "TST",
            "full_name": "Test Driver",
            "team_name": "Test Team",
            "team_colour": None,
        },
        {
            "driver_number": 99,
            "name_acronym": "TST",
            "full_name": "Test Driver",
            "team_name": "Test Team",
            "team_colour": "",
        },
    ]
    for case in test_cases:
        parsed = parse_drivers([case])
        assert parsed[0].team_colour is None

    # a non-string team_colour (e.g. 123) raises DataParseError
    with pytest.raises(DataParseError):
        parse_drivers(
            [
                {
                    "driver_number": 99,
                    "name_acronym": "TST",
                    "full_name": "Test Driver",
                    "team_name": "Test Team",
                    "team_colour": 123,
                }
            ]
        )

    # SessionDriver(driver_number=1, name_acronym="NOR", full_name="Lando Norris", team_name="McLaren") still constructs (default None)
    d = SessionDriver(driver_number=1, name_acronym="NOR", full_name="Lando Norris", team_name="McLaren")
    assert d.team_colour is None

    # dataclass stays frozen
    with pytest.raises(AttributeError):
        d.team_colour = "F47600"  # type: ignore # noqa: PGH003


# ---- iter15 AC-1: the OpenF1 parse-error taxonomy bridge ----


def test_openf1_data_error_bridges_both_taxonomies():
    from pitwall.errors import DataParseError, JolpicaError
    from pitwall.openf1.errors import OpenF1DataError, OpenF1Error

    assert issubclass(OpenF1DataError, DataParseError)
    assert issubclass(OpenF1DataError, OpenF1Error)
    assert issubclass(OpenF1DataError, JolpicaError)


def test_openf1_parse_errors_are_openf1_errors():
    import pytest

    from pitwall.openf1.errors import OpenF1Error
    from pitwall.openf1.models import parse_position

    with pytest.raises(OpenF1Error):
        parse_position([{"driver_number": 1, "date": "2026-05-24T20:30:00+00:00", "position": "banana"}])
    with pytest.raises(OpenF1Error):
        parse_position({"not": "a list"})
