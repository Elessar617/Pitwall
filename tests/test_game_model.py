"""Strategy-game plan model contracts (SPEC-12 AC-1)."""

import pytest

from pitwall.game.model import Decision, GamePrompt, StrategyPlan

PLAN_A = StrategyPlan(
    driver_number=1,
    compounds=("INTERMEDIATE", "MEDIUM", "MEDIUM"),
    pit_laps=(1, 14),
    predicted_position=12,
)
PLAN_B = StrategyPlan(
    driver_number=1,
    compounds=("MEDIUM", "MEDIUM"),
    pit_laps=(16,),
    predicted_position=14,
)


def test_plans_construct_and_expose_fields():
    assert PLAN_A.driver_number == 1
    assert PLAN_A.compounds == ("INTERMEDIATE", "MEDIUM", "MEDIUM")
    assert PLAN_A.pit_laps == (1, 14)
    assert PLAN_A.predicted_position == 12
    assert PLAN_B.compounds == ("MEDIUM", "MEDIUM")
    assert PLAN_B.pit_laps == (16,)
    assert PLAN_B.predicted_position == 14


def test_plan_is_frozen():
    with pytest.raises((AttributeError, TypeError), match=r"frozen|cannot assign|read-only"):
        PLAN_A.driver_number = 2  # ty: ignore[invalid-assignment] - intentional frozen mutation check


@pytest.mark.parametrize("bad", [0, -1])
def test_driver_number_positive(bad):
    with pytest.raises(ValueError, match=r"driver_number must be a positive integer"):
        StrategyPlan(driver_number=bad, compounds=("MEDIUM",), pit_laps=(), predicted_position=10)


@pytest.mark.parametrize("compounds", [(), ("MEDIUM",) * 9])
def test_stint_count_bounds(compounds):
    pit_laps = tuple(range(1, len(compounds))) if compounds else ()
    with pytest.raises(ValueError, match=r"plan must have between 1 and 8 stints"):
        StrategyPlan(driver_number=1, compounds=compounds, pit_laps=pit_laps, predicted_position=10)


def test_unknown_compound():
    with pytest.raises(ValueError, match=r"unknown compound: SUPERSOFT"):
        StrategyPlan(driver_number=1, compounds=("SUPERSOFT",), pit_laps=(), predicted_position=10)


def test_pit_lap_count_rule():
    with pytest.raises(ValueError, match=r"pit_laps must have exactly one fewer entry than compounds"):
        StrategyPlan(driver_number=1, compounds=("MEDIUM", "MEDIUM"), pit_laps=(), predicted_position=10)


@pytest.mark.parametrize("pit_laps", [(14, 14), (14, 1)])
def test_pit_laps_strictly_increasing(pit_laps):
    with pytest.raises(ValueError, match=r"pit laps must be strictly increasing"):
        StrategyPlan(
            driver_number=1,
            compounds=("MEDIUM", "MEDIUM", "MEDIUM"),
            pit_laps=pit_laps,
            predicted_position=10,
        )


@pytest.mark.parametrize("lap", [0, 100])
def test_pit_lap_bounds(lap):
    with pytest.raises(ValueError, match=r"pit lap must be between 1 and 99"):
        StrategyPlan(driver_number=1, compounds=("MEDIUM", "MEDIUM"), pit_laps=(lap,), predicted_position=10)


@pytest.mark.parametrize("pos", [0, 100])
def test_predicted_position_bounds(pos):
    with pytest.raises(ValueError, match=r"predicted position must be between 1 and 99"):
        StrategyPlan(driver_number=1, compounds=("MEDIUM",), pit_laps=(), predicted_position=pos)


def test_decision_validation():
    assert Decision(16, "pit").choice == "pit"
    assert Decision(16, "stay").choice == "stay"
    with pytest.raises(ValueError, match=r"choice must be 'pit' or 'stay'"):
        Decision(16, "later")


def test_game_prompt_kinds():
    assert GamePrompt("window", 15, 16).kind == "window"
    assert GamePrompt("pit", 15, 16).kind == "pit"
    with pytest.raises(ValueError, match=r"kind must be 'window' or 'pit'"):
        GamePrompt("flag", 15, 16)
