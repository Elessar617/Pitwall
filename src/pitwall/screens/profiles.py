import sqlite3

from textual import work
from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from pitwall.cache.store import Source
from pitwall.errors import JolpicaError
from pitwall.models import Constructor, Driver
from pitwall.screens.base import PitwallScreen
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


class StoreNotInitializedError(RuntimeError):
    """Exception raised when the store is not initialized on the app."""

    def __init__(self) -> None:
        super().__init__("App store is not initialized")


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

    async def _fetch_drivers(self, season: int) -> tuple[bool, list[Driver] | None]:
        # Concurrency: executes within the profile-rosters exclusive worker group.
        # Failure mode: catching JolpicaError and sqlite3.Error prevents one section's
        # fetch failure from aborting the other section's fetch.
        store = self.app.store
        if store is None:
            # Invariant: _fetch_rosters raises before dispatching these helpers.
            raise StoreNotInitializedError()
        try:
            store_res = await store.get_drivers(season)
            if store_res.source == Source.STALE_CACHE:
                as_of = f"{store_res.fetched_at:%H:%M}"
                self.app.notify(f"Serving stale cached drivers (as of {as_of} UTC).", severity="warning")
        except (JolpicaError, sqlite3.Error):
            return False, None
        else:
            return True, store_res.data

    async def _fetch_constructors(self, season: int) -> tuple[bool, list[Constructor] | None]:
        # Concurrency: executes within the profile-rosters exclusive worker group.
        # Failure mode: catching JolpicaError and sqlite3.Error prevents one section's
        # fetch failure from aborting the other section's fetch.
        store = self.app.store
        if store is None:
            # Invariant: _fetch_rosters raises before dispatching these helpers.
            raise StoreNotInitializedError()
        try:
            store_res = await store.get_constructors(season)
            if store_res.source == Source.STALE_CACHE:
                as_of = f"{store_res.fetched_at:%H:%M}"
                self.app.notify(f"Serving stale cached constructors (as of {as_of} UTC).", severity="warning")
        except (JolpicaError, sqlite3.Error):
            return False, None
        else:
            return True, store_res.data

    def _render_drivers_section(self, season: int, drivers_data: tuple[bool, list[Driver] | None]) -> None:
        success, drivers_list = drivers_data
        status = self.query_one("#profiles-drivers-status", Static)
        table = self.query_one("#profiles-drivers-table", DataTable)

        if success:
            if not drivers_list:
                status.update(f"No drivers listed for season {season}.")
                status.display = True
                table.display = False
            else:
                status.display = False
                table.clear(columns=True)
                table.add_columns("No", "Driver", "Code", "Nationality", "Born")
                # Loop bound: len(drivers_list) <= 30 (maximum grid size for F1).
                for row in build_driver_rows(drivers_list):
                    table.add_row(*safe_row(row))
                table.display = True
        else:
            status.update("Drivers unavailable — fetch failed.")
            status.display = True
            table.display = False

    def _render_constructors_section(
        self, season: int, constructors_data: tuple[bool, list[Constructor] | None]
    ) -> None:
        success, constructors_list = constructors_data
        status = self.query_one("#profiles-constructors-status", Static)
        table = self.query_one("#profiles-constructors-table", DataTable)

        if success:
            if not constructors_list:
                status.update(f"No constructors listed for season {season}.")
                status.display = True
                table.display = False
            else:
                status.display = False
                table.clear(columns=True)
                table.add_columns("Team", "Nationality")
                # Loop bound: len(constructors_list) <= 15 (maximum team count for F1).
                for row in build_constructor_rows(constructors_list):
                    table.add_row(*safe_row(row))
                table.display = True
        else:
            status.update("Constructors unavailable — fetch failed.")
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
        drivers_data = await self._fetch_drivers(season)
        self._render_drivers_section(season, drivers_data)

        # Fetch constructors
        constructors_data = await self._fetch_constructors(season)
        self._render_constructors_section(season, constructors_data)

        # Apply focus
        self._apply_focus()
