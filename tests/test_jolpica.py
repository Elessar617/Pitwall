import httpx
import pytest
from conftest import wrap_transport

from pitwall import __version__
from pitwall.api.jolpica import JolpicaClient
from pitwall.errors import (
    DataParseError,
    JolpicaHttpError,
    JolpicaNetworkError,
    RateLimitedError,
)
from pitwall.models import (
    Constructor,
    ConstructorStanding,
    Driver,
    DriverStanding,
    Race,
    RaceResult,
)


@pytest.mark.asyncio
async def test_get_races_success(jolpica_payload) -> None:
    """AC-06: get_races issues GET to /f1/{season}/races/, unwraps MRData, and returns list of Race."""
    # Invariant: Offline testing demands all HTTP calls are intercepted by httpx.MockTransport.
    recorded_requests = []
    payload = jolpica_payload("races")

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=payload)

    transport = wrap_transport(handler)
    async with JolpicaClient(transport=transport) as client:
        races = await client.get_races(season=2026)

    # Assert model types and expected fixture counts (22 races)
    assert len(races) == 22
    assert all(isinstance(r, Race) for r in races)

    # Verify request metadata
    assert len(recorded_requests) == 1
    req = recorded_requests[0]
    assert req.method == "GET"
    assert req.url.path == "/ergast/f1/2026/races/"
    assert req.url.params.get("limit") == "100"
    assert req.headers.get("user-agent") == f"pitwall/{__version__}"


@pytest.mark.asyncio
async def test_get_driver_standings_success(jolpica_payload) -> None:
    """AC-06: get_driver_standings issues GET to /f1/{season}/driverstandings/, unwraps MRData, and returns list of DriverStanding."""
    # Invariant: Offline testing demands all HTTP calls are intercepted by httpx.MockTransport.
    recorded_requests = []
    payload = jolpica_payload("driverstandings")

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=payload)

    transport = wrap_transport(handler)
    async with JolpicaClient(transport=transport) as client:
        standings = await client.get_driver_standings(season=2026)

    # Assert model types and expected fixture counts (22 driver standings)
    assert len(standings) == 22
    assert all(isinstance(s, DriverStanding) for s in standings)

    # Verify request metadata
    assert len(recorded_requests) == 1
    req = recorded_requests[0]
    assert req.method == "GET"
    assert req.url.path == "/ergast/f1/2026/driverstandings/"
    assert req.url.params.get("limit") == "100"
    assert req.headers.get("user-agent") == f"pitwall/{__version__}"


@pytest.mark.asyncio
async def test_get_constructor_standings_success(jolpica_payload) -> None:
    """AC-06: get_constructor_standings issues GET to /f1/{season}/constructorstandings/, unwraps MRData, and returns list of ConstructorStanding."""
    # Invariant: Offline testing demands all HTTP calls are intercepted by httpx.MockTransport.
    recorded_requests = []
    payload = jolpica_payload("constructorstandings")

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=payload)

    transport = wrap_transport(handler)
    async with JolpicaClient(transport=transport) as client:
        standings = await client.get_constructor_standings(season=2026)

    # Assert model types and expected fixture counts (11 constructor standings)
    assert len(standings) == 11
    assert all(isinstance(s, ConstructorStanding) for s in standings)

    # Verify request metadata
    assert len(recorded_requests) == 1
    req = recorded_requests[0]
    assert req.method == "GET"
    assert req.url.path == "/ergast/f1/2026/constructorstandings/"
    assert req.url.params.get("limit") == "100"
    assert req.headers.get("user-agent") == f"pitwall/{__version__}"


@pytest.mark.asyncio
async def test_get_results_success(jolpica_payload) -> None:
    """AC-06: get_results issues GET to /f1/{season}/{round}/results/, unwraps MRData, and returns list of RaceResult."""
    # Invariant: Offline testing demands all HTTP calls are intercepted by httpx.MockTransport.
    recorded_requests = []
    payload = jolpica_payload("results")

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=payload)

    transport = wrap_transport(handler)
    async with JolpicaClient(transport=transport) as client:
        results = await client.get_results(season=2026, round=6)

    # Assert model types and expected fixture counts (22 race results)
    assert len(results) == 22
    assert all(isinstance(r, RaceResult) for r in results)

    # Verify request metadata
    assert len(recorded_requests) == 1
    req = recorded_requests[0]
    assert req.method == "GET"
    assert req.url.path == "/ergast/f1/2026/6/results/"
    assert req.url.params.get("limit") == "100"
    assert req.headers.get("user-agent") == f"pitwall/{__version__}"


@pytest.mark.asyncio
async def test_get_drivers_success(jolpica_payload) -> None:
    """AC-06: get_drivers issues GET to /f1/{season}/drivers/, unwraps MRData, and returns list of Driver."""
    # Invariant: Offline testing demands all HTTP calls are intercepted by httpx.MockTransport.
    recorded_requests = []
    payload = jolpica_payload("drivers")

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=payload)

    transport = wrap_transport(handler)
    async with JolpicaClient(transport=transport) as client:
        drivers = await client.get_drivers(season=2026)

    # Assert model types and expected fixture counts (23 drivers)
    assert len(drivers) == 23
    assert all(isinstance(d, Driver) for d in drivers)

    # Verify request metadata
    assert len(recorded_requests) == 1
    req = recorded_requests[0]
    assert req.method == "GET"
    assert req.url.path == "/ergast/f1/2026/drivers/"
    assert req.url.params.get("limit") == "100"
    assert req.headers.get("user-agent") == f"pitwall/{__version__}"


