import datetime
import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pitwall.errors import DataParseError


@dataclass(frozen=True)
class Circuit:
    circuit_id: str
    url: str
    circuit_name: str
    lat: float
    long: float
    locality: str
    country: str


@dataclass(frozen=True)
class Driver:
    driver_id: str
    permanent_number: int | None
    code: str | None
    url: str | None
    given_name: str
    family_name: str
    date_of_birth: datetime.date | None
    nationality: str | None


@dataclass(frozen=True)
class Constructor:
    constructor_id: str
    url: str
    name: str
    nationality: str


@dataclass(frozen=True)
class DriverStanding:
    position: int
    position_text: str
    points: float
    wins: int
    driver: Driver
    constructors: list[Constructor]


@dataclass(frozen=True)
class ConstructorStanding:
    position: int
    position_text: str
    points: float
    wins: int
    constructor: Constructor


@dataclass(frozen=True)
class Race:
    season: int
    round: int
    url: str
    race_name: str
    circuit: Circuit
    start: datetime.datetime
    fp1: datetime.datetime | None
    fp2: datetime.datetime | None
    fp3: datetime.datetime | None
    qualifying: datetime.datetime | None
    sprint: datetime.datetime | None
    sprint_qualifying: datetime.datetime | None


@dataclass(frozen=True)
class FastestLap:
    rank: int | None
    lap: int
    time: str


@dataclass(frozen=True)
class RaceResult:
    number: int
    position: int | None
    position_text: str
    points: float
    driver: Driver
    constructor: Constructor
    grid: int
    laps: int
    status: str
    time_millis: int | None
    time_str: str | None
    fastest_lap: FastestLap | None


def coerce_int(val: Any, field_name: str) -> int:
    """Coerce value to an integer, raising DataParseError on failure."""
    if isinstance(val, bool):
        # Invariant: boolean values (True/False) must be explicitly rejected
        # to prevent Python from silently coercing them to 1 or 0.
        raise DataParseError.malformed_coercion("integer", field_name, val)
    try:
        if isinstance(val, (int, float)):
            # Invariant: non-finite numeric floats (nan/inf) must raise DataParseError.
            # We explicitly reject nan and inf before testing conversion equivalence.
            if not math.isfinite(val):
                raise DataParseError.malformed_coercion("integer", field_name, val)
            # Assumption: numeric inputs must not have a fractional part.
            # We reject any value where the float representation differs from its integer truncation.
            if val != int(val):
                raise DataParseError.malformed_coercion("integer", field_name, val)
        return int(val)
    except (ValueError, TypeError, OverflowError) as e:
        raise DataParseError.malformed_coercion("integer", field_name, val) from e


def coerce_optional_int(val: Any, field_name: str) -> int | None:
    """Coerce value to an integer or None if empty/null, raising DataParseError on failure."""
    if val is None or val == "":
        return None
    # Invariant: non-null values obey the same bool/nan/inf/fractional rejections as coerce_int.
    return coerce_int(val, field_name)


def coerce_float(val: Any, field_name: str) -> float:
    """Coerce value to a float, raising DataParseError on failure."""
    if isinstance(val, bool):
        raise DataParseError.malformed_coercion("float", field_name, val)
    try:
        f = float(val)
    except (ValueError, TypeError) as e:
        raise DataParseError.malformed_coercion("float", field_name, val) from e
    if not math.isfinite(f):
        raise DataParseError.malformed_coercion("float", field_name, val)
    return f


def coerce_position(val: Any) -> int | None:
    """Coerce position text to an integer, returning None if non-numeric (e.g. retired status 'R')."""
    if val is None or val == "":
        return None
    if isinstance(val, bool):
        # Invariant: boolean values are not valid race positions and must be rejected.
        raise DataParseError.malformed_coercion("integer", "position", val)
    try:
        if isinstance(val, (int, float)):
            # Invariant: numeric positions obey coerce_int's nan/inf/fractional rejections
            # (DataParseError propagates directly; it is not re-wrapped by the except below).
            return coerce_int(val, "position")
        if isinstance(val, str):
            try:
                return int(val)
            except ValueError:
                try:
                    float(val)  # If it parses as a float but not as an int, it's a malformed float string
                    # Invariant: any string representing a number that isn't a simple integer (e.g. '1.0', '1.5', 'nan', 'inf')
                    # must raise DataParseError at the boundary.
                    raise DataParseError.malformed_coercion("integer", "position", val)
                except ValueError:
                    pass
                # Invariant: non-numeric position texts like 'R', 'D', 'W', '-' represent
                # race exclusions or retirements, which map to a None numeric position.
                return None
    except (ValueError, TypeError, OverflowError) as e:
        raise DataParseError.malformed_coercion("integer", "position", val) from e
    raise DataParseError.malformed_coercion("integer", "position", val)


