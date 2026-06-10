"""Strategy screen contracts (SPEC-12 AC-7..10)."""

# ruff: noqa: RUF001  (pinned status literals contain the multiplication sign)

import asyncio

from conftest import notifications
from textual.widgets import Static

from pitwall.app import PitwallApp
from pitwall.config import AppConfig
from pitwall.screens import StrategyScreen


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


def widgets(screen):
    return {
        name: screen.query_one(f"#game-{name}", Static)
        for name in ("status", "form", "plan", "prompt", "event", "score")
    }


async def settle(pilot, predicate, tries=100):
    for _ in range(tries):
        if predicate():
            return
        await pilot.pause()
    raise AssertionError("condition never settled")  # noqa: TRY003 - test helper


NO_REPLAY = "Strategy game requires a replay — start pitwall with --replay <fixtures-dir>."
COMMIT_PROMPT = "Strategy — commit a plan to start the race."
PLAN_LINE = "Plan — NOR · MEDIUM → MEDIUM · pit 16 · P14"
WINDOW_PROMPT = "Pit window — planned stop at lap 16: [1] pit now · [2] stay out"
SCORE_PANEL_B = (
    "Final score: 20\n"
    "Tyres: +5 (planned MEDIUM, MEDIUM · actual INTERMEDIATE, MEDIUM, MEDIUM)\n"
    "Pit laps: 0 (planned 16 · actual 1, 14)\n"
    "Decisions: +5 (1 of 1 matched)\n"
    "Finish: +10 (predicted P14 · actual P14)"
)


def make_app(store, gate, replay_dir=None, live=False):
    config = (
        AppConfig(season=2026, live=True)
        if live
        else AppConfig(season=2026, replay_dir=replay_dir, replay_speed=60.0)
        if replay_dir
        else AppConfig(season=2026)
    )
    return PitwallApp(config=config, store=store, replay_sleep=gate.sleep)


async def goto_game(app, pilot):
    await app.workers.wait_for_complete()
    await pilot.press("g")
    await pilot.pause()


# ---- AC-7: chassis ----


async def test_no_replay_state(injected_store):
    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate)
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_game(app, pilot)
        assert isinstance(app.screen, StrategyScreen)
        w = widgets(app.screen)
        assert str(w["status"].content) == NO_REPLAY
        for name in ("form", "plan", "prompt", "event", "score"):
            assert w[name].display is False
        gate.release()
        await pilot.pause()
        assert gate.history == []
    await client.aclose()


async def test_live_mode_same_string(injected_store):
    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, live=True)
    app.openf1_transport = None
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_game(app, pilot)
        assert str(widgets(app.screen)["status"].content) == NO_REPLAY
    await client.aclose()


# ---- AC-8: setup flow ----

WIZARD_PRESSES = ["enter", "2", "2", "enter", "1", "6", "enter", "1", "4"]
EXPECTED_RENDERS = [
    "Tyres: — · 1=S 2=M 3=H 4=I 5=W · Backspace undo · Enter confirm",
    "Tyres: MEDIUM · 1=S 2=M 3=H 4=I 5=W · Backspace undo · Enter confirm",
    "Tyres: MEDIUM, MEDIUM · 1=S 2=M 3=H 4=I 5=W · Backspace undo · Enter confirm",
    "Pit 1 of 1: lap — · digits · Backspace undo · Enter confirm",
    "Pit 1 of 1: lap 1 · digits · Backspace undo · Enter confirm",
    "Pit 1 of 1: lap 16 · digits · Backspace undo · Enter confirm",
    "Predicted finish: P— · digits · Backspace undo · Enter commit",
    "Predicted finish: P1 · digits · Backspace undo · Enter commit",
    "Predicted finish: P14 · digits · Backspace undo · Enter commit",
]


