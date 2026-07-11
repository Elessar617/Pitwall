# ruff: noqa: RUF001, RUF002
import asyncio
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

import rich.text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import DataTable, Static

from pitwall.errors import DataParseError
from pitwall.openf1 import (
    TICK_INTERVAL_S,
    LiveSource,
    LocationFeed,
    OpenF1Client,
    OpenF1Error,
    ReplayDataError,
    ReplayEngine,
    ReplayEvent,
    Session,
    load_location_all,
    load_session,
    merge_events,
)
from pitwall.openf1.live import session_window
from pitwall.screens.base import PitwallScreen
from pitwall.screens.live_views import (
    VIEWS,
    build_view_rows,
    driver_styles,
    filter_markers,
)
from pitwall.screens.live_views import (
    build_tower_rows as build_tower_rows,
)
from pitwall.screens.live_views import (
    format_interval as format_interval,
)
from pitwall.screens.live_views import (
    format_lap_time as format_lap_time,
)
from pitwall.screens.live_views import (
    tyre_for as tyre_for,
)
from pitwall.screens.track_map import (
    LocationPoint,
    MapProjection,
    build_outline,
    build_projection,
    render_map,
)

MAP_MIN_SPLIT_WIDTH = 100


def format_speed(speed: float) -> str:
    """Format replay speed.

    >>> format_speed(60.0)
    '×60'
    >>> format_speed(1.5)
    '×1.5'
    """
    return f"×{speed:g}"


def fold_events(
    events: Sequence[ReplayEvent],
    state: tuple[
        dict[int, int], dict[int, tuple[float | str | None, float | str | None]], dict[int, float], dict[int, int]
    ]
    | None = None,
) -> tuple[dict[int, int], dict[int, tuple[float | str | None, float | str | None]], dict[int, float], dict[int, int]]:
    """Fold events to get end-state mapping of drivers timing attributes.

    Returns new state objects (input state unmutated).
    """
    if state is None:
        positions: dict[int, int] = {}
        intervals: dict[int, tuple[float | str | None, float | str | None]] = {}
        last_laps: dict[int, float] = {}
        current_laps: dict[int, int] = {}
    else:
        positions = dict(state[0])
        intervals = dict(state[1])
        last_laps = dict(state[2])
        current_laps = dict(state[3])

    for e in events:
        drv_num = getattr(e.payload, "driver_number", None)
        if drv_num is None:
            continue

        if e.kind == "position":
            positions[drv_num] = e.payload.position
        elif e.kind == "interval":
            intervals[drv_num] = (e.payload.interval, e.payload.gap_to_leader)
        elif e.kind == "lap_started":
            current_laps[drv_num] = e.payload.lap_number
        elif e.kind == "lap_completed":
            last_laps[drv_num] = e.payload.lap_duration

    return positions, intervals, last_laps, current_laps