def coerce_required_string(val: Any, field_name: str) -> str:
    """Coerce value to a non-empty string, raising DataParseError naming the field if invalid."""
    # Invariant: The value must be a non-empty string type to prevent downstream database identity corruption.
    # Assumption: Inputs are untrusted JSON payload dictionary values.
    # Failure Mode: None, empty string '', or non-str types raise DataParseError.
    if val is None or not isinstance(val, str) or val == "":
        raise DataParseError.invalid_required_string(field_name, val)
    return val


def parse_utc_datetime(date_str: str, time_str: str, field_name: str) -> datetime.datetime:
    """Combine date and time strings to form a tz-aware UTC datetime."""
    val = f"{date_str}T{time_str}"
    try:
        dt = datetime.datetime.fromisoformat(val)
        dt = dt.replace(tzinfo=datetime.UTC) if dt.tzinfo is None else dt.astimezone(datetime.UTC)
    except (ValueError, TypeError) as e:
        raise DataParseError.malformed_coercion("datetime", field_name, val) from e
    else:
        return dt


def parse_session(session_dict: Any, field_name: str) -> datetime.datetime | None:
    """Parse an optional practice or qualifying session block."""
    if session_dict is None:
        return None
    # Invariant: Present-but-falsey values (e.g. {}, [], "", 0, False) represent payload corruption
    # and must raise a DataParseError naming the session key.
    if not session_dict:
        raise DataParseError.present_but_falsey_session(field_name, session_dict)
    if not isinstance(session_dict, dict):
        raise DataParseError.expected_dict_for_session(field_name, type(session_dict).__name__)
    date_str = session_dict.get("date")
    time_str = session_dict.get("time")
    if not date_str:
        raise DataParseError.missing_field(field_name, "date")
    if not time_str:
        raise DataParseError.missing_field(field_name, "time")
    return parse_utc_datetime(date_str, time_str, field_name)


def _unwrap_envelope(payload: dict, table_key: str, list_key: str) -> list[dict]:
    """Unwrap the standard MRData envelope and validate its structural integrity."""
    if not isinstance(payload, dict) or "MRData" not in payload:
        raise DataParseError.missing_envelope()
    mr_data = payload["MRData"]
    if not isinstance(mr_data, dict) or table_key not in mr_data:
        raise DataParseError.missing_table(table_key)
    table = mr_data[table_key]
    if not isinstance(table, dict) or list_key not in table:
        raise DataParseError.missing_container(list_key, table_key)
    items = table[list_key]
    if not isinstance(items, list):
        raise DataParseError.expected_list(list_key, type(items).__name__)
    return items


def _parse_driver(d: dict) -> Driver:
    """Parse a Driver object from a raw dictionary."""
    if not isinstance(d, dict):
        raise DataParseError.expected_dict("Driver")
    for k in ("driverId", "givenName", "familyName"):
        if k not in d:
            raise DataParseError.missing_field("Driver", k)

    driver_id = coerce_required_string(d["driverId"], "driverId")
    given_name = coerce_required_string(d["givenName"], "givenName")
    family_name = coerce_required_string(d["familyName"], "familyName")

    perm_num = d.get("permanentNumber")
    permanent_number = coerce_optional_int(perm_num, "permanentNumber")

    code = d.get("code")
    url = d.get("url")

    dob_str = d.get("dateOfBirth")
    date_of_birth = None
    if dob_str is not None:
        try:
            date_of_birth = datetime.date.fromisoformat(dob_str)
        except (ValueError, TypeError) as e:
            raise DataParseError.malformed_dob(dob_str) from e

    nationality = d.get("nationality")

    return Driver(
        driver_id=driver_id,
        permanent_number=permanent_number,
        code=code,
        url=url,
        given_name=given_name,
        family_name=family_name,
        date_of_birth=date_of_birth,
        nationality=nationality,
    )


def _parse_constructor(c: dict) -> Constructor:
    """Parse a Constructor object from a raw dictionary."""
    if not isinstance(c, dict):
        raise DataParseError.expected_dict("Constructor")
    for k in ("constructorId", "url", "name", "nationality"):
        if k not in c:
            raise DataParseError.missing_field("Constructor", k)
    return Constructor(
        constructor_id=coerce_required_string(c["constructorId"], "constructorId"),
        url=c["url"],
        name=coerce_required_string(c["name"], "name"),
        nationality=c["nationality"],
    )


