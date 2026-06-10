#!/usr/bin/env python3
# ruff: noqa: C901, S101, RUF001  (verification script: enumerated checks + asserts are the design)
"""Derive live timing view and colour literals from the committed excerpt — STDLIB-ONLY.

F11-clean: no pitwall imports. Re-implements projection, folding, views, and styles.
"""

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXCERPT_DIR = REPO_ROOT / "tests/fixtures/openf1/1285_11291_excerpt"

# D5 VIEWS config
VIEWS = [
    {"key": "all", "label": "all", "lo": None, "hi": None},
    {"key": "lead", "label": "lead fight", "lo": 1, "hi": 5},
    {"key": "podium", "label": "podium fight", "lo": 1, "hi": 4},
    {"key": "points", "label": "points fight", "lo": 8, "hi": 12},
]

EXPECTED_COLOURS = {
    1: "F47600",
    3: "4781D7",
    5: "F50537",
    6: "4781D7",
    10: "00A1E8",
    11: "909090",
    12: "00D7B6",
    14: "229971",
    16: "ED1131",
    18: "229971",
    23: "1868DB",
    27: "F50537",
    30: "6C98FF",
    31: "9C9FA2",
    41: "6C98FF",
    43: "00A1E8",
    44: "ED1131",
    55: "1868DB",
    63: "00D7B6",
    77: "909090",
    81: "F47600",
    87: "9C9FA2",
}

MAP_GRID_WIDTH = 56
MAP_GRID_HEIGHT = 32
BIT_MAP = {
    (0, 0): 0x01,
    (0, 1): 0x02,
    (0, 2): 0x04,
    (1, 0): 0x08,
    (1, 1): 0x10,
    (1, 2): 0x20,
    (0, 3): 0x40,
    (1, 3): 0x80,
}


