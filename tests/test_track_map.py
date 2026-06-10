import time
from datetime import UTC, datetime

import pytest


def test_projection_literals(excerpt_dir):
    # AC-5: build_projection literals (x/y min/max, scale 127/19034, 273 distinct dots, dot_for the two pinned points)
    from pitwall.openf1.location import load_location
    from pitwall.screens.track_map import build_projection, dot_for

    points = load_location(excerpt_dir)
    proj = build_projection(points)

    assert proj.x_min == -2449.0
    assert proj.x_max == 3899.0
    assert proj.y_min == -2273.0
    assert proj.y_max == 16761.0
    assert proj.scale == 127 / 19034

    # dot_for literals
    assert dot_for(proj, 3231.0, 1807.0) == (72, 100)
    assert dot_for(proj, -472.0, 16521.0) == (48, 2)

    # Support method access as well
    if hasattr(proj, "dot_for"):
        assert proj.dot_for(3231.0, 1807.0) == (72, 100)
        assert proj.dot_for(-472.0, 16521.0) == (48, 2)

    # 273 distinct dots
    dots = set()
    for p in points:
        dots.add(dot_for(proj, p.x, p.y))
    assert len(dots) == 273


def test_outline_grid_pinned(excerpt_dir):
    # AC-5: build_outline equals the SPEC's pinned 32-line grid (101 non-blank cells)
    from pitwall.openf1.location import load_location
    from pitwall.screens.track_map import (
        MAP_GRID_HEIGHT,
        MAP_GRID_WIDTH,
        build_outline,
        build_projection,
    )

    points = load_location(excerpt_dir)
    proj = build_projection(points)
    outline = build_outline(points, proj)

    assert isinstance(outline, tuple)
    assert len(outline) == MAP_GRID_HEIGHT
    for line in outline:
        assert len(line) == MAP_GRID_WIDTH

    non_blank_cells = sum(1 for line in outline for char in line if char != "⠀")
    assert non_blank_cells == 101

    expected_grid = (
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠙⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡄⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢃⠸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠓⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⢠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⢁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠈⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠃⠀⠀⠀⠀⠈⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡼⠀⠀⠀⠀⠀⠀⢃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠇⠀⠀⠀⠀⠀⠀⠐⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡴⠒⠁⠀⠀⠀⠀⠀⠀⠀⠀⠣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢨⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢨⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢘⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠓⠒⠲⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⡅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡱⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠢⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢦⠀⠀⠀⠀⠀⠀⠀⠀⢐⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠰⢡⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⣀⠀⠀⠀⠀⠀⠀⢸⠐⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠲⢄⡀⠀⠀⠀⠸⣄⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠒⠤⢄⣀⣀⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
    )
    assert outline == expected_grid


def test_projection_edges():
    # AC-5: build_projection([]) raises ValueError; a single-point list yields exactly one non-blank cell
    from pitwall.openf1.models import LocationPoint
    from pitwall.screens.track_map import build_outline, build_projection

    with pytest.raises(ValueError):
        build_projection([])

    single_point = LocationPoint(
        date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC),
        driver_number=1,
        x=3231.0,
        y=1807.0,
    )
    proj = build_projection([single_point])
    outline = build_outline([single_point], proj)

    non_blank_cells = sum(1 for line in outline for char in line if char != "⠀")
    assert non_blank_cells == 1
    # single-point list yields exactly one non-blank cell at (28, 16) (dot (56, 64))
    # char cell (dot_col // 2, dot_row // 4) -> (56 // 2, 64 // 4) = (28, 16)
    assert outline[16][28] != "⠀"


def test_overlay_markers_pinned(excerpt_dir):
    # AC-6: overlay_markers per-tick cells (the six pinned (col,row) cells)
    from pitwall.openf1.location import LocationFeed, load_location
    from pitwall.screens.track_map import (
        MAP_GRID_HEIGHT,
        MAP_GRID_WIDTH,
        MARKER_GLYPH,
        build_outline,
        build_projection,
        overlay_markers,
    )

    points = load_location(excerpt_dir)
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
    expected_cells = [
        (36, 25),
        (29, 29),
        (22, 8),
        (33, 19),
        (22, 23),
        (24, 0),
    ]

    for ph, (expected_col, expected_row) in zip(playheads, expected_cells, strict=True):
        markers = feed.advance(ph)
        res = overlay_markers(outline, markers, proj)
        lines = res.split("\n")
        assert len(lines) == MAP_GRID_HEIGHT
        # Marker ● replacement
        assert lines[expected_row][expected_col] == MARKER_GLYPH

        # Outline unmutated (outline parameter is tuple and remains unchanged)
        assert outline == build_outline(points, proj)

        # Confirm other cells are unmodified
        for r in range(MAP_GRID_HEIGHT):
            for c in range(MAP_GRID_WIDTH):
                if (c, r) == (expected_col, expected_row):
                    assert lines[r][c] == MARKER_GLYPH
                else:
                    assert lines[r][c] == outline[r][c]


