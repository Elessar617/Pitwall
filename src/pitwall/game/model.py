"""Strategy-game plan model (SPEC-12 D1): frozen, loudly validated."""

from dataclasses import dataclass

COMPOUNDS = ("SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET")
MAX_PLAN_STINTS = 8
MAX_PIT_LAP = 99
MAX_PREDICTED_POSITION = 99


@dataclass(frozen=True)
class StrategyPlan:
    driver_number: int
    compounds: tuple[str, ...]
    pit_laps: tuple[int, ...]
    predicted_position: int

    def __post_init__(self) -> None:
        # Defense in depth: the wizard validates incrementally, but the model
        # is the last gate before scoring consumes a plan.
        if not isinstance(self.driver_number, int) or self.driver_number <= 0:
            raise ValueError("driver_number must be a positive integer")  # noqa: TRY003 - spec-pinned message
        if not 1 <= len(self.compounds) <= MAX_PLAN_STINTS:
            raise ValueError("plan must have between 1 and 8 stints")  # noqa: TRY003 - spec-pinned message
        for compound in self.compounds:
            if compound not in COMPOUNDS:
                raise ValueError(f"unknown compound: {compound}")  # noqa: TRY003
        if len(self.pit_laps) != len(self.compounds) - 1:
            raise ValueError("pit_laps must have exactly one fewer entry than compounds")  # noqa: TRY003 - spec-pinned message
        for lap in self.pit_laps:
            if not 1 <= lap <= MAX_PIT_LAP:
                raise ValueError("pit lap must be between 1 and 99")  # noqa: TRY003 - spec-pinned message
        if any(b <= a for a, b in zip(self.pit_laps, self.pit_laps[1:], strict=False)):
            raise ValueError("pit laps must be strictly increasing")  # noqa: TRY003 - spec-pinned message
        if not 1 <= self.predicted_position <= MAX_PREDICTED_POSITION:
            raise ValueError("predicted position must be between 1 and 99")  # noqa: TRY003 - spec-pinned message


@dataclass(frozen=True)
class Decision:
    planned_lap: int
    choice: str

    def __post_init__(self) -> None:
        if self.choice not in ("pit", "stay"):
            raise ValueError("choice must be 'pit' or 'stay'")  # noqa: TRY003 - spec-pinned message


@dataclass(frozen=True)
class GamePrompt:
    kind: str
    lap: int
    planned_lap: int | None

    def __post_init__(self) -> None:
        if self.kind not in ("window", "pit"):
            raise ValueError("kind must be 'window' or 'pit'")  # noqa: TRY003 - spec-pinned message
