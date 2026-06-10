"""Strategy-game fold, actual outcome, scoring, rendering (SPEC-12 AC-3..6)."""

import subprocess
import sys
from pathlib import Path

import pytest
from conftest import EXCERPT_DIR

from pitwall.game.model import Decision, GamePrompt, StrategyPlan
from pitwall.game.score import (
    GAME_START,
    ActualOutcome,
    ScoreBreakdown,
    actual_outcome,
    advance,
    render_score,
    score_plan,
)
from pitwall.openf1.replay import ReplayEvent, load_session, merge_events

PLAN_A = StrategyPlan(
    driver_number=1,
    compounds=("INTERMEDIATE", "MEDIUM", "MEDIUM"),
    pit_laps=(1, 14),
    predicted_position=12,
)
PLAN_B = StrategyPlan(driver_number=1, compounds=("MEDIUM", "MEDIUM"), pit_laps=(16,), predicted_position=14)


class _Lap:
    def __init__(self, driver_number, lap_number):
        self.driver_number = driver_number
        self.lap_number = lap_number


class _Pit:
    def __init__(self, driver_number, lap_number):
        self.driver_number = driver_number
        self.lap_number = lap_number


class _Pos:
    def __init__(self, driver_number, position):
        self.driver_number = driver_number
        self.position = position


def ev(kind, payload):
    import datetime

    return ReplayEvent(ts=datetime.datetime(2026, 5, 24, 20, 30, tzinfo=datetime.UTC), kind=kind, payload=payload)


# ---- AC-3: the game fold ----


def test_window_prompt_idempotent():
    events = (ev("lap_started", _Lap(1, 15)),)
    state, prompts = advance(GAME_START, events, PLAN_B)
    assert prompts == (GamePrompt("window", 15, 16),)
    assert state.prompted == {16}
    _again, prompts2 = advance(state, events, PLAN_B)
    assert prompts2 == ()


def test_window_fallback_on_planned_lap():
    _state, prompts = advance(GAME_START, (ev("lap_started", _Lap(1, 16)),), PLAN_B)
    assert prompts == (GamePrompt("window", 16, 16),)


def test_pit_events_planned_and_unplanned():
    state, prompts = advance(GAME_START, (ev("pit", _Pit(1, 15)),), PLAN_B)
    assert state.pit_event_laps == (15,)
    assert prompts == (GamePrompt("pit", 15, 16),)
    state2, prompts2 = advance(state, (ev("pit", _Pit(1, 18)),), PLAN_B)
    assert prompts2 == (GamePrompt("pit", 18, None),)
    state3, prompts3 = advance(state2, (ev("pit", _Pit(1, None)),), PLAN_B)
    assert state3.pit_event_laps == state2.pit_event_laps
    assert prompts3 == ()


def test_other_drivers_ignored_and_position_last_wins():
    state, prompts = advance(GAME_START, (ev("lap_started", _Lap(4, 15)), ev("pit", _Pit(4, 15))), PLAN_B)
    assert state == GAME_START
    assert prompts == ()
    state2, _ = advance(GAME_START, (ev("position", _Pos(1, 3)), ev("position", _Pos(1, 7))), PLAN_B)
    assert state2.last_position == 7


def test_pit_tie_lower_planned_lap_wins():
    plan = StrategyPlan(
        driver_number=1, compounds=("MEDIUM", "MEDIUM", "MEDIUM"), pit_laps=(5, 7), predicted_position=10
    )
    _state, prompts = advance(GAME_START, (ev("pit", _Pit(1, 6)),), plan)
    assert prompts == (GamePrompt("pit", 6, 5),)


def test_multi_window_duplicate_lap_starts():
    plan = StrategyPlan(
        driver_number=1, compounds=("MEDIUM", "MEDIUM", "MEDIUM"), pit_laps=(5, 6), predicted_position=10
    )
    state, prompts = advance(GAME_START, (ev("lap_started", _Lap(1, 5)),), plan)
    assert prompts == (GamePrompt("window", 5, 5),)
    _state2, prompts2 = advance(state, (ev("lap_started", _Lap(1, 5)),), plan)
    assert prompts2 == (GamePrompt("window", 5, 6),)


