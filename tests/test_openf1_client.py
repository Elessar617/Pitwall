import httpx
import pytest
from conftest import wrap_transport

from pitwall import __version__
from pitwall.openf1.client import OpenF1Client, build_query
from pitwall.openf1.errors import (
    OpenF1HttpError,
    OpenF1NetworkError,
    OpenF1RateLimitedError,
)


def test_build_query_literal():
    # AC-2a: build_query byte-equal literal with percent-encoded operators in param NAMES
    params = {"session_key": 11291, "driver_number": 1}
    filters = [
        ("date", ">", "2026-05-24T20:00:00"),
        ("date", "<", "2026-05-24T20:10:00"),
    ]
    query = build_query(params, filters)
    assert query == "session_key=11291&driver_number=1&date%3E2026-05-24T20:00:00&date%3C2026-05-24T20:10:00"

    # Unsupported operator (>=) raises ValueError
    with pytest.raises(ValueError):
        build_query({"session_key": 11291}, [("date", ">=", "2026-05-24T20:00:00")])


@pytest.mark.asyncio
async def test_404_yields_empty_list() -> None:
    # AC-2b: On MockTransport: a 404 response yields [] from every get_* method, raising nothing
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not Found")

    transport = wrap_transport(handler)
    async with OpenF1Client(transport=transport) as client:
        assert await client.get_drivers(session_key=11291) == []
        assert await client.get_laps(session_key=11291) == []
        assert await client.get_intervals(session_key=11291) == []
        assert await client.get_position(session_key=11291) == []
        assert await client.get_stints(session_key=11291) == []
        assert await client.get_pit(session_key=11291) == []
        assert await client.get_race_control(session_key=11291) == []


@pytest.mark.asyncio
async def test_429_retry_and_success() -> None:
    # AC-2c: A 429-then-200 sequence retries with recorded injected sleeps [1.0] then succeeds
    responses = [
        httpx.Response(429, text="Too Many Requests"),
        httpx.Response(200, json=[]),
    ]
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        resp = responses[request_count]
        request_count += 1
        return resp

    recorded_sleeps = []

    async def fake_sleep(seconds: float) -> None:
        recorded_sleeps.append(seconds)

    transport = wrap_transport(handler)
    async with OpenF1Client(transport=transport, sleep=fake_sleep) as client:
        res = await client.get_laps(session_key=11291)

    assert res == []
    assert request_count == 2
    assert recorded_sleeps == [1.0]


@pytest.mark.asyncio
async def test_429_retry_exhaustion() -> None:
    # AC-2c: four 429s raise OpenF1RateLimitedError after recorded sleeps [1.0, 2.0, 4.0]
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(429, text="Too Many Requests")

    recorded_sleeps = []

    async def fake_sleep(seconds: float) -> None:
        recorded_sleeps.append(seconds)

    transport = wrap_transport(handler)
    async with OpenF1Client(transport=transport, sleep=fake_sleep) as client:
        with pytest.raises(OpenF1RateLimitedError):
            await client.get_laps(session_key=11291)

    assert request_count == 4
    assert recorded_sleeps == [1.0, 2.0, 4.0]


@pytest.mark.asyncio
async def test_500_raises_http_error() -> None:
    # AC-2c: a 500 raises OpenF1HttpError carrying the status
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport = wrap_transport(handler)
    async with OpenF1Client(transport=transport) as client:
        with pytest.raises(OpenF1HttpError) as exc_info:
            await client.get_laps(session_key=11291)
        assert exc_info.value.status == 500


@pytest.mark.asyncio
async def test_transport_error_raises_network_error() -> None:
    # AC-2c: a transport error raises OpenF1NetworkError
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection failed")  # noqa: TRY003

    transport = wrap_transport(handler)
    async with OpenF1Client(transport=transport) as client:
        with pytest.raises(OpenF1NetworkError):
            await client.get_laps(session_key=11291)


@pytest.mark.asyncio
async def test_request_shape_and_user_agent() -> None:
    # AC-2d: The recorded request for get_laps(...) has URL query matching build_query and User-Agent header pitwall/<version>
    recorded_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=[])

    transport = wrap_transport(handler)
    async with OpenF1Client(transport=transport) as client:
        await client.get_laps(
            session_key=11291,
            date_gt="2026-05-24T20:00:00",
            date_lt="2026-05-24T20:10:00",
        )

    assert len(recorded_requests) == 1
    req = recorded_requests[0]
    assert req.method == "GET"
    # The URL query path should contain the percent-encoded filters exactly
    # Since date_gt and date_lt are rendered as:
    # date%3E2026-05-24T20:00:00 and date%3C2026-05-24T20:10:00
    # Let's check the query portion of the URL
    query_str = req.url.query.decode("utf-8")
    # For openf1 client, get_laps(session_key=11291, date_gt=..., date_lt=...) is expected to build the query.
    # The query should be: session_key=11291&date%3E2026-05-24T20:00:00&date%3C2026-05-24T20:10:00
    assert query_str == "session_key=11291&date%3E2026-05-24T20:00:00&date%3C2026-05-24T20:10:00"
    assert req.headers.get("user-agent") == f"pitwall/{__version__}"


