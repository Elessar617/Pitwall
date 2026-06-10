import ast
import asyncio
import json
import re
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from conftest import notifications, wrap_transport
from textual.widgets import DataTable, Static

from pitwall.app import PitwallApp
from pitwall.config import AppConfig


# Gate helper
class SleepGate:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.history = []

    async def sleep(self, seconds: float):
        self.history.append(seconds)
        await self.queue.get()
        self.queue.task_done()

    def release(self):
        self.queue.put_nowait(True)


# We import the new components. They don't exist yet, so this will fail to import,
# which is perfect for RED phase.

# Expected grid from SPEC-09
EXPECTED_GRID = [
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
]

# Tower rows from SPEC-08 AC-7
EXPECTED_TOWER_ROWS = [
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


def build_live_handler(
    excerpt_dir, recorded_requests, sessions_gate=None, streams_404_after_tick0=True, fail_streams=False
):
    # Mock sessions API response
    mock_session = [
        {
            "session_key": 11291,
            "meeting_key": 1285,
            "session_name": "Race",
            "session_type": "Race",
            "date_start": "2026-05-24T19:00:00+00:00",
            "date_end": "2026-05-24T21:00:00+00:00",
            "circuit_short_name": "Montreal",
        }
    ]

    seen_streams = set()

    async def handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        url_str = str(request.url)

        if "sessions" in url_str:
            if sessions_gate is not None:
                await sessions_gate.wait()
            return httpx.Response(200, json=mock_session)

        if fail_streams:
            raise httpx.ConnectError("OpenF1 API connection error")  # noqa: TRY003

        mapping = {
            "drivers": "drivers.json",
            "stints": "stints.json",
            "position": "position.json",
            "intervals": "intervals.json",
            "laps": "laps.json",
            "pit": "pit.json",
            "race_control": "race_control.json",
            "location": "location.json",
        }

        for key, filename in mapping.items():
            if key in url_str:
                if streams_404_after_tick0 and key in seen_streams:
                    return httpx.Response(404, json=[])
                seen_streams.add(key)

                filepath = excerpt_dir / filename
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                return httpx.Response(200, json=data)

        return httpx.Response(404, json={"error": "not found"})

    return handler


@pytest.mark.asyncio
async def test_live_happy_path_stepped(injected_store, excerpt_dir):
    """AC-9: Live screen happy path (gate-stepped, deterministic)."""
    _conn, _client, store, _requests = injected_store
    gate = SleepGate()
    recorded_requests = []

    # wrap_transport
    handler = build_live_handler(excerpt_dir, recorded_requests)
    transport = wrap_transport(handler)

    test_clock = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)

    app = PitwallApp(
        config=AppConfig(season=2026, live=True),
        store=store,
        replay_sleep=gate.sleep,
        now=lambda: test_clock,
    )
    # Inject the transport seam
    app.openf1_transport = transport

    try:
        async with app.run_test(size=(120, 40)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            # Press 'l' to mount LiveTimingScreen
            await pilot.press("l")
            await pilot.pause()

            # Wait for worker to reach sleep (connecting or waiting for data)
            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach first sleep")  # noqa: TRY003

            # (a) Gate closed (post-discovery, pre-tick-0)
            status_widget = app.screen.query_one("#live-status", Static)
            assert str(status_widget.content) == "Live: Race — waiting for data…"
            table_widget = app.screen.query_one("#live-table", DataTable)
            map_widget = app.screen.query_one("#live-map", Static)
            assert table_widget.display is False
            assert map_widget.display is False
            assert map_widget.border_subtitle == ""

            # (b) Release tick 0
            gate.release()
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach second sleep")  # noqa: TRY003

            assert str(status_widget.content) == "Live · data to 20:32:29 UTC"
            assert table_widget.display is True
            assert table_widget.row_count == 22

            # Tower rows match end-state replay rows
            actual_rows = [[str(c) for c in table_widget.get_row_at(i)] for i in range(22)]
            assert actual_rows == [list(r) for r in EXPECTED_TOWER_ROWS]

            # Map visible and outline built
            assert map_widget.display is True
            grid_tick0 = list(EXPECTED_GRID)
            row_0 = grid_tick0[0]
            # marker at (24,0) cell (row 0, col 24)
            grid_tick0[0] = row_0[:24] + "●" + row_0[25:]
            expected_str_tick0 = "\n".join(grid_tick0)
            assert str(map_widget.content) == expected_str_tick0

            # Dimensions check and caption
            assert map_widget.region.width == 58
            assert map_widget.region.height == 34
            assert table_widget.region.width == 48
            assert map_widget.border_subtitle == "Montreal · 20:32:29 UTC"

            # (c) Release tick 1 (all-404)
            gate.release()
            for _ in range(100):
                if len(gate.history) >= 3:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach third sleep")  # noqa: TRY003

            assert str(status_widget.content) == "Live · data to 20:32:29 UTC"
            assert table_widget.display is True
            assert map_widget.display is True
            assert str(map_widget.content) == expected_str_tick0
            assert map_widget.border_subtitle == "Montreal · 20:32:29 UTC"

            # (e) Pinned 15-URL request log
            expected_urls = [
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
            actual_urls = [str(r.url) for r in recorded_requests]
            assert actual_urls == expected_urls
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_live_connecting_gated(injected_store, excerpt_dir):
    """AC-9d: Discovery-gated variant displays 'Connecting to live session…'."""
    _conn, _client, store, _requests = injected_store
    gate = SleepGate()
    recorded_requests = []
    sessions_gate = asyncio.Event()

    handler = build_live_handler(excerpt_dir, recorded_requests, sessions_gate=sessions_gate)
    transport = wrap_transport(handler)

    test_clock = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)

    app = PitwallApp(
        config=AppConfig(season=2026, live=True),
        store=store,
        replay_sleep=gate.sleep,
        now=lambda: test_clock,
    )
    app.openf1_transport = transport

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("l")
            await pilot.pause()

            # The worker is held at sessions discovery request, status should be Connecting
            status_widget = app.screen.query_one("#live-status", Static)
            assert str(status_widget.content) == "Connecting to live session…"

            # Let discovery complete
            sessions_gate.set()

            # Wait for first sleep to be reached
            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_live_discovery_error(injected_store):
    """AC-10a: Discovery transport error -> Live unavailable and notification."""
    _conn, _client, store, _requests = injected_store

    async def error_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection failed")  # noqa: TRY003

    transport = wrap_transport(error_handler)
    app = PitwallApp(
        config=AppConfig(season=2026, live=True),
        store=store,
    )
    app.openf1_transport = transport

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.press("l")
        await app.screen.workers.wait_for_complete()
        await pilot.pause()

        status_widget = app.screen.query_one("#live-status", Static)
        assert str(status_widget.content) == "Live unavailable — could not reach OpenF1."

        # exactly one error notification
        errors = [n.message for n in notifications(app) if n.severity == "error"]
        assert len(errors) == 1


@pytest.mark.asyncio
async def test_live_no_session(injected_store):
    """AC-10b: Discovery returns empty/404 -> Live unavailable — no session found."""
    _conn, _client, store, _requests = injected_store

    async def empty_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    transport = wrap_transport(empty_handler)
    app = PitwallApp(
        config=AppConfig(season=2026, live=True),
        store=store,
    )
    app.openf1_transport = transport

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.press("l")
        await app.screen.workers.wait_for_complete()
        await pilot.pause()

        status_widget = app.screen.query_one("#live-status", Static)
        assert str(status_widget.content) == "Live unavailable — no session found."


@pytest.mark.asyncio
async def test_live_ended_session(injected_store, excerpt_dir):
    """AC-10c: Clock after date_end + 3600 -> Live unavailable — latest session ended."""
    _conn, _client, store, _requests = injected_store
    recorded_requests = []
    handler = build_live_handler(excerpt_dir, recorded_requests)
    transport = wrap_transport(handler)

    # Ended clock (2026-05-25 12:00:00 UTC)
    test_clock = datetime(2026, 5, 25, 12, 0, 0, tzinfo=UTC)

    app = PitwallApp(
        config=AppConfig(season=2026, live=True),
        store=store,
        now=lambda: test_clock,
    )
    app.openf1_transport = transport

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.press("l")
        await app.screen.workers.wait_for_complete()
        await pilot.pause()

        status_widget = app.screen.query_one("#live-status", Static)
        assert str(status_widget.content) == "Live unavailable — latest session (Race) ended 21:00 UTC."


@pytest.mark.asyncio
async def test_live_upcoming(injected_store, excerpt_dir):
    """AC-10d: Clock before date_start - 900 -> Live: Race has not started — begins 19:00 UTC."""
    _conn, _client, store, _requests = injected_store
    recorded_requests = []
    handler = build_live_handler(excerpt_dir, recorded_requests)
    transport = wrap_transport(handler)

    # Upcoming clock (2026-05-24 17:00:00 UTC)
    test_clock = datetime(2026, 5, 24, 17, 0, 0, tzinfo=UTC)

    app = PitwallApp(
        config=AppConfig(season=2026, live=True),
        store=store,
        now=lambda: test_clock,
    )
    app.openf1_transport = transport

    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.press("l")
        await app.screen.workers.wait_for_complete()
        await pilot.pause()

        status_widget = app.screen.query_one("#live-status", Static)
        assert str(status_widget.content) == "Live: Race has not started — begins 19:00 UTC."


@pytest.mark.asyncio
async def test_live_waiting_no_data(injected_store, excerpt_dir):
    """AC-10e: Backfill all 404 -> status 'waiting for data' and table hidden."""
    _conn, _client, store, _requests = injected_store
    gate = SleepGate()
    recorded_requests = []

    # All streams return empty/404
    async def empty_streams_handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        url_str = str(request.url)
        if "sessions" in url_str:
            return httpx.Response(
                200,
                json=[
                    {
                        "session_key": 11291,
                        "meeting_key": 1285,
                        "session_name": "Race",
                        "session_type": "Race",
                        "date_start": "2026-05-24T19:00:00+00:00",
                        "date_end": "2026-05-24T21:00:00+00:00",
                        "circuit_short_name": "Montreal",
                    }
                ],
            )
        return httpx.Response(404, json=[])

    transport = wrap_transport(empty_streams_handler)
    test_clock = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)

    app = PitwallApp(
        config=AppConfig(season=2026, live=True),
        store=store,
        replay_sleep=gate.sleep,
        now=lambda: test_clock,
    )
    app.openf1_transport = transport

    try:
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.press("l")
            await pilot.pause()

            # Wait for first sleep (before tick 0 poll)
            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach first sleep")  # noqa: TRY003

            # Release tick 0
            gate.release()

            # Wait for second sleep (tick 0 completed/yielded against all-404 streams)
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach second sleep")  # noqa: TRY003

            status_widget = app.screen.query_one("#live-status", Static)
            assert str(status_widget.content) == "Live: Race — waiting for data…"
            table_widget = app.screen.query_one("#live-table", DataTable)
            assert table_widget.display is False
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_live_location_lag(injected_store, excerpt_dir):
    """AC-10f: Location 404s but other streams healthy -> 22 rows shown, map never displays."""
    _conn, _client, store, _requests = injected_store
    gate = SleepGate()
    recorded_requests = []

    # Serve excerpt streams but 404 for location
    base_handler = build_live_handler(excerpt_dir, recorded_requests)

    async def location_404_handler(request: httpx.Request) -> httpx.Response:
        if "location" in str(request.url):
            recorded_requests.append(request)
            return httpx.Response(404, json=[])
        return await base_handler(request)

    transport = wrap_transport(location_404_handler)
    test_clock = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)

    app = PitwallApp(
        config=AppConfig(season=2026, live=True),
        store=store,
        replay_sleep=gate.sleep,
        now=lambda: test_clock,
    )
    app.openf1_transport = transport

    try:
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.press("l")
            await pilot.pause()

            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()

            # Release tick 0
            gate.release()
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()

            status_widget = app.screen.query_one("#live-status", Static)
            assert str(status_widget.content) == "Live · data to 20:32:15 UTC"

            table_widget = app.screen.query_one("#live-table", DataTable)
            assert table_widget.display is True
            assert table_widget.row_count == 22

            map_widget = app.screen.query_one("#live-map", Static)
            assert map_widget.display is False
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_live_retrying(injected_store, excerpt_dir):
    """AC-10g: Failing poll after healthy tick 0 -> 'retrying (1)' suffix."""
    _conn, _client, store, _requests = injected_store
    gate = SleepGate()
    recorded_requests = []

    # Healthy tick 0, then fail subsequent streams
    fail_state = False
    base_handler = build_live_handler(excerpt_dir, recorded_requests)

    async def dynamic_handler(request: httpx.Request) -> httpx.Response:
        if fail_state and "sessions" not in str(request.url):
            recorded_requests.append(request)
            raise httpx.ConnectError("API down")  # noqa: TRY003
        return await base_handler(request)

    transport = wrap_transport(dynamic_handler)
    test_clock = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)

    app = PitwallApp(
        config=AppConfig(season=2026, live=True),
        store=store,
        replay_sleep=gate.sleep,
        now=lambda: test_clock,
    )
    app.openf1_transport = transport

    try:
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.press("l")
            await pilot.pause()

            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()

            # Release tick 0 (healthy)
            gate.release()
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()

            # Now fail next poll (tick 1)
            fail_state = True
            gate.release()
            for _ in range(100):
                if len(gate.history) >= 3:
                    break
                await pilot.pause()

            status_widget = app.screen.query_one("#live-status", Static)
            assert str(status_widget.content) == "Live · data to 20:32:29 UTC · retrying (1)"
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_live_ended_loop(injected_store, excerpt_dir):
    """AC-10h: Clock stepped past end + 3600 -> Live ended · data to ..."""
    _conn, _client, store, _requests = injected_store
    gate = SleepGate()
    recorded_requests = []

    clock_time = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)

    def clock_step():
        return clock_time

    handler = build_live_handler(excerpt_dir, recorded_requests)
    transport = wrap_transport(handler)

    app = PitwallApp(
        config=AppConfig(season=2026, live=True),
        store=store,
        replay_sleep=gate.sleep,
        now=clock_step,
    )
    app.openf1_transport = transport

    try:
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.press("l")
            await pilot.pause()

            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()

            # Release tick 0
            gate.release()
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()

            # Step clock past overrun window (end + 3600 = 22:00:00 UTC)
            clock_time = datetime(2026, 5, 24, 22, 0, 1, tzinfo=UTC)

            # Release tick 1, the loop should break immediately on next iteration without yielding
            gate.release()
            await app.screen.workers.wait_for_complete()
            await pilot.pause()

            status_widget = app.screen.query_one("#live-status", Static)
            assert str(status_widget.content) == "Live ended · data to 20:32:29 UTC"
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_live_chassis_isolation(injected_store, excerpt_dir):
    """AC-10i: Subtitle and Jolpica requests isolated from live worker."""
    _conn, _client, store, requests_log = injected_store
    gate = SleepGate()
    recorded_requests = []

    clock_time = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)

    def clock_step():
        return clock_time

    handler = build_live_handler(excerpt_dir, recorded_requests)
    transport = wrap_transport(handler)

    app = PitwallApp(
        config=AppConfig(season=2026, live=True),
        store=store,
        replay_sleep=gate.sleep,
        now=clock_step,
    )
    app.openf1_transport = transport

    try:
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            # Jolpica requests should be 3
            assert len(requests_log) == 3

            await pilot.press("l")
            await pilot.pause()

            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()

            # Release tick 0
            gate.release()
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()

            # Step clock past overrun window
            clock_time = datetime(2026, 5, 24, 22, 0, 1, tzinfo=UTC)
            gate.release()
            await app.screen.workers.wait_for_complete()
            await pilot.pause()

            # Isolation check
            assert app.sub_title == "season 2026 · data as of 14:30 UTC"
            assert len(requests_log) == 3
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_live_wander_away_cancels(injected_store, excerpt_dir, monkeypatch):
    """Adversary C1: screen switch cancels live worker and closes client."""
    _conn, _client, store, _requests = injected_store
    gate = SleepGate()
    recorded_requests = []

    handler = build_live_handler(excerpt_dir, recorded_requests)
    transport = wrap_transport(handler)

    transport_closed = False
    original_aclose = transport.aclose

    async def tracking_aclose():
        nonlocal transport_closed
        transport_closed = True
        await original_aclose()

    transport.aclose = tracking_aclose

    clients = []
    from pitwall.openf1 import OpenF1Client

    original_init = OpenF1Client.__init__

    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        clients.append(self)

    monkeypatch.setattr(OpenF1Client, "__init__", new_init)

    test_clock = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)

    app = PitwallApp(
        config=AppConfig(season=2026, live=True),
        store=store,
        replay_sleep=gate.sleep,
        now=lambda: test_clock,
    )
    app.openf1_transport = transport

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            # Press 'l' to mount LiveTimingScreen
            await pilot.press("l")
            await pilot.pause()

            # Wait for worker to reach first sleep (pre-tick-0)
            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach first sleep")  # noqa: TRY003

            # Release tick 0
            gate.release()
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()
            else:
                raise AssertionError("Worker did not reach second sleep")  # noqa: TRY003

            # Wander away by pressing 's' (Schedule Screen)
            await pilot.press("s")
            await pilot.pause()

            # Let the event loop run for cancellation to process
            for _ in range(10):
                await pilot.pause()

            # The live worker must cancel and close client/transport
            assert transport_closed is True
            assert len(clients) > 0
            assert all(c.client.is_closed for c in clients)
    finally:
        for _ in range(10):
            gate.release()


