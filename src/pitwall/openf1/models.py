import functools
import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from pitwall.errors import DataParseError
from pitwall.models import (
    coerce_float,
    coerce_int,
    coerce_optional_int,
    coerce_required_string,
)
from pitwall.openf1.errors import OpenF1DataError


@dataclass(frozen=True)
class SessionDriver:
    driver_number: int
    name_acronym: str
    full_name: str
    team_name: str
    team_colour: str | None = None


@dataclass(frozen=True)
class Stint:
    driver_number: int
    stint_number: int
    compound: str | None
    lap_start: int
    lap_end: int
    tyre_age_at_start: int | None


@dataclass(frozen=True)
class Lap:
    driver_number: int
    lap_number: int
    date_start: datetime | None
    lap_duration: float | None


@dataclass(frozen=True)
class PositionUpdate:
    date: datetime
    driver_number: int
    position: int


@dataclass(frozen=True)
class IntervalPoint:
    date: datetime
    driver_number: int
    gap_to_leader: float | str | None
    interval: float | str | None


@dataclass(frozen=True)
class PitStop:
    date: datetime
    driver_number: int
    lap_number: int | None
    pit_duration: float | None


@dataclass(frozen=True)
class RaceControlMessage:
    date: datetime
    message: str
    category: str | None
    flag: str | None
    scope: str | None
    lap_number: int | None
    driver_number: int | None


def get_required(d: dict[str, Any], field_name: str, entity: str) -> Any:
    """Extract required field from a dictionary or raise DataParseError."""
    if field_name not in d:
        raise DataParseError.missing_field(entity, field_name)
    return d[field_name]


def parse_timestamp(val: Any, field_name: str) -> datetime:
    """Parse ISO-8601 string to localized UTC datetime, or raise DataParseError."""
    if not isinstance(val, str) or not val:
        raise DataParseError.malformed_coercion("datetime", field_name, val)
    try:
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
    except ValueError as e:
        raise DataParseError.malformed_coercion("datetime", field_name, val) from e
    else:
        return dt


def parse_optional_timestamp(val: Any, field_name: str) -> datetime | None:
    """Parse ISO-8601 string to localized UTC datetime or return None if absent/empty."""
    if val is None or val == "":
        return None
    return parse_timestamp(val, field_name)


def _optional_float(val: Any, field_name: str) -> float | None:
    """Coerce value to float or return None if empty/absent, validating finiteness."""
    if val is None or val == "":
        return None
    return coerce_float(val, field_name)


def _optional_string(val: Any, field_name: str) -> str | None:
    """Coerce value to string or return None if empty/absent."""
    if val is None or val == "":
        return None
    if not isinstance(val, str):
        raise DataParseError.invalid_required_string(field_name, val)
    return val


def _gap_value(val: Any, field_name: str) -> float | str | None:
    """Coerce gap/interval value which can be float, string like '+1 LAP', or None."""
    if val is None or val == "":
        return None
    if isinstance(val, bool):
        raise DataParseError.malformed_coercion("gap_value", field_name, val)
    if isinstance(val, (int, float)):
        if not math.isfinite(val):
            raise DataParseError.malformed_coercion("gap_value", field_name, val)
        return float(val)
    if isinstance(val, str):
        return val
    raise DataParseError.malformed_coercion("gap_value", field_name, val)


