#!/usr/bin/env python3
# ruff: noqa: C901  (operator capture script: end-to-end flow in one function is intentional)
"""OpenF1 Session Capture Script.

Downloads stream endpoints and multi-driver location chunks.
"""

import argparse
import datetime
import json
import os
import sys
import time
import urllib.parse
import urllib.request

MAX_DRIVERS_CAP = 40
MAX_WINDOWS_CAP = 200


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Capture OpenF1 session data.")
    parser.add_argument("meeting_key", type=int, help="Meeting key")
    parser.add_argument("session_key", type=int, help="Session key")
    parser.add_argument("--plan-only", action="store_true", help="Print plan URLs and exit")
    parser.add_argument("--date-start", type=str, default=None, help="Start time override")
    parser.add_argument("--date-end", type=str, default=None, help="End time override")
    parser.add_argument("--drivers", type=str, default=None, help="Comma-separated driver numbers")
    return parser.parse_args()


def print_plan(session_key: int, date_start: str, date_end: str, drivers_str: str) -> None:
    """Print the planned URLs for plan-only mode."""
    streams = ["drivers", "laps", "position", "intervals", "stints", "pit", "race_control"]
    for stream in streams:
        print(f"https://api.openf1.org/v1/{stream}?session_key={session_key}")

    drivers = [int(d.strip()) for d in drivers_str.split(",") if d.strip()]
    start_dt = datetime.datetime.fromisoformat(date_start.replace("Z", "+00:00"))
    end_dt = datetime.datetime.fromisoformat(date_end.replace("Z", "+00:00"))

    for drv in drivers:
        current_dt = start_dt
        window_count = 0
        while current_dt < end_dt and window_count < MAX_WINDOWS_CAP:
            window_count += 1
            next_dt = min(current_dt + datetime.timedelta(minutes=10), end_dt)
            start_s = current_dt.strftime("%Y-%m-%dT%H:%M:%S")
            end_s = next_dt.strftime("%Y-%m-%dT%H:%M:%S")
            url = (
                f"https://api.openf1.org/v1/location?session_key={session_key}"
                f"&driver_number={drv}&date%3E{start_s}&date%3C{end_s}"
            )
            print(url)
            current_dt = next_dt


def make_request(url: str, retry: bool = True) -> tuple[int, str]:
    """Execute HTTP request with 1.0s sleep and retry once."""
    time.sleep(1.0)
    headers = {"User-Agent": "pitwall-capture/1.0"}
    if not url.startswith("https://"):
        raise ValueError("refusing non-https URL")  # noqa: TRY003
    req = urllib.request.Request(url, headers=headers)  # noqa: S310 - https enforced above
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 - scheme validated above
            return resp.status, resp.read().decode("utf-8")
    except Exception as e:
        if retry:
            time.sleep(1.0)
            return make_request(url, retry=False)
        sys.stderr.write(f"request failed after retry: {url}: {e}\n")
        return 0, str(e)


