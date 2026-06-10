import asyncio
import math
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from pitwall.openf1.client import OpenF1Client
from pitwall.openf1.errors import OpenF1Error
from pitwall.openf1.models import (
    LocationPoint,
    Session,
    SessionDriver,
    Stint,
)
from pitwall.openf1.replay import KIND_PRIORITY, ReplayEvent, ReplayTick, TickSource

LIVE_PRE_SESSION_GRACE_S = 900.0
LIVE_OVERRUN_GRACE_S = 3600.0
LIVE_POLL_INTERVAL_S = 10.0
LIVE_LOCATION_BACKFILL_S = 300.0
LIVE_CURSOR_OVERLAP_S = 1.0
# 240 s covers the longest realistic lap; +1 s guards the exact-second
# boundary that strict date> filtering would otherwise drop (adversary-10-1 C3).
LAP_REFETCH_OVERLAP_S = 241.0
LIVE_SEEN_RETENTION_S = 2.0
STINTS_REFRESH_TICKS = 6
MAX_LIVE_TICKS = 2160
LIVE_LOCATION_BUFFER_CAP = 100_000


def session_window(session: Session, now: datetime) -> str:
    """Determine the status of the session window based on current time."""
    start_bound = session.date_start - timedelta(seconds=LIVE_PRE_SESSION_GRACE_S)
    end_bound = session.date_end + timedelta(seconds=LIVE_OVERRUN_GRACE_S)
    if now < start_bound:
        return "upcoming"
    elif now > end_bound:
        return "ended"
    else:
        return "open"