def _parse_circuit(c: dict) -> Circuit:
    """Parse a Circuit object from a raw dictionary."""
    if not isinstance(c, dict):
        raise DataParseError.expected_dict("Circuit")
    for k in ("circuitId", "url", "circuitName", "Location"):
        if k not in c:
            raise DataParseError.missing_field("Circuit", k)

    loc = c["Location"]
    if not isinstance(loc, dict):
        raise DataParseError.expected_circuit_location()

    for k in ("lat", "long", "locality", "country"):
        if k not in loc:
            raise DataParseError.missing_circuit_location_field(k)

    lat = coerce_float(loc["lat"], "lat")
    long = coerce_float(loc["long"], "long")

    return Circuit(
        circuit_id=coerce_required_string(c["circuitId"], "circuitId"),
        url=c["url"],
        circuit_name=coerce_required_string(c["circuitName"], "circuitName"),
        lat=lat,
        long=long,
        locality=loc["locality"],
        country=loc["country"],
    )


def _parse_race(r: dict) -> Race:
    """Parse a Race object from a raw Grand Prix schedule dictionary."""
    if not isinstance(r, dict):
        raise DataParseError.expected_dict("Race")
    for k in ("season", "round", "url", "raceName", "Circuit", "date", "time"):
        if k not in r:
            raise DataParseError.missing_field("Race", k)

    season = coerce_int(r["season"], "season")
    round_val = coerce_int(r["round"], "round")
    circuit = _parse_circuit(r["Circuit"])

    start = parse_utc_datetime(r["date"], r["time"], "start")

    fp1 = parse_session(r.get("FirstPractice"), "FirstPractice") if "FirstPractice" in r else None
    fp2 = parse_session(r.get("SecondPractice"), "SecondPractice") if "SecondPractice" in r else None
    fp3 = parse_session(r.get("ThirdPractice"), "ThirdPractice") if "ThirdPractice" in r else None
    qualifying = parse_session(r.get("Qualifying"), "Qualifying") if "Qualifying" in r else None
    sprint = parse_session(r.get("Sprint"), "Sprint") if "Sprint" in r else None

    # Invariant: SprintQualifying and SprintShootout are equivalent aliases used
    # in the F1 schedule to define the sprint qualifying session.
    sprint_qualifying = None
    if "SprintQualifying" in r:
        sprint_qualifying = parse_session(r.get("SprintQualifying"), "SprintQualifying")
    elif "SprintShootout" in r:
        sprint_qualifying = parse_session(r.get("SprintShootout"), "SprintShootout")

    return Race(
        season=season,
        round=round_val,
        url=r["url"],
        race_name=coerce_required_string(r["raceName"], "raceName"),
        circuit=circuit,
        start=start,
        fp1=fp1,
        fp2=fp2,
        fp3=fp3,
        qualifying=qualifying,
        sprint=sprint,
        sprint_qualifying=sprint_qualifying,
    )


def _parse_driver_standing(ds: dict) -> DriverStanding:
    """Parse a DriverStanding object from a raw dictionary."""
    if not isinstance(ds, dict):
        raise DataParseError.expected_dict("DriverStanding")
    for k in ("position", "positionText", "points", "wins", "Driver", "Constructors"):
        if k not in ds:
            raise DataParseError.missing_field("DriverStanding", k)

    pos = coerce_int(ds["position"], "position")
    points = coerce_float(ds["points"], "points")
    wins = coerce_int(ds["wins"], "wins")

    driver = _parse_driver(ds["Driver"])

    constructors_list = ds["Constructors"]
    if not isinstance(constructors_list, list):
        raise DataParseError.expected_constructors_list()
    constructors = [_parse_constructor(item) for item in constructors_list]

    return DriverStanding(
        position=pos,
        position_text=coerce_required_string(ds["positionText"], "positionText"),
        points=points,
        wins=wins,
        driver=driver,
        constructors=constructors,
    )


def _parse_constructor_standing(cs: dict) -> ConstructorStanding:
    """Parse a ConstructorStanding object from a raw dictionary."""
    if not isinstance(cs, dict):
        raise DataParseError.expected_dict("ConstructorStanding")
    for k in ("position", "positionText", "points", "wins", "Constructor"):
        if k not in cs:
            raise DataParseError.missing_field("ConstructorStanding", k)

    pos = coerce_int(cs["position"], "position")
    points = coerce_float(cs["points"], "points")
    wins = coerce_int(cs["wins"], "wins")

    constructor = _parse_constructor(cs["Constructor"])

    return ConstructorStanding(
        position=pos,
        position_text=coerce_required_string(cs["positionText"], "positionText"),
        points=points,
        wins=wins,
        constructor=constructor,
    )


