import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import rich.text

from pitwall.openf1.location import LocationFeed
from pitwall.openf1.models import LocationPoint, SessionDriver
from pitwall.openf1.replay import load_session, merge_events
from pitwall.screens.live_timing import (
    build_tower_rows,
    fold_events,
)
from pitwall.screens.live_views import (
    VIEWS,
    TowerView,
    build_view_rows,
    driver_styles,
    filter_markers,
    style_for_team_colour,
)


# AC-4: (a) style_for_team_colour literals
def test_style_for_team_colour():
    assert style_for_team_colour("F47600") == "#F47600"
    assert style_for_team_colour("00d7b6") == "#00d7b6"
    assert style_for_team_colour(None) == ""
    assert style_for_team_colour("") == ""
    assert style_for_team_colour("F4760") == ""
    assert style_for_team_colour("GGGGGG") == ""
    assert style_for_team_colour("F47600AA") == ""


# AC-4: (b) the VIEWS tuple exactly per D5
def test_views_pinned():
    assert len(VIEWS) == 4
    # VIEWS = (TowerView("all", "all", None, None), TowerView("lead", "lead fight", 1, 5), TowerView("podium", "podium fight", 1, 4), TowerView("points", "points fight", 8, 12))
    assert isinstance(VIEWS[0], TowerView)
    assert VIEWS[0].key == "all"
    assert VIEWS[0].label == "all"
    assert VIEWS[0].lo is None
    assert VIEWS[0].hi is None

    assert isinstance(VIEWS[1], TowerView)
    assert VIEWS[1].key == "lead"
    assert VIEWS[1].label == "lead fight"
    assert VIEWS[1].lo == 1
    assert VIEWS[1].hi == 5

    assert isinstance(VIEWS[2], TowerView)
    assert VIEWS[2].key == "podium"
    assert VIEWS[2].label == "podium fight"
    assert VIEWS[2].lo == 1
    assert VIEWS[2].hi == 4

    assert isinstance(VIEWS[3], TowerView)
    assert VIEWS[3].key == "points"
    assert VIEWS[3].label == "points fight"
    assert VIEWS[3].lo == 8
    assert VIEWS[3].hi == 12


# AC-4: (c) build_view_rows over the full-fold end state with driver_styles
def test_view_rows_end_state(excerpt_dir):
    session = load_session(excerpt_dir)
    events = merge_events(session)
    state = fold_events(events)

    # driver_styles helper
    styles = driver_styles(session.drivers)
    assert styles[1] == "#F47600"
    assert styles[3] == "#4781D7"
    assert styles[63] == "#00D7B6"

    # 1. View: all (the pinned 22-row table with per-team Text styles)
    rows_all = build_view_rows(state, session.drivers, session.stints, VIEWS[0], styles)
    assert len(rows_all) == 22

    expected_rows = [
        ("1", "RUS", "—", "—", "1:16.545", "S"),
        ("2", "ANT", "+0.506", "+0.506", "1:16.531", "S"),
        ("3", "VER", "+5.048", "+5.491", "1:16.088", "S"),
        ("4", "HAM", "+0.826", "+6.317", "1:16.068", "S"),
        ("5", "LEC", "+6.480", "+12.792", "1:16.553", "S"),
        ("6", "HAD", "+0.645", "+13.437", "1:16.499", "S"),
        ("7", "COL", "—", "+32.599", "1:17.292", "M"),
        ("8", "LAW", "+4.920", "+37.318", "1:17.801", "M"),
        ("9", "GAS", "+8.545", "+45.310", "1:17.569", "M"),
        ("10", "BEA", "+1.860", "+47.152", "1:18.120", "S"),
        ("11", "SAI", "+12.608", "+59.528", "1:17.544", "M"),
        ("12", "ALO", "+2.315", "+61.828", "1:20.409", "S"),
        ("13", "OCO", "+0.409", "+62.237", "1:38.391", "M"),
        ("14", "NOR", "+2.521", "+64.706", "1:23.114", "M"),
        ("15", "HUL", "+0.364", "+65.070", "1:19.039", "S"),
        ("16", "BOR", "+5.412", "+70.038", "1:17.752", "S"),
        ("17", "PIA", "+13.730", "+1 LAP", "1:17.308", "M"),
        ("18", "PER", "+12.148", "+1 LAP", "1:24.198", "M"),
        ("19", "STR", "+7.365", "+1 LAP", "1:22.036", "S"),
        ("20", "BOT", "+28.684", "+1 LAP", "1:19.225", "M"),
        ("21", "ALB", "—", "—", "—", "S"),
        ("22", "LIN", "—", "—", "—", "M"),
    ]

    for row, expected in zip(rows_all, expected_rows, strict=True):
        assert len(row) == 6
        assert str(row[1]) == expected[1]
        assert str(row[0]) == expected[0]
        assert str(row[2]) == expected[2]
        assert str(row[3]) == expected[3]
        assert str(row[4]) == expected[4]
        assert str(row[5]) == expected[5]

        assert isinstance(row[1], rich.text.Text)
        d_num = next(d.driver_number for d in session.drivers if d.name_acronym == expected[1])
        assert row[1].style == styles.get(d_num, "")

    # 2. View: lead (rows 1-5 with pinned styles)
    rows_lead = build_view_rows(state, session.drivers, session.stints, VIEWS[1], styles)
    assert len(rows_lead) == 5
    lead_acronyms = ["RUS", "ANT", "VER", "HAM", "LEC"]
    lead_styles = ["#00D7B6", "#00D7B6", "#4781D7", "#ED1131", "#ED1131"]
    for row, expected_acr, expected_style in zip(rows_lead, lead_acronyms, lead_styles, strict=True):
        assert str(row[1]) == expected_acr
        assert isinstance(row[1], rich.text.Text)
        assert row[1].style == expected_style

    # 3. View: podium (rows 1-4)
    rows_podium = build_view_rows(state, session.drivers, session.stints, VIEWS[2], styles)
    assert len(rows_podium) == 4
    podium_acronyms = ["RUS", "ANT", "VER", "HAM"]
    for row, expected_acr in zip(rows_podium, podium_acronyms, strict=True):
        assert str(row[1]) == expected_acr
        assert isinstance(row[1], rich.text.Text)

    # 4. View: points (rows 8-12 LAW/GAS/BEA/SAI/ALO with pinned styles)
    rows_points = build_view_rows(state, session.drivers, session.stints, VIEWS[3], styles)
    assert len(rows_points) == 5
    points_acronyms = ["LAW", "GAS", "BEA", "SAI", "ALO"]
    points_styles = ["#6C98FF", "#00A1E8", "#9C9FA2", "#1868DB", "#229971"]
    for row, expected_acr, expected_style in zip(rows_points, points_acronyms, points_styles, strict=True):
        assert str(row[1]) == expected_acr
        assert isinstance(row[1], rich.text.Text)
        assert row[1].style == expected_style

    # AC-4: (d) build_tower_rows unchanged + re-export works
    orig_rows = build_tower_rows(state, session.drivers, session.stints)
    assert orig_rows == expected_rows


