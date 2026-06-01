"""Tests for heat map SVG component."""

import pytest

from app.ui.components.heatmap import build_heatmap_svg


def test_heatmap_basic():
    """Test basic heat map generation."""
    points = [
        (0.2, 0.2, 18.0),  # Cold corner
        (0.8, 0.8, 24.0),  # Warm corner
        (0.5, 0.5, 21.0),  # Center
    ]
    svg = build_heatmap_svg(
        width=400,
        height=300,
        temperature_points=points,
        grid_resolution=10,
    )

    assert '<svg' in svg
    assert 'class="heatmap"' in svg
    assert 'width="400"' in svg
    assert 'height="300"' in svg
    assert '<rect' in svg
    assert 'fill="#' in svg


def test_heatmap_empty_points():
    """Test heat map with no temperature points."""
    svg = build_heatmap_svg(
        width=400,
        height=300,
        temperature_points=[],
        grid_resolution=10,
    )

    assert '<svg' in svg
    assert 'heatmap--empty' in svg
    assert 'Недостаточно данных' in svg


def test_heatmap_single_point():
    """Test heat map with single temperature point."""
    points = [(0.5, 0.5, 22.0)]
    svg = build_heatmap_svg(
        width=400,
        height=300,
        temperature_points=points,
        grid_resolution=10,
    )

    assert '<svg' in svg
    assert 'heatmap--empty' in svg


def test_heatmap_with_legend():
    """Test heat map with color legend."""
    points = [
        (0.2, 0.2, 18.0),
        (0.8, 0.8, 24.0),
    ]
    svg = build_heatmap_svg(
        width=400,
        height=300,
        temperature_points=points,
        show_legend=True,
    )

    assert '<svg' in svg
    assert 'heatmap-legend' in svg
    assert 'linearGradient' in svg
    assert '°C' in svg


def test_heatmap_without_legend():
    """Test heat map without legend."""
    points = [
        (0.2, 0.2, 18.0),
        (0.8, 0.8, 24.0),
    ]
    svg = build_heatmap_svg(
        width=400,
        height=300,
        temperature_points=points,
        show_legend=False,
    )

    assert '<svg' in svg
    assert 'heatmap-legend' not in svg


def test_heatmap_custom_temperature_range():
    """Test heat map with custom temperature range."""
    points = [
        (0.2, 0.2, 10.0),
        (0.8, 0.8, 30.0),
    ]
    svg = build_heatmap_svg(
        width=400,
        height=300,
        temperature_points=points,
        min_temp=10.0,
        max_temp=30.0,
        show_legend=True,
    )

    assert '<svg' in svg
    assert '10°C' in svg
    assert '30°C' in svg


def test_heatmap_grid_resolution():
    """Test heat map with different grid resolutions."""
    points = [
        (0.2, 0.2, 18.0),
        (0.8, 0.8, 24.0),
    ]

    # Low resolution
    svg_low = build_heatmap_svg(
        width=400,
        height=300,
        temperature_points=points,
        grid_resolution=5,
    )
    assert '<svg' in svg_low
    # Should have 5x5 = 25 cells
    assert svg_low.count('<rect') >= 25

    # High resolution
    svg_high = build_heatmap_svg(
        width=400,
        height=300,
        temperature_points=points,
        grid_resolution=20,
    )
    assert '<svg' in svg_high
    # Should have 20x20 = 400 cells
    assert svg_high.count('<rect') >= 400


def test_heatmap_measurement_points_overlay():
    """Test that measurement points are shown as circles."""
    points = [
        (0.2, 0.2, 18.0),
        (0.5, 0.5, 21.0),
        (0.8, 0.8, 24.0),
    ]
    svg = build_heatmap_svg(
        width=400,
        height=300,
        temperature_points=points,
    )

    assert '<svg' in svg
    assert 'heatmap-points' in svg
    assert '<circle' in svg
    # Should have 3 circles for 3 measurement points
    assert svg.count('<circle') == 3


def test_heatmap_blur_filter():
    """Test that Gaussian blur filter is applied."""
    points = [
        (0.2, 0.2, 18.0),
        (0.8, 0.8, 24.0),
    ]
    svg = build_heatmap_svg(
        width=400,
        height=300,
        temperature_points=points,
    )

    assert '<svg' in svg
    assert 'heatmap-blur' in svg
    assert 'feGaussianBlur' in svg
    assert 'filter="url(#heatmap-blur)"' in svg


def test_heatmap_custom_class():
    """Test heat map with custom CSS class."""
    points = [
        (0.2, 0.2, 18.0),
        (0.8, 0.8, 24.0),
    ]
    svg = build_heatmap_svg(
        width=400,
        height=300,
        temperature_points=points,
        class_name="custom-heatmap",
    )

    assert '<svg' in svg
    assert 'class="custom-heatmap"' in svg


def test_heatmap_temperature_interpolation():
    """Test that temperatures are interpolated across the grid."""
    # Create points at corners with different temperatures
    points = [
        (0.0, 0.0, 18.0),  # Bottom-left: cold
        (1.0, 0.0, 18.0),  # Bottom-right: cold
        (0.0, 1.0, 24.0),  # Top-left: warm
        (1.0, 1.0, 24.0),  # Top-right: warm
    ]
    svg = build_heatmap_svg(
        width=400,
        height=300,
        temperature_points=points,
        grid_resolution=10,
    )

    assert '<svg' in svg
    # Should have gradient of colors from cold (blue) to warm (red)
    assert 'fill="#' in svg
    # Check that multiple different colors are present
    assert svg.count('fill="#') > 10


def test_heatmap_extreme_temperatures():
    """Test heat map with temperatures outside normal range."""
    points = [
        (0.2, 0.2, 5.0),   # Very cold
        (0.8, 0.8, 35.0),  # Very hot
    ]
    svg = build_heatmap_svg(
        width=400,
        height=300,
        temperature_points=points,
        min_temp=0.0,
        max_temp=40.0,
    )

    assert '<svg' in svg
    assert '<rect' in svg
    # Should handle extreme values without errors
