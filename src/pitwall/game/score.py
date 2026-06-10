"""Strategy-game fold, outcome extraction, scoring, rendering (SPEC-12 D2-D4)."""

from dataclasses import dataclass
from typing import Any

from pitwall.game.model import Decision, GamePrompt, StrategyPlan

PIT_TOLERANCE_LAPS = 1
COMPOUND_MATCH_POINTS = 10
STINT_COUNT_PENALTY = 5
PIT_EXACT_POINTS = 10
PIT_CLOSE_POINTS = 5
DECISION_MATCH_POINTS = 5
DECISION_MISS_PENALTY = 5
CLASSIFICATION_EXACT_POINTS = 10
CLASSIFICATION_CLOSE_POINTS = 5


@dataclass(frozen=True)
class GameState:
    prompted: frozenset[int]
    last_position: int | None
    pit_event_laps: tuple[int, ...]


GAME_START = GameState(frozenset(), None, ())


@dataclass(frozen=True)
class ActualOutcome:
    compounds: tuple[str, ...]
    pit_laps: tuple[int, ...]
    pit_event_laps: tuple[int, ...]
    final_position: int | None


@dataclass(frozen=True)
class ScoreBreakdown:
    tyres: int
    pit_laps: int
    decisions: int
    finish: int
    total: int
    decisions_matched: int
    prompts_total: int


def _nearest_planned_lap(event_lap: int, pit_laps: tuple[int, ...]) -> int | None:
    """Closest planned lap within PIT_TOLERANCE_LAPS; ties resolve to the lower lap."""
    best: int | None = None
    # Loop bound: len(pit_laps) <= MAX_PLAN_STINTS - 1 (PoT #2).
    for planned in pit_laps:
        delta = abs(event_lap - planned)
        if delta > PIT_TOLERANCE_LAPS:
            continue
        if best is None or delta < abs(event_lap - best) or (delta == abs(event_lap - best) and planned < best):
            best = planned
    return best


def advance(state: GameState, events: tuple[Any, ...], plan: StrategyPlan) -> tuple[GameState, tuple[GamePrompt, ...]]:
    """Fold one tick's events into game state; pure, inputs unmutated."""
    prompted = set(state.prompted)
    last_position = state.last_position
    pit_event_laps = list(state.pit_event_laps)
    prompts: list[GamePrompt] = []

    # Loop bound: one tick's event count (PoT #2).
    for event in events:
        payload = event.payload
        if getattr(payload, "driver_number", None) != plan.driver_number:
            continue
        if event.kind == "position":
            last_position = payload.position
        elif event.kind == "pit":
            # An un-attributable stop (no lap number) cannot map to a planned
            # lap or score later; skipping it is safe and loud-free by design.
            if payload.lap_number is None:
                continue
            pit_event_laps.append(payload.lap_number)
            prompts.append(
                GamePrompt("pit", payload.lap_number, _nearest_planned_lap(payload.lap_number, plan.pit_laps))
            )
        elif event.kind == "lap_started":
            lap = payload.lap_number
            # Lowest unprompted planned lap whose window {L-1, L} contains this
            # lap: L-1 gives one lap of warning; L covers lap-data gaps.
            for planned in sorted(plan.pit_laps):
                if planned not in prompted and lap in (planned - 1, planned):
                    prompted.add(planned)
                    prompts.append(GamePrompt("window", lap, planned))
                    break

    new_state = GameState(frozenset(prompted), last_position, tuple(pit_event_laps))
    return new_state, tuple(prompts)


def actual_outcome(stints: list[Any], state: GameState, driver_number: int) -> ActualOutcome:
    """The driver's observed outcome: stint compounds, boundary laps, pits, classification."""
    driver_stints = sorted((s for s in stints if s.driver_number == driver_number), key=lambda s: s.stint_number)
    if not driver_stints:
        return ActualOutcome((), (), (), None)
    compounds = tuple(s.compound if s.compound is not None else "?" for s in driver_stints)
    pit_laps = tuple(s.lap_end for s in driver_stints[:-1])
    return ActualOutcome(compounds, pit_laps, state.pit_event_laps, state.last_position)


