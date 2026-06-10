"""Season worker: one load per launch through SeasonStore (SPEC-02 scope D5)."""

import datetime
from dataclasses import dataclass

from textual.message import Message

from pitwall.cache.store import SeasonStore, Source, StoreResult


@dataclass(frozen=True)
class SeasonSnapshot:
    """Immutable result of one season load across the three launch scopes."""

    schedule: StoreResult
    driver_standings: StoreResult
    constructor_standings: StoreResult

    @property
    def has_stale(self) -> bool:
        """True when any scope was served from stale cache.

        >>> import datetime as dt
        >>> r = StoreResult(data=[], fetched_at=dt.datetime(2026, 1, 1, tzinfo=dt.UTC), source=Source.CACHE)
        >>> SeasonSnapshot(schedule=r, driver_standings=r, constructor_standings=r).has_stale
        False
        """
        results = (self.schedule, self.driver_standings, self.constructor_standings)
        return any(result.source == Source.STALE_CACHE for result in results)

    @property
    def oldest_fetched_at(self) -> datetime.datetime:
        """The oldest fetch timestamp across scopes — the honest 'data as of' time."""
        results = (self.schedule, self.driver_standings, self.constructor_standings)
        return min(result.fetched_at for result in results)


class SeasonLoaded(Message):
    """Posted when the season load completes; carries the snapshot."""

    def __init__(self, snapshot: SeasonSnapshot) -> None:
        self.snapshot = snapshot
        super().__init__()


class SeasonLoadFailed(Message):
    """Posted when the season load fails; carries the error text."""

    def __init__(self, error: str) -> None:
        self.error = error
        super().__init__()


async def load_season(store: SeasonStore, season: int) -> SeasonSnapshot:
    """Read the three launch scopes through the store.

    Failure mode: JolpicaError / sqlite3.Error propagate to the caller's
    worker wrapper — no handling here by contract (SPEC-02 error contract).
    """
    schedule = await store.get_schedule(season)
    driver_standings = await store.get_driver_standings(season)
    constructor_standings = await store.get_constructor_standings(season)
    return SeasonSnapshot(
        schedule=schedule,
        driver_standings=driver_standings,
        constructor_standings=constructor_standings,
    )