def _openf1_parse_boundary(fn):
    """Convert shared-boundary DataParseError into the bridged OpenF1DataError."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except OpenF1DataError:
            raise
        except DataParseError as exc:
            raise OpenF1DataError(str(exc)) from exc

    return wrapper


def _parse_records(data: Any, list_name: str, entity: str, build: Callable[[dict[str, Any]], Any]) -> list[Any]:
    """Validate list-of-dict shape and build one record per element.

    Shared scaffolding for the per-stream parsers; error behavior is identical
    to the previously inlined loops.
    """
    # Loop Bound: bounded by length of data list.
    # Failure Modes: raises DataParseError if data is not a list, if any element
    # is not a dict, or if build rejects an element's fields.
    if not isinstance(data, list):
        raise DataParseError.expected_list(list_name, type(data).__name__)
    result = []
    for d in data:
        if not isinstance(d, dict):
            raise DataParseError.expected_dict(entity)
        result.append(build(d))
    return result


def _required_timestamp(d: dict[str, Any], field: str, entity: str) -> datetime:
    """Extract a required, non-empty field and parse it as a timestamp."""
    val = get_required(d, field, entity)
    if val is None or val == "":
        raise DataParseError.malformed_coercion("datetime", field, val)
    return parse_timestamp(val, field)


@_openf1_parse_boundary
def parse_drivers(data: Any) -> list[SessionDriver]:
    """Parse list of driver dictionaries into SessionDriver instances."""
    return _parse_records(
        data,
        "drivers",
        "driver",
        lambda d: SessionDriver(
            driver_number=coerce_int(get_required(d, "driver_number", "driver"), "driver_number"),
            name_acronym=coerce_required_string(get_required(d, "name_acronym", "driver"), "name_acronym"),
            full_name=coerce_required_string(get_required(d, "full_name", "driver"), "full_name"),
            team_name=coerce_required_string(get_required(d, "team_name", "driver"), "team_name"),
            team_colour=_optional_string(d.get("team_colour"), "team_colour"),
        ),
    )


@_openf1_parse_boundary
def parse_stints(data: Any) -> list[Stint]:
    """Parse list of stint dictionaries into Stint instances."""
    return _parse_records(
        data,
        "stints",
        "stint",
        lambda d: Stint(
            driver_number=coerce_int(get_required(d, "driver_number", "stint"), "driver_number"),
            stint_number=coerce_int(get_required(d, "stint_number", "stint"), "stint_number"),
            compound=_optional_string(d.get("compound"), "compound"),
            lap_start=coerce_int(get_required(d, "lap_start", "stint"), "lap_start"),
            lap_end=coerce_int(get_required(d, "lap_end", "stint"), "lap_end"),
            tyre_age_at_start=coerce_optional_int(d.get("tyre_age_at_start"), "tyre_age_at_start"),
        ),
    )


@_openf1_parse_boundary
def parse_laps(data: Any) -> list[Lap]:
    """Parse list of lap dictionaries into Lap instances."""
    return _parse_records(
        data,
        "laps",
        "lap",
        lambda d: Lap(
            driver_number=coerce_int(get_required(d, "driver_number", "lap"), "driver_number"),
            lap_number=coerce_int(get_required(d, "lap_number", "lap"), "lap_number"),
            date_start=parse_optional_timestamp(d.get("date_start"), "date_start"),
            lap_duration=_optional_float(d.get("lap_duration"), "lap_duration"),
        ),
    )


@_openf1_parse_boundary
def parse_position(data: Any) -> list[PositionUpdate]:
    """Parse list of position dictionaries into PositionUpdate instances."""
    return _parse_records(
        data,
        "position",
        "position",
        lambda d: PositionUpdate(
            date=parse_timestamp(get_required(d, "date", "position"), "date"),
            driver_number=coerce_int(get_required(d, "driver_number", "position"), "driver_number"),
            position=coerce_int(get_required(d, "position", "position"), "position"),
        ),
    )


@_openf1_parse_boundary
def parse_intervals(data: Any) -> list[IntervalPoint]:
    """Parse list of interval dictionaries into IntervalPoint instances."""
    return _parse_records(
        data,
        "intervals",
        "interval",
        lambda d: IntervalPoint(
            date=parse_timestamp(get_required(d, "date", "interval"), "date"),
            driver_number=coerce_int(get_required(d, "driver_number", "interval"), "driver_number"),
            gap_to_leader=_gap_value(d.get("gap_to_leader"), "gap_to_leader"),
            interval=_gap_value(d.get("interval"), "interval"),
        ),
    )


@_openf1_parse_boundary
def parse_pit(data: Any) -> list[PitStop]:
    """Parse list of pit stop dictionaries into PitStop instances."""
    return _parse_records(
        data,
        "pit",
        "pit",
        lambda d: PitStop(
            date=parse_timestamp(get_required(d, "date", "pit"), "date"),
            driver_number=coerce_int(get_required(d, "driver_number", "pit"), "driver_number"),
            lap_number=coerce_optional_int(d.get("lap_number"), "lap_number"),
            pit_duration=_optional_float(d.get("pit_duration"), "pit_duration"),
        ),
    )


@_openf1_parse_boundary
def parse_race_control(data: Any) -> list[RaceControlMessage]:
    """Parse list of race control dictionaries into RaceControlMessage instances."""
    return _parse_records(
        data,
        "race_control",
        "race_control",
        lambda d: RaceControlMessage(
            date=parse_timestamp(get_required(d, "date", "race_control"), "date"),
            message=coerce_required_string(get_required(d, "message", "race_control"), "message"),
            category=_optional_string(d.get("category"), "category"),
            flag=_optional_string(d.get("flag"), "flag"),
            scope=_optional_string(d.get("scope"), "scope"),
            lap_number=coerce_optional_int(d.get("lap_number"), "lap_number"),
            driver_number=coerce_optional_int(d.get("driver_number"), "driver_number"),
        ),
    )


@dataclass(frozen=True)
class LocationPoint:
    date: datetime
    driver_number: int
    x: float
    y: float


@_openf1_parse_boundary
def parse_location(data: Any) -> list[LocationPoint]:
    """Parse list of location dictionaries into LocationPoint instances."""
    # Loop Bound: bounded by length of data list (typically 500-1000 items in excerpt, up to 25k).
    # Invariants: x and y coordinates are finite floats representing track coordinates.
    # Failure Modes: throws DataParseError if data is not list, or if required fields are missing,
    # or if coordinates are non-finite or boolean values.
    return _parse_records(
        data,
        "location",
        "location",
        lambda d: LocationPoint(
            date=parse_timestamp(get_required(d, "date", "location"), "date"),
            driver_number=coerce_int(get_required(d, "driver_number", "location"), "driver_number"),
            x=coerce_float(get_required(d, "x", "location"), "x"),
            y=coerce_float(get_required(d, "y", "location"), "y"),
        ),
    )


@dataclass(frozen=True)
class Session:
    session_key: int
    meeting_key: int
    session_name: str
    date_start: datetime
    date_end: datetime


@_openf1_parse_boundary
def parse_sessions(data: Any) -> list[Session]:
    """Parse list of session dictionaries into Session instances."""
    # Loop Bound: Bounded by the number of dictionary items in the input list.
    # Invariants: Every parsed Session has a valid, non-negative integer for session_key and meeting_key,
    # a non-empty name string, and timezone-aware datetimes for date_start and date_end.
    # Failure Modes: Raises DataParseError if data is not a list, if any list element is not a dict,
    # if required keys are missing, if types cannot be coerced, or if datetime strings are malformed.
    return _parse_records(
        data,
        "sessions",
        "session",
        lambda d: Session(
            session_key=coerce_int(get_required(d, "session_key", "session"), "session_key"),
            meeting_key=coerce_int(get_required(d, "meeting_key", "session"), "meeting_key"),
            session_name=coerce_required_string(get_required(d, "session_name", "session"), "session_name"),
            date_start=_required_timestamp(d, "date_start", "session"),
            date_end=_required_timestamp(d, "date_end", "session"),
        ),
    )