async def setup_to_predicted(app, pilot):
    await goto_game(app, pilot)
    w = widgets(app.screen)
    await settle(pilot, lambda: str(w["status"].content) == COMMIT_PROMPT)
    assert str(w["form"].content) == "Driver: 1 NOR · Up/Down select · Enter confirm"
    for key, expected in zip(WIZARD_PRESSES, EXPECTED_RENDERS, strict=True):
        await pilot.press(key)
        await pilot.pause()
        assert str(w["form"].content) == expected
    return w


async def test_setup_flow_and_precommit_gating(injected_store, excerpt_dir):
    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, replay_dir=str(excerpt_dir))
    async with app.run_test(size=(80, 24)) as pilot:
        await setup_to_predicted(app, pilot)
        assert gate.history == []  # pre-race by construction
    await client.aclose()


async def test_invalid_pit_lap_recovers(injected_store, excerpt_dir):
    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, replay_dir=str(excerpt_dir))
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_game(app, pilot)
        w = widgets(app.screen)
        await settle(pilot, lambda: str(w["status"].content) == COMMIT_PROMPT)
        for key in ("enter", "2", "2", "enter", "enter"):
            await pilot.press(key)
            await pilot.pause()
        assert str(w["form"].content).endswith("\nInvalid: pit lap must be between 1 and 99")
        for key in ("1", "6", "enter"):
            await pilot.press(key)
            await pilot.pause()
        assert str(w["form"].content) == "Predicted finish: P— · digits · Backspace undo · Enter commit"
    await client.aclose()


async def test_load_failure_and_empty(injected_store, tmp_path):
    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, replay_dir=str(tmp_path))
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_game(app, pilot)
        w = widgets(app.screen)
        await settle(
            pilot,
            lambda: str(w["status"].content) == "Strategy game unavailable — failed to load replay data.",
        )
        errors = [n for n in notifications(app) if n.severity == "error"]
        assert len(errors) == 1
    await client.aclose()


async def test_zero_events_state(injected_store, tmp_path, excerpt_dir):
    import json
    import shutil

    for f in excerpt_dir.iterdir():
        shutil.copy(f, tmp_path / f.name)
    for name in ("laps", "position", "intervals", "pit", "race_control"):
        (tmp_path / f"{name}.json").write_text("[]")
    (tmp_path / "manifest.json").write_text(json.dumps({"replay_window": {"start": "2026-05-24T20:30:00+00:00"}}))
    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, replay_dir=str(tmp_path))
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_game(app, pilot)
        w = widgets(app.screen)
        await settle(
            pilot,
            lambda: str(w["status"].content) == "Strategy game unavailable — replay data contains no events.",
        )
    await client.aclose()


# ---- AC-9: race flow ----


async def run_race(app, pilot, decision_key):
    w = await setup_to_predicted(app, pilot)
    gate = app._test_gate
    await pilot.press("enter")
    await pilot.pause()
    assert w["form"].display is False
    assert str(w["plan"].content) == PLAN_LINE
    assert str(w["status"].content) == "Game ×60 · NOR · starting…"
    await settle(pilot, lambda: len(gate.history) == 1)

    gate.release()
    await settle(pilot, lambda: str(w["status"].content) == "Game ×60 · NOR · 20:30:00 UTC")
    assert w["prompt"].display is True
    assert str(w["prompt"].content) == WINDOW_PROMPT

    await pilot.press(decision_key)
    await pilot.pause()
    verb = "pit now" if decision_key == "1" else "stay out"
    assert str(w["prompt"].content) == f"Decision recorded — {verb} (planned lap 16)."

    gate.release()
    await settle(pilot, lambda: str(w["status"].content) == "Game ×60 · NOR · 20:30:30 UTC")
    assert str(w["event"].content) == "NOR pitted — lap 15 (planned lap 16)."

    for _ in range(4):
        gate.release()
    await app.workers.wait_for_complete()
    await pilot.pause()
    return w


