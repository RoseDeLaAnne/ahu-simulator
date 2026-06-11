"""Tests for sparkline SVG component."""


from app.ui.components.sparkline import build_sparkline_svg


def test_sparkline_basic():
    """Test basic sparkline generation."""
    values = [10, 20, 15, 25, 30]
    svg = build_sparkline_svg(values=values, width=80, height=24)

    assert '<svg' in svg
    assert 'class="sparkline"' in svg
    assert 'width="80"' in svg
    assert 'height="24"' in svg
    assert '<path' in svg
    assert 'stroke=' in svg


def test_sparkline_empty_values():
    """Test sparkline with empty values."""
    svg = build_sparkline_svg(values=[], width=80, height=24)

    assert '<svg' in svg
    assert 'sparkline--empty' in svg
    assert 'stroke-dasharray' in svg  # Dashed line for empty state


def test_sparkline_single_value():
    """Test sparkline with single value."""
    svg = build_sparkline_svg(values=[42], width=80, height=24)

    assert '<svg' in svg
    assert 'sparkline--empty' in svg


def test_sparkline_flat_values():
    """Test sparkline with all equal values."""
    values = [20, 20, 20, 20]
    svg = build_sparkline_svg(values=values, width=80, height=24)

    assert '<svg' in svg
    assert 'sparkline--flat' in svg
    assert '<line' in svg


def test_sparkline_with_fill():
    """Test sparkline with area fill."""
    values = [10, 20, 15, 25, 30]
    svg = build_sparkline_svg(
        values=values,
        width=80,
        height=24,
        fill_color="#3b82f6",
    )

    assert '<svg' in svg
    # Should have two paths: one for fill, one for stroke
    assert svg.count('<path') == 2
    assert 'fill="#3b82f6"' in svg
    assert 'opacity="0.2"' in svg


def test_sparkline_with_dots():
    """Test sparkline with data point dots."""
    values = [10, 20, 15, 25, 30]
    svg = build_sparkline_svg(
        values=values,
        width=80,
        height=24,
        show_dots=True,
        dot_radius=2.0,
    )

    assert '<svg' in svg
    assert '<circle' in svg
    # Should have 5 circles for 5 data points
    assert svg.count('<circle') == 5
    assert 'r="2.0"' in svg


def test_sparkline_custom_colors():
    """Test sparkline with custom colors."""
    values = [10, 20, 15, 25, 30]
    svg = build_sparkline_svg(
        values=values,
        width=80,
        height=24,
        stroke_color="#ef4444",
        stroke_width=2.0,
    )

    assert '<svg' in svg
    assert 'stroke="#ef4444"' in svg
    assert 'stroke-width="2.0"' in svg


def test_sparkline_custom_class():
    """Test sparkline with custom CSS class."""
    values = [10, 20, 15, 25, 30]
    svg = build_sparkline_svg(
        values=values,
        width=80,
        height=24,
        class_name="custom-sparkline",
    )

    assert '<svg' in svg
    assert 'class="custom-sparkline"' in svg


def test_sparkline_negative_values():
    """Test sparkline with negative values."""
    values = [-10, -5, 0, 5, 10]
    svg = build_sparkline_svg(values=values, width=80, height=24)

    assert '<svg' in svg
    assert '<path' in svg
    # Should normalize and render correctly


def test_sparkline_large_range():
    """Test sparkline with large value range."""
    values = [0, 100, 50, 200, 150]
    svg = build_sparkline_svg(values=values, width=80, height=24)

    assert '<svg' in svg
    assert '<path' in svg


def test_sparkline_small_dimensions():
    """Test sparkline with small dimensions."""
    values = [10, 20, 15, 25, 30]
    svg = build_sparkline_svg(values=values, width=40, height=16)

    assert '<svg' in svg
    assert 'width="40"' in svg
    assert 'height="16"' in svg
    assert 'viewBox="0 0 40 16"' in svg