@pytest.mark.asyncio
async def test_client_close_and_other_endpoints_filters() -> None:
    recorded_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=[])

    transport = wrap_transport(handler)
    client = OpenF1Client(transport=transport)
    try:
        await client.get_drivers(11291, date_gt="2026-05-24T20:00:00", date_lt="2026-05-24T20:10:00")
        await client.get_stints(11291, date_gt="2026-05-24T20:00:00", date_lt="2026-05-24T20:10:00")
        await client.get_position(11291, date_gt="2026-05-24T20:00:00", date_lt="2026-05-24T20:10:00")
        await client.get_intervals(11291, date_gt="2026-05-24T20:00:00", date_lt="2026-05-24T20:10:00")
        await client.get_pit(11291, date_gt="2026-05-24T20:00:00", date_lt="2026-05-24T20:10:00")
        await client.get_race_control(11291, date_gt="2026-05-24T20:00:00", date_lt="2026-05-24T20:10:00")
    finally:
        await client.close()

    assert len(recorded_requests) == 6
    for req in recorded_requests:
        query_str = req.url.query.decode("utf-8")
        assert query_str == "session_key=11291&date%3E2026-05-24T20:00:00&date%3C2026-05-24T20:10:00"


def test_client_constants():
    # AC-7: BASE_URL and MAX_RETRIES exported and correct
    import pitwall.openf1.client as client

    assert client.BASE_URL == "https://api.openf1.org/v1"
    assert client.MAX_RETRIES == 3


@pytest.mark.asyncio
async def test_get_sessions_latest() -> None:
    # AC-2a: get_sessions('latest') byte-exact URL + parse + 404->[]
    recorded_requests = []
    mock_record = {
        "session_key": 11291,
        "meeting_key": 1285,
        "session_name": "Race",
        "session_type": "Race",
        "date_start": "2026-05-24T19:00:00+00:00",
        "date_end": "2026-05-24T21:00:00+00:00",
        "circuit_short_name": "Montreal",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=[mock_record])

    transport = wrap_transport(handler)
    async with OpenF1Client(transport=transport) as client:
        sessions = await client.get_sessions("latest")

    assert len(recorded_requests) == 1
    assert str(recorded_requests[0].url) == "https://api.openf1.org/v1/sessions?session_key=latest"
    assert len(sessions) == 1
    assert sessions[0].session_key == 11291


@pytest.mark.asyncio
async def test_get_sessions_404() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not Found")

    transport = wrap_transport(handler)
    async with OpenF1Client(transport=transport) as client:
        assert await client.get_sessions("latest") == []


@pytest.mark.asyncio
async def test_get_location_filtering() -> None:
    # AC-2b: get_location URL with driver_number and date filters, driver_number omitted when None
    recorded_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=[])

    transport = wrap_transport(handler)
    async with OpenF1Client(transport=transport) as client:
        await client.get_location(11291, driver_number=1, date_gt="2026-05-24T20:00:00", date_lt="2026-05-24T20:10:00")
        await client.get_location(11291, driver_number=None, date_gt="2026-05-24T20:00:00")

    assert len(recorded_requests) == 2

    url1 = str(recorded_requests[0].url)
    assert (
        url1
        == "https://api.openf1.org/v1/location?session_key=11291&driver_number=1&date%3E2026-05-24T20:00:00&date%3C2026-05-24T20:10:00"
    )

    url2 = str(recorded_requests[1].url)
    assert url2 == "https://api.openf1.org/v1/location?session_key=11291&date%3E2026-05-24T20:00:00"


def test_f16_single_helper_delegation():
    # AC-2c: F16 single-helper delegation (inspect: all nine get_* methods route through one private helper)
    import inspect

    from pitwall.openf1.client import OpenF1Client

    methods = [
        "get_drivers",
        "get_stints",
        "get_laps",
        "get_position",
        "get_intervals",
        "get_pit",
        "get_race_control",
        "get_sessions",
        "get_location",
    ]
    for method_name in methods:
        method = getattr(OpenF1Client, method_name)
        source = inspect.getsource(method)
        assert "self._get_stream" in source or "_get_stream" in source


def test_f14_grep_contract():
    # AC-2d: F14 grep contract via reading the file source (exactly one 'return []')
    import pathlib
    import re

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    client_path = repo_root / "src" / "pitwall" / "openf1" / "client.py"
    source = client_path.read_text(encoding="utf-8")
    matches = re.findall(r"return\s+\[\]", source)
    assert len(matches) == 1, f"Expected exactly one 'return []' statement, found {len(matches)}"


# ---- iter15 AC-1: non-JSON bodies are contained in the OpenF1 taxonomy ----


async def test_non_json_body_raises_openf1_error():
    from conftest import wrap_transport

    from pitwall.openf1 import OpenF1Client
    from pitwall.openf1.errors import OpenF1Error

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>downtime</html>")

    async with OpenF1Client(transport=wrap_transport(handler)) as client:
        with pytest.raises(OpenF1Error):
            await client.get_position(11291)
