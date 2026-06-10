import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import rich.text

from pitwall.openf1.models import LocationPoint, SessionDriver, Stint


@dataclass(frozen=True)
class TowerView:
    key: str
    label: str
    lo: int | None
    hi: int | None


VIEWS = (
    TowerView("all", "all", None, None),
    TowerView("lead", "lead fight", 1, 5),
    TowerView("podium", "podium fight", 1, 4),
    TowerView("points", "points fight", 8, 12),
)


def style_for_team_colour(colour: str | None) -> str:
    """Resolve CSS color style string for team_colour."""
    if colour and re.fullmatch(r"[0-9a-fA-F]{6}", colour):
        return f"#{colour}"
    return ""


def driver_styles(drivers: list[SessionDriver]) -> dict[int, str]:
    """Map driver_number -> style_for_team_colour."""
    return {d.driver_number: style_for_team_colour(d.team_colour) for d in drivers}


def format_interval(val: float | str | None) -> str:
    """Format interval/gap value per AC-8 rules."""
    if val is None:
        return "—"
    if isinstance(val, (int, float)):
        if float(val) == 0.0:
            return "—"
        return f"+{val:.3f}"
    return str(val)


def format_lap_time(val: float | None) -> str:
    """Format lap time in minutes and seconds per AC-8 rules."""
    if val is None:
        return "—"
    if val >= 60.0:
        m = int(val // 60)
        s = val % 60
        return f"{m}:{s:06.3f}"
    return f"{val:.3f}"


def tyre_for(driver_number: int, current_lap: int | None, stints: list[Stint]) -> str:
    """Select the correct tyre compound letter for a driver per D4 rules."""
    if current_lap is None:
        return "—"

    driver_stints = [s for s in stints if s.driver_number == driver_number]

    if not driver_stints:
        return "—"

    matching_stints = [s for s in driver_stints if s.lap_start <= current_lap <= s.lap_end]
    if matching_stints:
        best_stint = max(matching_stints, key=lambda s: s.lap_start)
    else:
        older_stints = [s for s in driver_stints if s.lap_start <= current_lap]
        if older_stints:
            best_stint = max(older_stints, key=lambda s: s.lap_start)
        else:
            return "—"

    if not best_stint.compound:
        return "—"
    return best_stint.compound[0].upper()


def build_tower_rows(
    state: tuple[
        dict[int, Any],
        dict[int, tuple[Any, Any]],
        dict[int, Any],
        dict[int, Any],
    ],
    drivers: list[SessionDriver],
    stints: list[Stint],
) -> list[tuple[str, ...]]:
    """Build and format rows sorted by (position is None, position, driver_number)."""
    positions, intervals, last_laps, current_laps = state
    rows = []

    for driver in drivers:
        drv_num = driver.driver_number
        pos_val = positions.get(drv_num)
        int_val, gap_val = intervals.get(drv_num, (None, None))
        last_val = last_laps.get(drv_num)
        current_lap = current_laps.get(drv_num)

        tyre = tyre_for(drv_num, current_lap, stints)

        pos_str = str(pos_val) if pos_val is not None else "—"
        drv_str = driver.name_acronym
        int_str = format_interval(int_val)
        gap_str = format_interval(gap_val)
        last_str = format_lap_time(last_val)

        rows.append((pos_val, drv_num, (pos_str, drv_str, int_str, gap_str, last_str, tyre)))

    rows.sort(key=lambda x: (x[0] is None, x[0], x[1]))
    return [x[2] for x in rows]


def build_view_rows(
    state: tuple[
        dict[int, Any],
        dict[int, tuple[Any, Any]],
        dict[int, Any],
        dict[int, Any],
    ],
    drivers: list[SessionDriver],
    stints: list[Stint],
    view: TowerView,
    styles: Mapping[int, str],
) -> list[tuple]:
    """Build view rows filtered by position bounds, Drv cell styled as rich.text.Text."""
    positions, intervals, last_laps, current_laps = state
    rows = []

    for driver in drivers:
        drv_num = driver.driver_number
        if drv_num not in positions and view.key != "all":
            continue
        pos_val = positions.get(drv_num)
        int_val, gap_val = intervals.get(drv_num, (None, None))
        last_val = last_laps.get(drv_num)
        current_lap = current_laps.get(drv_num)

        admitted = True if view.key == "all" else pos_val is not None and view.lo <= pos_val <= view.hi

        if not admitted:
            continue

        tyre = tyre_for(drv_num, current_lap, stints)

        pos_str = str(pos_val) if pos_val is not None else "—"
        style = styles.get(drv_num, "")
        drv_text = rich.text.Text(driver.name_acronym, style=style)
        # SEC-1: every string cell wraps in Text so no API field parses as markup.
        cells = (
            rich.text.Text(pos_str),
            drv_text,
            rich.text.Text(format_interval(int_val)),
            rich.text.Text(format_interval(gap_val)),
            rich.text.Text(format_lap_time(last_val)),
            rich.text.Text(tyre),
        )
        rows.append((pos_val, drv_num, cells))

    rows.sort(key=lambda x: (x[0] is None, x[0], x[1]))
    return [x[2] for x in rows]


def filter_markers(
    markers: Mapping[int, LocationPoint],
    positions: Mapping[int, int | None],
    view: TowerView,
) -> dict[int, LocationPoint]:
    """Filter markers to only include those admitted by the view."""
    if view.key == "all":
        return dict(markers)

    filtered = {}
    for drv_num, point in markers.items():
        pos_val = positions.get(drv_num)
        if pos_val is not None and view.lo is not None and view.hi is not None and view.lo <= pos_val <= view.hi:
            filtered[drv_num] = point
    return filtered