async def test_race_flow_pit_decision(injected_store, excerpt_dir):
    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, replay_dir=str(excerpt_dir))
    app._test_gate = gate
    async with app.run_test(size=(80, 24)) as pilot:
        w = await run_race(app, pilot, "1")
        assert str(w["status"].content) == "Game over · NOR · final score 20"
        assert w["score"].display is True
        assert str(w["score"].content) == SCORE_PANEL_B
        await pilot.press("1")
        await pilot.pause()
        assert str(w["status"].content) == "Game over · NOR · final score 20"
    await client.aclose()


async def test_race_flow_stay_decision(injected_store, excerpt_dir):
    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, replay_dir=str(excerpt_dir))
    app._test_gate = gate
    async with app.run_test(size=(80, 24)) as pilot:
        w = await run_race(app, pilot, "2")
        assert str(w["status"].content) == "Game over · NOR · final score 10"
        assert "Decisions: -5 (0 of 1 matched)" in str(w["score"].content)
    await client.aclose()


async def test_digits_noop_before_commit(injected_store, excerpt_dir):
    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, replay_dir=str(excerpt_dir))
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_game(app, pilot)
        w = widgets(app.screen)
        await settle(pilot, lambda: str(w["status"].content) == COMMIT_PROMPT)
        before = str(w["form"].content)
        await pilot.press("9")
        await pilot.pause()
        assert str(w["form"].content) == before
    await client.aclose()


# ---- AC-10: isolation + lifecycle ----


async def test_wander_away_cancels_game(injected_store, excerpt_dir):
    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, replay_dir=str(excerpt_dir))
    app._test_gate = gate
    async with app.run_test(size=(80, 24)) as pilot:
        w = await setup_to_predicted(app, pilot)
        await pilot.press("enter")
        await pilot.pause()
        await settle(pilot, lambda: len(gate.history) == 1)
        gate.release()
        await settle(pilot, lambda: str(w["status"].content) == "Game ×60 · NOR · 20:30:00 UTC")

        await pilot.press("s")
        await pilot.pause()
        history_len = len(gate.history)
        gate.release()
        await pilot.pause()
        await pilot.pause()
        assert len(gate.history) == history_len

        await pilot.press("g")
        await pilot.pause()
        assert str(w["status"].content) == "Game ×60 · NOR · 20:30:00 UTC"
    await client.aclose()


async def test_chassis_isolation(injected_store, excerpt_dir):
    _conn, client, store, requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, replay_dir=str(excerpt_dir))
    app._test_gate = gate
    async with app.run_test(size=(80, 24)) as pilot:
        baseline = len(requests)
        w = await run_race(app, pilot, "1")
        assert str(w["status"].content).startswith("Game over")
        assert app.sub_title == "season 2026 · data as of 14:30 UTC"
        assert len(requests) == baseline
    await client.aclose()


# ---- fix cycle: adversary F1 (same-tick multi-window FIFO) + review F5 (AC-9f states) ----


async def test_same_tick_multi_window_fifo(injected_store, excerpt_dir, tmp_path):
    """Adversary F1: two same-tick windows — the rendered prompt is the queue head."""
    import json
    import shutil

    for f in excerpt_dir.iterdir():
        shutil.copy(f, tmp_path / f.name)
    # Two duplicate lap-5 starts at-or-before the window start land in tick 0
    # (AC-3g: the duplicate advances the adjacent planned window).
    lap = {
        "session_key": 11291,
        "meeting_key": 1285,
        "driver_number": 1,
        "lap_number": 5,
        "date_start": "2026-05-24T20:29:59+00:00",
        "lap_duration": None,
    }
    (tmp_path / "laps.json").write_text(json.dumps([lap, dict(lap)]))
    (tmp_path / "pit.json").write_text("[]")

    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, replay_dir=str(tmp_path))
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_game(app, pilot)
        w = widgets(app.screen)
        await settle(pilot, lambda: str(w["status"].content) == COMMIT_PROMPT)
        # Plan with pit laps (5, 6): both windows fire from the duplicate lap-5 events.
        for key in ("enter", "2", "2", "2", "enter", "5", "enter", "6", "enter", "1", "4", "enter"):
            await pilot.press(key)
            await pilot.pause()
        await settle(pilot, lambda: len(gate.history) == 1)
        gate.release()
        await settle(pilot, lambda: "Pit window" in str(w["prompt"].content))
        assert str(w["prompt"].content) == "Pit window — planned stop at lap 5: [1] pit now · [2] stay out"
        await pilot.press("1")
        await pilot.pause()
        # The decision targets the DISPLAYED lap 5; the next pending prompt renders.
        assert str(w["prompt"].content) == "Pit window — planned stop at lap 6: [1] pit now · [2] stay out"
        await pilot.press("2")
        await pilot.pause()
        assert str(w["prompt"].content) == "Decision recorded — stay out (planned lap 6)."
    await client.aclose()