@pytest.mark.asyncio
async def test_live_lap_cursor_edge_backfill():  # noqa: C901 - scenario-handler breadth is intentional
    """Adversary C3: Lap completion at the exact lap-cursor window edge (date_start == cursor-240s) is not lost."""
    from pitwall.openf1 import OpenF1Client
    from pitwall.openf1.live import LiveSource
    from pitwall.openf1.models import Session

    session = Session(
        session_key=11291,
        meeting_key=1285,
        session_name="Race",
        date_start=datetime(2026, 5, 24, 19, 0, 0, tzinfo=UTC),
        date_end=datetime(2026, 5, 24, 21, 0, 0, tzinfo=UTC),
    )

    urls_requested = []

    async def transport_handler(request: httpx.Request) -> httpx.Response:  # noqa: C901 - mock API surface
        url_str = str(request.url)
        urls_requested.append(url_str)

        # Default responses for other endpoints
        if "sessions" in url_str:
            return httpx.Response(200, json=[])
        if "drivers" in url_str:
            return httpx.Response(200, json=[])
        if "stints" in url_str:
            return httpx.Response(200, json=[])
        if "position" in url_str:
            return httpx.Response(200, json=[])
        if "intervals" in url_str:
            return httpx.Response(200, json=[])
        if "pit" in url_str:
            return httpx.Response(200, json=[])
        if "race_control" in url_str:
            return httpx.Response(200, json=[])
        if "location" in url_str:
            return httpx.Response(200, json=[])

        # Laps stream handling
        if "laps" in url_str:
            if "date%3E" in url_str:
                # Operator lives percent-encoded in the param NAME with the
                # value inline (no '='): extract by prefix from the raw query.
                date_gt_str = url_str.split("date%3E", 1)[1].split("&", 1)[0]
                if date_gt_str:
                    laps = []
                    # Lap 10: date_start exactly cursor-240s.
                    # Since query is strict date > date_gt_str, it is excluded if date_gt_str >= "2026-05-24T20:30:00"
                    if date_gt_str < "2026-05-24T20:30:00":
                        laps.append(
                            {
                                "session_key": 11291,
                                "meeting_key": 1285,
                                "driver_number": 1,
                                "lap_number": 10,
                                "date_start": "2026-05-24T20:30:00+00:00",
                                "lap_duration": 76.5,
                            }
                        )
                    if date_gt_str < "2026-05-24T20:34:00":
                        laps.append(
                            {
                                "session_key": 11291,
                                "meeting_key": 1285,
                                "driver_number": 1,
                                "lap_number": 11,
                                "date_start": "2026-05-24T20:34:00+00:00",
                                "lap_duration": None,
                            }
                        )
                    return httpx.Response(200, json=laps)
            else:
                # Tick 0 query: no date filter.
                return httpx.Response(
                    200,
                    json=[
                        {
                            "session_key": 11291,
                            "meeting_key": 1285,
                            "driver_number": 1,
                            "lap_number": 10,
                            "date_start": "2026-05-24T20:30:00+00:00",
                            "lap_duration": None,
                        },
                        {
                            "session_key": 11291,
                            "meeting_key": 1285,
                            "driver_number": 1,
                            "lap_number": 11,
                            "date_start": "2026-05-24T20:34:00+00:00",
                            "lap_duration": None,
                        },
                    ],
                )

        return httpx.Response(404, json=[])

    transport = wrap_transport(transport_handler)
    clock_time = datetime(2026, 5, 24, 20, 35, 0, tzinfo=UTC)

    async with OpenF1Client(transport=transport) as client:
        source = LiveSource(
            client,
            session,
            sleep=lambda s: asyncio.sleep(0.001),
            clock=lambda: clock_time,
        )

        iterator = source.ticks().__aiter__()

        tick0 = await iterator.__anext__()
        lap_started_events = [e for e in tick0.events if e.kind == "lap_started"]
        lap_completed_events = [e for e in tick0.events if e.kind == "lap_completed"]
        assert len(lap_started_events) == 2
        assert len(lap_completed_events) == 0

        tick1 = await iterator.__anext__()
        lap_completed_events_tick1 = [e for e in tick1.events if e.kind == "lap_completed"]
        assert len(lap_completed_events_tick1) == 1
        assert lap_completed_events_tick1[0].payload.lap_number == 10


