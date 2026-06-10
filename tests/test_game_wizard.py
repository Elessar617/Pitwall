"""Strategy-game plan wizard state machine (SPEC-12 AC-2)."""

import pytest

from pitwall.game.model import StrategyPlan
from pitwall.game.wizard import draft_plan, draft_press, new_draft, render_draft, render_plan

DRIVERS = ((1, "NOR"), (4, "PIA"), (16, "LEC"))

PLAN_B = StrategyPlan(driver_number=1, compounds=("MEDIUM", "MEDIUM"), pit_laps=(16,), predicted_position=14)
PLAN_A = StrategyPlan(
    driver_number=1,
    compounds=("INTERMEDIATE", "MEDIUM", "MEDIUM"),
    pit_laps=(1, 14),
    predicted_position=12,
)


def press_all(draft, keys):
    for key in keys:
        draft = draft_press(draft, key)
    return draft


def test_constructor_sorts_and_rejects_empty():
    draft = new_draft(((16, "LEC"), (1, "NOR"), (4, "PIA")))
    assert render_draft(draft) == "Driver: 1 NOR · Up/Down select · Enter confirm"
    with pytest.raises(ValueError, match=r"drivers must not be empty"):
        new_draft(())


def test_driver_selection_wraps():
    draft = new_draft(DRIVERS)
    assert render_draft(draft) == "Driver: 1 NOR · Up/Down select · Enter confirm"
    draft = draft_press(draft, "down")
    assert render_draft(draft) == "Driver: 4 PIA · Up/Down select · Enter confirm"
    draft = press_all(draft, ["down", "down"])
    assert render_draft(draft) == "Driver: 1 NOR · Up/Down select · Enter confirm"
    draft = draft_press(new_draft(DRIVERS), "up")
    assert render_draft(draft) == "Driver: 16 LEC · Up/Down select · Enter confirm"


def test_tyre_entry_and_backspace():
    draft = press_all(new_draft(DRIVERS), ["enter"])
    assert render_draft(draft) == "Tyres: — · 1=S 2=M 3=H 4=I 5=W · Backspace undo · Enter confirm"
    draft = press_all(draft, ["2", "2"])
    assert render_draft(draft) == "Tyres: MEDIUM, MEDIUM · 1=S 2=M 3=H 4=I 5=W · Backspace undo · Enter confirm"
    draft = draft_press(draft, "backspace")
    assert render_draft(draft) == "Tyres: MEDIUM · 1=S 2=M 3=H 4=I 5=W · Backspace undo · Enter confirm"


def test_empty_tyres_invalid_and_ninth_ignored():
    draft = press_all(new_draft(DRIVERS), ["enter"])
    invalid = draft_press(draft, "enter")
    assert render_draft(invalid) == (
        "Tyres: — · 1=S 2=M 3=H 4=I 5=W · Backspace undo · Enter confirm"
        "\nInvalid: plan must have between 1 and 8 stints"
    )
    draft = press_all(draft, ["2"] * 8)
    eight = render_draft(draft)
    assert render_draft(draft_press(draft, "2")) == eight


def test_single_compound_skips_pit_step():
    draft = press_all(new_draft(DRIVERS), ["enter", "1", "enter"])
    assert render_draft(draft) == "Predicted finish: P— · digits · Backspace undo · Enter commit"
    draft = press_all(draft, ["1", "4", "enter"])
    plan = draft_plan(draft)
    assert plan is not None
    assert plan.pit_laps == ()


def test_pit_lap_entry_path():
    draft = press_all(new_draft(DRIVERS), ["enter", "2", "2", "enter"])
    assert render_draft(draft) == "Pit 1 of 1: lap — · digits · Backspace undo · Enter confirm"
    draft = press_all(draft, ["1", "6"])
    assert render_draft(draft) == "Pit 1 of 1: lap 16 · digits · Backspace undo · Enter confirm"
    third = draft_press(draft, "7")
    assert render_draft(third) == "Pit 1 of 1: lap 16 · digits · Backspace undo · Enter confirm"


def test_pit_lap_validations():
    draft = press_all(new_draft(DRIVERS), ["enter", "2", "2", "enter"])
    invalid = draft_press(draft, "enter")
    assert render_draft(invalid).endswith("\nInvalid: pit lap must be between 1 and 99")
    three = press_all(new_draft(DRIVERS), ["enter", "2", "2", "2", "enter", "1", "0", "enter"])
    second_low = press_all(three, ["9", "enter"])
    assert render_draft(second_low).endswith("\nInvalid: pit laps must be strictly increasing")


def test_predicted_and_commit():
    draft = press_all(new_draft(DRIVERS), ["enter", "2", "2", "enter", "1", "6", "enter"])
    assert render_draft(draft) == "Predicted finish: P— · digits · Backspace undo · Enter commit"
    draft = press_all(draft, ["1", "4"])
    assert render_draft(draft) == "Predicted finish: P14 · digits · Backspace undo · Enter commit"
    committed = draft_press(draft, "enter")
    assert draft_plan(committed) == PLAN_B
    assert draft_plan(draft_press(committed, "down")) == PLAN_B


def test_unknown_keys_never_change_state_and_precommit_none():
    draft = new_draft(DRIVERS)
    for key in ("x", "tab", "space"):
        assert render_draft(draft_press(draft, key)) == render_draft(draft)
    assert draft_plan(draft) is None
    mid = press_all(draft, ["enter", "2"])
    assert draft_plan(mid) is None


def test_render_plan_literals():
    assert render_plan(PLAN_B, "NOR") == "Plan — NOR · MEDIUM → MEDIUM · pit 16 · P14"
    assert render_plan(PLAN_A, "NOR") == "Plan — NOR · INTERMEDIATE → MEDIUM → MEDIUM · pit 1, 14 · P12"


def test_unknown_keys_in_later_steps_and_committed_render():
    draft = press_all(new_draft(DRIVERS), ["enter", "2", "2", "enter"])
    assert render_draft(draft_press(draft, "x")) == render_draft(draft)
    draft = press_all(draft, ["1", "6", "enter"])
    assert render_draft(draft_press(draft, "x")) == render_draft(draft)
    draft = press_all(draft, ["9", "9", "9"])
    assert render_draft(draft).startswith("Predicted finish: P99")
    draft = press_all(draft, ["backspace", "backspace", "1", "4"])
    committed = draft_press(draft, "enter")
    assert render_draft(committed) == "Plan — NOR · MEDIUM → MEDIUM · pit 16 · P14"


def test_pit_buffer_backspace_and_three_compound_flow():
    draft = press_all(new_draft(DRIVERS), ["enter", "2", "2", "2", "enter", "1", "backspace", "5", "enter"])
    assert render_draft(draft) == "Pit 2 of 2: lap — · digits · Backspace undo · Enter confirm"
    draft = press_all(draft, ["7", "enter", "1", "0", "enter"])
    plan = draft_plan(draft)
    assert plan is not None
    assert plan.pit_laps == (5, 7)


def test_unknown_key_in_tyres_step():
    draft = press_all(new_draft(DRIVERS), ["enter", "2"])
    assert render_draft(draft_press(draft, "x")) == render_draft(draft)
