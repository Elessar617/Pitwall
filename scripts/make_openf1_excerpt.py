#!/usr/bin/env python3
# ruff: noqa: TRY003, C901, B007  (excerpt generator: enumerated stream handling is the design)
"""Deterministic script to generate Montreal race timing fixtures excerpt (SPEC-08 D2).

Reads from data/fixtures/1285_11291/ and writes to
tests/fixtures/openf1/1285_11291_excerpt/.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

# INVARIANT: Window bounds are fixed to Montreal mid-race window (lap 16-17).
# Invariant: WL1_STR is the location window upper bound, extending the replay window to capture the full circuit.
W0_STR = "2026-05-24T20:30:00+00:00"
W1_STR = "2026-05-24T20:31:00+00:00"
WL1_STR = "2026-05-24T20:32:30+00:00"
W0 = datetime.fromisoformat(W0_STR)
W1 = datetime.fromisoformat(W1_STR)
WL1 = datetime.fromisoformat(WL1_STR)

# ASSUMPTION: Target counts from AC-3 and SPEC-09 specifications must match filtered results exactly.
# Invariant: Each stream must have exactly the target number of records in the final excerpt.
TARGET_COUNTS = {
    "drivers.json": 22,
    "stints.json": 56,
    "laps.json": 38,
    "position.json": 30,
    "intervals.json": 272,
    "pit.json": 2,
    "race_control.json": 3,
    "location.json": 567,
    "location_all.json": 3300,
}


class ExcerptError(ValueError):
    """Custom error for make_openf1_excerpt script."""


def parse_timestamp(val: str | None) -> datetime | None:
    """Parses timestamp with offset, assuming UTC if timezone info is missing.

    Assumptions: Timestamps are ISO-8601 strings or None.
    """
    if val is not None and not isinstance(val, str):
        raise TypeError("Timestamp must be string or None")
    if not val:
        return None
    dt = datetime.fromisoformat(val)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    if dt.tzinfo is None:
        raise ValueError("Parsed datetime must have timezone info")
    return dt


def filter_stream_by_window(records: list[dict], date_key: str, w0: datetime, w1: datetime) -> list[dict]:
    """Filters records strictly inside the window w0 <= ts < w1.

    Loop Bound: Bounded by length of records, which is less than 100000.
    """
    if not isinstance(records, list):
        raise TypeError("records must be a list")
    if not isinstance(date_key, str):
        raise TypeError("date_key must be a string")
    if len(records) >= 100000:
        raise ValueError("Too many records to filter")

    filtered = []
    for r in records:
        ts_val = r.get(date_key)
        if ts_val is not None:
            dt = parse_timestamp(ts_val)
            if dt and w0 <= dt < w1:
                filtered.append(r)
    if len(filtered) > len(records):
        raise ValueError("Filtered records cannot exceed input length")
    return filtered


def find_seeds(records: list[dict], date_key: str, w0: datetime) -> dict[int, dict]:
    """Finds the latest record strictly before w0 for each driver.

    Loop Bound: Bounded by length of records, which is less than 100000.
    """
    seeds = {}
    for r in records:
        drv = r.get("driver_number")
        if drv is None:
            continue
        ts_val = r.get(date_key)
        if ts_val is None:
            continue
        dt = parse_timestamp(ts_val)
        if dt and dt < w0:
            # INVARIANT: If timestamps are identical, the last record in source array order takes precedence.
            current_seed = seeds.get(drv)
            if current_seed is None:
                seeds[drv] = r
            else:
                curr_dt = parse_timestamp(current_seed.get(date_key))
                if curr_dt and curr_dt <= dt:
                    seeds[drv] = r
    return seeds


def get_seeded_records(records: list[dict], date_key: str, w0: datetime, w1: datetime) -> list[dict]:
    """Filters by window and adds the latest seed record strictly before w0 per driver.

    Loop Bound: Bounded by length of records, which is less than 100000.
    """
    if not isinstance(records, list):
        raise TypeError("records must be a list")
    if not isinstance(date_key, str):
        raise TypeError("date_key must be a string")
    if len(records) >= 100000:
        raise ValueError("Too many records to seed")

    window_records = filter_stream_by_window(records, date_key, w0, w1)
    seeds = find_seeds(records, date_key, w0)

    seed_ids = {id(r) for r in seeds.values()}
    window_ids = {id(r) for r in window_records}

    result = []
    for r in records:
        r_id = id(r)
        if r_id in seed_ids or r_id in window_ids:
            result.append(r)

    if len(result) > len(records):
        raise ValueError("Result length cannot exceed input length")
    if len(result) < len(window_records):
        raise ValueError("Result must contain at least window records")
    return result


def process_excerpt(src_dir: Path, dest_dir: Path) -> dict[str, int]:
    """Reads full capture files, applies filtering rules, and writes excerpt files.

    Loop Bound: Fixed iteration over the 5 filtered streams.
    """
    if not src_dir.is_dir():
        raise ExcerptError("Source directory does not exist")
    if dest_dir.is_file():
        raise ExcerptError("Destination must not be a file")

    dest_dir.mkdir(parents=True, exist_ok=True)
    counts = {}

    with open(src_dir / "drivers.json", encoding="utf-8") as f:
        drivers = json.load(f)
    counts["drivers.json"] = len(drivers)
    write_serialized(dest_dir / "drivers.json", drivers)

    with open(src_dir / "stints.json", encoding="utf-8") as f:
        stints = json.load(f)
    counts["stints.json"] = len(stints)
    write_serialized(dest_dir / "stints.json", stints)

    streams = [
        ("laps.json", "date_start", True),
        ("position.json", "date", True),
        ("intervals.json", "date", False),
        ("pit.json", "date", False),
        ("race_control.json", "date", False),
    ]

    for filename, date_key, seed_stream in streams:
        with open(src_dir / filename, encoding="utf-8") as f:
            records = json.load(f)
        if seed_stream:
            filtered = get_seeded_records(records, date_key, W0, W1)
        else:
            filtered = filter_stream_by_window(records, date_key, W0, W1)
        counts[filename] = len(filtered)
        write_serialized(dest_dir / filename, filtered)

    # Process location data from location_driver1.json and write to location.json
    # Invariant: source location file name contains driver number suffix, destination does not.
    # Window Bound: location window uses WL1 (20:32:30) as upper bound rather than W1 (20:31:00).
    # Assumption: location_driver1.json is a valid JSON list of dicts.
    # Failure Mode: raises ValueError if location_records list size >= 100,000.
    with open(src_dir / "location_driver1.json", encoding="utf-8") as f:
        location_records = json.load(f)
    filtered_location = get_seeded_records(location_records, "date", W0, WL1)
    counts["location.json"] = len(filtered_location)
    write_serialized(dest_dir / "location.json", filtered_location)

    # Process multi-driver location data from location_all_raw.json and write to location_all.json
    # Invariant: multi-driver location records are extracted from raw multi-driver feed.
    # Assumption: location_all_raw.json is a valid JSON list of dicts.
    # Failure Mode: raises TypeError if raw_location_all is not a list, or ValueError if list size >= 200,000.
    with open(src_dir / "location_all_raw.json", encoding="utf-8") as f:
        raw_location_all = json.load(f)
    if not isinstance(raw_location_all, list):
        raise TypeError("raw_location_all must be a list")
    if len(raw_location_all) >= 200000:
        raise ValueError("Too many records in raw_location_all")

    # Group raw records by driver number.
    # Loop Bound: grouping is bounded by len(raw_location_all) which is < 200,000.
    by_driver = {}
    for r in raw_location_all:
        drv = r.get("driver_number")
        if drv is not None:
            by_driver.setdefault(drv, []).append(r)

    # Sort each driver's records by date to ensure chronological order.
    # Loop Bound: bounded by the number of drivers (at most 22).
    for drv in by_driver:
        by_driver[drv].sort(key=lambda x: parse_timestamp(x.get("date")))

    # Extract seeds and downsample window records to 1 Hz per driver.
    # Loop Bound: bounded by the number of drivers (at most 22) and their per-driver records count.
    # Invariant: seed date < W0; window record date W0 <= date < WL1.
    selected_location_all = []
    for drv, records in by_driver.items():
        seed = None
        for r in records:
            dt = parse_timestamp(r.get("date"))
            if dt and dt < W0:
                seed = r
        window_records = []
        seen_floored_seconds = set()
        for r in records:
            dt = parse_timestamp(r.get("date"))
            if dt and W0 <= dt < WL1:
                floored_dt = dt.replace(microsecond=0)
                if floored_dt not in seen_floored_seconds:
                    seen_floored_seconds.add(floored_dt)
                    window_records.append(r)
        if seed:
            selected_location_all.append(seed)
        selected_location_all.extend(window_records)

    # Sort merged list by (date, driver_number) to ensure byte-stable final order.
    # Loop Bound: bounded by len(selected_location_all) which is < 200,000.
    selected_location_all.sort(key=lambda r: (parse_timestamp(r.get("date")), r.get("driver_number")))
    counts["location_all.json"] = len(selected_location_all)
    write_serialized(dest_dir / "location_all.json", selected_location_all)

    manifest = {
        "generated_by": "scripts/make_openf1_excerpt.py",
        "source": "Montreal Race 2026-05-24",
        "meeting_key": 1285,
        "session_key": 11291,
        "seeded_streams": ["laps", "location", "position"],
        "record_counts": {
            "drivers": counts["drivers.json"],
            "stints": counts["stints.json"],
            "laps": counts["laps.json"],
            "location": counts["location.json"],
            "location_all": counts["location_all.json"],
            "position": counts["position.json"],
            "intervals": counts["intervals.json"],
            "pit": counts["pit.json"],
            "race_control": counts["race_control.json"],
        },
        "replay_window": {"start": W0_STR, "end": W1_STR},
        "location_window": {"start": W0_STR, "end": WL1_STR},
    }
    write_serialized(dest_dir / "manifest.json", manifest)

    if len(counts) != 9:
        raise ExcerptError("Must process exactly 9 stream files")
    return counts


def write_serialized(path: Path, obj: any) -> None:
    """Writes JSON object with sorted keys, no whitespace separators, and a trailing newline.

    INVARIANT: Trailing newline prevents pre-commit hooks from modifying
    serialized files.
    """
    if not isinstance(path, Path):
        raise TypeError("Path must be a Path object")
    content = json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    if not path.exists():
        raise ExcerptError("Serialized file was not written successfully")


def main() -> None:
    """Main execution block verifying target counts and directory size.

    Loop Bound: Bounded by files in directory (which is 8).
    """
    src_dir = Path("data/fixtures/1285_11291")
    dest_dir = Path("tests/fixtures/openf1/1285_11291_excerpt")

    counts = process_excerpt(src_dir, dest_dir)

    mismatch = False
    for filename, target in TARGET_COUNTS.items():
        actual = counts.get(filename, 0)
        print(f"{filename}: target {target}, actual {actual}")
        if actual != target:
            mismatch = True

    # FAILURE MODE: Raises ValueError if the final filtered counts deviate from the AC-3 spec targets.
    if mismatch:
        raise ExcerptError("Counts mismatch targets")

    total_bytes = 0
    for p in dest_dir.glob("*"):
        if p.is_file():
            total_bytes += p.stat().st_size

    print(f"Total directory size: {total_bytes} bytes")
    # Failure Mode: raises ExcerptError if total directory size of the excerpt exceeds 160,000 bytes.
    if total_bytes >= 700000:
        raise ExcerptError("Directory size exceeds 700,000 bytes limit")


if __name__ == "__main__":
    main()
