import sqlite3
from collections.abc import Awaitable, Callable, Iterable
from typing import Any

from textual import work
from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from pitwall.cache.store import SeasonStore, Source, StoreResult
from pitwall.errors import JolpicaError
from pitwall.models import Constructor, Driver
from pitwall.screens.base import PitwallScreen, StoreNotInitializedError
from pitwall.screens.cells import EM_DASH, safe_row
from pitwall.workers.season import SeasonSnapshot


def build_driver_rows(drivers: list[Driver]) -> list[tuple[str, ...]]:
    sorted_drivers = sorted(drivers, key=lambda d: (d.family_name, d.given_name))
    rows = []
    for d in sorted_drivers:
        num = str(d.permanent_number) if d.permanent_number is not None else EM_DASH
        name = f"{d.given_name} {d.family_name}"
        code = d.code if d.code is not None else EM_DASH
        nationality = d.nationality if d.nationality is not None else EM_DASH
        born = d.date_of_birth.isoformat() if d.date_of_birth is not None else EM_DASH
        rows.append((num, name, code, nationality, born))
    return rows


def build_constructor_rows(constructors: list[Constructor]) -> list[tuple[str, str]]:
    sorted_constructors = sorted(constructors, key=lambda c: c.name)
    return [(c.name, c.nationality) for c in sorted_constructors]


