import datetime
import sqlite3

import rich.text
from textual import work
from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from pitwall.cache.store import Source
from pitwall.errors import JolpicaError
from pitwall.models import Race, RaceResult
from pitwall.screens.base import PitwallScreen, StoreNotInitializedError
from pitwall.screens.cells import EM_DASH, format_points, safe_row
from pitwall.workers.season import SeasonSnapshot


class ResultsScreen(PitwallScreen):
    """Screen for displaying per-round race results (D1)."""

    DEFAULT_CSS = """
    ResultsScreen #results-rounds-table {
        height: 1fr;
    }
    ResultsScreen #results-table {
        height: 2fr;
    }
    """

    def compose_body(self) -> ComposeResult:
        yield Static("Loading results…", id="results-status")

        rounds_table = DataTable(id="results-rounds-table")
        rounds_table.cursor_type = "row"
        rounds_table.display = False
        yield rounds_table

        detail_title = Static(id="results-detail-title")
        detail_title.display = False
        yield detail_title

        detail_status = Static(id="results-detail-status")
        detail_status.display = False
        yield detail_status

        results_table = DataTable(id="results-table")
        results_table.cursor_type = "row"
        results_table.display = False
        yield results_table

    def on_mount(self) -> None:
        self._races: list[Race] = []
        self._selected_round: int | None = None
        # Invariant: self._season_started is True if and only if at least one race
        # in the season calendar has a start time strictly before the current app clock.
        # This determines whether to fetch default round results on screen load.
        self._season_started: bool = False
        self.watch(self.app, "snapshot", self._render_snapshot, init=True)
        self.watch(self.app, "load_error", self._render_error, init=True)

    def _render_snapshot(self, snapshot: SeasonSnapshot | None) -> None:
        if snapshot is None:
            return

        races: list[Race] = snapshot.schedule.data
        status = self.query_one("#results-status", Static)
        rounds_table = self.query_one("#results-rounds-table", DataTable)

        if not races:
            status.update(f"No rounds available for season {self.app.config.season}.")
            status.display = True
            rounds_table.display = False
            self._hide_detail()
            return

        self._races = sorted(races, key=lambda r: r.round)
        self._selected_round = None

        rounds_table.clear(columns=True)
        rounds_table.add_columns("Rnd", "Race")

        # Bounded loop: len(self._races) <= 22, bounded by the F1 calendar size.
        for row in build_round_rows(self._races):
            rounds_table.add_row(*safe_row(row))

        status.display = False
        rounds_table.display = True

        idx = default_round_index(self._races, self.app.clock())
        self._season_started = idx is not None
        cursor_idx = idx if idx is not None else 0
        rounds_table.move_cursor(row=cursor_idx)

        if self.app.screen is self:
            rounds_table.focus()

        if idx is not None:
            race = self._races[idx]
            self._selected_round = race.round
            self._fetch_results(self.app.config.season, race.round)
        else:
            # Pin the detail widgets hidden in pre-season state when no round is selected.
            self._hide_detail()

    def _hide_detail(self) -> None:
        self.query_one("#results-detail-title", Static).display = False
        self.query_one("#results-detail-status", Static).display = False
        self.query_one("#results-table", DataTable).display = False

    def _render_error(self, error: str | None) -> None:
        if error is None:
            return

        status = self.query_one("#results-status", Static)
        status.update("Results unavailable — season load failed.")
        status.display = True

        self.query_one("#results-rounds-table", DataTable).display = False
        self._hide_detail()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        table = event.data_table
        if table.id != "results-rounds-table":
            return

        if event.row_key is not None and table.cursor_row != event.cursor_row:
            return

        row_idx = event.cursor_row
        if not self._races or row_idx >= len(self._races):
            return

        race = self._races[row_idx]
        if self._selected_round == race.round:
            return

        # Safety/Invariant check: Pre-season fetches must be avoided.
        # If the season has not started, self._season_started is False, so we suppress
        # all detail fetching. Manual navigation (up/down arrow keys) on the rounds table
        # pre-season will also be ignored to enforce zero fetching before the first race start.
        if not self._season_started:
            return

        self._selected_round = race.round
        self._fetch_results(self.app.config.season, race.round)

    @work(exclusive=True, group="round-results")
    async def _fetch_results(self, season: int, round_val: int) -> None:
        if self.app.store is None:
            raise StoreNotInitializedError()

        race_name = next((race.race_name for race in self._races if race.round == round_val), f"Round {round_val}")

        detail_title = self.query_one("#results-detail-title", Static)
        detail_title.update(rich.text.Text(f"Round {round_val} {EM_DASH} {race_name}"))
        detail_title.display = True

        detail_status = self.query_one("#results-detail-status", Static)
        detail_status.update(f"Loading results for round {round_val}…")
        detail_status.display = True

        results_table = self.query_one("#results-table", DataTable)
        results_table.display = False

        try:
            store_res = await self.app.store.get_race_results(season, round_val)
        except (JolpicaError, sqlite3.Error):
            detail_status.update(f"Results unavailable — fetch failed for round {round_val}.")
            detail_status.display = True
            results_table.display = False
            return

        results = store_res.data
        if not results:
            detail_status.update(f"No results available for round {round_val}.")
            detail_status.display = True
            results_table.display = False
        else:
            results_table.clear(columns=True)
            results_table.add_columns("Pos", "Driver", "Team", "Grid", "Laps", "Time", "Status", "Pts")

            # Bounded loop: len(results) <= 26, bounded by maximum driver field size in F1.
            for row in build_result_rows(results):
                results_table.add_row(*safe_row(row))

            detail_status.display = False
            results_table.display = True

            if store_res.source == Source.STALE_CACHE:
                as_of = f"{store_res.fetched_at:%H:%M}"
                self.app.notify(
                    f"Serving stale cached results for round {round_val} (as of {as_of} UTC).", severity="warning"
                )


def build_result_rows(results: list[RaceResult]) -> list[tuple[str, ...]]:
    """Pure results-table rows, sorted by position ascending with None last (AC-2)."""
    sorted_results = sorted(results, key=lambda r: (r.position is None, r.position))
    rows = []
    # Loop bound: len(results) <= one API page (PoT #2).
    for r in sorted_results:
        driver_name = f"{r.driver.given_name} {r.driver.family_name}"
        time_cell = r.time_str if (r.time_str is not None and r.time_str != "") else EM_DASH
        rows.append(
            (
                r.position_text,
                driver_name,
                r.constructor.name,
                str(r.grid),
                str(r.laps),
                time_cell,
                r.status,
                format_points(r.points),
            )
        )
    return rows


def build_round_rows(races: list[Race]) -> list[tuple[str, str]]:
    """Pure round-table rows, sorted by round ascending (AC-3)."""
    # Loop bound: len(races) <= one API page (PoT #2).
    return [(str(race.round), race.race_name) for race in sorted(races, key=lambda r: r.round)]


def default_round_index(races: list[Race], now: datetime.datetime) -> int | None:
    """Index of the last race whose start is strictly less than now (AC-4)."""
    sorted_races = sorted(races, key=lambda r: r.round)
    last_idx = None
    # Loop bound: len(races) <= one API page (PoT #2).
    for index, race in enumerate(sorted_races):
        if race.start < now:
            last_idx = index
    return last_idx