def test_overlay_edges(excerpt_dir):
    # AC-6: empty markers verbatim, multi-driver same-cell/different-cell/sort-order edges
    from pitwall.openf1.location import load_location
    from pitwall.openf1.models import LocationPoint
    from pitwall.screens.track_map import (
        MARKER_GLYPH,
        build_outline,
        build_projection,
        dot_for,
        overlay_markers,
    )

    points = load_location(excerpt_dir)
    proj = build_projection(points)
    outline = build_outline(points, proj)

    # Empty markers verbatim
    res_empty = overlay_markers(outline, {}, proj)
    assert res_empty == "\n".join(outline)

    # different-cell edge
    # Let's create two synthetic points that map to different cells
    p1 = LocationPoint(date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC), driver_number=1, x=-2449.0, y=-2273.0)
    p2 = LocationPoint(date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC), driver_number=2, x=3899.0, y=16761.0)

    # Project them
    dot1 = dot_for(proj, p1.x, p1.y)
    dot2 = dot_for(proj, p2.x, p2.y)
    cell1 = (dot1[0] // 2, dot1[1] // 4)
    cell2 = (dot2[0] // 2, dot2[1] // 4)
    assert cell1 != cell2

    res_diff = overlay_markers(outline, {1: p1, 2: p2}, proj)
    lines_diff = res_diff.split("\n")
    assert lines_diff[cell1[1]][cell1[0]] == MARKER_GLYPH
    assert lines_diff[cell2[1]][cell2[0]] == MARKER_GLYPH

    # same-cell edge
    # Let's create two synthetic points that map to the same cell
    p3 = LocationPoint(date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC), driver_number=3, x=3231.0, y=1807.0)
    p4 = LocationPoint(date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC), driver_number=4, x=3231.0, y=1807.0)
    dot3 = dot_for(proj, p3.x, p3.y)
    dot4 = dot_for(proj, p4.x, p4.y)
    cell3 = (dot3[0] // 2, dot3[1] // 4)
    cell4 = (dot4[0] // 2, dot4[1] // 4)
    assert cell3 == cell4

    res_same = overlay_markers(outline, {3: p3, 4: p4}, proj)
    lines_same = res_same.split("\n")
    assert lines_same[cell3[1]][cell3[0]] == MARKER_GLYPH
    # Count of MARKER_GLYPH in the grid
    marker_count = sum(line.count(MARKER_GLYPH) for line in lines_same)
    assert marker_count == 1

    # sort-order edge
    # To test sort order, we check that keys are processed in sorted driver_number order.
    # We trace property accesses on the points.
    log = []

    class TracePoint:
        def __init__(self, driver_number, x, y):
            self.driver_number = driver_number
            self._x = x
            self._y = y

        @property
        def x(self):
            log.append(f"x_{self.driver_number}")
            return self._x

        @property
        def y(self):
            log.append(f"y_{self.driver_number}")
            return self._y

    tp_low = TracePoint(10, -2449.0, -2273.0)
    tp_high = TracePoint(20, 3899.0, 16761.0)

    # Pass dict with unsorted order of keys
    overlay_markers(outline, {20: tp_high, 10: tp_low}, proj)

    # The property accesses should occur in sorted driver_number order (10 then 20)
    assert "10" in log[0] or "10" in log[1]
    assert "20" in log[-1] or "20" in log[-2]
    # Check that driver 10 reads happen before driver 20 reads
    idx_10 = max(i for i, val in enumerate(log) if "10" in val)
    idx_20 = min(i for i, val in enumerate(log) if "20" in val)
    assert idx_10 < idx_20


def test_outline_benchmark():
    # AC-12: build_projection + build_outline over 25,000 synthetic points < 2.0 s
    from pitwall.openf1.models import LocationPoint
    from pitwall.screens.track_map import MAP_GRID_HEIGHT, build_outline, build_projection

    points = [
        LocationPoint(
            date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC),
            driver_number=1,
            x=float(i % 100),
            y=float(i % 200),
        )
        for i in range(25000)
    ]
    start = time.perf_counter()
    proj = build_projection(points)
    outline = build_outline(points, proj)
    duration = time.perf_counter() - start
    assert len(outline) == MAP_GRID_HEIGHT
    assert duration < 2.0


def test_marker_cells_pinned(excerpt_dir):
    # AC-5: marker_cells reproducing today's pinned cells
    from pitwall.openf1.location import LocationFeed, load_location
    from pitwall.screens.track_map import (
        build_projection,
        marker_cells,
    )

    points = load_location(excerpt_dir)
    proj = build_projection(points)
    feed = LocationFeed(points)

    # tick-0 playhead
    ph_0 = datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC)
    markers_0 = feed.advance(ph_0)
    cells_0 = marker_cells(markers_0, proj)
    # reproduces today's pinned cell: (row=25, col=36)
    assert cells_0.get((25, 36)) == 1

    # final playhead
    ph_final = datetime(2026, 5, 24, 20, 32, 30, tzinfo=UTC)
    markers_final = feed.advance(ph_final)
    cells_final = marker_cells(markers_final, proj)
    # reproduces today's pinned cell: (row=0, col=24)
    assert cells_final.get((0, 24)) == 1


