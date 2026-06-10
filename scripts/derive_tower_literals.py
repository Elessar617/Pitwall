#!/usr/bin/env python3
"""Derive live-timing tower literals from the committed excerpt — STDLIB-ONLY.

Independent of src/pitwall by construction (review-08-1 finding 8): raw JSON +
datetime reimplementation of the load/merge/tick/fold rules, so the printed
literals verify the production code rather than echo it.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXCERPT_DIR = REPO_ROOT / "tests/fixtures/openf1/1285_11291_excerpt"

# Tick parameters pinned by SPEC AC-6.
SPEED = 60.0
TICK_INTERVAL_S = 0.5

# INVARIANT: Pinned SPEC AC-7 rows as target for verification.
# Each tuple represents: (Pos, Drv, Int, Gap, Last, Tyre)
EXPECTED_AC7 = [
    ("1", "RUS", "—", "—", "1:16.545", "S"),
    ("2", "ANT", "+0.506", "+0.506", "1:16.531", "S"),
    ("3", "VER", "+5.048", "+5.491", "1:16.088", "S"),
    ("4", "HAM", "+0.826", "+6.317", "1:16.068", "S"),
    ("5", "LEC", "+6.480", "+12.792", "1:16.553", "S"),
    ("6", "HAD", "+0.645", "+13.437", "1:16.499", "S"),
    ("7", "COL", "—", "+32.599", "1:17.292", "M"),
    ("8", "LAW", "+4.920", "+37.318", "1:17.801", "M"),
    ("9", "GAS", "+8.545", "+45.310", "1:17.569", "M"),
    ("10", "BEA", "+1.860", "+47.152", "1:18.120", "S"),
    ("11", "SAI", "+12.608", "+59.528", "1:17.544", "M"),
    ("12", "ALO", "+2.315", "+61.828", "1:20.409", "S"),
    ("13", "OCO", "+0.409", "+62.237", "1:38.391", "M"),
    ("14", "NOR", "+2.521", "+64.706", "1:23.114", "M"),
    ("15", "HUL", "+0.364", "+65.070", "1:19.039", "S"),
    ("16", "BOR", "+5.412", "+70.038", "1:17.752", "S"),
    ("17", "PIA", "+13.730", "+1 LAP", "1:17.308", "M"),
    ("18", "PER", "+12.148", "+1 LAP", "1:24.198", "M"),
    ("19", "STR", "+7.365", "+1 LAP", "1:22.036", "S"),
    ("20", "BOT", "+28.684", "+1 LAP", "1:19.225", "M"),
    ("21", "ALB", "—", "—", "—", "S"),
    ("22", "LIN", "—", "—", "—", "M"),
]


def format_interval(val: float | str | None) -> str:
    """Format interval/gap value per AC-8 rules.

    Units: Seconds (if float).
    Range: Positive values or special strings like "+1 LAP".
    """
    if val is None:
        return "—"
    if isinstance(val, (int, float)):
        # INVARIANT: Gaps of exactly 0.0 (the leader) are formatted as em-dash.
        if float(val) == 0.0:
            return "—"
        return f"+{val:.3f}"
    return str(val)


def format_lap_time(val: float | None) -> str:
    """Format lap time in minutes and seconds per AC-8 rules.

    Units: Seconds.
    Range: Positive float representing lap duration.
    """
    if val is None:
        return "—"
    # FAILURE MODE: Large values >= 60.0 are split into MM:SS.sss format.
    if val >= 60.0:
        m = int(val // 60)
        s = val % 60
        # INVARIANT: Seconds are zero-padded to 6 characters including decimal point.
        return f"{m}:{s:06.3f}"
    return f"{val:.3f}"


def tyre_for(driver_number: int, current_lap: int | None, stints: list[dict]) -> str:
    """Select the correct tyre compound letter for a driver per D4 rules.

    Assumptions: The stints list is the complete stint history of the session.
    Loop Bound: Bounded by the number of stints for the given driver (at most 10).
    """
    if current_lap is None:
        return "—"

    driver_stints = [s for s in stints if s.get("driver_number") == driver_number]
    if not driver_stints:
        return "—"

    # Rule 1: Find the stint where lap_start <= current_lap <= lap_end.
    matching_stints = [s for s in driver_stints if s["lap_start"] <= current_lap <= s["lap_end"]]
    if matching_stints:
        # In case of tie, take the one with the greatest lap_start (latest).
        best_stint = max(matching_stints, key=lambda s: s["lap_start"])
    else:
        # Rule-2: Fall back to the stint with the greatest lap_start <= current_lap.
        older_stints = [s for s in driver_stints if s["lap_start"] <= current_lap]
        if older_stints:
            best_stint = max(older_stints, key=lambda s: s["lap_start"])
        else:
            return "—"

    if not best_stint.get("compound"):
        return "—"
    return best_stint["compound"][0].upper()


def compute_ticks(events: list[tuple], t0: datetime) -> list[tuple[int, str, int]]:
    """Pure tick reimplementation: span = SPEED * TICK_INTERVAL_S seconds.

    Tick 0 is the catch-up tick (ts <= t0); tick k covers (t0+(k-1)*span, t0+k*span];
    ticks continue (empty spans included) until every event is consumed.
    """
    span = timedelta(seconds=SPEED * TICK_INTERVAL_S)
    records = []
    consumed = sum(1 for ts, _, _ in events if ts <= t0)
    records.append((0, t0.strftime("%H:%M:%S"), consumed))
    k = 0
    # Loop bound: ceil((last_ts - t0) / span) ticks for a finite event list.
    while consumed < len(events):
        k += 1
        lo, hi = t0 + (k - 1) * span, t0 + k * span
        n = sum(1 for ts, _, _ in events if lo < ts <= hi)
        consumed += n
        records.append((k, hi.strftime("%H:%M:%S"), n))
    return records


def print_event_counts(events: list[tuple]) -> None:
    """Computes and prints AC-5 Event Count Table.

    Loop Bound: Bounded by the number of merged events (exactly 381 in excerpt).
    """
    counts_by_kind: dict[str, int] = {}
    for _ts, kind, _payload in events:
        counts_by_kind[kind] = counts_by_kind.get(kind, 0) + 1

    print("--- AC-5 Event Count Table ---")
    print(f"Total Events: {len(events)}")
    for kind in sorted(counts_by_kind.keys()):
        print(f"  {kind}: {counts_by_kind[kind]}")
    print()


def print_tick_table(events: list[tuple], start_at: datetime) -> None:
    """Runs replay ticks and prints AC-6 Tick Table.

    Assumptions: Speed is 60x and tick interval is 0.5s.
    """
    tick_records = compute_ticks(events, start_at)
    print("--- AC-6 Tick Table ---")
    print(f"Total Ticks: {len(tick_records)}")
    for idx, playhead, count in tick_records:
        print(f"  Tick {idx}: Playhead={playhead} UTC, Events={count}")
    print()


def fold_events(events: list[tuple]) -> tuple[dict, dict, dict, dict]:
    """Fold events to get end-state mapping of drivers timing attributes.

    Loop Bound: Bounded by total merged events (exactly 381 in excerpt).
    """
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


def build_and_sort_rows(
    drivers: list[dict],
    stints: list[dict],
    positions: dict,
    intervals: dict,
    last_laps: dict,
    current_laps: dict,
) -> list[tuple[str, ...]]:
    """Build and format rows sorted by (position is None, position, driver_number).

    Loop Bound: Bounded by the number of drivers (exactly 22 in F1 session).
    """
    rows = []
    for driver in drivers:
        drv_num = driver["driver_number"]
        pos_val = positions.get(drv_num)
        int_val, gap_val = intervals.get(drv_num, (None, None))
        last_val = last_laps.get(drv_num)
        current_lap = current_laps.get(drv_num)

        tyre = tyre_for(drv_num, current_lap, stints)

        pos_str = str(pos_val) if pos_val is not None else "—"
        drv_str = driver["name_acronym"]
        int_str = format_interval(int_val)
        gap_str = format_interval(gap_val)
        last_str = format_lap_time(last_val)

        rows.append((pos_val, drv_num, (pos_str, drv_str, int_str, gap_str, last_str, tyre)))

    # Sort rows by: (position is None, position, driver_number)
    # INVARIANT: Python's sort is stable; false sorts before true.
    rows.sort(key=lambda x: (x[0] is None, x[0], x[1]))
    return [x[2] for x in rows]


def verify_rows(final_rows: list[tuple[str, ...]]) -> None:
    """Print timing tower rows and check verification against SPEC AC-7.

    Loop Bound: Bounded by 22 target rows.
    """
    print("--- AC-7 Timing Tower Rows ---")
    for r in final_rows:
        print(f"  {r}")
    print()

    match = True
    for i, (actual, expected) in enumerate(zip(final_rows, EXPECTED_AC7, strict=True)):
        if actual != expected:
            print(f"Mismatch at index {i}: expected {expected}, got {actual}")
            match = False

    print("--- Verdict ---")
    if match and len(final_rows) == len(EXPECTED_AC7):
        print("MATCH VERDICT: SUCCESS (Printed rows EXACTLY match the SPEC AC-7 table)")
    else:
        print("MATCH VERDICT: FAILED (Printed rows do NOT match the SPEC AC-7 table)")


def _parse_ts(value: str) -> datetime:
    """ISO-8601; naive timestamps are UTC by capture convention."""
    dt = datetime.fromisoformat(value)
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def _load(name: str) -> list | dict:
    return json.loads((EXCERPT_DIR / f"{name}.json").read_text(encoding="utf-8"))


def merge_raw_events() -> list[tuple]:
    """Stdlib merge mirroring the pinned rules: ts, kind-priority, driver, seq."""
    keyed: list[tuple] = []

    def add(records: list[dict], kind_idx: int, kind: str, ts_field: str) -> None:
        # Loop bound: len(records) per stream (excerpt-scale).
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


def print_file_counts() -> None:
    """D2 section: per-file record counts of the committed excerpt."""
    print("--- Excerpt Per-File Record Counts ---")
    # Loop bound: 7 stream files + manifest.
    for name in ["drivers", "stints", "laps", "position", "intervals", "pit", "race_control"]:
        print(f"  {name}.json: {len(_load(name))}")
    print("  manifest.json: dict")
    print()


def print_tick0_rows(events: list[tuple], t0: datetime) -> None:
    """D2 section: tick-0 seeded tower rows (AC-9 literals — seeds only)."""
    tick0 = [e for e in events if e[0] <= t0]
    positions, intervals, last_laps, current_laps = fold_events(tick0)
    rows = build_and_sort_rows(_load("drivers"), _load("stints"), positions, intervals, last_laps, current_laps)
    print("--- AC-9 Tick-0 Seeded Rows ---")
    for r in rows:
        print(f"  {r}")
    print()


def main() -> None:
    """Load raw excerpt, merge, fold, format, verify, print — no pitwall imports."""
    events = merge_raw_events()
    manifest = _load("manifest")
    t0 = _parse_ts(manifest["replay_window"]["start"])

    print_file_counts()
    print_event_counts(events)
    print_tick_table(events, t0)
    print_tick0_rows(events, t0)

    positions, intervals, last_laps, current_laps = fold_events(events)

    final_rows = build_and_sort_rows(
        _load("drivers"),
        _load("stints"),
        positions,
        intervals,
        last_laps,
        current_laps,
    )

    verify_rows(final_rows)


if __name__ == "__main__":
    main()
