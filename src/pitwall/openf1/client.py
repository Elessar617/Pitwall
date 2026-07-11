import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import quote

import httpx

from pitwall import __version__
from pitwall.openf1.errors import (
    OpenF1DataError,
    OpenF1HttpError,
    OpenF1NetworkError,
    OpenF1RateLimitedError,
)
from pitwall.openf1.models import (
    IntervalPoint,
    Lap,
    LocationPoint,
    PitStop,
    PositionUpdate,
    RaceControlMessage,
    Session,
    SessionDriver,
    Stint,
    parse_drivers,
    parse_intervals,
    parse_laps,
    parse_location,
    parse_pit,
    parse_position,
    parse_race_control,
    parse_sessions,
    parse_stints,
)

BASE_URL = "https://api.openf1.org/v1"
MAX_RETRIES = 3


def build_query(params: dict[str, Any], filters: list[tuple[str, str, Any]] | None = None) -> str:
    """Build URL query string with custom percent-encoding for operators in param names."""
    parts = []
    for k, v in params.items():
        parts.append(f"{k}={quote(str(v), safe=':')}")
    if filters:
        for field, op, val in filters:
            encoded_op = {">": "%3E", "<": "%3C"}.get(op)
            if encoded_op is None:
                raise ValueError(f"Unsupported operator: {op}")  # noqa: TRY003
            parts.append(f"{field}{encoded_op}{quote(str(val), safe=':')}")
    return "&".join(parts)


class OpenF1Client:
    """Async API client for OpenF1 API."""

    def __init__(
        self,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self.base_url = BASE_URL
        self.sleep = sleep or asyncio.sleep
        self.client = httpx.AsyncClient(
            transport=transport,
            headers={"User-Agent": f"pitwall/{__version__}"},
            timeout=10.0,
        )

    async def __aenter__(self) -> "OpenF1Client":
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def _request(
        self,
        endpoint: str,
        params: dict[str, Any],
        filters: list[tuple[str, str, Any]] | None = None,
    ) -> list[Any]:
        # Loop Bound: Loop executes at most MAX_RETRIES + 1 (4) times.
        # Invariants: backoff factor doubles on each 429 response.
        # Failure Modes: Raises OpenF1NetworkError for transport/network issues,
        # OpenF1HttpError for non-200/404/429 statuses, and OpenF1RateLimitedError
        # once the retry limit is exhausted.
        query = build_query(params, filters)
        url = f"{self.base_url}/{endpoint}"
        if query:
            url = f"{url}?{query}"

        backoff = 1.0

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self.client.get(url)
            except httpx.RequestError as e:
                raise OpenF1NetworkError(e) from e

            if response.status_code == 404:
                return []
            elif response.status_code == 429:
                if attempt < MAX_RETRIES:
                    await self.sleep(backoff)
                    backoff *= 2.0
                    continue
                else:
                    raise OpenF1RateLimitedError()
            elif response.status_code != 200:
                raise OpenF1HttpError(response.status_code)
            else:
                try:
                    return response.json()
                except json.JSONDecodeError as exc:
                    raise OpenF1DataError(f"Non-JSON response body from {endpoint}") from exc  # noqa: TRY003
        raise OpenF1RateLimitedError()

    async def _get_stream(
        self,
        endpoint: str,
        parser: Callable[[Any], list[Any]],
        session_key: int | str,
        driver_number: int | None = None,
        date_gt: str | None = None,
        date_lt: str | None = None,
    ) -> list[Any]:
        # Invariants: session_key must be passed to identify the F1 session.
        # driver_number is optional and omitted from params if None.
        # Failure Modes: Propagates exceptions raised by _request or the parser function.
        params: dict[str, Any] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        filters = []
        if date_gt is not None:
            filters.append(("date", ">", date_gt))
        if date_lt is not None:
            filters.append(("date", "<", date_lt))
        data = await self._request(endpoint, params, filters)
        return parser(data)

    async def get_drivers(
        self,
        session_key: int,
        date_gt: str | None = None,
        date_lt: str | None = None,
    ) -> list[SessionDriver]:
        """Fetch drivers for a session."""
        return await self._get_stream(
            "drivers",
            parse_drivers,
            session_key,
            date_gt=date_gt,
            date_lt=date_lt,
        )

    async def get_stints(
        self,
        session_key: int,
        date_gt: str | None = None,
        date_lt: str | None = None,
    ) -> list[Stint]:
        """Fetch stints for a session."""
        return await self._get_stream(
            "stints",
            parse_stints,
            session_key,
            date_gt=date_gt,
            date_lt=date_lt,
        )

    async def get_laps(
        self,
        session_key: int,
        date_gt: str | None = None,
        date_lt: str | None = None,
    ) -> list[Lap]:
        """Fetch laps for a session."""
        return await self._get_stream(
            "laps",
            parse_laps,
            session_key,
            date_gt=date_gt,
            date_lt=date_lt,
        )

    async def get_position(
        self,
        session_key: int,
        date_gt: str | None = None,
        date_lt: str | None = None,
    ) -> list[PositionUpdate]:
        """Fetch position updates for a session."""
        return await self._get_stream(
            "position",
            parse_position,
            session_key,
            date_gt=date_gt,
            date_lt=date_lt,
        )

    async def get_intervals(
        self,
        session_key: int,
        date_gt: str | None = None,
        date_lt: str | None = None,
    ) -> list[IntervalPoint]:
        """Fetch interval points for a session."""
        return await self._get_stream(
            "intervals",
            parse_intervals,
            session_key,
            date_gt=date_gt,
            date_lt=date_lt,
        )

    async def get_pit(
        self,
        session_key: int,
        date_gt: str | None = None,
        date_lt: str | None = None,
    ) -> list[PitStop]:
        """Fetch pit stops for a session."""
        return await self._get_stream(
            "pit",
            parse_pit,
            session_key,
            date_gt=date_gt,
            date_lt=date_lt,
        )

    async def get_race_control(
        self,
        session_key: int,
        date_gt: str | None = None,
        date_lt: str | None = None,
    ) -> list[RaceControlMessage]:
        """Fetch race control messages for a session."""
        return await self._get_stream(
            "race_control",
            parse_race_control,
            session_key,
            date_gt=date_gt,
            date_lt=date_lt,
        )

    async def get_sessions(self, session_key: int | str) -> list[Session]:
        """Fetch sessions matching the session key."""
        return await self._get_stream("sessions", parse_sessions, session_key)

    async def get_location(
        self,
        session_key: int,
        driver_number: int | None = None,
        date_gt: str | None = None,
        date_lt: str | None = None,
    ) -> list[LocationPoint]:
        """Fetch driver location data for a session."""
        return await self._get_stream(
            "location",
            parse_location,
            session_key,
            driver_number=driver_number,
            date_gt=date_gt,
            date_lt=date_lt,
        )