@pytest.mark.asyncio
async def test_live_backfill_benchmark():  # noqa: C901 - scenario-handler breadth is intentional
    """AC-14: One LiveSource backfill tick over 25,000 synthetic records completes < 2.0 s."""
    import time

    from pitwall.openf1 import OpenF1Client
    from pitwall.openf1.live import LiveSource
    from pitwall.openf1.models import Session

    # 25,000 synthetic records:
    position_data = [
        {"date": "2026-05-24T20:30:00+00:00", "driver_number": i % 20 + 1, "position": i % 20 + 1} for i in range(5000)
    ]
    interval_data = [
        {"date": "2026-05-24T20:30:00+00:00", "driver_number": i % 20 + 1, "gap_to_leader": 0.0, "interval": 0.0}
        for i in range(5000)
    ]
    lap_data = [
        {
            "date_start": "2026-05-24T20:30:00+00:00",
            "driver_number": i % 20 + 1,
            "lap_number": i // 20 + 1,
            "lap_duration": 75.0,
        }
        for i in range(5000)
    ]
    location_data = [
        {"date": "2026-05-24T20:30:00+00:00", "driver_number": i % 20 + 1, "x": 100.0, "y": 200.0} for i in range(5000)
    ]
    stint_data = [
        {"driver_number": i % 20 + 1, "stint_number": i // 20 + 1, "compound": "SOFT", "lap_start": 1, "lap_end": 10}
        for i in range(4000)
    ]
    pit_data = [
        {
            "date": "2026-05-24T20:30:00+00:00",
            "driver_number": i % 20 + 1,
            "lap_number": i // 20 + 1,
            "pit_duration": 22.5,
        }
        for i in range(500)
    ]
    rc_data = [{"date": "2026-05-24T20:30:00+00:00", "message": "GREEN FLAG"} for i in range(500)]

    total_records = (
        len(position_data)
        + len(interval_data)
        + len(lap_data)
        + len(location_data)
        + len(stint_data)
        + len(pit_data)
        + len(rc_data)
    )
    assert total_records == 25000

    async def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "drivers" in url_str:
            return httpx.Response(
                200,
                json=[
                    {"driver_number": i, "name_acronym": f"DRV{i}", "full_name": f"Driver {i}", "team_name": "Team"}
                    for i in range(1, 21)
                ],
            )
        if "stints" in url_str:
            return httpx.Response(200, json=stint_data)
        if "position" in url_str:
            return httpx.Response(200, json=position_data)
        if "intervals" in url_str:
            return httpx.Response(200, json=interval_data)
        if "laps" in url_str:
            return httpx.Response(200, json=lap_data)
        if "pit" in url_str:
            return httpx.Response(200, json=pit_data)
        if "race_control" in url_str:
            return httpx.Response(200, json=rc_data)
        if "location" in url_str:
            return httpx.Response(200, json=location_data)
        return httpx.Response(404, json=[])

    transport = wrap_transport(handler)

    session = Session(
        session_key=11291,
        meeting_key=1285,
        session_name="Race",
        date_start=datetime(2026, 5, 24, 19, 0, 0, tzinfo=UTC),
        date_end=datetime(2026, 5, 24, 21, 0, 0, tzinfo=UTC),
    )

    clock_time = datetime(2026, 5, 24, 20, 35, 0, tzinfo=UTC)

    async with OpenF1Client(transport=transport) as client:
        source = LiveSource(
            client,
            session,
            sleep=lambda s: asyncio.sleep(0.001),
            clock=lambda: clock_time,
        )

        start_time = time.perf_counter()
        async for _tick in source.ticks():
            break
        duration = time.perf_counter() - start_time

        assert duration < 2.0, f"Benchmark failed: backfill tick took {duration:.3f}s (max 2.0s)"


def test_ac11_live_timing_imports_hoisted():
    """AC-11a: LiveTimingScreen function-local track_map imports hoisted."""

    pattern = re.compile(r"^\s+(import|from)\s")
    repo_root = Path(__file__).resolve().parent.parent
    file_path = repo_root / "src" / "pitwall" / "screens" / "live_timing.py"
    matches = []
    with open(file_path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if pattern.match(line):
                matches.append((line_no, line.strip()))

    assert not matches, f"Found indented imports in live_timing.py: {matches}"


def test_ac11_track_map_no_any():
    """AC-11b: track_map.py has zero Any usages."""

    repo_root = Path(__file__).resolve().parent.parent
    file_path = repo_root / "src" / "pitwall" / "screens" / "track_map.py"
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    matches = re.findall(r"\bAny\b", content)
    assert len(matches) == 0, f"Found {len(matches)} occurrences of 'Any' in track_map.py"


def test_ac11_init_map_signature():
    """AC-11b: _init_map's signature is fully typed with no bare list or Any."""

    repo_root = Path(__file__).resolve().parent.parent
    file_path = repo_root / "src" / "pitwall" / "screens" / "live_timing.py"
    with open(file_path, encoding="utf-8") as f:
        tree = ast.parse(f.read())

    class InitMapFinder(ast.NodeVisitor):
        def __init__(self):
            self.node = None

        def visit_FunctionDef(self, node):
            if node.name == "_init_map":
                self.node = node
            self.generic_visit(node)

    finder = InitMapFinder()
    finder.visit(tree)

    assert finder.node is not None, "Could not find _init_map function in live_timing.py"

    args = finder.node.args
    assert len(args.args) >= 2, "Expected self and location_points arguments"
    loc_points_arg = args.args[1]
    assert loc_points_arg.arg == "location_points"

    annotation = loc_points_arg.annotation
    assert annotation is not None, "location_points has no type annotation"

    annotation_src = ast.unparse(annotation)
    assert annotation_src != "list", "location_points should not be a bare list"
    assert "Any" not in annotation_src, "location_points signature should not contain Any"

    returns = finder.node.returns
    assert returns is not None, "_init_map has no return type annotation"
    returns_src = ast.unparse(returns)
    assert "Any" not in returns_src, "_init_map return type should not contain Any"


@pytest.mark.asyncio
async def test_live_view_colours(injected_store, excerpt_dir):  # noqa: C901
    """AC-10a: Live styled rows including a driver without team_colour, suffix to status, cycling back."""
    _conn, _client, store, _requests = injected_store
    gate = SleepGate()
    recorded_requests = []

    # Custom drivers JSON with team_colours
    async def custom_handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        url_str = str(request.url)

        if "sessions" in url_str:
            mock_session = [
                {
                    "session_key": 11291,
                    "meeting_key": 1285,
                    "session_name": "Race",
                    "session_type": "Race",
                    "date_start": "2026-05-24T19:00:00+00:00",
                    "date_end": "2026-05-24T21:00:00+00:00",
                    "circuit_short_name": "Montreal",
                }
            ]
            return httpx.Response(200, json=mock_session)

        if "drivers" in url_str:
            # Serve custom drivers list
            # Driver 1 has team_colour, Driver 3 does not
            filepath = excerpt_dir / "drivers.json"
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            for d in data:
                if d["driver_number"] == 1:
                    d["team_colour"] = "F47600"
                elif d["driver_number"] == 3:
                    d["team_colour"] = None  # Without team colour
            return httpx.Response(200, json=data)

        mapping = {
            "stints": "stints.json",
            "position": "position.json",
            "intervals": "intervals.json",
            "laps": "laps.json",
            "pit": "pit.json",
            "race_control": "race_control.json",
            "location": "location.json",
        }

        for key, filename in mapping.items():
            if key in url_str:
                filepath = excerpt_dir / filename
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                return httpx.Response(200, json=data)

        return httpx.Response(404, json={"error": "not found"})

    transport = wrap_transport(custom_handler)
    test_clock = datetime(2026, 5, 24, 20, 33, 0, tzinfo=UTC)

    app = PitwallApp(
        config=AppConfig(season=2026, live=True),
        store=store,
        replay_sleep=gate.sleep,
        now=lambda: test_clock,
    )
    app.openf1_transport = transport

    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()

            await pilot.press("l")
            await pilot.pause()

            # Wait for first sleep (waiting for data)
            for _ in range(100):
                if len(gate.history) >= 1:
                    break
                await pilot.pause()

            # Pre-data live status should NOT have the view suffix
            status_widget = app.screen.query_one("#live-status", Static)
            assert str(status_widget.content) == "Live: Race — waiting for data…"

            # Try cycling view - should be no-op when pre-data
            await pilot.press("v")
            await pilot.pause()
            assert str(status_widget.content) == "Live: Race — waiting for data…"

            # Release tick 0
            gate.release()

            # Wait for second sleep (data received)
            for _ in range(100):
                if len(gate.history) >= 2:
                    break
                await pilot.pause()

            assert str(status_widget.content) == "Live · data to 20:32:29 UTC"

            table_widget = app.screen.query_one("#live-table", DataTable)

            # Find rows for driver 1 (NOR) and driver 3 (VER)
            nor_row_idx = None
            ver_row_idx = None
            for idx in range(table_widget.row_count):
                row = table_widget.get_row_at(idx)
                if str(row[1]) == "NOR":
                    nor_row_idx = idx
                elif str(row[1]) == "VER":
                    ver_row_idx = idx

            assert nor_row_idx is not None
            assert ver_row_idx is not None

            nor_drv_cell = table_widget.get_row_at(nor_row_idx)[1]
            ver_drv_cell = table_widget.get_row_at(ver_row_idx)[1]

            # Driver 1 has team_colour style, Driver 3 has fallback empty style
            assert str(nor_drv_cell.style) == "#F47600"
            assert ver_drv_cell.style == "" or str(ver_drv_cell.style) == ""

            # Press v -> cycle to lead fight
            await pilot.press("v")
            await pilot.pause()

            # Suffix appended to status line
            assert str(status_widget.content) == "Live · data to 20:32:29 UTC · view: lead fight"
            assert table_widget.row_count == 5

            # Cycle back to all (v, v, v)
            await pilot.press("v")  # lead -> podium
            await pilot.pause()
            await pilot.press("v")  # podium -> points
            await pilot.pause()
            await pilot.press("v")  # points -> all
            await pilot.pause()

            # Status is restored to the exact pre-existing string without suffix
            assert str(status_widget.content) == "Live · data to 20:32:29 UTC"
            assert table_widget.row_count == 22
    finally:
        for _ in range(10):
            gate.release()
