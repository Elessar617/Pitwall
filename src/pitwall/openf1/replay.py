import asyncio
import json
import math
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pitwall.errors import DataParseError
from pitwall.openf1.errors import ReplayDataError
from pitwall.openf1.models import (
    IntervalPoint,
    Lap,
    PitStop,
    PositionUpdate,
    RaceControlMessage,
    SessionDriver,
    Stint,
    parse_drivers,
    parse_intervals,
    parse_laps,
    parse_pit,
    parse_position,
    parse_race_control,
    parse_stints,
    parse_timestamp,
)

TICK_INTERVAL_S = 0.5
KIND_PRIORITY = {
    "position": 0,
    "interval": 1,
    "lap_started": 2,
    "lap_completed": 3,
    "pit": 4,
    "race_control": 5,
}


@dataclass(frozen=True)
class ReplaySession:
    drivers: list[SessionDriver]
    stints: list[Stint]
    laps: list[Lap]
    position: list[PositionUpdate]
    intervals: list[IntervalPoint]
    pit: list[PitStop]
    race_control: list[RaceControlMessage]
    replay_start: datetime | None


@dataclass(frozen=True)
class ReplayEvent:
    ts: datetime
    kind: str
    payload: Any


@dataclass(frozen=True)
class ReplayTick:
    index: int
    playhead: datetime
    events: tuple[ReplayEvent, ...]


@runtime_checkable
class TickSource(Protocol):
    def ticks(self) -> AsyncIterator[ReplayTick]: ...


def _read_json(file_path: Path) -> Any:
    """Read and decode a JSON file, raising ReplayDataError naming the file on invalid JSON."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ReplayDataError(f"Invalid JSON in {file_path.name}: {e}") from e  # noqa: TRY003


def _read_replay_start(path: Path) -> datetime | None:
    """Read and parse replay start timestamp from manifest.json."""
    # Safety containment wrapper for reading replay_start from manifest.json.
    # Invariant: If manifest.json is missing, malformed, or has invalid types,
    # we return None as the fallback start time, isolating failures from halting timing replay.
    # Concurrency/Ownership: Synchronous file access, read-only.
    manifest_path = path / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest_data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(manifest_data, dict):
        window = manifest_data.get("replay_window", {})
        if isinstance(window, dict) and "start" in window:
            try:
                return parse_timestamp(window["start"], "replay_window.start")
            except DataParseError:
                return None
    return None


def load_session(path: Path) -> ReplaySession:
    """Load and parse F1 timing streams from a directory."""
    parsers: dict[str, Callable[[Any], list[Any]]] = {
        "drivers": parse_drivers,
        "stints": parse_stints,
        "laps": parse_laps,
        "position": parse_position,
        "intervals": parse_intervals,
        "pit": parse_pit,
        "race_control": parse_race_control,
    }
    loaded = {}
    for name, parser in parsers.items():
        file_path = path / f"{name}.json"
        if not file_path.exists():
            raise ReplayDataError(f"Missing required file: {name}.json")  # noqa: TRY003
        loaded[name] = parser(_read_json(file_path))

    replay_start = _read_replay_start(path)

    return ReplaySession(
        drivers=loaded["drivers"],
        stints=loaded["stints"],
        laps=loaded["laps"],
        position=loaded["position"],
        intervals=loaded["intervals"],
        pit=loaded["pit"],
        race_control=loaded["race_control"],
        replay_start=replay_start,
    )


def merge_events(session: ReplaySession) -> list[ReplayEvent]:
    """Pure deterministic merge of all timing streams into a sorted timeline."""
    events_with_keys = []

    def add_events(records: list[Any], kind: str) -> None:
        # Loop Bound: bounded by records list length (typically up to 272).
        # Invariants: events are priority sorted based on KIND_PRIORITY index.
        kind_idx = KIND_PRIORITY[kind]
        for seq, r in enumerate(records):
            ts = getattr(r, "date", None) or getattr(r, "date_start", None)
            if ts is not None:
                drv_num = r.driver_number if r.driver_number is not None else -1
                events_with_keys.append(((ts, kind_idx, drv_num, seq), ReplayEvent(ts, kind, r)))
                if kind == "lap_started" and getattr(r, "lap_duration", None) is not None:
                    comp_ts = ts + timedelta(seconds=r.lap_duration)
                    comp_idx = KIND_PRIORITY["lap_completed"]
                    events_with_keys.append(
                        ((comp_ts, comp_idx, drv_num, seq), ReplayEvent(comp_ts, "lap_completed", r))
                    )

    add_events(session.position, "position")
    add_events(session.intervals, "interval")
    add_events(session.laps, "lap_started")
    add_events(session.pit, "pit")
    add_events(session.race_control, "race_control")

    events_with_keys.sort(key=lambda x: x[0])
    return [x[1] for x in events_with_keys]


class ReplayEngine:
    """Deterministic, tick-driven engine that plays back merged F1 session events."""

    def __init__(
        self,
        events: list[ReplayEvent],
        speed: float,
        tick_interval_s: float = TICK_INTERVAL_S,
        sleep: Callable[[float], Awaitable[None]] | None = None,
        start_at: datetime | None = None,
    ) -> None:
        if speed <= 0:
            raise ValueError("Speed must be positive")  # noqa: TRY003
        if tick_interval_s <= 0:
            raise ValueError("Tick interval must be positive")  # noqa: TRY003
        self.events = events
        self.speed = speed
        self.tick_interval_s = tick_interval_s
        self.sleep = sleep or asyncio.sleep
        self.start_at = start_at

    async def ticks(self) -> AsyncIterator[ReplayTick]:
        """Awaits sleep and yields ReplayTick for each step in the session timeline."""
        if not self.events:
            return

        t0 = self.start_at if self.start_at is not None else self.events[0].ts
        last_ts = self.events[-1].ts
        step_sec = self.tick_interval_s * self.speed
        step = timedelta(seconds=step_sec)

        # NASA style comment:
        # Loop bound: The maximum tick count is pre-calculated from the timeline span.
        # This guarantees that the loop terminates deterministically and does not run indefinitely.
        if last_ts <= t0:
            tick_count = 1
        else:
            diff = (last_ts - t0).total_seconds()
            tick_count = 1 + math.ceil(diff / step_sec)

        event_idx = 0
        num_events = len(self.events)
        # None on the first tick: everything at or before t0 is drained without
        # the strictly-greater filter, matching the previous two-branch drain.
        prev_playhead: datetime | None = None

        for k in range(tick_count):
            await self.sleep(self.tick_interval_s)

            playhead = t0 if k == 0 else t0 + k * step
            tick_events = []
            while event_idx < num_events and self.events[event_idx].ts <= playhead:
                if prev_playhead is None or self.events[event_idx].ts > prev_playhead:
                    tick_events.append(self.events[event_idx])
                event_idx += 1
            prev_playhead = playhead

            yield ReplayTick(index=k, playhead=playhead, events=tuple(tick_events))