async def test_decision_keys_noop_before_tick0_and_after_decision(injected_store, excerpt_dir):
    """AC-9f: 1/2 are no-ops pre-tick-0 and after the prompt is answered."""
    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, replay_dir=str(excerpt_dir))
    async with app.run_test(size=(80, 24)) as pilot:
        w = await setup_to_predicted(app, pilot)
        await pilot.press("enter")
        await pilot.pause()
        before = str(w["prompt"].content)
        await pilot.press("1")
        await pilot.pause()
        assert str(w["prompt"].content) == before  # pre-tick-0: nothing pending

        await settle(pilot, lambda: len(gate.history) == 1)
        gate.release()
        await settle(pilot, lambda: "Pit window" in str(w["prompt"].content))
        await pilot.press("1")
        await pilot.pause()
        answered = str(w["prompt"].content)
        assert answered == "Decision recorded — pit now (planned lap 16)."
        await pilot.press("2")
        await pilot.pause()
        assert str(w["prompt"].content) == answered  # after-decision: no-op
    await client.aclose()


async def test_v_inert_in_game(injected_store, excerpt_dir):
    """AC-10c: pressing v on the strategy screen changes no game widget and records no decision."""
    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, replay_dir=str(excerpt_dir))
    try:
        async with app.run_test(size=(80, 24)) as pilot:
            await goto_game(app, pilot)
            assert isinstance(app.screen, StrategyScreen)
            w = widgets(app.screen)

            # Record initial state of all game widgets
            initial_contents = {name: str(w[name].content) if w[name].display else None for name in w}
            initial_displays = {name: w[name].display for name in w}

            # Press 'v'
            await pilot.press("v")
            await pilot.pause()

            # Check widgets are unchanged
            for name in w:
                assert w[name].display == initial_displays[name]
                if w[name].display:
                    assert str(w[name].content) == initial_contents[name]

            # Ensure no decisions/actions were recorded or run
            # The playhead/sleep history should be unchanged
            assert gate.history == []
    finally:
        for _ in range(10):
            gate.release()
        await client.aclose()


async def test_draft_acronym_markup_safe(injected_store, excerpt_dir, tmp_path):
    """iter15 SEC-1 residual: a malformed driver acronym in the wizard must not crash."""
    import json
    import shutil

    for f in excerpt_dir.iterdir():
        shutil.copy(f, tmp_path / f.name)
    drivers = json.loads((tmp_path / "drivers.json").read_text())
    drivers[0]["name_acronym"] = "bad [/] X [@click=app.bell]Y"
    (tmp_path / "drivers.json").write_text(json.dumps(drivers))

    _conn, client, store, _requests = injected_store
    gate = SleepGate()
    app = make_app(store, gate, replay_dir=str(tmp_path))
    async with app.run_test(size=(80, 24)) as pilot:
        await goto_game(app, pilot)
        w = widgets(app.screen)
        await settle(pilot, lambda: str(w["status"].content) == COMMIT_PROMPT)
        # The first driver's malformed acronym renders verbatim, no MarkupError.
        assert "bad [/] X" in str(w["form"].content)
    await client.aclose()
