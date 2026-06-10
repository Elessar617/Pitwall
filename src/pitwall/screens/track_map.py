from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

import rich.text

MAP_GRID_WIDTH = 56
MAP_GRID_HEIGHT = 32
MARKER_GLYPH = "●"

# U+28xx Braille bit maps indexed by relative dot position (dx in [0, 1], dy in [0, 3]).
BIT_MAP = {
    (0, 0): 0x01,
    (0, 1): 0x02,
    (0, 2): 0x04,
    (1, 0): 0x08,
    (1, 1): 0x10,
    (1, 2): 0x20,
    (0, 3): 0x40,
    (1, 3): 0x80,
}


class LocationPoint(Protocol):
    """Protocol for location coordinate objects."""

    x: float
    y: float


@dataclass(frozen=True)
class MapProjection:
    """Calculated projection parameters for mapping track coordinates to screen coordinates."""

    x_min: float
    x_max: float
    y_min: float
    y_max: float
    scale: float
    offset_x: float
    offset_y: float

    def dot_for(self, x: float, y: float) -> tuple[int, int]:
        """Map track coordinates (x, y) to a dot grid cell (col, row)."""
        # Invariant: Maps floating point F1 coordinates to integer dot grid.
        # Banker's rounding via round() is used to minimize coordinate drift.
        dot_col = round((x - self.x_min) * self.scale + self.offset_x)
        dot_row = round((self.y_max - y) * self.scale + self.offset_y)
        return dot_col, dot_row


def dot_for(proj: MapProjection, x: float, y: float) -> tuple[int, int]:
    """Map track coordinates (x, y) to a dot grid cell (col, row) using projection."""
    return proj.dot_for(x, y)


def build_projection(points: Sequence[LocationPoint]) -> MapProjection:
    """Build MapProjection bounding box and scale over all points."""
    # Safety Check: empty list is a ValueError.
    if not points:
        raise ValueError("Cannot build projection from empty points list")  # noqa: TRY003

    x_values = [p.x for p in points]
    y_values = [p.y for p in points]
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)

    span_x = x_max - x_min
    span_y = y_max - y_min

    # Guard: prevent division by zero for degenerate single-point lists.
    scale = min(111.0 / max(span_x, 1.0), 127.0 / max(span_y, 1.0))
    offset_x = (111.0 - span_x * scale) / 2.0
    offset_y = (127.0 - span_y * scale) / 2.0

    return MapProjection(
        x_min=float(x_min),
        x_max=float(x_max),
        y_min=float(y_min),
        y_max=float(y_max),
        scale=scale,
        offset_x=offset_x,
        offset_y=offset_y,
    )


def build_outline(points: Sequence[LocationPoint], proj: MapProjection) -> tuple[str, ...]:
    """Generate the static track outline character grid using Braille characters."""
    # Loop Bound: bounded by MAP_GRID_HEIGHT (32 rows) and MAP_GRID_WIDTH (56 columns).
    # Space complexity: 32x56 integer cell bit masks.
    grid = [[0 for _ in range(MAP_GRID_WIDTH)] for _ in range(MAP_GRID_HEIGHT)]

    # Loop Bound: bounded by len(points) (up to 25,000 points).
    # Invariant: x and y coordinates map to grid cells within [0, 55] and [0, 31].
    for p in points:
        dot_col, dot_row = proj.dot_for(p.x, p.y)
        col = dot_col // 2
        row = dot_row // 4
        dx = dot_col % 2
        dy = dot_row % 4
        if 0 <= col < MAP_GRID_WIDTH and 0 <= row < MAP_GRID_HEIGHT:
            grid[row][col] |= BIT_MAP[(dx, dy)]

    lines = []
    # Loop Bound: 32 rows.
    for r in range(MAP_GRID_HEIGHT):
        row_chars = []
        # Loop Bound: 56 columns.
        for c in range(MAP_GRID_WIDTH):
            row_chars.append(chr(0x2800 + grid[r][c]))
        lines.append("".join(row_chars))

    return tuple(lines)


def marker_cells(
    markers: Mapping[int, LocationPoint],
    proj: MapProjection,
) -> dict[tuple[int, int], int]:
    """Map cell coordinates (row, col) to the owning driver_number, handling collisions."""
    cells = {}
    for driver_number in sorted(markers.keys()):
        pt = markers[driver_number]
        dot_col, dot_row = proj.dot_for(pt.x, pt.y)
        col = dot_col // 2
        row = dot_row // 4
        if 0 <= col < MAP_GRID_WIDTH and 0 <= row < MAP_GRID_HEIGHT:
            cells[(row, col)] = driver_number
    return cells


def overlay_markers(
    outline: tuple[str, ...],
    markers: Mapping[int, LocationPoint],
    proj: MapProjection,
) -> str:
    """Overlay active driver position markers U+25CF on top of the track outline."""
    grid = [list(line) for line in outline]
    cells = marker_cells(markers, proj)
    for row, col in cells:
        grid[row][col] = MARKER_GLYPH
    return "\n".join("".join(row) for row in grid)


def render_map(
    outline: tuple[str, ...],
    markers: Mapping[int, LocationPoint],
    proj: MapProjection,
    styles: Mapping[int, str],
) -> rich.text.Text:
    """Render track map with active driver position markers, returning a styled rich.text.Text."""
    plain_overlay = overlay_markers(outline, markers, proj)
    text = rich.text.Text(plain_overlay)
    cells = marker_cells(markers, proj)
    for (row, col), driver_number in cells.items():
        style = styles.get(driver_number, "")
        if style:
            offset = row * 57 + col
            text.stylize(style, offset, offset + 1)
    return text
