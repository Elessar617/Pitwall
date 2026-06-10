import dataclasses
from datetime import UTC, datetime

from pitwall.cache.db import DEFAULT_DB_PATH

# Season validation boundaries defined by the F1 championship start (1950)
# and a reasonable future limit (2100) to catch input errors.
MIN_SEASON: int = 1950
MAX_SEASON: int = 2100

# Refresh interval constraints. A minimum of 5 seconds is enforced
# to protect the API endpoint from rate limits/excessive traffic.
MIN_REFRESH_INTERVAL_S: int = 5
DEFAULT_REFRESH_INTERVAL_S: int = 30

DEFAULT_REPLAY_SPEED: float = 60.0
MIN_REPLAY_SPEED: float = 1.0
MAX_REPLAY_SPEED: float = 600.0


@dataclasses.dataclass(frozen=True)
class AppConfig:
    """Configuration for the Pitwall application.

    Invariants:
        season: must be in [1950, 2100]
        refresh_interval_s: must be >= 5
        replay_speed: must be in [1.0, 600.0]
    """

    season: int
    refresh_interval_s: int = DEFAULT_REFRESH_INTERVAL_S
    db_path: str = DEFAULT_DB_PATH
    replay_dir: str | None = None
    replay_speed: float = DEFAULT_REPLAY_SPEED
    live: bool = False

    def __post_init__(self) -> None:
        if not (MIN_SEASON <= self.season <= MAX_SEASON):
            raise ValueError(  # noqa: TRY003
                f"season must be between {MIN_SEASON} and {MAX_SEASON}"
            )
        if self.refresh_interval_s < MIN_REFRESH_INTERVAL_S:
            raise ValueError(  # noqa: TRY003
                f"refresh_interval_s must be at least {MIN_REFRESH_INTERVAL_S}"
            )
        if not (MIN_REPLAY_SPEED <= self.replay_speed <= MAX_REPLAY_SPEED):
            raise ValueError(  # noqa: TRY003
                f"replay_speed must be between {MIN_REPLAY_SPEED} and {MAX_REPLAY_SPEED}"
            )
        if self.live and self.replay_dir is not None:
            raise ValueError("cannot enable live mode with replay_dir set")  # noqa: TRY003


def default_season(now: datetime | None = None) -> int:
    """Determine the default season based on the current UTC year."""
    if now is None:
        now = datetime.now(UTC)
    return now.year
