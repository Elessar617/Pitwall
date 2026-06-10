"""Tests for shared cell formatting primitives."""

from pitwall.screens.cells import EM_DASH, format_points


def test_format_points_returns_expected_strings_for_pinned_literals():
    # Arrange
    # (Inputs are pinned float values)

    # Act & Assert
    assert format_points(156.0) == "156"
    assert format_points(90.0) == "90"
    assert format_points(0.0) == "0"
    assert format_points(7.5) == "7.5"
    assert format_points(33.5) == "33.5"


def test_em_dash_value_is_unicode_em_dash():
    # Arrange
    # (No arrangement needed)

    # Act
    val = EM_DASH

    # Assert
    assert val == "—"
