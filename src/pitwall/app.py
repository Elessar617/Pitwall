import asyncio
import datetime
import sqlite3
from collections.abc import Awaitable, Callable
from typing import ClassVar

import httpx
from textual import work
from textual.app import App
from textual.binding import Binding
from textual.reactive import var

from pitwall.api.jolpica import JolpicaClient
from pitwall.cache.db import connect, init_schema
from pitwall.cache.store import SeasonStore
from pitwall.config import AppConfig
from pitwall.errors import JolpicaError
from pitwall.screens import (
    LiveTimingScreen,
    ProfilesScreen,
    ResultsScreen,
    ScheduleScreen,
    StandingsScreen,
    StrategyScreen,
)
from pitwall.workers.season import (
    SeasonLoaded,
    SeasonLoadFailed,
    SeasonSnapshot,
    load_season,
)


class PitwallApp(App[None]):
    """App shell: chassis, navigation bindings, season-load lifecycle."""

    TITLE = "Pitwall"

    # Watchable season-load state (SPEC-03 D1): the one source of truth screens watch.
    snapshot: var[SeasonSnapshot | None] = var(None)
    load_error: var[str | None] = var(None)
    SCREENS: ClassVar[dict] = {
        "schedule": ScheduleScreen,
        "standings": StandingsScreen,
        "results": ResultsScreen,
        "profiles": ProfilesScreen,
        "live": LiveTimingScreen,
        "strategy": StrategyScreen,
    }
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("s", "show_screen('schedule')", "Schedule"),
        Binding("n", "show_screen('standings')", "Standings"),
        Binding("r", "show_screen('results')", "Results"),
        Binding("p", "show_screen('profiles')", "Profiles"),
        Binding("l", "show_screen('live')", "Live"),
        Binding("g", "show_screen('strategy')", "Game"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        config: AppConfig,
        store: SeasonStore | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        now: Callable[[], datetime.datetime] | None = None,
        replay_sleep: Callable[[float], Awaitable[None]] | None = None,
        openf1_transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        # Ownership: an injected store's resources belong to the caller; when no
        # store is given the app builds and later closes its own conn + client.
        super().__init__()
        self.config = config
        self.store = store
        self._store_injected = store is not None
        self._transport = transport
        self._now = now
        self._replay_sleep = replay_sleep
        self.openf1_transport = openf1_transport
        self._owned_conn: sqlite3.Connection | None = None
        self._owned_client: JolpicaClient | None = None

    @property
    def owned_connection(self) -> sqlite3.Connection | None:
        return self._owned_conn

    @property
    def owned_client(self) -> JolpicaClient | None:
        return self._owned_client

    @property
    def replay_sleep(self) -> Callable[[float], Awaitable[None]]:
        if self._replay_sleep is not None:
            return self._replay_sleep
        return asyncio.sleep

    @property
    def clock(self) -> Callable[[], datetime.datetime]:
        """The injected clock, or UTC now — screens use this, never wall time directly."""
        if self._now is not None:
            return self._now
        return lambda: datetime.datetime.now(datetime.UTC)

    @property
    def loading_subtitle(self) -> str:
        return f"season {self.config.season} · loading…"

    def on_mount(self) -> None:
        if not self._store_injected:
            self._owned_conn = connect(self.config.db_path)
            init_schema(self._owned_conn)
            self._owned_client = (
                JolpicaClient(transport=self._transport) if self._transport is not None else JolpicaClient()
            )
            self.store = SeasonStore(self._owned_conn, self._owned_client, now=self._now)
        self.push_screen("schedule")
        self.sub_title = self.loading_subtitle
        self._load_season()

    @work(exclusive=True)
    async def _load_season(self) -> None:
        # Error contract: exactly the store's typed boundaries are converted to
        # a failure message; anything else stays loud (programming errors).
        store = self.store
        if store is None:
            # Invariant: on_mount builds the store before dispatching this worker.
            return
        try:
            snapshot = await load_season(store, self.config.season)
        except (JolpicaError, sqlite3.Error) as exc:
            self.post_message(SeasonLoadFailed(str(exc)))
            return
        self.post_message(SeasonLoaded(snapshot))

    def on_season_loaded(self, message: SeasonLoaded) -> None:
        snapshot = message.snapshot
        self.snapshot = snapshot
        self.load_error = None
        as_of = f"{snapshot.oldest_fetched_at:%H:%M}"
        subtitle = f"season {self.config.season} · data as of {as_of} UTC"
        if snapshot.has_stale:
            subtitle += " · stale"
            self.notify(
                f"Serving stale cached data (as of {as_of} UTC).",
                severity="warning",
            )
        self.sub_title = subtitle

    def on_season_load_failed(self, message: SeasonLoadFailed) -> None:
        self.load_error = message.error
        self.sub_title = f"season {self.config.season} · load failed"
        self.notify(message.error, severity="error")

    def action_show_screen(self, name: str) -> None:
        # No-op when the requested screen is already active (AC-7).
        if self.screen is self.get_screen(name):
            return
        self.switch_screen(name)

    async def on_unmount(self) -> None:
        if self._owned_client is not None:
            await self._owned_client.aclose()
        if self._owned_conn is not None:
            self._owned_conn.close()
