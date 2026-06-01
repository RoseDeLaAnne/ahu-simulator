"""SVG sparkline component for inline trend visualization."""

from __future__ import annotations

from typing import Sequence


def build_sparkline_svg(
    *,
    values: Sequence[float],
    width: int = 80,
    height: int = 24,
    stroke_width: float = 1.5,
    stroke_color: str = "#64748b",
    fill_color: str | None = None,
    show_dots: bool = False,
    dot_radius: float = 2.0,
    class_name: str = "sparkline",
) -> str:
    """
    Generate inline SVG sparkline for trend visualization.

    Args:
        values: Sequence of numeric values to plot
        width: SVG width in pixels
        height: SVG height in pixels
        stroke_width: Line stroke width
        stroke_color: Line stroke color (CSS color)
        fill_color: Optional fill color for area under curve
        show_dots: Whether to show dots at data points
        dot_radius: Radius of dots if show_dots=True
        class_name: CSS class name for the SVG element

    Returns:
        SVG markup string
    """
    if not values or len(values) < 2:
        return _empty_sparkline(width, height, class_name)

    # Normalize values to fit in viewport
    min_val = min(values)
    max_val = max(values)
    value_range = max_val - min_val

    if value_range == 0:
        # Flat line - all values are the same
        return _flat_sparkline(width, height, class_name, stroke_color, stroke_width)

    # Add padding
    padding = 4
    plot_width = width - 2 * padding
    plot_height = height - 2 * padding

    # Calculate points
    x_step = plot_width / (len(values) - 1)
    points = []

    for i, value in enumerate(values):
        x = padding + i * x_step
        # Invert y because SVG y-axis goes down
        normalized = (value - min_val) / value_range
        y = padding + plot_height * (1 - normalized)
        points.append((x, y))

    # Build path
    path_d = _build_path(points)

    # Build area path if fill requested
    area_path = ""
    if fill_color:
        area_d = _build_area_path(points, height, padding)
        area_path = f'<path d="{area_d}" fill="{fill_color}" opacity="0.2"/>'

    # Build dots if requested
    dots = ""
    if show_dots:
        dots_list = [
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{dot_radius}" '
            f'fill="{stroke_color}" opacity="0.8"/>'
            for x, y in points
        ]
        dots = "".join(dots_list)

    return (
        f'<svg class="{class_name}" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        f"{area_path}"
        f'<path d="{path_d}" fill="none" stroke="{stroke_color}" '
        f'stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"/>'
        f"{dots}"
        f"</svg>"
    )


def _build_path(points: list[tuple[float, float]]) -> str:
    """Build SVG path data from points."""
    if not points:
        return ""

    path_parts = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]

    for x, y in points[1:]:
        path_parts.append(f"L {x:.1f} {y:.1f}")

    return " ".join(path_parts)


def _build_area_path(
    points: list[tuple[float, float]], height: int, padding: int
) -> str:
    """Build SVG area path (filled region under curve)."""
    if not points:
        return ""

    baseline_y = height - padding

    # Start at bottom-left
    path_parts = [f"M {points[0][0]:.1f} {baseline_y}"]

    # Go up to first point
    path_parts.append(f"L {points[0][0]:.1f} {points[0][1]:.1f}")

    # Follow the curve
    for x, y in points[1:]:
        path_parts.append(f"L {x:.1f} {y:.1f}")

    # Go down to baseline at last point
    path_parts.append(f"L {points[-1][0]:.1f} {baseline_y}")

    # Close path
    path_parts.append("Z")

    return " ".join(path_parts)


def _empty_sparkline(width: int, height: int, class_name: str) -> str:
    """Return empty sparkline placeholder."""
    return (
        f'<svg class="{class_name} sparkline--empty" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        f'<line x1="4" y1="{height/2}" x2="{width-4}" y2="{height/2}" '
        f'stroke="#94a3b8" stroke-width="1" stroke-dasharray="2,2" opacity="0.3"/>'
        f"</svg>"
    )


def _flat_sparkline(
    width: int, height: int, class_name: str, stroke_color: str, stroke_width: float
) -> str:
    """Return flat line sparkline (all values equal)."""
    y = height / 2
    return (
        f'<svg class="{class_name} sparkline--flat" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        f'<line x1="4" y1="{y}" x2="{width-4}" y2="{y}" '
        f'stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round"/>'
        f"</svg>"
    )