def _validate_decisions(plan: StrategyPlan, decisions: tuple[Decision, ...], prompts_total: int) -> None:
    seen: set[int] = set()
    # Loop bound: len(decisions) <= prompts_total (PoT #2).
    for decision in decisions:
        if decision.planned_lap not in plan.pit_laps:
            raise ValueError("decision references an unplanned lap")  # noqa: TRY003 - spec-pinned message
        if decision.planned_lap in seen:
            raise ValueError("duplicate decision for planned lap")  # noqa: TRY003 - spec-pinned message
        seen.add(decision.planned_lap)
    if len(decisions) > prompts_total:
        raise ValueError("decisions cannot exceed prompts")  # noqa: TRY003 - spec-pinned message


def score_plan(
    plan: StrategyPlan,
    actual: ActualOutcome,
    decisions: tuple[Decision, ...],
    prompts_total: int,
) -> ScoreBreakdown:
    """The single pinned formula (D3); total always equals the component sum."""
    _validate_decisions(plan, decisions, prompts_total)

    tyres = sum(
        COMPOUND_MATCH_POINTS
        for i in range(min(len(plan.compounds), len(actual.compounds)))
        if plan.compounds[i] == actual.compounds[i]
    )
    tyres -= STINT_COUNT_PENALTY * abs(len(plan.compounds) - len(actual.compounds))

    pit_points = 0
    # Loop bound: min plan/actual pit counts (PoT #2).
    for planned, observed in zip(plan.pit_laps, actual.pit_laps, strict=False):
        delta = abs(planned - observed)
        if delta == 0:
            pit_points += PIT_EXACT_POINTS
        elif delta == 1:
            pit_points += PIT_CLOSE_POINTS

    decision_points = 0
    matched = 0
    for decision in decisions:
        actual_pitted = any(abs(e - decision.planned_lap) <= PIT_TOLERANCE_LAPS for e in actual.pit_event_laps)
        if (decision.choice == "pit") == actual_pitted:
            decision_points += DECISION_MATCH_POINTS
            matched += 1
        else:
            decision_points -= DECISION_MISS_PENALTY

    if actual.final_position is None:
        finish = 0
    else:
        delta = abs(plan.predicted_position - actual.final_position)
        if delta == 0:
            finish = CLASSIFICATION_EXACT_POINTS
        elif delta <= 2:
            finish = CLASSIFICATION_CLOSE_POINTS
        else:
            finish = 0

    total = tyres + pit_points + decision_points + finish
    return ScoreBreakdown(tyres, pit_points, decision_points, finish, total, matched, prompts_total)


def _signed(n: int) -> str:
    return f"{n:+d}" if n else "0"


def _seq(values: tuple) -> str:
    return ", ".join(str(v) for v in values) if values else "—"


def render_score(plan: StrategyPlan, actual: ActualOutcome, breakdown: ScoreBreakdown) -> str:
    """Exactly five pinned lines (D4)."""
    finish_actual = (
        f"actual P{actual.final_position}" if actual.final_position is not None else "no classification observed"
    )
    return "\n".join(
        (
            f"Final score: {breakdown.total}",
            f"Tyres: {_signed(breakdown.tyres)} (planned {_seq(plan.compounds)} · actual {_seq(actual.compounds)})",
            f"Pit laps: {_signed(breakdown.pit_laps)} (planned {_seq(plan.pit_laps)} · actual {_seq(actual.pit_laps)})",
            f"Decisions: {_signed(breakdown.decisions)} ({breakdown.decisions_matched} of {breakdown.prompts_total} matched)",
            f"Finish: {_signed(breakdown.finish)} (predicted P{plan.predicted_position} · {finish_actual})",
        )
    )