# AC-4: (e) synthetic edge cases
def test_view_rows_edges():
    # 3 classified, ties, None positions, missing colour
    drivers = [
        SessionDriver(
            driver_number=1, name_acronym="NOR", full_name="Lando Norris", team_name="McLaren", team_colour="F47600"
        ),
        SessionDriver(
            driver_number=3, name_acronym="VER", full_name="Max Verstappen", team_name="Red Bull", team_colour="4781D7"
        ),
        SessionDriver(
            driver_number=16, name_acronym="LEC", full_name="Charles Leclerc", team_name="Ferrari", team_colour="ED1131"
        ),
        SessionDriver(
            driver_number=44, name_acronym="HAM", full_name="Lewis Hamilton", team_name="Ferrari", team_colour=None
        ),
        SessionDriver(
            driver_number=63, name_acronym="RUS", full_name="George Russell", team_name="Mercedes", team_colour=""
        ),
    ]

    styles = {1: "#F47600", 3: "#4781D7", 16: "#ED1131", 44: "", 63: ""}

    # 1. 3 classified (lead & podium return exactly 3, points returns 0)
    state_3: tuple[
        dict[int, int | None],
        dict[int, tuple[float | str | None, float | str | None]],
        dict[int, float | None],
        dict[int, int | None],
    ] = ({1: 1, 3: 2, 16: 3}, {}, {}, {})
    rows_lead = build_view_rows(state_3, drivers, [], VIEWS[1], styles)
    assert len(rows_lead) == 3
    assert [str(r[1]) for r in rows_lead] == ["NOR", "VER", "LEC"]

    rows_podium = build_view_rows(state_3, drivers, [], VIEWS[2], styles)
    assert len(rows_podium) == 3
    assert [str(r[1]) for r in rows_podium] == ["NOR", "VER", "LEC"]

    rows_points = build_view_rows(state_3, drivers, [], VIEWS[3], styles)
    assert len(rows_points) == 0

    # 2. ties (NOR and VER tied at position 2, LEC at position 1) -> ordered by driver_number
    state_ties: tuple[
        dict[int, int | None],
        dict[int, tuple[float | str | None, float | str | None]],
        dict[int, float | None],
        dict[int, int | None],
    ] = ({1: 2, 3: 2, 16: 1}, {}, {}, {})
    rows_ties = build_view_rows(state_ties, drivers, [], VIEWS[1], styles)
    assert len(rows_ties) == 3
    assert [str(r[1]) for r in rows_ties] == ["LEC", "NOR", "VER"]

    # 3. None positions (appear in 'all' sorted last, but not in bounded views)
    state_none: tuple[
        dict[int, int | None],
        dict[int, tuple[float | str | None, float | str | None]],
        dict[int, float | None],
        dict[int, int | None],
    ] = ({1: 1, 3: None, 16: None}, {}, {}, {})
    rows_all = build_view_rows(state_none, drivers, [], VIEWS[0], styles)
    assert len(rows_all) == 5
    assert [str(r[1]) for r in rows_all] == ["NOR", "VER", "LEC", "HAM", "RUS"]

    rows_lead_none = build_view_rows(state_none, drivers, [], VIEWS[1], styles)
    assert len(rows_lead_none) == 1
    assert str(rows_lead_none[0][1]) == "NOR"

    # 4. missing colour (team_colour=None, team_colour="" -> style "")
    state_colours: tuple[
        dict[int, int | None],
        dict[int, tuple[float | str | None, float | str | None]],
        dict[int, float | None],
        dict[int, int | None],
    ] = ({1: 1, 44: 2, 63: 3}, {}, {}, {})
    rows_colours = build_view_rows(state_colours, drivers, [], VIEWS[0], styles)
    assert len(rows_colours) == 5
    assert str(rows_colours[0][1]) == "NOR"
    assert rows_colours[0][1].style == "#F47600"
    assert str(rows_colours[1][1]) == "HAM"
    assert rows_colours[1][1].style == ""
    assert str(rows_colours[2][1]) == "RUS"
    assert rows_colours[2][1].style == ""

    # 5. missing positions completely (adversary C1 regression)
    # 3 SessionDrivers, positions {1: 1} only, view all -> ALL 3 rows with the position-less two sorted last (driver_number order)
    # ALSO pin that bounded views still exclude them.
    drivers_c1 = [
        SessionDriver(1, "AAA", "A", "Team A"),
        SessionDriver(2, "BBB", "B", "Team B"),
        SessionDriver(3, "CCC", "C", "Team C"),
    ]
    state_c1: tuple[
        dict[int, int | None],
        dict[int, tuple[float | str | None, float | str | None]],
        dict[int, float | None],
        dict[int, int | None],
    ] = ({1: 1}, {}, {}, {})
    rows_all_c1 = build_view_rows(state_c1, drivers_c1, [], VIEWS[0], {})
    assert len(rows_all_c1) == 3
    assert [str(r[1]) for r in rows_all_c1] == ["AAA", "BBB", "CCC"]

    rows_lead_c1 = build_view_rows(state_c1, drivers_c1, [], VIEWS[1], {})
    assert len(rows_lead_c1) == 1
    assert str(rows_lead_c1[0][1]) == "AAA"

    rows_podium_c1 = build_view_rows(state_c1, drivers_c1, [], VIEWS[2], {})
    assert len(rows_podium_c1) == 1
    assert str(rows_podium_c1[0][1]) == "AAA"

    rows_points_c1 = build_view_rows(state_c1, drivers_c1, [], VIEWS[3], {})
    assert len(rows_points_c1) == 0