def test_inputs_never_mutated():
    events = (ev("lap_started", _Lap(1, 15)),)
    before = GAME_START
    advance(GAME_START, events, PLAN_B)
    assert before == GAME_START
    assert len(events) == 1


# ---- AC-4: actual outcome from the fixture ----


def test_actual_outcome_from_excerpt():
    session = load_session(EXCERPT_DIR)
    events = tuple(merge_events(session))
    state, _prompts = advance(GAME_START, events, PLAN_A)
    outcome = actual_outcome(session.stints, state, 1)
    assert outcome == ActualOutcome(("INTERMEDIATE", "MEDIUM", "MEDIUM"), (1, 14), (15,), 14)
    absent = actual_outcome(session.stints, state, 99)
    assert absent == ActualOutcome((), (), (), None)


# ---- AC-5: scoring ----

OUTCOME = ActualOutcome(("INTERMEDIATE", "MEDIUM", "MEDIUM"), (1, 14), (15,), 14)


def test_score_plan_a():
    breakdown = score_plan(PLAN_A, OUTCOME, decisions=(), prompts_total=0)
    assert breakdown == ScoreBreakdown(
        tyres=30, pit_laps=20, decisions=0, finish=5, total=55, decisions_matched=0, prompts_total=0
    )


def test_score_plan_b():
    breakdown = score_plan(PLAN_B, OUTCOME, decisions=(Decision(16, "pit"),), prompts_total=1)
    assert breakdown == ScoreBreakdown(
        tyres=5, pit_laps=0, decisions=5, finish=10, total=20, decisions_matched=1, prompts_total=1
    )


@pytest.mark.parametrize(
    ("plan", "outcome", "decisions", "prompts_total", "expected"),
    [
        # absent driver: -5 x 2 stints, no finish points
        (PLAN_B, ActualOutcome((), (), (), None), (), 0, (-10, 0, 0, 0, -10)),
        # unclassified: tyres match, pit |D|=1 -> PIT_CLOSE, finish 0
        (PLAN_B, ActualOutcome(("MEDIUM", "MEDIUM"), (15,), (15,), None), (), 0, (20, 5, 0, 0, 25)),
        # pit |D|=1 the other side -> PIT_CLOSE; finish exact
        (PLAN_B, ActualOutcome(("MEDIUM", "MEDIUM"), (17,), (17,), 14), (), 0, (20, 5, 0, 10, 35)),
        # pit |D|=2 -> 0
        (PLAN_B, ActualOutcome(("MEDIUM", "MEDIUM"), (18,), (18,), 14), (), 0, (20, 0, 0, 10, 30)),
        # stay matched (no pit events near 16)
        (PLAN_B, ActualOutcome(("MEDIUM", "MEDIUM"), (16,), (), 14), (Decision(16, "stay"),), 1, (20, 10, 5, 10, 45)),
        # stay missed (pitted at 16)
        (
            PLAN_B,
            ActualOutcome(("MEDIUM", "MEDIUM"), (16,), (16,), 14),
            (Decision(16, "stay"),),
            1,
            (20, 10, -5, 10, 35),
        ),
        # pit missed (no pit events)
        (PLAN_B, ActualOutcome(("MEDIUM", "MEDIUM"), (16,), (), 14), (Decision(16, "pit"),), 1, (20, 10, -5, 10, 35)),
        # unanswered prompt contributes 0
        (PLAN_B, ActualOutcome(("MEDIUM", "MEDIUM"), (16,), (16,), 14), (), 1, (20, 10, 0, 10, 40)),
        # |D|>2 finish branch: prediction P14 vs actual P1 -> 0 finish points
        (PLAN_B, ActualOutcome(("MEDIUM", "MEDIUM"), (16,), (16,), 1), (), 0, (20, 10, 0, 0, 30)),
        # negative total
        (PLAN_A, ActualOutcome((), (), (), None), (), 2, (-15, 0, 0, 0, -15)),
    ],
)
def test_score_full_breakdowns(plan, outcome, decisions, prompts_total, expected):
    b = score_plan(plan, outcome, decisions=decisions, prompts_total=prompts_total)
    assert (b.tyres, b.pit_laps, b.decisions, b.finish, b.total) == expected
    assert b.total == b.tyres + b.pit_laps + b.decisions + b.finish


