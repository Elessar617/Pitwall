#!/usr/bin/env python3
# ruff: noqa: C901  (verification script: enumerated checks + asserts are the design)
"""Derive live timing literals from the committed excerpt — STDLIB-ONLY."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXCERPT_DIR = REPO_ROOT / "tests/fixtures/openf1/1285_11291_excerpt"


def _parse_ts(value: str) -> datetime:
    """Parse ISO-8601 string to UTC datetime."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def main() -> None:
    # 1. Load data files
    files = {
        "position": "position.json",
        "intervals": "intervals.json",
        "laps": "laps.json",
        "pit": "pit.json",
        "race_control": "race_control.json",
        "location": "location.json",
    }

    data = {}
    for key, filename in files.items():
        filepath = EXCERPT_DIR / filename
        with open(filepath, encoding="utf-8") as f:
            data[key] = json.load(f)

    # 2. Derive max timestamps
    max_position = max(_parse_ts(r["date"]) for r in data["position"])
    max_intervals = max(_parse_ts(r["date"]) for r in data["intervals"])
    max_laps = max(_parse_ts(r["date_start"]) for r in data["laps"] if r.get("date_start"))
    max_pit = max(_parse_ts(r["date"]) for r in data["pit"])
    max_race_control = max(_parse_ts(r["date"]) for r in data["race_control"])

    loc_dates = [_parse_ts(r["date"]) for r in data["location"]]
    max_location = max(loc_dates)

    # 3. Compute cursor values
    cursor_pos = (max_position - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S")
    cursor_intervals = (max_intervals - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S")
    cursor_laps = (max_laps - timedelta(seconds=241)).strftime("%Y-%m-%dT%H:%M:%S")
    cursor_pit = (max_pit - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S")
    cursor_race_control = (max_race_control - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S")
    cursor_location = (max_location - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S")

    # 4. Compute location stats
    loc_span = (max(loc_dates) - min(loc_dates)).total_seconds()
    loc_count = len(loc_dates)
    loc_ready = loc_span >= 150.0 and loc_count >= 500

    # 5. Build URL sequences
    sessions_url = "https://api.openf1.org/v1/sessions?session_key=latest"

    backfill_urls = [
        "https://api.openf1.org/v1/drivers?session_key=11291",
        "https://api.openf1.org/v1/stints?session_key=11291",
        "https://api.openf1.org/v1/position?session_key=11291",
        "https://api.openf1.org/v1/intervals?session_key=11291",
        "https://api.openf1.org/v1/laps?session_key=11291",
        "https://api.openf1.org/v1/pit?session_key=11291",
        "https://api.openf1.org/v1/race_control?session_key=11291",
        "https://api.openf1.org/v1/location?session_key=11291&date%3E2026-05-24T20:28:00",
    ]

    steady_urls = [
        f"https://api.openf1.org/v1/position?session_key=11291&date%3E{cursor_pos}",
        f"https://api.openf1.org/v1/intervals?session_key=11291&date%3E{cursor_intervals}",
        f"https://api.openf1.org/v1/laps?session_key=11291&date%3E{cursor_laps}",
        f"https://api.openf1.org/v1/pit?session_key=11291&date%3E{cursor_pit}",
        f"https://api.openf1.org/v1/race_control?session_key=11291&date%3E{cursor_race_control}",
        f"https://api.openf1.org/v1/location?session_key=11291&date%3E{cursor_location}",
    ]

    total_sequence = [sessions_url, *backfill_urls, *steady_urls]

    # 6. Verify against expected values
    verdict = True

    # Expected values
    expected_pos = "2026-05-24T20:30:34"
    expected_intervals = "2026-05-24T20:30:58"
    expected_laps = "2026-05-24T20:26:52"
    expected_pit = "2026-05-24T20:30:46"
    expected_race_control = "2026-05-24T20:30:45"
    expected_location = "2026-05-24T20:32:28"

    expected_data_head = "2026-05-24T20:32:29.886000+00:00"
    expected_data_head_formatted = "20:32:29"

    print("--- Derived Cursors ---")
    print(f"  position:     {cursor_pos} (expected: {expected_pos})")
    print(f"  intervals:    {cursor_intervals} (expected: {expected_intervals})")
    print(f"  laps:         {cursor_laps} (expected: {expected_laps})")
    print(f"  pit:          {cursor_pit} (expected: {expected_pit})")
    print(f"  race_control: {cursor_race_control} (expected: {expected_race_control})")
    print(f"  location:     {cursor_location} (expected: {expected_location})")
    print()

    if cursor_pos != expected_pos:
        verdict = False
    if cursor_intervals != expected_intervals:
        verdict = False
    if cursor_laps != expected_laps:
        verdict = False
    if cursor_pit != expected_pit:
        verdict = False
    if cursor_race_control != expected_race_control:
        verdict = False
    if cursor_location != expected_location:
        verdict = False

    print("--- Data Head ---")
    data_head_str = max_location.isoformat()
    formatted_data_head = max_location.strftime("%H:%M:%S")
    print(f"  data_head:           {data_head_str} (expected: {expected_data_head})")
    print(f"  data_head formatted: {formatted_data_head} (expected: {expected_data_head_formatted})")
    print()

    if data_head_str != expected_data_head:
        verdict = False
    if formatted_data_head != expected_data_head_formatted:
        verdict = False

    print("--- Location Facts ---")
    print(f"  span:  {loc_span:.2f} s (expected: 150.14 s)")
    print(f"  count: {loc_count} (expected: 567)")
    print(f"  ready: {loc_ready} (expected: True)")
    print()

    if abs(loc_span - 150.14) > 0.01:
        verdict = False
    if loc_count != 567:
        verdict = False
    if loc_ready is not True:
        verdict = False

    print("--- URL Sequence ---")
    for idx, url in enumerate(total_sequence):
        print(f"  {idx + 1:02d}: {url}")
    print()

    expected_sequence = [
        "https://api.openf1.org/v1/sessions?session_key=latest",
        "https://api.openf1.org/v1/drivers?session_key=11291",
        "https://api.openf1.org/v1/stints?session_key=11291",
        "https://api.openf1.org/v1/position?session_key=11291",
        "https://api.openf1.org/v1/intervals?session_key=11291",
        "https://api.openf1.org/v1/laps?session_key=11291",
        "https://api.openf1.org/v1/pit?session_key=11291",
        "https://api.openf1.org/v1/race_control?session_key=11291",
        "https://api.openf1.org/v1/location?session_key=11291&date%3E2026-05-24T20:28:00",
        "https://api.openf1.org/v1/position?session_key=11291&date%3E2026-05-24T20:30:34",
        "https://api.openf1.org/v1/intervals?session_key=11291&date%3E2026-05-24T20:30:58",
        "https://api.openf1.org/v1/laps?session_key=11291&date%3E2026-05-24T20:26:52",
        "https://api.openf1.org/v1/pit?session_key=11291&date%3E2026-05-24T20:30:46",
        "https://api.openf1.org/v1/race_control?session_key=11291&date%3E2026-05-24T20:30:45",
        "https://api.openf1.org/v1/location?session_key=11291&date%3E2026-05-24T20:32:28",
    ]

    if total_sequence != expected_sequence:
        print("  [FAIL] URL sequence mismatch!")
        verdict = False
    else:
        print("  [OK] URL sequence matches expected sequence.")

    if verdict:
        print("MATCH VERDICT: SUCCESS")
    else:
        print("MATCH VERDICT: FAILED")


if __name__ == "__main__":
    main()