class LiveTimingScreen(PitwallScreen):
    """Timing tower screen driven by OpenF1 session replay."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("v", "cycle_view", "View"),
    ]

    DEFAULT_CSS = """
    LiveTimingScreen #live-body {
        height: 1fr;
    }
    LiveTimingScreen #live-table {
        width: 48;
        height: 1fr;
    }
    LiveTimingScreen #live-table.tower-only {
        width: 80;
    }
    LiveTimingScreen #live-map {
        width: 58;
        height: 34;
        align: center middle;
        border: round;
        border-title-align: center;
    }
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.view_index = 0

    def compose_body(self) -> ComposeResult:
        if self.app.config.live:
            msg = "Connecting to live session…"
        elif self.app.config.replay_dir:
            msg = "Loading replay…"
        else:
            msg = "No live session — start pitwall with --live or --replay <fixtures-dir>."
        yield Static(msg, id="live-status")
        with Horizontal(id="live-body"):
            table = DataTable(id="live-table")
            table.display = False
            table.add_class("tower-only")
            yield table

            map_widget = Static(id="live-map")
            map_widget.border_title = ""
            map_widget.border_subtitle = ""
            map_widget.display = False
            yield map_widget

    def on_mount(self) -> None:
        if self.app.config.live:
            self._live_worker()
        elif self.app.config.replay_dir:
            self._replay_worker()

    def on_screen_suspend(self) -> None:
        # NASA style comment:
        # Concurrency: Cancels all background live polling and replay workers
        # when the user switches away from the LiveTimingScreen.
        self.workers.cancel_group(self, "live-replay")

    def on_unmount(self) -> None:
        # NASA style comment:
        # Concurrency: Cancels all background live polling and replay workers
        # when the LiveTimingScreen is unmounted/removed from the screen stack.
        self.workers.cancel_group(self, "live-replay")

    def _init_map(
        self, location_points: Sequence[LocationPoint]
    ) -> tuple[bool, MapProjection | None, tuple[str, ...] | None, LocationFeed | None]:
        """Initialize projection, outline, and feed if points exist."""
        # NASA style comment:
        # Invariant: Empty points list returns False indicator with None values to safely
        # bypass map rendering, preventing division-by-zero during bounding box calculation.
        if not location_points:
            return False, None, None, None

        projection = build_projection(location_points)
        outline = build_outline(location_points, projection)
        feed = LocationFeed(list(location_points))  # ty: ignore[invalid-argument-type] - Protocol/model unification below
        return True, projection, outline, feed

    def _init_table(self, table: DataTable) -> None:
        """Clear and initialize timing table columns."""
        table.clear(columns=True)
        table.add_columns("Pos", "Drv", "Int", "Gap", "Last", "Tyre")

    def _apply_map_layout(self, table: DataTable, map_widget: Static) -> None:
        """Show the map beside the tower only when the terminal is wide enough."""
        if self.size.width >= MAP_MIN_SPLIT_WIDTH:
            map_widget.display = True
            table.remove_class("tower-only")
        else:
            map_widget.display = False
            table.add_class("tower-only")

    def _show_unavailable(
        self,
        message: str,
        status: Static,
        table: DataTable,
        map_widget: Static,
        exc: Exception | None = None,
    ) -> None:
        """Show an unavailable status, hide data widgets, and optionally notify."""
        status.update(message)
        table.display = False
        map_widget.display = False
        if exc is not None:
            self.app.notify(str(exc), severity="error")

    def action_cycle_view(self) -> None:
        table = self.query_one("#live-table", DataTable)
        if not table.display:
            return
        self.view_index = (self.view_index + 1) % len(VIEWS)
        self._refresh_display()

    def _is_data_bearing(self, status_str: str) -> bool:
        return status_str.startswith(("Replay ", "Live · ", "Live ended "))

    def _get_status_text(self, base_status: str) -> rich.text.Text:
        # SEC-1: the live status embeds replay/API-sourced session_name; render
        # via Text so no field is interpreted as Rich markup.
        view = VIEWS[self.view_index]
        if not self._is_data_bearing(base_status) or view.key == "all":
            return rich.text.Text(base_status)
        return rich.text.Text(f"{base_status} · view: {view.label}")

    def _refresh_display(self) -> None:
        """Shared render logic for LiveTimingScreen using instance context."""
        table = self.query_one("#live-table", DataTable)
        map_widget = self.query_one("#live-map", Static)
        status = self.query_one("#live-status", Static)

        if hasattr(self, "_status_base"):
            status.update(self._get_status_text(self._status_base))

        if not table.display:
            return

        view = VIEWS[self.view_index]

        # 1. Update timing table rows
        if hasattr(self, "_state") and hasattr(self, "_drivers") and hasattr(self, "_stints"):
            positions, intervals, last_laps, current_laps = self._state
            # NASA style comment:
            # Invariant: Pre-populates all session driver numbers in positions_full to prevent
            # build_view_rows from excluding drivers who have not yet received any position updates.
            positions_full = {d.driver_number: positions.get(d.driver_number) for d in self._drivers}
            state_full = (positions_full, intervals, last_laps, current_laps)

            rows = build_view_rows(
                state_full,
                self._drivers,
                self._stints,
                view,
                self._styles,
            )
            table.clear(columns=False)
            table.add_rows(rows)

        # 2. Update map markers
        if hasattr(self, "_has_map") and self._has_map and hasattr(self, "_markers"):
            outline, projection = self._outline, self._projection
            if outline is None or projection is None:
                # Invariant: _has_map is set only after a successful map build.
                return
            filtered = filter_markers(self._markers, self._state[0], view)
            map_content = render_map(
                outline,
                filtered,
                projection,
                self._styles,
            )
            map_widget.update(map_content)
            title, subtitle = "", ""
            if map_widget.display:
                title = "Track"
                # NASA style comment:
                # Invariant: caption playhead is extracted from the data-bearing status
                # to prevent clock drift/desynchronization between the status and the map.
                if hasattr(self, "_status_base"):
                    time_match = re.search(r"\b\d{2}:\d{2}:\d{2}\b", self._status_base)
                    if time_match:
                        subtitle = f"Montreal · {time_match.group(0)} UTC"
            map_widget.border_title = title
            map_widget.border_subtitle = subtitle

    @work(exclusive=True, group="live-replay")
    async def _replay_worker(self) -> None:
        replay_dir = self.app.config.replay_dir
        status = self.query_one("#live-status", Static)
        table = self.query_one("#live-table", DataTable)
        map_widget = self.query_one("#live-map", Static)

        # NASA style comment:
        # Failure Modes: Catches ReplayDataError, DataParseError, or OSError if files are
        # absent or corrupt, notifying the user and gracefully resetting display states.
        if replay_dir is None:
            # Invariant: the replay worker only starts when config.replay_dir is set.
            return
        try:
            session = await asyncio.to_thread(load_session, Path(replay_dir))
            events = merge_events(session)
            location_points = await asyncio.to_thread(load_location_all, Path(replay_dir))
        except (ReplayDataError, DataParseError, OSError) as exc:
            self._show_unavailable("Replay unavailable — failed to load replay data.", status, table, map_widget, exc)
            return

        if not events:
            self._show_unavailable("Replay unavailable — replay data contains no events.", status, table, map_widget)
            return

        engine = ReplayEngine(
            events=events,
            speed=self.app.config.replay_speed,
            tick_interval_s=TICK_INTERVAL_S,
            start_at=session.replay_start,
            sleep=self.app.replay_sleep,
        )
        self._init_table(table)
        state = fold_events([])
        last_playhead = session.replay_start
        has_map, projection, outline, feed = self._init_map(location_points)

        # NASA style comment:
        # Ownership: Binds current replay session metadata and styling contexts to the
        # screen instance so that manual view cycling can re-render the exact same frame.
        self._state = state
        self._drivers = session.drivers
        self._stints = session.stints
        self._styles = driver_styles(session.drivers)
        self._has_map = has_map
        self._projection = projection
        self._outline = outline
        self._markers = {}

        async for tick in engine.ticks():
            state = fold_events(tick.events, state)
            self._state = state

            # NASA style comment:
            # Loop Bound: Loop advances monotonically through the ReplayEngine ticks.
            # Invariant: feed cursor advances based on tick playhead without regression.
            if has_map and feed is not None:
                self._markers = feed.advance(tick.playhead)

            if not table.display:
                table.display = True
                if has_map:
                    self._apply_map_layout(table, map_widget)

            speed_str = format_speed(self.app.config.replay_speed)
            self._status_base = f"Replay {speed_str} · {tick.playhead.strftime('%H:%M:%S')} UTC"
            self._refresh_display()
            last_playhead = tick.playhead

        if last_playhead:
            self._status_base = f"Replay finished · {last_playhead.strftime('%H:%M:%S')} UTC"
            self._refresh_display()

    def _handle_out_of_window(
        self, window: str, session: Session, status: Static, table: DataTable, map_widget: Static
    ) -> None:
        table.display = False
        map_widget.display = False
        if window == "upcoming":
            start_str = session.date_start.strftime("%H:%M")
            status.update(rich.text.Text(f"Live: {session.session_name} has not started — begins {start_str} UTC."))
        else:
            end_str = session.date_end.strftime("%H:%M")
            status.update(
                rich.text.Text(f"Live unavailable — latest session ({session.session_name}) ended {end_str} UTC.")
            )

    async def _run_live_loop(
        self, client: OpenF1Client, session: Session, status: Static, table: DataTable, map_widget: Static
    ) -> None:
        source = LiveSource(
            client,
            session,
            sleep=self.app.replay_sleep,
            clock=self.app.clock,
        )
        self._init_table(table)
        status.update(rich.text.Text(f"Live: {session.session_name} — waiting for data…"))
        state = fold_events([])
        self._has_map = False

        # NASA style comment:
        # Concurrency: The loop runs asynchronously awaiting the next polled tick from LiveSource.
        # Loop Bound: Continuously executes until the live session ends or the worker is cancelled.
        try:
            async for tick in source.ticks():
                state = fold_events(tick.events, state)
                self._state = state
                self._drivers = list(source.drivers)
                self._stints = list(source.stints)
                self._styles = driver_styles(self._drivers)

                if not self._has_map and source.outline_ready:
                    location_points = source.take_outline_points()
                    if location_points:
                        self._projection = build_projection(location_points)
                        self._outline = build_outline(location_points, self._projection)
                        self._has_map = True
                        self._apply_map_layout(table, map_widget)

                if self._has_map:
                    self._markers = source.latest_location()

                if not table.display and self._drivers:
                    table.display = True

                # Update live status string
                status_str = (
                    f"Live: {session.session_name} — waiting for data…"
                    if source.data_head is None
                    else f"Live · data to {source.data_head.strftime('%H:%M:%S')} UTC"
                )
                if source.consecutive_failures > 0:
                    status_str += f" · retrying ({source.consecutive_failures})"

                self._status_base = status_str

                # Render timing table and map markers
                self._refresh_display()
        finally:
            # NASA style comment:
            # Ownership: Closes the OpenF1Client's underlying HTTP client session on exit.
            await client.close()

        formatted_end = (source.data_head or session.date_start).strftime("%H:%M:%S")
        self._status_base = f"Live ended · data to {formatted_end} UTC"
        status.update(self._get_status_text(self._status_base))

    @work(exclusive=True, group="live-replay")
    async def _live_worker(self) -> None:
        status = self.query_one("#live-status", Static)
        table = self.query_one("#live-table", DataTable)
        map_widget = self.query_one("#live-map", Static)
        status.update("Connecting to live session…")
        try:
            async with OpenF1Client(transport=self.app.openf1_transport) as client:
                sessions = await client.get_sessions("latest")
                if not sessions:
                    self._show_unavailable("Live unavailable — no session found.", status, table, map_widget)
                    return
                session = sessions[-1]
                now = self.app.clock()
                window = session_window(session, now)
                if window != "open":
                    self._handle_out_of_window(window, session, status, table, map_widget)
                    return

                await self._run_live_loop(client, session, status, table, map_widget)
        except OpenF1Error as exc:
            self._show_unavailable("Live unavailable — could not reach OpenF1.", status, table, map_widget, exc)
