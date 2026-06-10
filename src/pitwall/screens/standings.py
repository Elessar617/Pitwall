"""Standings screen: driver + constructor championship tables (SPEC-04)."""

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from pitwall.models import ConstructorStanding, DriverStanding
from pitwall.screens.base import PitwallScreen
from pitwall.screens.cells import EM_DASH, format_points, safe_row
from pitwall.workers.season import SeasonSnapshot


def build_driver_rows(standings: list[DriverStanding]) -> list[tuple[str, ...]]:
    """Pure driver-table rows, sorted by position ascending (D3/D4)."""
    rows = []
    # Loop bound: len(standings) <= one API page (PoT #2).
    for standing in sorted(standings, key=lambda s: s.position):
        teams = " / ".join(constructor.name for constructor in standing.constructors)
        rows.append(
            (
                standing.position_text,
                f"{standing.driver.given_name} {standing.driver.family_name}",
                standing.driver.code if standing.driver.code is not None else EM_DASH,
                teams if teams else EM_DASH,
                format_points(standing.points),
                str(standing.wins),
            )
        )
    return rows


def build_constructor_rows(standings: list[ConstructorStanding]) -> list[tuple[str, ...]]:
    """Pure constructor-table rows, sorted by position ascending (D3/D4)."""
    rows = []
    # Loop bound: len(standings) <= one API page (PoT #2).
    for standing in sorted(standings, key=lambda s: s.position):
        rows.append(
            (
                standing.position_text,
                standing.constructor.name,
                format_points(standing.points),
                str(standing.wins),
            )
        )
    return rows


DRIVER_COLUMNS = ("Pos", "Driver", "Code", "Team", "Pts", "Wins")
CONSTRUCTOR_COLUMNS = ("Pos", "Team", "Pts", "Wins")
LOADING_TEXT = "Loading standings…"
ERROR_TEXT = "Standings unavailable — season load failed."


class StandingsScreen(PitwallScreen):
    """Both championships stacked, visible together at 80x24 (D2)."""

    DEFAULT_CSS = """
    StandingsScreen #standings-drivers-table,
    StandingsScreen #standings-constructors-table {
        height: 1fr;
    }
    """

    def compose_body(self) -> ComposeResult:
        yield Static(LOADING_TEXT, id="standings-status")
        yield Static("Driver standings", id="standings-drivers-title")
        yield DataTable(id="standings-drivers-table")
        yield Static("Constructor standings", id="standings-constructors-title")
        yield DataTable(id="standings-constructors-table")

    def on_mount(self) -> None:
        self._set_sections(False, False)
        self.watch(self.app, "snapshot", self._render_snapshot, init=True)
        self.watch(self.app, "load_error", self._render_error, init=True)

    def _set_sections(self, drivers: bool, constructors: bool) -> None:
        self.query_one("#standings-drivers-title", Static).display = drivers
        self.query_one("#standings-drivers-table", DataTable).display = drivers
        self.query_one("#standings-constructors-title", Static).display = constructors
        self.query_one("#standings-constructors-table", DataTable).display = constructors

    def _fill(self, table_id: str, columns: tuple[str, ...], rows: list[tuple[str, ...]]) -> DataTable:
        table = self.query_one(table_id, DataTable)
        table.clear(columns=True)
        table.add_columns(*columns)
        # Loop bound: len(rows) <= one API page (PoT #2).
        for row in rows:
            table.add_row(*safe_row(row))
        return table

    def _render_snapshot(self, snapshot: SeasonSnapshot | None) -> None:
        if snapshot is None:
            return
        drivers: list[DriverStanding] = snapshot.driver_standings.data
        constructors: list[ConstructorStanding] = snapshot.constructor_standings.data
        status = self.query_one("#standings-status", Static)
        if not drivers and not constructors:
            status.update(f"No standings available for season {self.app.config.season}.")
            status.display = True
            self._set_sections(False, False)
            return
        status.display = False
        self._set_sections(bool(drivers), bool(constructors))
        if drivers:
            table = self._fill("#standings-drivers-table", DRIVER_COLUMNS, build_driver_rows(drivers))
            if self.app.screen is self:
                table.focus()
        if constructors:
            table = self._fill(
                "#standings-constructors-table", CONSTRUCTOR_COLUMNS, build_constructor_rows(constructors)
            )
            if not drivers and self.app.screen is self:
                table.focus()

    def _render_error(self, error: str | None) -> None:
        if error is None:
            return
        status = self.query_one("#standings-status", Static)
        status.update(ERROR_TEXT)
        status.display = True
        self._set_sections(False, False)