def test_score_absent_driver_negative_tyres():
    b = score_plan(PLAN_B, ActualOutcome((), (), (), None), decisions=(), prompts_total=0)
    assert b.tyres == -5 * len(PLAN_B.compounds)
    assert b.finish == 0


def test_score_negative_total_possible():
    b = score_plan(PLAN_A, ActualOutcome((), (), (), None), decisions=(), prompts_total=2)
    assert b.total < 0


def test_decision_validation_rules():
    with pytest.raises(ValueError, match=r"decision references an unplanned lap"):
        score_plan(PLAN_B, OUTCOME, decisions=(Decision(99, "pit"),), prompts_total=1)
    with pytest.raises(ValueError, match=r"duplicate decision for planned lap"):
        score_plan(PLAN_B, OUTCOME, decisions=(Decision(16, "pit"), Decision(16, "stay")), prompts_total=2)
    with pytest.raises(ValueError, match=r"decisions cannot exceed prompts"):
        score_plan(PLAN_B, OUTCOME, decisions=(Decision(16, "pit"),), prompts_total=0)


# ---- AC-6: score rendering + derive script ----


def test_render_score_plan_b():
    b = score_plan(PLAN_B, OUTCOME, decisions=(Decision(16, "pit"),), prompts_total=1)
    assert render_score(PLAN_B, OUTCOME, b).splitlines() == [
        "Final score: 20",
        "Tyres: +5 (planned MEDIUM, MEDIUM · actual INTERMEDIATE, MEDIUM, MEDIUM)",
        "Pit laps: 0 (planned 16 · actual 1, 14)",
        "Decisions: +5 (1 of 1 matched)",
        "Finish: +10 (predicted P14 · actual P14)",
    ]


def test_render_score_plan_a():
    b = score_plan(PLAN_A, OUTCOME, decisions=(), prompts_total=0)
    assert render_score(PLAN_A, OUTCOME, b).splitlines() == [
        "Final score: 55",
        "Tyres: +30 (planned INTERMEDIATE, MEDIUM, MEDIUM · actual INTERMEDIATE, MEDIUM, MEDIUM)",
        "Pit laps: +20 (planned 1, 14 · actual 1, 14)",
        "Decisions: 0 (0 of 0 matched)",
        "Finish: +5 (predicted P12 · actual P14)",
    ]


def test_render_score_edges():
    empty = ActualOutcome((), (), (), None)
    b = score_plan(PLAN_B, empty, decisions=(), prompts_total=0)
    text = render_score(PLAN_B, empty, b)
    assert "—" in text
    assert "no classification observed" in text
    assert "-" in text.splitlines()[1]


def test_derive_game_literals_script():
    script = Path(__file__).resolve().parent.parent / "scripts" / "derive_game_literals.py"
    result = subprocess.run(  # noqa: S603 - our own script via sys.executable
        [sys.executable, "-I", "-S", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "MATCH VERDICT: SUCCESS" in result.stdout


def test_advance_benchmark():
    """AC-11 benchmark: one advance over 25,000 synthetic events < 1.0 s."""
    import time

    events = tuple(
        ev("position", _Pos(1, (i % 20) + 1)) if i % 2 else ev("lap_started", _Lap(1, (i % 70) + 1))
        for i in range(25_000)
    )
    start = time.perf_counter()
    advance(GAME_START, events, PLAN_A)
    assert time.perf_counter() - start < 1.0


def test_no_prompt_after_window_passed():
    """iter15 mutation killer: a lap start AFTER the planned window emits nothing."""
    _state, prompts = advance(GAME_START, (ev("lap_started", _Lap(1, 17)),), PLAN_B)
    assert prompts == ()
