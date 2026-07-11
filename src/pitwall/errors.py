from typing import Any


class JolpicaError(Exception):
    """Base exception for all Jolpica-related errors."""


class JolpicaHttpError(JolpicaError):
    """Exception raised for non-200/non-429 HTTP responses from the Jolpica API."""

    def __init__(self, status: int) -> None:
        super().__init__(f"HTTP request failed with status: {status}")
        self.status = status


class JolpicaNetworkError(JolpicaError):
    """Exception raised for transport-level errors when communicating with the Jolpica API."""

    def __init__(self, cause: Exception | str | None = None) -> None:
        if cause:
            super().__init__(f"Transport error communicating with Jolpica API: {cause}")
        else:
            super().__init__("Transport error communicating with Jolpica API")


class RateLimitedError(JolpicaError):
    """Exception raised when the client is rate-limited (HTTP 429) after all retry attempts are exhausted."""

    def __init__(self) -> None:
        super().__init__("Rate limit exceeded after maximum retry attempts.")


class DataParseError(JolpicaError):
    """Exception raised when payload validation, coercion, or envelope structure checks fail."""

    def __init__(self, message: str = "Data parse error") -> None:
        super().__init__(message)

    @classmethod
    def missing_envelope(cls) -> "DataParseError":
        return cls("Missing 'MRData' envelope in payload")

    @classmethod
    def missing_table(cls, table_key: str) -> "DataParseError":
        return cls(f"Missing '{table_key}' in MRData envelope")

    @classmethod
    def expected_list(cls, list_key: str, got_type: str) -> "DataParseError":
        return cls(f"Expected list for '{list_key}', got {got_type}")

    @classmethod
    def expected_dict(cls, entity: str) -> "DataParseError":
        return cls(f"Expected dictionary for {entity}")

    @classmethod
    def missing_field(cls, entity: str, field: str) -> "DataParseError":
        return cls(f"Missing required {entity} field: '{field}'")

    @classmethod
    def present_but_falsey_session(cls, key: str, val: Any) -> "DataParseError":
        return cls(f"Present-but-falsey session block for '{key}': {val}")

    @classmethod
    def expected_dict_for_session(cls, key: str, got_type: str) -> "DataParseError":
        return cls(f"Expected dict for session block '{key}', got {got_type}")

    @classmethod
    def malformed_dob(cls, dob_str: str) -> "DataParseError":
        return cls(f"Malformed dateOfBirth: '{dob_str}'")

    @classmethod
    def malformed_coercion(cls, type_name: str, field: str, val: Any) -> "DataParseError":
        if type_name == "datetime":
            return cls(f"Malformed datetime for field '{field}': {val}")
        return cls(f"Malformed {type_name} value for field '{field}': {val}")

    @classmethod
    def invalid_json(cls) -> "DataParseError":
        return cls("Invalid JSON response body")

    @classmethod
    def malformed_total(cls, cause: Exception) -> "DataParseError":
        return cls(f"Malformed or missing total in MRData envelope: {cause}")

    @classmethod
    def pagination_overflow(cls, total: int, records_count: int) -> "DataParseError":
        return cls(f"Pagination overflow: MRData total ({total}) exceeds returned records ({records_count})")

    @classmethod
    def expected_dict_with_time(cls, entity: str) -> "DataParseError":
        return cls(f"Expected dictionary with 'time' for {entity}")

    @classmethod
    def expected_constructors_list(cls) -> "DataParseError":
        return cls("Expected list for Constructors in DriverStanding")

    @classmethod
    def missing_container(cls, container: str, parent: str) -> "DataParseError":
        return cls(f"Missing '{container}' in {parent}")

    @classmethod
    def expected_list_for(cls, field: str) -> "DataParseError":
        return cls(f"Expected list for '{field}'")

    @classmethod
    def expected_circuit_location(cls) -> "DataParseError":
        return cls("Expected dictionary for Circuit Location")

    @classmethod
    def missing_circuit_location_field(cls, field: str) -> "DataParseError":
        return cls(f"Missing required Circuit Location field: '{field}'")

    @classmethod
    def expected_fastest_lap_time_dict(cls) -> "DataParseError":
        return cls("Expected dictionary with 'time' for FastestLap Time")

    @classmethod
    def expected_race_result_time_dict(cls) -> "DataParseError":
        return cls("Expected dictionary for RaceResult Time")

    @classmethod
    def expected_standings_lists_entry(cls) -> "DataParseError":
        return cls("Expected dictionary for StandingsLists entry")

    @classmethod
    def expected_race_entry(cls) -> "DataParseError":
        return cls("Expected dictionary for Race entry")

    @classmethod
    def invalid_required_string(cls, field: str, val: Any) -> "DataParseError":
        return cls(f"Field '{field}' must be a non-empty string, got {val!r}")