# AC-4: (f) filter_markers rules
def test_filter_markers():
    p1 = LocationPoint(date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC), driver_number=1, x=1.0, y=2.0)
    p3 = LocationPoint(date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC), driver_number=3, x=3.0, y=4.0)
    p16 = LocationPoint(date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC), driver_number=16, x=5.0, y=6.0)

    markers = {1: p1, 3: p3, 16: p16}
    positions = {1: 1, 3: 6, 16: None}

    # view 'all' passes every marker through (including one whose driver has no position)
    res_all = filter_markers(markers, positions, VIEWS[0])
    assert res_all == markers
    assert res_all is not markers  # not mutated/copied

    # bounded view 'lead' (1 to 5) -> driver 1 (P1) kept, driver 3 (P6) excluded, driver 16 (None) excluded
    res_lead = filter_markers(markers, positions, VIEWS[1])
    assert res_lead == {1: p1}

    # Input mappings not mutated
    assert markers == {1: p1, 3: p3, 16: p16}
    assert positions == {1: 1, 3: 6, 16: None}


# AC-6: subprocess test for scripts/derive_view_literals.py
def test_derive_view_literals_script():
    script = Path(__file__).resolve().parent.parent / "scripts" / "derive_view_literals.py"
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-I", "-S", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "MATCH VERDICT: SUCCESS" in result.stdout


# AC-11 benchmark
def test_render_benchmark(excerpt_dir):
    from pitwall.openf1.location import load_location_all
    from pitwall.screens.track_map import build_outline, build_projection, render_map

    start = time.perf_counter()
    points = load_location_all(excerpt_dir)
    proj = build_projection(points)
    outline = build_outline(points, proj)
    feed = LocationFeed(points)

    playheads = [
        datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 30, 30, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 31, 0, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 31, 30, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 32, 0, tzinfo=UTC),
        datetime(2026, 5, 24, 20, 32, 30, tzinfo=UTC),
    ]

    styles = {d.driver_number: f"#{d.team_colour}" if d.team_colour else "" for d in load_session(excerpt_dir).drivers}

    for ph in playheads:
        markers = feed.advance(ph)
        render_map(outline, markers, proj, styles)

    duration = time.perf_counter() - start
    assert duration < 1.0
