"""Plan wizard: a pure key-driven state machine (SPEC-12 D5)."""

from dataclasses import dataclass, replace

from pitwall.game.model import MAX_PLAN_STINTS, StrategyPlan

_COMPOUND_KEYS = {"1": "SOFT", "2": "MEDIUM", "3": "HARD", "4": "INTERMEDIATE", "5": "WET"}
_TYRE_LEGEND = "1=S 2=M 3=H 4=I 5=W"


@dataclass(frozen=True)
class PlanDraft:
    drivers: tuple[tuple[int, str], ...]
    step: str  # driver | tyres | pits | predicted | committed
    driver_index: int
    compounds: tuple[str, ...]
    pit_laps: tuple[int, ...]
    buffer: str
    error: str
    plan: StrategyPlan | None


def new_draft(drivers: tuple[tuple[int, str], ...]) -> PlanDraft:
    if not drivers:
        raise ValueError("drivers must not be empty")  # noqa: TRY003 - spec-pinned message
    ordered = tuple(sorted(drivers, key=lambda d: d[0]))
    return PlanDraft(ordered, "driver", 0, (), (), "", "", None)


def draft_plan(draft: PlanDraft) -> StrategyPlan | None:
    return draft.plan


def _commit(draft: PlanDraft) -> PlanDraft:
    """Validate via the model (single source of truth); invalid -> error line."""
    try:
        plan = StrategyPlan(
            driver_number=draft.drivers[draft.driver_index][0],
            compounds=draft.compounds,
            pit_laps=draft.pit_laps,
            predicted_position=int(draft.buffer) if draft.buffer else 0,
        )
    except ValueError as exc:
        return replace(draft, error=str(exc))
    return replace(draft, step="committed", buffer="", error="", plan=plan)


def _press_pits(draft: PlanDraft) -> PlanDraft:
    lap = int(draft.buffer) if draft.buffer else 0
    if not 1 <= lap <= 99:
        return replace(draft, error="pit lap must be between 1 and 99")
    if draft.pit_laps and lap <= draft.pit_laps[-1]:
        return replace(draft, error="pit laps must be strictly increasing")
    pit_laps = (*draft.pit_laps, lap)
    if len(pit_laps) < len(draft.compounds) - 1:
        return replace(draft, pit_laps=pit_laps, buffer="", error="")
    return replace(draft, step="predicted", pit_laps=pit_laps, buffer="", error="")


def _press_driver(draft: PlanDraft, key: str) -> PlanDraft:
    count = len(draft.drivers)
    if key == "down":
        return replace(draft, driver_index=(draft.driver_index + 1) % count)
    if key == "up":
        return replace(draft, driver_index=(draft.driver_index - 1) % count)
    if key == "enter":
        return replace(draft, step="tyres", error="")
    return draft


def _press_tyres(draft: PlanDraft, key: str) -> PlanDraft:
    if key in _COMPOUND_KEYS:
        if len(draft.compounds) >= MAX_PLAN_STINTS:
            return draft
        return replace(draft, compounds=(*draft.compounds, _COMPOUND_KEYS[key]), error="")
    if key == "backspace":
        return replace(draft, compounds=draft.compounds[:-1], error="")
    if key == "enter":
        if not draft.compounds:
            return replace(draft, error="plan must have between 1 and 8 stints")
        step = "predicted" if len(draft.compounds) == 1 else "pits"
        return replace(draft, step=step, buffer="", error="")
    return draft


def _press_buffered(draft: PlanDraft, key: str, on_enter) -> PlanDraft:
    """Shared digit-buffer handling for the pit-lap and predicted steps."""
    if key.isdigit():
        if len(draft.buffer) >= 2:
            return draft
        return replace(draft, buffer=draft.buffer + key, error="")
    if key == "backspace":
        return replace(draft, buffer=draft.buffer[:-1], error="")
    if key == "enter":
        return on_enter(draft)
    return draft


def draft_press(draft: PlanDraft, key: str) -> PlanDraft:
    """Pure transition; unknown keys leave the draft unchanged."""
    if draft.step == "driver":
        return _press_driver(draft, key)
    if draft.step == "tyres":
        return _press_tyres(draft, key)
    if draft.step == "pits":
        return _press_buffered(draft, key, _press_pits)
    if draft.step == "predicted":
        return _press_buffered(draft, key, _commit)
    return draft


def render_draft(draft: PlanDraft) -> str:
    if draft.step == "driver":
        num, acronym = draft.drivers[draft.driver_index]
        line = f"Driver: {num} {acronym} · Up/Down select · Enter confirm"
    elif draft.step == "tyres":
        tyres = ", ".join(draft.compounds) if draft.compounds else "—"
        line = f"Tyres: {tyres} · {_TYRE_LEGEND} · Backspace undo · Enter confirm"
    elif draft.step == "pits":
        total = len(draft.compounds) - 1
        line = (
            f"Pit {len(draft.pit_laps) + 1} of {total}: lap {draft.buffer or '—'}"
            " · digits · Backspace undo · Enter confirm"
        )
    elif draft.step == "predicted":
        line = f"Predicted finish: P{draft.buffer or '—'} · digits · Backspace undo · Enter commit"
    else:
        num, acronym = draft.drivers[draft.driver_index]
        line = render_plan(draft.plan, acronym) if draft.plan else ""
    if draft.error:
        return f"{line}\nInvalid: {draft.error}"
    return line


def render_plan(plan: StrategyPlan, acronym: str) -> str:
    laps = ", ".join(str(lap) for lap in plan.pit_laps) if plan.pit_laps else "—"
    compounds = " → ".join(plan.compounds)
    return f"Plan — {acronym} · {compounds} · pit {laps} · P{plan.predicted_position}"
