import dataclasses
from datetime import UTC, datetime

import pytest

from pitwall.config import AppConfig, default_season


def test_frozen():
    config = AppConfig(season=2026, refresh_interval_s=10, db_path="data/pitwall.db")

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.season = 2027  # ty: ignore[invalid-assignment] - intentional frozen mutation check


@pytest.mark.parametrize(
    "season,refresh_interval_s",
    [
        (1949, 10),
        (2101, 10),
        (2026, 4),
    ],
)
def test_validation_rejects_bad_values(season, refresh_interval_s):
    with pytest.raises(ValueError) as exc_info:
        AppConfig(season=season, refresh_interval_s=refresh_interval_s)

    error_msg = str(exc_info.value)
    if refresh_interval_s < 5:
        assert "refresh_interval_s" in error_msg
    else:
        assert "season" in error_msg


def test_default_season_clock_injection():
    fixed_time = datetime(2026, 6, 10, 12, 0, 0, tzinfo=UTC)

    season = default_season(now=fixed_time)

    assert season == 2026


def test_live_mode_validation():
    # AppConfig(season=2026, live=True) valid
    config = AppConfig(season=2026, live=True)
    assert config.live is True

    # AppConfig(season=2026, live=True, replay_dir="x") raises ValueError
    with pytest.raises(ValueError) as exc_info:
        AppConfig(season=2026, live=True, replay_dir="x")
    assert "cannot enable live mode with replay_dir set" in str(exc_info.value)

    # default live is False
    config_default = AppConfig(season=2026)
    assert config_default.live is False