def _parse_ts(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def _load(name: str) -> list | dict:
    return json.loads((EXCERPT_DIR / f"{name}.json").read_text(encoding="utf-8"))


def style_for_team_colour(colour: str | None) -> str:
    if colour and re.fullmatch(r"[0-9a-fA-F]{6}", colour):
        return f"#{colour}"
    return ""


def get_driver_styles(drivers: list) -> dict:
    styles = {}
    for d in drivers:
        styles[d["driver_number"]] = style_for_team_colour(d.get("team_colour"))
    return styles


def format_interval(val: float | str | None) -> str:
    if val is None:
        return "—"
    if isinstance(val, (int, float)):
        if float(val) == 0.0:
            return "—"
        return f"+{val:.3f}"
    return str(val)


def format_lap_time(val: float | None) -> str:
    if val is None:
        return "—"
    if val >= 60.0:
        m = int(val // 60)
        s = val % 60
        return f"{m}:{s:06.3f}"
    return f"{val:.3f}"


def tyre_for(driver_number: int, current_lap: int | None, stints: list) -> str:
    if current_lap is None:
        return "—"
    driver_stints = [s for s in stints if s.get("driver_number") == driver_number]
    if not driver_stints:
        return "—"
    matching_stints = [s for s in driver_stints if s["lap_start"] <= current_lap <= s["lap_end"]]
    if matching_stints:
        best_stint = max(matching_stints, key=lambda s: s["lap_start"])
    else:
        older_stints = [s for s in driver_stints if s["lap_start"] <= current_lap]
        if older_stints:
            best_stint = max(older_stints, key=lambda s: s["lap_start"])
        else:
            return "—"
    if not best_stint.get("compound"):
        return "—"
    return best_stint["compound"][0].upper()


def merge_raw_events() -> list[tuple]:
    keyed = []

    def add(records: list[dict], kind_idx: int, kind: str, ts_field: str) -> None:
        for seq, r in enumerate(records):
            ts_raw = r.get(ts_field)
            if ts_raw is None:
                continue
            ts = _parse_ts(ts_raw)
            drv = r.get("driver_number")
            drv = -1 if drv is None else drv
            keyed.append(((ts, kind_idx, drv, seq), kind, r))
            if kind == "lap_started" and r.get("lap_duration") is not None:
                comp_ts = ts + timedelta(seconds=r["lap_duration"])
                keyed.append((((comp_ts), 3, drv, seq), "lap_completed", r))

    add(_load("position"), 0, "position", "date")
    add(_load("intervals"), 1, "interval", "date")
    add(_load("laps"), 2, "lap_started", "date_start")
    add(_load("pit"), 4, "pit", "date")
    add(_load("race_control"), 5, "race_control", "date")
    keyed.sort(key=lambda x: x[0])
    return [(key[0], kind, r) for key, kind, r in keyed]


def fold_events(events: list) -> tuple[dict, dict, dict, dict]:
    positions = {}
    intervals = {}
    last_laps = {}
    current_laps = {}
    for _ts, kind, payload in events:
        drv_num = payload.get("driver_number")
        if drv_num is None:
            continue
        if kind == "position":
            positions[drv_num] = payload["position"]
        elif kind == "interval":
            intervals[drv_num] = (payload.get("interval"), payload.get("gap_to_leader"))
        elif kind == "lap_started":
            current_laps[drv_num] = payload["lap_number"]
        elif kind == "lap_completed":
            last_laps[drv_num] = payload.get("lap_duration")
    return positions, intervals, last_laps, current_laps


def build_view_rows(
    state: tuple[dict, dict, dict, dict],
    drivers: list[dict],
    stints: list[dict],
    view: dict,
    styles: dict,
) -> list:
    positions, intervals, last_laps, current_laps = state
    rows = []
    for driver in drivers:
        drv_num = driver["driver_number"]
        pos_val = positions.get(drv_num)
        admitted = True if view["key"] == "all" else pos_val is not None and view["lo"] <= pos_val <= view["hi"]
        if not admitted:
            continue
        _int_val, _gap_val = intervals.get(drv_num, (None, None))
        last_laps.get(drv_num)
        current_lap = current_laps.get(drv_num)
        tyre = tyre_for(drv_num, current_lap, stints)
        pos_str = str(pos_val) if pos_val is not None else "—"
        drv_str = driver["name_acronym"]
        style = styles.get(drv_num, "")
        rows.append((pos_val, drv_num, (pos_str, drv_str, style, tyre)))
    rows.sort(key=lambda x: (x[0] is None, x[0], x[1]))
    return [x[2] for x in rows]


def main() -> None:
    # 1. Colors parsing check
    drivers = _load("drivers")
    styles = get_driver_styles(drivers)
    for d_num, colour in EXPECTED_COLOURS.items():
        assert styles[d_num] == f"#{colour}"
    print("--- AC-2 Colour Table Verified ---")

    # 2. location_all facts
    loc_all = _load("location_all")
    assert len(loc_all) == 3300
    distinct_drivers = {r["driver_number"] for r in loc_all}
    assert len(distinct_drivers) >= 18
    # Sortedness
    keys = [(_parse_ts(r["date"]), r["driver_number"]) for r in loc_all]
    assert all(keys[i] <= keys[i + 1] for i in range(len(keys) - 1))
    print("--- AC-1c location_all Facts Verified ---")

    # 3. Projection and Outline Grid
    # Compute projection bounds for all multi-driver points
    x_vals = [r["x"] for r in loc_all]
    y_vals = [r["y"] for r in loc_all]
    x_min, x_max = min(x_vals), max(x_vals)
    y_min, y_max = min(y_vals), max(y_vals)
    span_x = x_max - x_min
    span_y = y_max - y_min
    scale = min(111.0 / max(span_x, 1.0), 127.0 / max(span_y, 1.0))
    offset_x = (111.0 - span_x * scale) / 2.0
    offset_y = (127.0 - span_y * scale) / 2.0

    print("--- AC-7 Multi-Driver Projection Literals ---")
    print(f"  x_min: {x_min}, x_max: {x_max}")
    print(f"  y_min: {y_min}, y_max: {y_max}")
    print(f"  scale: {scale:.6f}, offset_x: {offset_x:.6f}, offset_y: {offset_y:.6f}")

    # Build outline grid
    grid = [[0 for _ in range(MAP_GRID_WIDTH)] for _ in range(MAP_GRID_HEIGHT)]
    for r in loc_all:
        dot_col = round((r["x"] - x_min) * scale + offset_x)
        dot_row = round((y_max - r["y"]) * scale + offset_y)
        col = dot_col // 2
        row = dot_row // 4
        dx = dot_col % 2
        dy = dot_row % 4
        if 0 <= col < MAP_GRID_WIDTH and 0 <= row < MAP_GRID_HEIGHT:
            grid[row][col] |= BIT_MAP[(dx, dy)]
    outline = []
    for r_idx in range(MAP_GRID_HEIGHT):
        row_chars = []
        for c_idx in range(MAP_GRID_WIDTH):
            row_chars.append(chr(0x2800 + grid[r_idx][c_idx]))
        outline.append("".join(row_chars))

    print("--- AC-7 Outline Grid (20 lines) ---")
    for line in outline:
        print(f"  {line}")

    # 4. Tick-0 and Final marker cell->driver->style maps
    # Setup feed: playheads 20:30:00 and 20:32:30
    t0 = datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC)
    t_end = datetime(2026, 5, 24, 20, 32, 30, tzinfo=UTC)

    def get_markers(playhead: datetime) -> dict:
        latest = {}
        for r in loc_all:
            dt = _parse_ts(r["date"])
            if dt <= playhead:
                latest[r["driver_number"]] = r
        return latest

    def get_marker_cells(markers: dict) -> dict:
        cells = {}
        for d_num in sorted(markers.keys()):
            r = markers[d_num]
            dot_col = round((r["x"] - x_min) * scale + offset_x)
            dot_row = round((y_max - r["y"]) * scale + offset_y)
            col = dot_col // 2
            row = dot_row // 4
            if 0 <= col < MAP_GRID_WIDTH and 0 <= row < MAP_GRID_HEIGHT:
                cells[(row, col)] = d_num
        return cells

    markers_t0 = get_markers(t0)
    cells_t0 = get_marker_cells(markers_t0)
    print("--- AC-7 Tick-0 Marker Cells & Styles ---")
    print(f"  Marker cells count: {len(cells_t0)}")
    for cell, d_num in sorted(cells_t0.items()):
        print(f"  {cell} -> Driver {d_num} -> Style {styles[d_num]}")

    markers_end = get_markers(t_end)
    cells_end = get_marker_cells(markers_end)
    print("--- AC-7 Final Marker Cells & Styles ---")
    print(f"  Marker cells count: {len(cells_end)}")
    for cell, d_num in sorted(cells_end.items()):
        print(f"  {cell} -> Driver {d_num} -> Style {styles[d_num]}")

    EXPECTED_OUTLINE = (
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠙⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡄⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢧⠹⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⢳⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⢳⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠈⢧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠈⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠃⠀⠀⠀⠀⠸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡸⠀⠀⠀⠀⠀⠀⢳⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠇⠀⠀⠀⠀⠀⠀⠘⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠚⠁⠀⠀⠀⠀⠀⠀⠀⠀⢣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠡⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠓⠒⠲⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣹⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢳⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠢⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢦⠀⠀⠀⠀⠀⠀⠀⠀⢸⡃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⢸⢁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠳⣄⠀⠀⠀⠀⠀⠀⢸⠈⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠳⢄⡀⠀⠀⠀⠸⣄⡢⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠒⠤⢄⣀⣀⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    )
    EXPECTED_CELLS_T0 = {
        (0, 22): 11,
        (1, 24): 23,
        (2, 23): 63,
        (3, 23): 12,
        (7, 22): 81,
        (8, 22): 3,
        (8, 29): 27,
        (9, 22): 44,
        (13, 17): 16,
        (13, 32): 31,
        (14, 17): 6,
        (14, 32): 55,
        (21, 20): 18,
        (21, 34): 41,
        (23, 35): 77,
        (25, 36): 1,
        (27, 36): 87,
        (28, 36): 10,
        (29, 28): 43,
        (31, 33): 30,
    }
    EXPECTED_CELLS_END = {
        (0, 22): 5,
        (0, 23): 1,
        (0, 24): 27,
        (1, 24): 23,
        (5, 23): 63,
        (6, 23): 12,
        (7, 28): 55,
        (10, 19): 44,
        (10, 20): 3,
        (12, 18): 81,
        (15, 32): 77,
        (16, 17): 31,
        (18, 17): 16,
        (19, 17): 6,
        (20, 33): 87,
        (21, 34): 41,
        (22, 34): 10,
        (27, 26): 11,
        (30, 30): 18,
        (30, 38): 30,
        (31, 34): 43,
    }
    EXPECTED_VIEW_CELLS_T0 = {
        "all": [
            (0, 22),
            (1, 24),
            (2, 23),
            (3, 23),
            (7, 22),
            (8, 22),
            (8, 29),
            (9, 22),
            (13, 17),
            (13, 32),
            (14, 17),
            (14, 32),
            (21, 20),
            (21, 34),
            (23, 35),
            (25, 36),
            (27, 36),
            (28, 36),
            (29, 28),
            (31, 33),
        ],
        "lead": [(2, 23), (3, 23), (8, 22), (9, 22), (13, 17)],
        "podium": [(2, 23), (3, 23), (8, 22), (9, 22)],
        "points": [(14, 32), (25, 36), (27, 36), (28, 36), (31, 33)],
    }
    EXPECTED_SPAN_OFFSETS_T0 = {
        "all": [
            22,
            81,
            137,
            194,
            421,
            478,
            485,
            535,
            758,
            773,
            815,
            830,
            1217,
            1231,
            1346,
            1461,
            1575,
            1632,
            1681,
            1800,
        ],
        "lead": [137, 194, 478, 535, 758],
        "podium": [137, 194, 478, 535],
        "points": [830, 1461, 1575, 1632, 1800],
    }

    # 5. Timing views
    events = merge_raw_events()
    stints = _load("stints")

    # Tick 0 timing
    tick0_events = [e for e in events if e[0] <= t0]
    state_t0 = fold_events(tick0_events)

    # Compute view cells and offsets
    view_cells_t0 = {}
    view_offsets_t0 = {}
    for v in VIEWS:
        admitted = []
        for d in drivers:
            drv_num = d["driver_number"]
            pos_val = state_t0[0].get(drv_num)
            is_adm = True if v["key"] == "all" else pos_val is not None and v["lo"] <= pos_val <= v["hi"]
            if is_adm:
                admitted.append(drv_num)
        v_markers = {d: markers_t0[d] for d in admitted if d in markers_t0}
        v_cells = get_marker_cells(v_markers)
        view_cells_t0[v["key"]] = sorted(v_cells.keys())
        view_offsets_t0[v["key"]] = sorted([r * 57 + c for r, c in v_cells])

    assert tuple(outline) == EXPECTED_OUTLINE
    assert cells_t0 == EXPECTED_CELLS_T0
    assert cells_end == EXPECTED_CELLS_END
    assert view_cells_t0 == EXPECTED_VIEW_CELLS_T0
    assert view_offsets_t0 == EXPECTED_SPAN_OFFSETS_T0

    # End state timing
    state_end = fold_events(events)

    print("--- AC-4c Timing Views ---")
    for state_name, state in [("Tick-0", state_t0), ("End-State", state_end)]:
        print(f"  {state_name}:")
        for v in VIEWS:
            rows = build_view_rows(state, drivers, stints, v, styles)
            acronyms = [r[1] for r in rows]
            row_styles = [r[2] for r in rows]
            print(f"    View {v['key']}: Acronyms={acronyms}, Styles={row_styles}")

    # 6. Suffixed status strings
    print("--- AC-9 Suffixed Status Strings ---")
    base_t0 = "Replay ×60 · 20:30:00 UTC"
    base_end = "Replay finished · 20:32:30 UTC"
    for base in [base_t0, base_end]:
        for v in VIEWS:
            suffix = f" · view: {v['label']}" if v["key"] != "all" else ""
            print(f"  Status: {base}{suffix}")

    print("MATCH VERDICT: SUCCESS")


if __name__ == "__main__":
    main()
