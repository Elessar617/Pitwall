import subprocess
import sys
from pathlib import Path


def test_plan_only_output():
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "capture_openf1_session.py"

    cmd = [
        sys.executable,
        str(script_path),
        "1285",
        "11291",
        "--plan-only",
        "--date-start",
        "2026-05-24T19:00:00",
        "--date-end",
        "2026-05-24T21:00:00",
        "--drivers",
        "1,4",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
    assert result.returncode == 0

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    # Prints exactly 31 URL lines:
    # 7 stream URLs then 24 location URLs
    assert len(lines) == 31

    # 7 stream URLs
    expected_streams = [
        "https://api.openf1.org/v1/drivers?session_key=11291",
        "https://api.openf1.org/v1/laps?session_key=11291",
        "https://api.openf1.org/v1/position?session_key=11291",
        "https://api.openf1.org/v1/intervals?session_key=11291",
        "https://api.openf1.org/v1/stints?session_key=11291",
        "https://api.openf1.org/v1/pit?session_key=11291",
        "https://api.openf1.org/v1/race_control?session_key=11291",
    ]
    assert lines[:7] == expected_streams

    # first location line exactly:
    first_loc = "https://api.openf1.org/v1/location?session_key=11291&driver_number=1&date%3E2026-05-24T19:00:00&date%3C2026-05-24T19:10:00"
    assert lines[7] == first_loc

    # last location line exactly:
    last_loc = "https://api.openf1.org/v1/location?session_key=11291&driver_number=4&date%3E2026-05-24T20:50:00&date%3C2026-05-24T21:00:00"
    assert lines[-1] == last_loc


def test_plan_only_requires_args():
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "capture_openf1_session.py"

    # --plan-only without all three overrides exits 2 with a usage error.
    cmd = [sys.executable, str(script_path), "1285", "11291", "--plan-only"]

    result = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
    assert result.returncode == 2
