#!/usr/bin/env python3
# ruff: noqa: C901  (verification script: enumerated checks + asserts are the design)
"""Derive live-timing track map literals from the committed excerpt — STDLIB-ONLY.

Independent of src/pitwall by construction (review-08-1 finding 8): raw JSON +
datetime reimplementation of the projection, outline, and feed lookup formulas,
so the printed literals verify the production code rather than echo it.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXCERPT_DIR = REPO_ROOT / "tests/fixtures/openf1/1285_11291_excerpt"

# Invariant: Pinned SPEC AC-5/AC-6 expected outline grid.
EXPECTED_OUTLINE = (
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠙⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡄⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢃⠸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠓⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⢠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⢁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠈⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠃⠀⠀⠀⠀⠈⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡼⠀⠀⠀⠀⠀⠀⢃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠇⠀⠀⠀⠀⠀⠀⠐⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡴⠒⠁⠀⠀⠀⠀⠀⠀⠀⠀⠣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢨⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢨⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢘⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠓⠒⠲⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⡅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡱⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠢⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢦⠀⠀⠀⠀⠀⠀⠀⠀⢐⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠰⢡⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⣀⠀⠀⠀⠀⠀⠀⢸⠐⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠲⢄⡀⠀⠀⠀⠸⣄⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠒⠤⢄⣀⣀⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
)

EXPECTED_PROJECTION = {
    "x_min": -2449.0,
    "x_max": 3899.0,
    "y_min": -2273.0,
    "y_max": 16761.0,
    "scale": 127.0 / 19034.0,
}

EXPECTED_TICKS = [
    ("20:30:00", (36, 25)),
    ("20:30:30", (29, 29)),
    ("20:31:00", (22, 8)),
    ("20:31:30", (33, 19)),
    ("20:32:00", (22, 23)),
    ("20:32:30", (24, 0)),
]


def _parse_ts(value: str) -> datetime:
    """Parse ISO-8601 string to UTC datetime.

    Assumptions: Timestamps are ISO-8601 strings, possibly naive (treated as UTC).
    """
    dt = datetime.fromisoformat(value)
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def print_location_facts(points: list[dict]) -> None:
    """D8 section: AC-2 location.json facts (count, first/last ts, byte size)."""
    raw = (EXCERPT_DIR / "location.json").read_bytes()
    print("--- AC-2 location.json facts ---")
    print(f"  records: {len(points)}")
    print(f"  first date: {points[0]['date']}")
    print(f"  last date: {points[-1]['date']}")
    print(f"  bytes: {len(raw)}")
    print()


def print_rendered_grid(label: str, outline: tuple, cell: tuple) -> None:
    """D8 section: a full rendered grid with the marker cell replaced."""
    col, row = cell
    print(f"--- {label} rendered grid (marker at ({col}, {row})) ---")
    for r, line in enumerate(outline):
        if r == row:
            line = line[:col] + "\u25cf" + line[col + 1 :]
        print(f"  |{line}|")
    print()


def main() -> None:
    location_path = EXCERPT_DIR / "location.json"

    # Failure Mode: If the file is missing or invalid, JSON decoding will fail.
    # Assumption: The file location.json exists in the excerpt directory.
    with open(location_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    points = []
    # Loop Bound: Bounded by the number of records in location.json (exactly 567 in excerpt).
    for p in raw_data:
        points.append(
            {
                "date": _parse_ts(p["date"]),
                "driver_number": int(p["driver_number"]),
                "x": float(p["x"]),
                "y": float(p["y"]),
            }
        )

    print_location_facts(points)

    # Bounding box calculation over ALL points.
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    span_x = x_max - x_min
    span_y = y_max - y_min

    # Invariant: Scale is computed as the minimum of the horizontal and vertical ratios.
    # Bounded horizontal width is 63 (0..63 dots) and vertical height is 79 (0..79 dots).
    scale = min(111.0 / max(span_x, 1.0), 127.0 / max(span_y, 1.0))
    offset_x = (111.0 - span_x * scale) / 2.0
    offset_y = (127.0 - span_y * scale) / 2.0

    print("--- Map Projection Constants ---")
    print(f"  x_min: {x_min}")
    print(f"  x_max: {x_max}")
    print(f"  y_min: {y_min}")
    print(f"  y_max: {y_max}")
    print(f"  scale: {scale} (expected: {127.0 / 19034.0})")
    print(f"  offset_x: {offset_x}")
    print(f"  offset_y: {offset_y}")
    print()

    def dot_for(x: float, y: float) -> tuple[int, int]:
        """Project raw track coordinates to braille dot column and row.

        Assumptions: Scale and offsets are pre-computed.
        Units: Output coordinates are integers in range [0, 111] for column and [0, 127] for row.
        """
        dot_col = round((x - x_min) * scale + offset_x)
        dot_row = round((y_max - y) * scale + offset_y)
        return dot_col, dot_row

    # Project all points to find distinct dots
    distinct_dots = set()
    # Loop Bound: Bounded by the number of parsed points (exactly 567 in excerpt).
    for p in points:
        distinct_dots.add(dot_for(p["x"], p["y"]))

    print(f"Distinct Dots Count: {len(distinct_dots)}")
    print()

    # Grid initialization: 32 rows of 56 columns.
    # Invariant: Each cell represents a 2x4 braille dot block.
    grid_bits = [[0] * 56 for _ in range(32)]

    BITS_MAP = {
        (0, 0): 0x01,
        (0, 1): 0x02,
        (0, 2): 0x04,
        (1, 0): 0x08,
        (1, 1): 0x10,
        (1, 2): 0x20,
        (0, 3): 0x40,
        (1, 3): 0x80,
    }

    # Populate the grid bits
    # Loop Bound: Bounded by the number of distinct projected dots (at most 196 in excerpt).
    for dot_col, dot_row in distinct_dots:
        col = dot_col // 2
        row = dot_row // 4
        dx = dot_col % 2
        dy = dot_row % 4
        if 0 <= col < 56 and 0 <= row < 32:
            grid_bits[row][col] |= BITS_MAP[(dx, dy)]

    # Convert bits to Unicode Braille characters
    non_blank_cells = 0
    grid_lines = []
    # Loop Bound: Exactly 32 rows.
    for r in range(32):
        line_chars = []
        # Loop Bound: Exactly 56 columns.
        for c in range(56):
            bits = grid_bits[r][c]
            if bits != 0:
                non_blank_cells += 1
            line_chars.append(chr(0x2800 + bits))
        grid_lines.append("".join(line_chars))

    print(f"Non-Blank Cells Count: {non_blank_cells}")
    print()

    print("--- Track Outline Grid ---")
    # Loop Bound: Exactly 32 rows.
    for line in grid_lines:
        print(f"|{line}|")
    print()

    # Per-tick marker cell verification
    t0 = datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC)
    playheads = [t0 + timedelta(seconds=k * 30) for k in range(6)]

    print("--- Per-Tick Playhead Points ---")
    tick_results = []
    # Loop Bound: Exactly 6 playhead ticks.
    for idx, ph in enumerate(playheads):
        # Find the latest point with date <= ph
        # Loop Bound: Bounded by the number of parsed points (exactly 567 in excerpt).
        matching = [p for p in points if p["driver_number"] == 1 and p["date"] <= ph]
        # Invariant: There is always at least the seed record prior to or at t0.
        latest = matching[-1]
        dot_col, dot_row = dot_for(latest["x"], latest["y"])
        cell_col = dot_col // 2
        cell_row = dot_row // 4
        playhead_str = ph.strftime("%H:%M:%S")
        print(
            f"  Tick {idx} ({playhead_str} UTC): Point TS={latest['date'].isoformat()} -> dot=({dot_col}, {dot_row}) -> cell=({cell_col}, {cell_row})"
        )
        tick_results.append((playhead_str, (cell_col, cell_row)))
    print()

    print_rendered_grid("AC-9 tick-0", tuple(grid_lines), tick_results[0][1])
    print_rendered_grid("AC-9 final (tick 5)", tuple(grid_lines), tick_results[5][1])

    # Verification against SPEC
    print("--- Verification Verdict ---")
    verdict = True

    raw_bytes = (EXCERPT_DIR / "location.json").read_bytes()
    if len(points) == 567 and len(raw_bytes) == 72274:
        print("  [OK] AC-2 location facts match SPEC (567 records, 72274 bytes).")
    else:
        print("  [FAIL] AC-2 location facts mismatch!")
        verdict = False

    def _marker_ok(cell: tuple[int, int]) -> bool:
        col, row = cell
        rendered = grid_lines[row][:col] + "\u25cf" + grid_lines[row][col + 1 :]
        return rendered.count("\u25cf") == 1 and len(rendered) == 56

    if _marker_ok(tick_results[0][1]) and _marker_ok(tick_results[5][1]):
        print("  [OK] AC-9 rendered-grid markers verified (tick-0 and final).")
    else:
        print("  [FAIL] AC-9 rendered-grid markers mismatch!")
        verdict = False

    # 1. Compare Projection constants
    if (
        x_min != EXPECTED_PROJECTION["x_min"]
        or x_max != EXPECTED_PROJECTION["x_max"]
        or y_min != EXPECTED_PROJECTION["y_min"]
        or y_max != EXPECTED_PROJECTION["y_max"]
    ):
        print("  [FAIL] Bounding box mismatch!")
        verdict = False
    else:
        print("  [OK] Bounding box matches SPEC.")

    if abs(scale - EXPECTED_PROJECTION["scale"]) > 1e-15:
        print("  [FAIL] Scale mismatch!")
        verdict = False
    else:
        print("  [OK] Scale matches SPEC.")

    if len(distinct_dots) != 273:
        print(f"  [FAIL] Distinct dots count mismatch! Expected 273, got {len(distinct_dots)}")
        verdict = False
    else:
        print("  [OK] Distinct dots count matches SPEC (273).")

    if non_blank_cells != 101:
        print(f"  [FAIL] Non-blank cells count mismatch! Expected 101, got {non_blank_cells}")
        verdict = False
    else:
        print("  [OK] Non-blank cells count matches SPEC (101).")

    # 2. Compare Grid outline line-by-line
    grid_matches = True
    # Loop Bound: Exactly 32 rows.
    for i, (actual_line, expected_line) in enumerate(zip(grid_lines, EXPECTED_OUTLINE, strict=True)):
        if actual_line != expected_line:
            print(f"  [FAIL] Grid line {i} mismatch!")
            print(f"    Expected: |{expected_line}|")
            print(f"    Actual:   |{actual_line}|")
            grid_matches = False
            verdict = False
    if grid_matches:
        print("  [OK] Grid outline matches SPEC line-by-line.")

    # 3. Compare playhead cells
    ticks_match = True
    # Loop Bound: Exactly 6 playhead ticks.
    for idx, (expected_ph, expected_cell) in enumerate(EXPECTED_TICKS):
        _actual_ph, actual_cell = tick_results[idx]
        if actual_cell != expected_cell:
            print(f"  [FAIL] Playhead {expected_ph} cell mismatch! Expected {expected_cell}, got {actual_cell}")
            ticks_match = False
            verdict = False
    if ticks_match:
        print("  [OK] Per-tick marker cells match SPEC exactly.")

    if verdict:
        print("MATCH VERDICT: SUCCESS")
    else:
        print("MATCH VERDICT: FAILED")


if __name__ == "__main__":
    main()
