"""Shared cell formatting primitives."""

EM_DASH = "—"


def format_points(points: float) -> str:
    """Locale-free championship points: whole floats drop the trailing .0.

    >>> format_points(156.0)
    '156'
    >>> format_points(7.5)
    '7.5'
    """
    return str(int(points)) if points == int(points) else str(points)


def safe_row(row: tuple) -> tuple:
    """Wrap string cells in rich Text so API data never parses as markup (SEC-1).

    Text stringifies to the plain value, so pinned str(cell) contracts survive.
    """
    import rich.text

    return tuple(rich.text.Text(cell) if isinstance(cell, str) else cell for cell in row)