@pytest.mark.asyncio
async def test_get_constructors_success(jolpica_payload) -> None:
    """AC-06: get_constructors issues GET to /f1/{season}/constructors/, unwraps MRData, and returns list of Constructor."""
    # Invariant: Offline testing demands all HTTP calls are intercepted by httpx.MockTransport.
    recorded_requests = []
    payload = jolpica_payload("constructors")

    def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        return httpx.Response(200, json=payload)

    transport = wrap_transport(handler)
    async with JolpicaClient(transport=transport) as client:
        constructors = await client.get_constructors(season=2026)

    # Assert model types and expected fixture counts (11 constructors)
    assert len(constructors) == 11
    assert all(isinstance(c, Constructor) for c in constructors)

    # Verify request metadata
    assert len(recorded_requests) == 1
    req = recorded_requests[0]
    assert req.method == "GET"
    assert req.url.path == "/ergast/f1/2026/constructors/"
    assert req.url.params.get("limit") == "100"
    assert req.headers.get("user-agent") == f"pitwall/{__version__}"


@pytest.mark.asyncio
async def test_http_failure_raises_jolpica_http_error() -> None:
    """AC-07: A non-200/non-429 response raises JolpicaHttpError carrying the status code."""

    # Invariant: JolpicaHttpError must extract and preserve the raw HTTP status code for upstream logic.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport = wrap_transport(handler)
    async with JolpicaClient(transport=transport) as client:
        with pytest.raises(JolpicaHttpError) as exc_info:
            await client.get_races(season=2026)

    assert exc_info.value.status == 500
    assert str(exc_info.value) == "HTTP request failed with status: 500"


@pytest.mark.asyncio
async def test_transport_failure_raises_jolpica_network_error() -> None:
    """AC-07: A transport-level failure raises JolpicaNetworkError chaining the original exception."""

    # Invariant: Network connection exceptions must be caught and chained explicitly using raise from.
    def handler(request: httpx.Request) -> httpx.Response:
        exc = httpx.ConnectError("Connection timed out")
        raise exc

    transport = wrap_transport(handler)
    async with JolpicaClient(transport=transport) as client:
        with pytest.raises(JolpicaNetworkError) as exc_info:
            await client.get_races(season=2026)

    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)


@pytest.mark.asyncio
async def test_invalid_json_body_raises_data_parse_error() -> None:
    """AC-07: A 200 response with a non-JSON body raises DataParseError."""

    # Invariant: Response payload must be syntactically valid JSON.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="Not JSON content")

    transport = wrap_transport(handler)
    async with JolpicaClient(transport=transport) as client:
        with pytest.raises(DataParseError):
            await client.get_races(season=2026)


@pytest.mark.asyncio
async def test_missing_mrdata_envelope_raises_data_parse_error() -> None:
    """AC-07: A 200 response with JSON but missing the MRData envelope raises DataParseError."""

    # Invariant: Response payload must conform to the Ergast/Jolpica envelope structure containing the MRData key.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"UnexpectedData": {}})

    transport = wrap_transport(handler)
    async with JolpicaClient(transport=transport) as client:
        with pytest.raises(DataParseError):
            await client.get_races(season=2026)


@pytest.mark.asyncio
async def test_retry_backoff_on_429_success(jolpica_payload) -> None:
    """AC-08: Scripted response sequence of 429, 429, 200 succeeds with backoff times [1.0, 2.0]."""
    # Invariant: Bounded exponential backoff must sleep for exact computed intervals (1.0s, 2.0s) and resolve successfully.
    responses = [
        httpx.Response(429, text="Too Many Requests"),
        httpx.Response(429, text="Too Many Requests"),
        httpx.Response(200, json=jolpica_payload("races")),
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
    async with JolpicaClient(transport=transport, sleep=fake_sleep) as client:
        races = await client.get_races(season=2026)

    assert len(races) == 22
    assert request_count == 3
    assert recorded_sleeps == [1.0, 2.0]


@pytest.mark.asyncio
async def test_retry_backoff_exhaustion_raises_rate_limited_error() -> None:
    """AC-08: Four consecutive 429 responses exhaust MAX_RETRIES (3) and raise RateLimitedError after exactly 4 requests."""
    # Invariant: Loop bound is statically constrained to MAX_RETRIES + 1 (4 requests) to prevent infinite loops (PoT #2).
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(429, text="Too Many Requests")

    recorded_sleeps = []

    async def fake_sleep(seconds: float) -> None:
        recorded_sleeps.append(seconds)

    transport = wrap_transport(handler)
    async with JolpicaClient(transport=transport, sleep=fake_sleep) as client:
        with pytest.raises(RateLimitedError):
            await client.get_races(season=2026)

    assert request_count == 4
    assert recorded_sleeps == [1.0, 2.0, 4.0]


@pytest.mark.asyncio
async def test_pagination_overflow_raises_data_parse_error(jolpica_payload) -> None:
    """AC-09: A response where MRData.total exceeds returned records raises DataParseError and makes exactly 1 request."""
    # Invariant: Truncation guard checks that response records cover MRData.total to prevent silent loss of data.
    # Invariant: No additional pages are requested; the method fails fast after the initial page.
    payload = jolpica_payload("driverstandings_pagination_overflow")
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(200, json=payload)

    transport = wrap_transport(handler)
    async with JolpicaClient(transport=transport) as client:
        with pytest.raises(DataParseError, match=r"(?i)pagination"):
            await client.get_driver_standings(season=2026)

    assert request_count == 1