class ProfilesScreen(PitwallScreen):
    """Screen for displaying driver and constructor profiles (D1)."""

    DEFAULT_CSS = """
    ProfilesScreen #profiles-drivers-table {
        height: 2fr;
    }
    ProfilesScreen #profiles-constructors-table {
        height: 1fr;
    }
    """

    def compose_body(self) -> ComposeResult:
        # Invariant: #profiles-status is displayed during season-level loading or failure,
        # during which all section-level widgets below must be hidden.
        yield Static("Loading profiles…", id="profiles-status")

        drivers_title = Static("Drivers", id="profiles-drivers-title")
        drivers_title.display = False
        yield drivers_title

        drivers_status = Static(id="profiles-drivers-status")
        drivers_status.display = False
        yield drivers_status

        drivers_table = DataTable(id="profiles-drivers-table")
        drivers_table.cursor_type = "row"
        drivers_table.display = False
        yield drivers_table

        constructors_title = Static("Constructors", id="profiles-constructors-title")
        constructors_title.display = False
        yield constructors_title

        constructors_status = Static(id="profiles-constructors-status")
        constructors_status.display = False
        yield constructors_status

        constructors_table = DataTable(id="profiles-constructors-table")
        constructors_table.cursor_type = "row"
        constructors_table.display = False
        yield constructors_table

    def on_mount(self) -> None:
        # Invariant: self._rosters_requested prevents duplicate launches of the
        # profile-rosters worker. It is set to True before launching the worker.
        self._rosters_requested = False
        self.watch(self.app, "snapshot", self._render_snapshot, init=True)
        self.watch(self.app, "load_error", self._render_error, init=True)

    def _render_snapshot(self, snapshot: SeasonSnapshot | None) -> None:
        if snapshot is None:
            return

        self.query_one("#profiles-status", Static).display = False

        if not self._rosters_requested:
            self._rosters_requested = True
            self._fetch_rosters(self.app.config.season)

    def _render_error(self, error: str | None) -> None:
        if error is None:
            return

        status = self.query_one("#profiles-status", Static)
        status.update("Profiles unavailable — season load failed.")
        status.display = True

        self.query_one("#profiles-drivers-title", Static).display = False
        self.query_one("#profiles-drivers-status", Static).display = False
        self.query_one("#profiles-drivers-table", DataTable).display = False
        self.query_one("#profiles-constructors-title", Static).display = False
        self.query_one("#profiles-constructors-status", Static).display = False
        self.query_one("#profiles-constructors-table", DataTable).display = False

    def _show_loading_states(self) -> None:
        drivers_title = self.query_one("#profiles-drivers-title", Static)
        drivers_title.display = True

        drivers_status = self.query_one("#profiles-drivers-status", Static)
        drivers_status.update("Loading drivers…")
        drivers_status.display = True

        self.query_one("#profiles-drivers-table", DataTable).display = False

        constructors_title = self.query_one("#profiles-constructors-title", Static)
        constructors_title.display = True

        constructors_status = self.query_one("#profiles-constructors-status", Static)
        constructors_status.update("Loading constructors…")
        constructors_status.display = True

        self.query_one("#profiles-constructors-table", DataTable).display = False

    async def _fetch_section(
        self,
        season: int,
        getter: Callable[[SeasonStore, int], Awaitable[StoreResult]],
        noun: str,
    ) -> tuple[bool, list[Any] | None]:
        # Concurrency: executes within the profile-rosters exclusive worker group.
        # Failure mode: catching JolpicaError and sqlite3.Error prevents one section's
        # fetch failure from aborting the other section's fetch.
        store = self.app.store
        if store is None:
            # Invariant: _fetch_rosters raises before dispatching this helper.
            raise StoreNotInitializedError()
        try:
            store_res = await getter(store, season)
            if store_res.source == Source.STALE_CACHE:
                as_of = f"{store_res.fetched_at:%H:%M}"
                self.app.notify(f"Serving stale cached {noun} (as of {as_of} UTC).", severity="warning")
        except (JolpicaError, sqlite3.Error):
            return False, None
        else:
            return True, store_res.data

    def _render_section(
        self,
        season: int,
        data: tuple[bool, list[Any] | None],
        status_id: str,
        table_id: str,
        columns: tuple[str, ...],
        row_builder: Callable[[list[Any]], Iterable[tuple[str, ...]]],
        noun: str,
    ) -> None:
        success, items = data
        status = self.query_one(status_id, Static)
        table = self.query_one(table_id, DataTable)

        if success:
            if not items:
                status.update(f"No {noun} listed for season {season}.")
                status.display = True
                table.display = False
            else:
                status.display = False
                table.clear(columns=True)
                table.add_columns(*columns)
                # Loop bound: len(items) is capped by the season entry list
                # (grid size for drivers, team count for constructors).
                for row in row_builder(items):
                    table.add_row(*safe_row(row))
                table.display = True
        else:
            status.update(f"{noun.capitalize()} unavailable — fetch failed.")
            status.display = True
            table.display = False

    def _apply_focus(self) -> None:
        # Invariant: App focus is only shifted if ProfilesScreen is the active screen.
        # This prevents background worker completion from stealing focus from other screens.
        if self.app.screen is self:
            drivers_table = self.query_one("#profiles-drivers-table", DataTable)
            constructors_table = self.query_one("#profiles-constructors-table", DataTable)
            if drivers_table.display:
                drivers_table.focus()
            elif constructors_table.display:
                constructors_table.focus()

    @work(exclusive=True, group="profile-rosters")
    async def _fetch_rosters(self, season: int) -> None:
        if self.app.store is None:
            raise StoreNotInitializedError()

        self._show_loading_states()

        # Fetch drivers
        drivers_data = await self._fetch_section(season, SeasonStore.get_drivers, "drivers")
        self._render_section(
            season,
            drivers_data,
            "#profiles-drivers-status",
            "#profiles-drivers-table",
            ("No", "Driver", "Code", "Nationality", "Born"),
            build_driver_rows,
            "drivers",
        )

        # Fetch constructors
        constructors_data = await self._fetch_section(season, SeasonStore.get_constructors, "constructors")
        self._render_section(
            season,
            constructors_data,
            "#profiles-constructors-status",
            "#profiles-constructors-table",
            ("Team", "Nationality"),
            build_constructor_rows,
            "constructors",
        )

        # Apply focus
        self._apply_focus()