def fetch_stream_data(session_key: int, endpoint: str, fixtures_dir: str) -> list[dict]:
    """Fetch data for a stream endpoint and write to a file."""
    url = f"https://api.openf1.org/v1/{endpoint}?session_key={session_key}"
    status, body = make_request(url)
    if status != 200:
        sys.stderr.write(f"capture FAILED for {endpoint}: HTTP {status} — no fixture written\n")
        return []
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"capture FAILED for {endpoint}: non-JSON body ({exc}) — no fixture written\n")
        return []
    filepath = os.path.join(fixtures_dir, f"{endpoint}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


def fetch_locations(
    session_key: int, drv: int, start_dt: datetime.datetime, end_dt: datetime.datetime
) -> tuple[list[dict], bool]:
    """Fetch a driver's locations in 10-minute windows. Returns (points, any_window_failed)."""
    locs = []
    any_failed = False
    current_dt = start_dt
    window_count = 0
    while current_dt < end_dt and window_count < MAX_WINDOWS_CAP:
        window_count += 1
        next_dt = min(current_dt + datetime.timedelta(minutes=10), end_dt)
        start_s = current_dt.strftime("%Y-%m-%dT%H:%M:%S")
        end_s = next_dt.strftime("%Y-%m-%dT%H:%M:%S")
        url = (
            f"https://api.openf1.org/v1/location?session_key={session_key}"
            f"&driver_number={drv}&date%3E{start_s}&date%3C{end_s}"
        )
        status, body = make_request(url)
        if status == 200:
            try:
                chunk = json.loads(body)
            except json.JSONDecodeError as exc:
                sys.stderr.write(f"location window parse FAILED ({exc}) — window skipped\n")
                chunk = None
                any_failed = True
            if isinstance(chunk, list):
                locs.extend(chunk)
        elif status != 404:
            sys.stderr.write(f"location window FAILED: HTTP {status} — window skipped\n")
            any_failed = True
        current_dt = next_dt
    return locs, any_failed


def run_network_capture(meeting_key: int, session_key: int, date_start: str | None, date_end: str | None) -> None:
    """Execute actual network capture process."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, ".."))
    fixtures_dir = os.path.join(repo_root, "data", "fixtures", f"{meeting_key}_{session_key}")
    os.makedirs(fixtures_dir, exist_ok=True)

    # Fetch 7 primary streams
    streams = ["drivers", "laps", "position", "intervals", "stints", "pit", "race_control"]
    drivers_data = []
    streams_written = 0
    for stream in streams:
        data = fetch_stream_data(session_key, stream, fixtures_dir)
        if data:
            streams_written += 1
        if stream == "drivers":
            drivers_data = data
    if streams_written == 0:
        sys.stderr.write("Capture ABORTED: every primary stream failed — no manifest written.\n")
        sys.exit(1)

    # Extract driver list
    drv_nums = sorted({int(d["driver_number"]) for d in drivers_data if "driver_number" in d})
    drv_nums = drv_nums[:MAX_DRIVERS_CAP]

    # Resolve date bounds
    if not date_start or not date_end:
        url = f"https://api.openf1.org/v1/sessions?session_key={session_key}"
        status, body = make_request(url)
        if status == 200:
            try:
                s_data = json.loads(body)
                if s_data:
                    date_start = s_data[0].get("date_start")
                    date_end = s_data[0].get("date_end")
            except json.JSONDecodeError as exc:
                sys.stderr.write(f"session lookup parse FAILED: {exc}\n")
    if not date_start or not date_end:
        sys.stderr.write("Error: Could not resolve session start/end times.\n")
        sys.exit(1)

    start_dt = datetime.datetime.fromisoformat(date_start.replace("Z", "+00:00"))
    end_dt = datetime.datetime.fromisoformat(date_end.replace("Z", "+00:00"))

    # Fetch location data for all drivers
    all_locations = []
    location_failed = False
    for drv in drv_nums:
        drv_locs, drv_failed = fetch_locations(session_key, drv, start_dt, end_dt)
        all_locations.extend(drv_locs)
        location_failed = location_failed or drv_failed

    # A total location failure (every window errored, nothing collected) must NOT
    # masquerade as a genuinely-empty session — abort before writing fixtures.
    if location_failed and not all_locations:
        sys.stderr.write("Capture ABORTED: every location window failed — no location.json or manifest written.\n")
        sys.exit(1)

    # Sort locations chronologically
    all_locations.sort(key=lambda p: (p.get("date", ""), p.get("driver_number", 0)))

    # Save locations
    loc_path = os.path.join(fixtures_dir, "location.json")
    with open(loc_path, "w", encoding="utf-8") as f:
        json.dump(all_locations, f, indent=2)

    # Write simple manifest
    manifest = {
        "meeting_key": meeting_key,
        "session_key": session_key,
        "captured_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "driver_count": len(drv_nums),
        "location_records": len(all_locations),
    }
    manifest_path = os.path.join(fixtures_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def main() -> None:
    """Main script runner."""
    args = parse_args()

    if args.plan_only:
        if not args.date_start or not args.date_end or not args.drivers:
            sys.stderr.write("Usage error: --plan-only requires overrides.\n")
            sys.exit(2)
        print_plan(args.session_key, args.date_start, args.date_end, args.drivers)
        sys.exit(0)

    run_network_capture(args.meeting_key, args.session_key, args.date_start, args.date_end)


if __name__ == "__main__":
    main()
