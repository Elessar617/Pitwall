from pitwall.errors import (
    DataParseError,
    JolpicaError,
    JolpicaHttpError,
    JolpicaNetworkError,
    RateLimitedError,
)


def test_error_hierarchy() -> None:
    """Verify exception hierarchy contract: all custom errors must subclass JolpicaError."""
    # Invariant: All domain-specific error classes must inherit from JolpicaError to allow unified catching.
    assert issubclass(JolpicaHttpError, JolpicaError)
    assert issubclass(JolpicaNetworkError, JolpicaError)
    assert issubclass(RateLimitedError, JolpicaError)
    assert issubclass(DataParseError, JolpicaError)
    assert issubclass(JolpicaError, Exception)


def test_http_error_initialization() -> None:
    """Verify HTTP status code extraction and standard error message formatting."""
    # Invariant: JolpicaHttpError must capture the raw integer status code for downstream retry/fallback decisions.
    err = JolpicaHttpError(404)
    assert err.status == 404
    assert str(err) == "HTTP request failed with status: 404"