def test_marker_cells_collision(excerpt_dir):
    # AC-5: the higher-driver-number collision rule
    from pitwall.openf1.location import load_location
    from pitwall.openf1.models import LocationPoint
    from pitwall.screens.track_map import (
        build_projection,
        marker_cells,
    )

    points = load_location(excerpt_dir)
    proj = build_projection(points)

    # Two synthetic drivers mapping to the same cell: (3231.0, 1807.0) maps to (25, 36)
    p1 = LocationPoint(date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC), driver_number=10, x=3231.0, y=1807.0)
    p2 = LocationPoint(date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC), driver_number=20, x=3231.0, y=1807.0)

    # 1. Unsorted keys: driver 20 first, driver 10 second -> higher driver number (20) owns the cell
    res_unsorted = marker_cells({20: p2, 10: p1}, proj)
    assert res_unsorted.get((25, 36)) == 20

    # 2. Sorted keys: driver 10 first, driver 20 second -> higher driver number (20) owns the cell
    res_sorted = marker_cells({10: p1, 20: p2}, proj)
    assert res_sorted.get((25, 36)) == 20


def test_render_map_plain_equality(excerpt_dir):
    # AC-5: render_map(...).plain equality with overlay_markers
    from pitwall.openf1.location import LocationFeed, load_location
    from pitwall.screens.track_map import (
        build_outline,
        build_projection,
        overlay_markers,
        render_map,
    )

    points = load_location(excerpt_dir)
    proj = build_projection(points)
    outline = build_outline(points, proj)
    feed = LocationFeed(points)

    ph = datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC)
    markers = feed.advance(ph)

    expected_overlay = overlay_markers(outline, markers, proj)
    rendered = render_map(outline, markers, proj, styles={})
    assert rendered.plain == expected_overlay


def test_render_map_styled_span(excerpt_dir):
    # AC-5: the styled-span placement case (offset row*57+col, length 1)
    from pitwall.openf1.location import load_location
    from pitwall.openf1.models import LocationPoint
    from pitwall.screens.track_map import (
        build_outline,
        build_projection,
        render_map,
    )

    points = load_location(excerpt_dir)
    proj = build_projection(points)
    outline = build_outline(points, proj)

    # Synthetic 2-driver case with styles: driver 1 -> "#F47600", driver 2 -> ""
    # Pinned cell for 1: (3231.0, 1807.0) -> col 36, row 25
    # Pinned cell for 2: (-472.0, 16521.0) -> col 24, row 0
    p1 = LocationPoint(date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC), driver_number=1, x=3231.0, y=1807.0)
    p2 = LocationPoint(date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC), driver_number=2, x=-472.0, y=16521.0)

    styles = {1: "#F47600", 2: ""}
    rendered = render_map(outline, {1: p1, 2: p2}, proj, styles)

    # The Text carries exactly one styled span of length 1 at offset row * 57 + col for driver 1's cell and none for driver 2's.
    assert len(rendered.spans) == 1
    span = rendered.spans[0]
    assert span.start == 25 * 57 + 36
    assert span.end == 25 * 57 + 36 + 1
    assert span.style == "#F47600"


def test_render_map_off_grid_empty(excerpt_dir):
    # AC-5: off-grid/empty edges
    from pitwall.openf1.location import load_location
    from pitwall.openf1.models import LocationPoint
    from pitwall.screens.track_map import (
        build_outline,
        build_projection,
        render_map,
    )

    points = load_location(excerpt_dir)
    proj = build_projection(points)
    outline = build_outline(points, proj)

    # 1. Empty markers
    rendered_empty = render_map(outline, {}, proj, styles={})
    assert rendered_empty.plain == "\n".join(outline)
    assert len(rendered_empty.spans) == 0

    # 2. Off-grid marker (should not add any spans and not raise)
    p_off = LocationPoint(date=datetime(2026, 5, 24, 20, 30, 0, tzinfo=UTC), driver_number=1, x=1000000.0, y=1000000.0)
    rendered_off = render_map(outline, {1: p_off}, proj, styles={1: "#F47600"})
    assert len(rendered_off.spans) == 0
