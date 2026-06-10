import asyncio
from collections.abc import Callable
from typing import Any, Self

import httpx

from pitwall import __version__
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
    parse_constructor_standings,
    parse_constructors,
    parse_driver_standings,
    parse_drivers,
    parse_races,
    parse_results,
)

BASE_URL = "https://api.jolpi.ca/ergast/f1"
PAGE_LIMIT = 100
REQUEST_TIMEOUT_S = 10.0
MAX_RETRIES = 3
BACKOFF_BASE_S = 1.0
BACKOFF_FACTOR = 2.0


class JolpicaClient:
    """Async client for the Jolpica-F1 API."""

    def __init__(
        self,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Any] | None = None,
        base_url: str = BASE_URL,
        timeout: float = REQUEST_TIMEOUT_S,
    ) -> None:
        # Invariant: Injectable transport permits offline testing by mocking HTTP calls.
        # Invariant: Injectable sleep allows deterministic rate-limit testing without real delays.
        # Concurrency & Ownership: The client owns its internal httpx.AsyncClient session.
        self.base_url = base_url
        self.timeout = timeout
        self.backoff_base_s = BACKOFF_BASE_S
        self.backoff_factor = BACKOFF_FACTOR

        headers = {
            "User-Agent": f"pitwall/{__version__}",
        }
        self._client = httpx.AsyncClient(
            transport=transport,
            headers=headers,
            timeout=timeout,
        )
        self._sleep = sleep if sleep is not None else asyncio.sleep

    async def __aenter__(self) -> Self:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def aclose(self) -> None:
        """Close the underlying HTTP client session."""
        await self._client.aclose()

    async def _request(self, url: str) -> dict[str, Any]:
        """Perform a GET request to the given URL, handling rate limits and exceptions.

        Loop Bound: Statically constrained to at most MAX_RETRIES + 1 (4 requests) to prevent infinite loops (PoT #2).
        Failure Mode: Raises JolpicaHttpError on non-200/non-429 status codes; raises RateLimitedError if 429 retries are exhausted.
        """
        params = {"limit": str(PAGE_LIMIT)}

        # Loop Bound: Exactly MAX_RETRIES + 1 attempts (value: 4). Statically defined and bounded (PoT #2).
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self._client.get(url, params=params)
            except httpx.TransportError as e:
                # Failure Mode: httpx.TransportError -> JolpicaNetworkError with raise-from chaining.
                raise JolpicaNetworkError(e) from e

            if response.status_code == 429:
                if attempt == MAX_RETRIES:
                    raise RateLimitedError()
                # Unit/Range: Exponential backoff calculation. sleep_duration is in seconds.
                # attempt ranges [0, 2], so sleep_duration ranges [1.0, 4.0] seconds.
                sleep_duration = self.backoff_base_s * (self.backoff_factor**attempt)
                await self._sleep(sleep_duration)
                continue

            # Failure Mode: Non-200/non-429 HTTP status codes raise JolpicaHttpError carrying the raw status code.
            if response.status_code != 200:
                raise JolpicaHttpError(response.status_code)

            break

        # Failure Mode: Invalid or non-JSON payload body raises DataParseError.
        try:
            payload = response.json()
        except (ValueError, TypeError) as e:
            raise DataParseError.invalid_json() from e

        return payload

    def _check_pagination(self, payload: dict[str, Any], records: list[Any]) -> None:
        """Verify that the retrieved list of records covers the total count in the envelope.

        Invariant: The client must raise DataParseError if the MRData total exceeds returned record counts (Pagination guard).
        """
        try:
            mr_data = payload["MRData"]
            total_str = mr_data["total"]
            total = int(total_str)
        except (KeyError, ValueError, TypeError) as e:
            # Failure Mode: Malformed or missing total in the envelope raises DataParseError.
            raise DataParseError.malformed_total(e) from e

        if total > len(records):
            raise DataParseError.pagination_overflow(total, len(records))

    async def get_races(self, season: int | str) -> list[Race]:
        """Fetch the schedule of races for the specified season.

        Invariant: Retrievable via the schedule endpoint and returned as a list of typed Race models.
        """
        url = f"{self.base_url}/{season}/races/"
        payload = await self._request(url)
        records = parse_races(payload)
        self._check_pagination(payload, records)
        return records

    async def get_driver_standings(self, season: int | str) -> list[DriverStanding]:
        """Fetch the driver standings for the specified season.

        Invariant: Retrievable via the driverstandings endpoint and returned as a list of typed DriverStanding models.
        """
        url = f"{self.base_url}/{season}/driverstandings/"
        payload = await self._request(url)
        records = parse_driver_standings(payload)
        self._check_pagination(payload, records)
        return records

    async def get_constructor_standings(self, season: int | str) -> list[ConstructorStanding]:
        """Fetch the constructor standings for the specified season.

        Invariant: Retrievable via the constructorstandings endpoint and returned as a list of typed ConstructorStanding models.
        """
        url = f"{self.base_url}/{season}/constructorstandings/"
        payload = await self._request(url)
        records = parse_constructor_standings(payload)
        self._check_pagination(payload, records)
        return records

    async def get_results(self, season: int | str, round: int | str) -> list[RaceResult]:  # noqa: A002
        """Fetch race results for a specific season and round.

        Invariant: Retrievable via the results endpoint and returned as a list of typed RaceResult models.
        """
        url = f"{self.base_url}/{season}/{round}/results/"
        payload = await self._request(url)
        records = parse_results(payload)
        self._check_pagination(payload, records)
        return records

    async def get_drivers(self, season: int | str) -> list[Driver]:
        """Fetch the list of drivers registered for the specified season.

        Invariant: Retrievable via the drivers endpoint and returned as a list of typed Driver models.
        """
        url = f"{self.base_url}/{season}/drivers/"
        payload = await self._request(url)
        records = parse_drivers(payload)
        self._check_pagination(payload, records)
        return records

    async def get_constructors(self, season: int | str) -> list[Constructor]:
        """Fetch the list of constructors registered for the specified season.

        Invariant: Retrievable via the constructors endpoint and returned as a list of typed Constructor models.
        """
        url = f"{self.base_url}/{season}/constructors/"
        payload = await self._request(url)
        records = parse_constructors(payload)
        self._check_pagination(payload, records)
        return records