def _parse_fastest_lap(fl_dict: dict | None) -> FastestLap | None:
    """Parse an optional FastestLap subobject."""
    if fl_dict is None:
        return None
    if not isinstance(fl_dict, dict):
        raise DataParseError.expected_dict("FastestLap")
    for k in ("lap", "Time"):
        if k not in fl_dict:
            raise DataParseError.missing_field("FastestLap", k)

    fl_lap = coerce_int(fl_dict["lap"], "lap")
    fl_rank = coerce_optional_int(fl_dict.get("rank"), "rank")

    fl_time_dict = fl_dict["Time"]
    if not isinstance(fl_time_dict, dict) or "time" not in fl_time_dict:
        raise DataParseError.expected_fastest_lap_time_dict()

    return FastestLap(
        rank=fl_rank,
        lap=fl_lap,
        time=fl_time_dict["time"],
    )


def _parse_result_time(time_dict: dict | None) -> tuple[int | None, str | None]:
    """Parse race result duration details."""
    if time_dict is None:
        return None, None
    if not isinstance(time_dict, dict):
        raise DataParseError.expected_race_result_time_dict()
    m = time_dict.get("millis")
    time_millis = coerce_optional_int(m, "millis")
    time_str = time_dict.get("time")
    return time_millis, time_str


def _parse_race_result(rr: dict) -> RaceResult:
    """Parse a RaceResult object from a raw dictionary."""
    if not isinstance(rr, dict):
        raise DataParseError.expected_dict("RaceResult")
    for k in ("number", "position", "positionText", "points", "Driver", "Constructor", "grid", "laps", "status"):
        if k not in rr:
            raise DataParseError.missing_field("RaceResult", k)

    number = coerce_int(rr["number"], "number")
    position = coerce_position(rr["position"])
    points = coerce_float(rr["points"], "points")
    grid = coerce_int(rr["grid"], "grid")
    laps = coerce_int(rr["laps"], "laps")

    driver = _parse_driver(rr["Driver"])
    constructor = _parse_constructor(rr["Constructor"])

    time_millis, time_str = _parse_result_time(rr.get("Time"))
    fastest_lap = _parse_fastest_lap(rr.get("FastestLap"))

    return RaceResult(
        number=number,
        position=position,
        position_text=coerce_required_string(rr["positionText"], "positionText"),
        points=points,
        driver=driver,
        constructor=constructor,
        grid=grid,
        laps=laps,
        status=coerce_required_string(rr["status"], "status"),
        time_millis=time_millis,
        time_str=time_str,
        fastest_lap=fastest_lap,
    )


# Boundary parse functions to be exported


def parse_drivers(payload: dict) -> list[Driver]:
    """Parse a list of Driver objects from the standard API payload."""
    items = _unwrap_envelope(payload, "DriverTable", "Drivers")
    return [_parse_driver(item) for item in items]


def parse_constructors(payload: dict) -> list[Constructor]:
    """Parse a list of Constructor objects from the standard API payload."""
    items = _unwrap_envelope(payload, "ConstructorTable", "Constructors")
    return [_parse_constructor(item) for item in items]


def parse_races(payload: dict) -> list[Race]:
    """Parse a list of Race objects from the standard schedule API payload."""
    items = _unwrap_envelope(payload, "RaceTable", "Races")
    return [_parse_race(item) for item in items]


def _parse_standings_lists[T](payload: dict, key: str, parse_item: Callable[[dict], T]) -> list[T]:
    """Unwrap StandingsLists entries and parse each entry's `key` list with parse_item."""
    lists = _unwrap_envelope(payload, "StandingsTable", "StandingsLists")
    result = []
    for s_list in lists:
        if not isinstance(s_list, dict):
            raise DataParseError.expected_standings_lists_entry()
        if key not in s_list:
            raise DataParseError.missing_container(key, "StandingsLists entry")
        standings = s_list[key]
        if not isinstance(standings, list):
            raise DataParseError.expected_list_for(key)
        for item in standings:
            result.append(parse_item(item))
    return result


def parse_driver_standings(payload: dict) -> list[DriverStanding]:
    """Parse a list of DriverStanding objects from the standard API payload."""
    return _parse_standings_lists(payload, "DriverStandings", _parse_driver_standing)


def parse_constructor_standings(payload: dict) -> list[ConstructorStanding]:
    """Parse a list of ConstructorStanding objects from the standard API payload."""
    return _parse_standings_lists(payload, "ConstructorStandings", _parse_constructor_standing)


def parse_results(payload: dict) -> list[RaceResult]:
    """Parse a list of RaceResult objects from the standard results API payload."""
    races = _unwrap_envelope(payload, "RaceTable", "Races")
    result = []
    for race in races:
        if not isinstance(race, dict):
            raise DataParseError.expected_race_entry()
        if "Results" not in race:
            raise DataParseError.missing_container("Results", "Race entry")
        results_list = race["Results"]
        if not isinstance(results_list, list):
            raise DataParseError.expected_list_for("Results")
        for item in results_list:
            result.append(_parse_race_result(item))
    return result
