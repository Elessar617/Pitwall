from pitwall.errors import DataParseError


class OpenF1Error(Exception):
    """Base exception for all OpenF1-related errors."""


class ReplayDataError(OpenF1Error):
    """Exception raised when loading or parsing replay data fails."""


class OpenF1HttpError(OpenF1Error):
    """Exception raised for non-200 HTTP responses from the OpenF1 API."""

    def __init__(self, status: int, message: str = "") -> None:
        super().__init__(message or f"HTTP request failed with status: {status}")
        self.status = status


class OpenF1RateLimitedError(OpenF1Error):
    """Exception raised when the client is rate-limited (HTTP 429) after retries are exhausted."""

    def __init__(self, message: str = "Rate limit exceeded after maximum retry attempts.") -> None:
        super().__init__(message)


class OpenF1NetworkError(OpenF1Error):
    """Exception raised for transport-level errors when communicating with the OpenF1 API."""

    def __init__(self, cause: Exception | str | None = None) -> None:
        suffix = f": {cause}" if cause else ""
        super().__init__(f"Transport error communicating with OpenF1 API{suffix}")


class OpenF1DataError(DataParseError, OpenF1Error):
    """Parse failure in an OpenF1 payload — a member of BOTH error taxonomies.

    Bridges the shared coercion boundary (which raises DataParseError, a
    JolpicaError) into the OpenF1 family so per-stream containment that
    catches OpenF1Error also contains malformed live data.
    """
