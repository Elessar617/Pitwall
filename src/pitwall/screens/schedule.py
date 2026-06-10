"""Real schedule screen: season calendar DataTable (SPEC-03 scope 3)."""

import datetime

from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from pitwall.models import Race
from pitwall.screens.base import PitwallScreen
from pitwall.screens.cells import EM_DASH, safe_row
from pitwall.workers.season import SeasonSnapshot

COLUMNS = ("Rnd", "Race", "Circuit", "Location", "Start (UTC)", "Quali (UTC)", "Sprint (UTC)")
LOADING_TEXT = "Loading schedule…"
ERROR_TEXT = "Schedule unavailable — season load failed."


def _format_session(value: datetime.datetime | None) -> str:
    # Locale-free numeric format (D3); absent optional sessions render as an em dash.
    return f"{value:%m-%d %H:%M}" if value is not None else EM_DASH


def build_rows(races: list[Race]) -> list[tuple[str, ...]]:
    """Pure row builder; defensively sorted by round (D3)."""
    rows = []
    # Loop bound: len(races) <= one API page (PoT #2).
    for race in sorted(races, key=lambda r: r.round):
        rows.append(
            (
                str(race.round),
                race.race_name,
                race.circuit.circuit_name,
                f"{race.circuit.locality}, {race.circuit.country}",
                _format_session(race.start),
                _format_session(race.qualifying),
                _format_session(race.sprint),
            )
        )
    return rows


def next_race_index(races: list[Race], now: datetime.datetime) -> int | None:
    """First round whose race start is >= now; None when the season is over (D4)."""
    # Loop bound: len(races) <= one API page (PoT #2).
    for index, race in enumerate(sorted(races, key=lambda r: r.round)):
        if race.start >= now:
            return index
    return None


class ScheduleScreen(PitwallScreen):
    """Season calendar view driven by the app's watchable load state (D1)."""

    def compose_body(self) -> ComposeResult:
        yield Static(LOADING_TEXT, id="schedule-status")
        table = DataTable(id="schedule-table")
        table.display = False
        yield table

    def on_mount(self) -> None:
        self.watch(self.app, "snapshot", self._render_snapshot, init=True)
        self.watch(self.app, "load_error", self._render_error, init=True)

    def _render_snapshot(self, snapshot: SeasonSnapshot | None) -> None:
        if snapshot is None:
            return
        races: list[Race] = snapshot.schedule.data
        status = self.query_one("#schedule-status", Static)
        table = self.query_one("#schedule-table", DataTable)
        if not races:
            status.update(f"No races scheduled for season {self.app.config.season}.")
            status.display = True
            table.display = False
            return
        table.clear(columns=True)
        table.add_columns(*COLUMNS)
        # Loop bound: len(races) rows (PoT #2).
        for row in build_rows(races):
            table.add_row(*safe_row(row))
        index = next_race_index(races, self.app.clock())
        table.move_cursor(row=index if index is not None else 0)
        status.display = False
        table.display = True
        if self.app.screen is self:
            table.focus()

    def _render_error(self, error: str | None) -> None:
        if error is None:
            return
        status = self.query_one("#schedule-status", Static)
        table = self.query_one("#schedule-table", DataTable)
        status.update(ERROR_TEXT)
        status.display = True
        table.display = False
