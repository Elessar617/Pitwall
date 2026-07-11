import datetime
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pitwall.api.jolpica import JolpicaClient
from pitwall.cache.db import (
    _fetchall,
    from_db_datetime,
    get_refresh_log_metadata,
    select_constructor_standings,
    select_constructors,
    select_driver_standings,
    select_drivers,
    select_race_results,
    select_races,
    set_refresh_log,
    upsert_constructor_standings,
    upsert_constructors,
    upsert_driver_standings,
    upsert_drivers,
    upsert_race_results,
    upsert_races,
)
from pitwall.cache.freshness import is_stale
from pitwall.errors import JolpicaError


class Source(StrEnum):
    CACHE = "CACHE"
    NETWORK = "NETWORK"
    STALE_CACHE = "STALE_CACHE"


@dataclass(frozen=True)
class StoreResult:
    data: Any
    fetched_at: datetime.datetime
    source: Source


class SeasonStore:
    """Read-through cache layer composing sqlite3 storage and JolpicaClient."""

    def __init__(
        self,
        db: sqlite3.Connection,
        client: JolpicaClient,
        now: Callable[[], datetime.datetime] | None = None,
    ) -> None:
        # Invariant: db connection and client are injected to isolate state.
        # Ownership: The store does not close the connection; caller manages it.
        self.db = db
        self.client = client
        self.now = now if now is not None else lambda: datetime.datetime.now(datetime.UTC)

    def _get_session_starts(self, season: int, round_num: int | None = None) -> list[datetime.datetime]:
        """Query race session start dates from the database to evaluate staleness.

        Invariant: For results scope, only the target round's sessions are evaluated.
        Invariant: For season-wide scopes, all sessions scheduled for the season are evaluated.
        """
        sql = """
            SELECT start, fp1, fp2, fp3, qualifying, sprint, sprint_qualifying
            FROM races
            WHERE season = ?
            """
        params: list[int] = [season]
        if round_num is not None:
            sql += " AND round = ?"
            params.append(round_num)
        rows = _fetchall(self.db, sql, tuple(params))

        starts = []
        # Loop Bound: Constrained by number of race rows and session columns (PoT #2).
        for row in rows:
            for val in row:
                if val is not None:
                    dt = from_db_datetime(val)
                    if dt is not None:
                        starts.append(dt)
        return starts

    async def _read_through(
        self,
        scope: str,
        season: int,
        round_num: int | None,
        select_fn: Callable[[], Any],
        upsert_fn: Callable[[Any], None],
        fetch_fn: Callable[[], Any],
    ) -> StoreResult:
        """Helper to execute the read-through logic for caching and staleness.

        Failure Mode: sqlite3 errors propagate immediately without swallow.
        Failure Mode: JolpicaError yields STALE_CACHE if cache is populated, otherwise propagates.
        """
        # 1. Query the refresh log and cache data for this scope
        fetched_at, record_count = get_refresh_log_metadata(self.db, scope)
        cached_data = select_fn() if fetched_at is not None else None

        # Cache presence = refresh_log row exists AND (record_count == 0 OR entity rows present).
        # Note: a refresh_log row without recorded fetch metadata (record_count is None) is a bogus/legacy log.
        if fetched_at is not None and record_count is not None:
            cache_present = (record_count == 0) or (cached_data is not None and len(cached_data) > 0)
        else:
            cache_present = False

        if cache_present:
            # If the cache is present and we legitimately fetched 0 records, cached_data must be normalized to []
            if record_count == 0 or cached_data is None:
                cached_data = []

            # 2. Check cache staleness using calendar events
            session_starts = self._get_session_starts(season, round_num)
            if fetched_at is None:
                # Invariant: cache_present implies a refresh-log timestamp.
                raise sqlite3.DataError("cache present without refresh log")  # noqa: TRY003
            stale = is_stale(fetched_at, self.now(), session_starts)

            if not stale:
                # Invariant: serve fresh cached data immediately.
                return StoreResult(data=cached_data, fetched_at=fetched_at, source=Source.CACHE)

        # 3. Cache miss or stale data: perform network fetch
        try:
            data = await fetch_fn()
        except JolpicaError:
            # Invariant: serve degraded stale cache if we have a valid cache present, else propagate error.
            if cache_present and fetched_at is not None:
                return StoreResult(data=cached_data, fetched_at=fetched_at, source=Source.STALE_CACHE)
            raise

        # 4. Fetch succeeded: persist new data and update refresh log
        upsert_fn(data)
        now_time = self.now()
        set_refresh_log(self.db, scope, now_time, record_count=len(data))

        return StoreResult(data=data, fetched_at=now_time, source=Source.NETWORK)

    async def get_schedule(self, season: int) -> StoreResult:
        """Fetch the schedule of races for the season (scope schedule:season)."""
        scope = f"schedule:{season}"
        return await self._read_through(
            scope=scope,
            season=season,
            round_num=None,
            select_fn=lambda: select_races(self.db, season),
            upsert_fn=lambda data: upsert_races(self.db, data, season=season),
            fetch_fn=lambda: self.client.get_races(season),
        )

    async def get_driver_standings(self, season: int) -> StoreResult:
        """Fetch driver standings for the season (scope driver_standings:season)."""
        scope = f"driver_standings:{season}"
        return await self._read_through(
            scope=scope,
            season=season,
            round_num=None,
            select_fn=lambda: select_driver_standings(self.db, season),
            upsert_fn=lambda data: upsert_driver_standings(self.db, season, data),
            fetch_fn=lambda: self.client.get_driver_standings(season),
        )

    async def get_constructor_standings(self, season: int) -> StoreResult:
        """Fetch constructor standings for the season (scope constructor_standings:season)."""
        scope = f"constructor_standings:{season}"
        return await self._read_through(
            scope=scope,
            season=season,
            round_num=None,
            select_fn=lambda: select_constructor_standings(self.db, season),
            upsert_fn=lambda data: upsert_constructor_standings(self.db, season, data),
            fetch_fn=lambda: self.client.get_constructor_standings(season),
        )

    async def get_race_results(self, season: int, round: int) -> StoreResult:  # noqa: A002
        """Fetch race results for a season round (scope results:season:round)."""
        scope = f"results:{season}:{round}"
        return await self._read_through(
            scope=scope,
            season=season,
            round_num=round,
            select_fn=lambda: select_race_results(self.db, season, round),
            upsert_fn=lambda data: upsert_race_results(self.db, season, round, data),
            fetch_fn=lambda: self.client.get_results(season, round),
        )

    async def get_drivers(self, season: int) -> StoreResult:
        """Fetch drivers registered for the season (scope drivers:season)."""
        scope = f"drivers:{season}"
        return await self._read_through(
            scope=scope,
            season=season,
            round_num=None,
            select_fn=lambda: select_drivers(self.db, season),
            upsert_fn=lambda data: upsert_drivers(self.db, data, season),
            fetch_fn=lambda: self.client.get_drivers(season),
        )

    async def get_constructors(self, season: int) -> StoreResult:
        """Fetch constructors registered for the season (scope constructors:season)."""
        scope = f"constructors:{season}"
        return await self._read_through(
            scope=scope,
            season=season,
            round_num=None,
            select_fn=lambda: select_constructors(self.db, season),
            upsert_fn=lambda data: upsert_constructors(self.db, data, season),
            fetch_fn=lambda: self.client.get_constructors(season),
        )