class LiveSource(TickSource):
    """A polling tick source that yields real-time data from the OpenF1 API."""

    def __init__(
        self,
        client: OpenF1Client,
        session: Session,
        *,
        poll_interval_s: float = LIVE_POLL_INTERVAL_S,
        sleep: Callable[[float], Awaitable[None]] | None = None,
        clock: Callable[[], datetime] | None = None,
        location_buffer_cap: int = LIVE_LOCATION_BUFFER_CAP,
    ) -> None:
        self.client = client
        self.session = session
        self.poll_interval_s = poll_interval_s
        self.sleep = sleep or asyncio.sleep
        self.clock = clock or (lambda: datetime.now(UTC))
        self.location_buffer_cap = location_buffer_cap

        # Exposed State
        self.drivers: tuple[SessionDriver, ...] = ()
        self.stints: tuple[Stint, ...] = ()
        self.data_head: datetime | None = None
        self.consecutive_failures: int = 0
        self.outline_ready: bool = False

        self._location_buffer: list[LocationPoint] = []
        self._outline_taken: bool = False
        self._latest_location_dict: dict[int, LocationPoint] = {}

        # Internal Polling State
        self._cursors: dict[str, datetime | None] = {
            "position": None,
            "intervals": None,
            "laps": None,
            "pit": None,
            "race_control": None,
            "location": None,
        }
        self._seen: dict[str, set[Any]] = {
            "position": set(),
            "intervals": set(),
            "pit": set(),
            "race_control": set(),
        }
        self._laps_started_emitted: set[tuple[int, int]] = set()
        self._laps_completed_emitted: set[tuple[int, int]] = set()
        self._any_failed: bool = False

    def take_outline_points(self) -> tuple[LocationPoint, ...]:
        """Return accumulated location points and clear the buffer (PERF-1: also stops buffering)."""
        self._outline_taken = True
        pts = tuple(self._location_buffer)
        self._location_buffer.clear()
        return pts

    def latest_location(self) -> dict[int, LocationPoint]:
        """Return a fresh copy of the latest location points per driver."""
        return dict(self._latest_location_dict)

    async def _poll_stream(self, fetch_fn: Callable[[], Awaitable[list[Any]]]) -> tuple[list[Any], bool]:
        """Wrap request in exception containment and record failures."""
        try:
            res = await fetch_fn()
        except OpenF1Error:
            # NASA style comment:
            # Failure Mode: OpenF1Error is contained per endpoint.
            # Capturing failures at the stream boundary prevents a single down stream
            # or connection error from crashing the entire live polling process.
            self._any_failed = True
            return [], False
        else:
            return res, True

    async def _update_drivers(self) -> None:
        """Fetch drivers wholesale on first tick."""
        data, success = await self._poll_stream(lambda: self.client.get_drivers(self.session.session_key))
        if success:
            self.drivers = tuple(data)

    async def _update_stints(self) -> None:
        """Fetch stints wholesale on STINTS_REFRESH_TICKS interval."""
        data, success = await self._poll_stream(lambda: self.client.get_stints(self.session.session_key))
        if success:
            self.stints = tuple(data)

    async def _update_simple_stream(self, index: int, name: str, kind: str, getter) -> list[ReplayEvent]:
        """Poll one cursor-windowed stream and dedupe into ReplayEvents.

        The four simple streams (position/intervals/pit/race_control) share
        this exact lifecycle; only laps and location have bespoke rules.
        """
        cursor = self._cursors[name]
        date_gt = (
            None
            if (index == 0 or cursor is None)
            else (cursor - timedelta(seconds=LIVE_CURSOR_OVERLAP_S)).strftime("%Y-%m-%dT%H:%M:%S")
        )
        data, success = await self._poll_stream(lambda: getter(date_gt))
        if not success:
            return []
        events = []
        new_cursor = cursor
        for r in data:
            if r in self._seen[name]:
                continue
            self._seen[name].add(r)
            events.append(ReplayEvent(ts=r.date, kind=kind, payload=r))
            if new_cursor is None or r.date > new_cursor:
                new_cursor = r.date
        self._cursors[name] = new_cursor
        if new_cursor is not None:
            limit = new_cursor - timedelta(seconds=LIVE_SEEN_RETENTION_S)
            self._seen[name] = {x for x in self._seen[name] if x.date >= limit}
        return events

    async def _update_laps(self, index: int) -> list[ReplayEvent]:
        """Poll laps and synthesize lap_started and lap_completed events."""
        cursor = self._cursors["laps"]
        date_gt = (
            None
            if (index == 0 or cursor is None)
            else (cursor - timedelta(seconds=LAP_REFETCH_OVERLAP_S)).strftime("%Y-%m-%dT%H:%M:%S")
        )
        data, success = await self._poll_stream(lambda: self.client.get_laps(self.session.session_key, date_gt=date_gt))
        if not success:
            return []
        events = []
        new_cursor = cursor
        # Cursor = max date_start; the 241 s query overlap (240 s lap coverage
        # + 1 s exact-boundary guard) re-fetches in-flight laps, and the
        # emitted-key sets dedupe re-served records. A lap left uncompleted
        # longer than 241 s loses its completion event — recorded limitation.
        for r in data:
            if r.date_start is None:
                continue
            key = (r.driver_number, r.lap_number)
            if key not in self._laps_started_emitted:
                self._laps_started_emitted.add(key)
                events.append(ReplayEvent(ts=r.date_start, kind="lap_started", payload=r))
            if r.lap_duration is not None and key not in self._laps_completed_emitted:
                self._laps_completed_emitted.add(key)
                comp_ts = r.date_start + timedelta(seconds=r.lap_duration)
                events.append(ReplayEvent(ts=comp_ts, kind="lap_completed", payload=r))
            if new_cursor is None or r.date_start > new_cursor:
                new_cursor = r.date_start
        self._cursors["laps"] = new_cursor
        return events

    async def _update_location(self, index: int) -> list[LocationPoint]:
        """Poll and store locations in outline buffer and latest marker mapping."""
        cursor = self._cursors["location"]
        if index == 0:
            date_gt = (self.clock() - timedelta(seconds=LIVE_LOCATION_BACKFILL_S)).strftime("%Y-%m-%dT%H:%M:%S")
        elif cursor is None:
            date_gt = None
        else:
            date_gt = (cursor - timedelta(seconds=LIVE_CURSOR_OVERLAP_S)).strftime("%Y-%m-%dT%H:%M:%S")
        data, success = await self._poll_stream(
            lambda: self.client.get_location(self.session.session_key, date_gt=date_gt)
        )
        if not success:
            return []
        new_cursor = cursor
        for p in data:
            # PERF-1: the buffer's sole consumer is the one-shot outline build;
            # once taken, buffering would only retain ~20 MiB nobody reads.
            if not self._outline_taken and len(self._location_buffer) < self.location_buffer_cap:
                self._location_buffer.append(p)
            drv = p.driver_number
            if drv not in self._latest_location_dict or p.date >= self._latest_location_dict[drv].date:
                self._latest_location_dict[drv] = p
            if new_cursor is None or p.date > new_cursor:
                new_cursor = p.date
        self._cursors["location"] = new_cursor

        if self._location_buffer and not self._outline_taken:
            dates = [pt.date for pt in self._location_buffer]
            span = (max(dates) - min(dates)).total_seconds()
            count = len(self._location_buffer)
            if (span >= 150.0 and count >= 500) or count >= self.location_buffer_cap:
                self.outline_ready = True
        return data

    async def _collect_tick_events(self, k: int) -> tuple[ReplayEvent, ...]:
        """Fetch events across all stream endpoints and compile a sorted list."""
        sk = self.session.session_key
        per_stream = [
            await self._update_simple_stream(
                k, "position", "position", lambda dg: self.client.get_position(sk, date_gt=dg)
            ),
            await self._update_simple_stream(
                k, "intervals", "interval", lambda dg: self.client.get_intervals(sk, date_gt=dg)
            ),
            await self._update_laps(k),
            await self._update_simple_stream(k, "pit", "pit", lambda dg: self.client.get_pit(sk, date_gt=dg)),
            await self._update_simple_stream(
                k, "race_control", "race_control", lambda dg: self.client.get_race_control(sk, date_gt=dg)
            ),
        ]
        # One ordering-sequence across every stream's events (stable tie-break).
        events_with_seq = [(e, seq) for seq, e in enumerate(ev for stream in per_stream for ev in stream)]

        events_with_seq.sort(
            key=lambda item: (
                item[0].ts,
                KIND_PRIORITY[item[0].kind],
                getattr(item[0].payload, "driver_number", -1)
                if getattr(item[0].payload, "driver_number", None) is not None
                else -1,
                item[1],
            )
        )
        return tuple(item[0] for item in events_with_seq)

    async def ticks(self) -> AsyncIterator[ReplayTick]:
        """Core polling loop yielding ReplayTick objects until bound or termination."""
        # Loop Bound: Bounded by tick_count computed once at start (maximum MAX_LIVE_TICKS).
        # Invariants: data_head is monotonic (only moves forward).
        # Failure Modes: Errors in stream requests are contained individually,
        # yielding empty ticks while incrementing consecutive_failures.
        now = self.clock()
        limit_date = self.session.date_end + timedelta(seconds=LIVE_OVERRUN_GRACE_S)
        diff_s = (limit_date - now).total_seconds()

        tick_count = 0 if diff_s <= 0 else min(MAX_LIVE_TICKS, 1 + math.ceil(diff_s / self.poll_interval_s))

        for k in range(tick_count):
            await self.sleep(self.poll_interval_s)

            if self.clock() > limit_date:
                break

            self._any_failed = False

            if k == 0:
                await self._update_drivers()

            if k % STINTS_REFRESH_TICKS == 0:
                await self._update_stints()

            tick_events = await self._collect_tick_events(k)
            loc_points = await self._update_location(k)

            max_ts = self.data_head
            for e in tick_events:
                if max_ts is None or e.ts > max_ts:
                    max_ts = e.ts
            for p in loc_points:
                if max_ts is None or p.date > max_ts:
                    max_ts = p.date
            self.data_head = max_ts

            if self._any_failed:
                self.consecutive_failures += 1
            else:
                self.consecutive_failures = 0

            yield ReplayTick(index=k, playhead=self.data_head or self.session.date_start, events=tick_events)
