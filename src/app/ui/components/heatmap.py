"""Heat map overlay component for temperature field visualization."""

from __future__ import annotations

import math
from typing import Sequence


def build_heatmap_svg(
    *,
    width: int,
    height: int,
    temperature_points: Sequence[tuple[float, float, float]],
    grid_resolution: int = 20,
    min_temp: float = 18.0,
    max_temp: float = 26.0,
    show_legend: bool = True,
    class_name: str = "heatmap",
) -> str:
    """
    Generate SVG heat map for temperature field visualization.

    Args:
        width: SVG width in pixels
        height: SVG height in pixels
        temperature_points: List of (x, y, temperature) tuples in normalized coords [0-1]
        grid_resolution: Number of grid cells per dimension
        min_temp: Minimum temperature for color scale (°C)
        max_temp: Maximum temperature for color scale (°C)
        show_legend: Whether to show color legend
        class_name: CSS class name for the SVG element

    Returns:
        SVG markup string with heat map visualization
    """
    if not temperature_points or len(temperature_points) < 2:
        return _empty_heatmap(width, height, class_name)

    # Generate grid cells with interpolated temperatures
    cells = []
    cell_width = width / grid_resolution
    cell_height = height / grid_resolution

    for row in range(grid_resolution):
        for col in range(grid_resolution):
            # Cell center in normalized coordinates
            x_norm = (col + 0.5) / grid_resolution
            y_norm = (row + 0.5) / grid_resolution

            # Interpolate temperature at this point
            temp = _interpolate_temperature(x_norm, y_norm, temperature_points)

            # Convert to color
            color = _temperature_to_color(temp, min_temp, max_temp)

            # Cell position in SVG coordinates
            x = col * cell_width
            y = row * cell_height

            cells.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" '
                f'width="{cell_width:.1f}" height="{cell_height:.1f}" '
                f'fill="{color}" opacity="0.6"/>'
            )

    # Build legend if requested
    legend = ""
    if show_legend:
        legend = _build_legend(width, height, min_temp, max_temp)

    # Build measurement points overlay
    points_overlay = _build_points_overlay(
        temperature_points, width, height, min_temp, max_temp
    )

    return (
        f'<svg class="{class_name}" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        f'<defs>'
        f'<filter id="heatmap-blur">'
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="3"/>'
        f'</filter>'
        f'</defs>'
        f'<g filter="url(#heatmap-blur)">{"".join(cells)}</g>'
        f"{points_overlay}"
        f"{legend}"
        f"</svg>"
    )


def _interpolate_temperature(
    x: float,
    y: float,
    points: Sequence[tuple[float, float, float]],
) -> float:
    """
    Interpolate temperature at (x, y) using inverse distance weighting (IDW).

    Args:
        x: X coordinate in normalized space [0-1]
        y: Y coordinate in normalized space [0-1]
        points: List of (x, y, temperature) measurement points

    Returns:
        Interpolated temperature in °C
    """
    # IDW parameters
    power = 2.0  # Distance decay power
    epsilon = 1e-6  # Small value to avoid division by zero

    weighted_sum = 0.0
    weight_sum = 0.0

    for px, py, temp in points:
        # Calculate distance
        dx = x - px
        dy = y - py
        distance = math.sqrt(dx * dx + dy * dy) + epsilon

        # Calculate weight (inverse distance)
        weight = 1.0 / (distance**power)

        weighted_sum += weight * temp
        weight_sum += weight

    return weighted_sum / weight_sum if weight_sum > 0 else 20.0


def _temperature_to_color(temp: float, min_temp: float, max_temp: float) -> str:
    """
    Convert temperature to color using blue-green-yellow-red gradient.

    Args:
        temp: Temperature in °C
        min_temp: Minimum temperature for scale
        max_temp: Maximum temperature for scale

    Returns:
        Hex color string
    """
    # Normalize temperature to [0, 1]
    t = (temp - min_temp) / (max_temp - min_temp)
    t = max(0.0, min(1.0, t))

    # Color gradient: blue -> cyan -> green -> yellow -> red
    if t < 0.25:
        # Blue to cyan
        ratio = t / 0.25
        r = 0
        g = int(128 + 127 * ratio)
        b = 255
    elif t < 0.5:
        # Cyan to green
        ratio = (t - 0.25) / 0.25
        r = 0
        g = 255
        b = int(255 * (1 - ratio))
    elif t < 0.75:
        # Green to yellow
        ratio = (t - 0.5) / 0.25
        r = int(255 * ratio)
        g = 255
        b = 0
    else:
        # Yellow to red
        ratio = (t - 0.75) / 0.25
        r = 255
        g = int(255 * (1 - ratio))
        b = 0

    return f"#{r:02x}{g:02x}{b:02x}"


def _build_legend(width: int, height: int, min_temp: float, max_temp: float) -> str:
    """Build color legend for temperature scale."""
    legend_width = 20
    legend_height = 120
    legend_x = width - legend_width - 10
    legend_y = 10

    # Generate gradient stops
    stops = []
    num_stops = 10
    for i in range(num_stops):
        t = i / (num_stops - 1)
        temp = min_temp + t * (max_temp - min_temp)
        color = _temperature_to_color(temp, min_temp, max_temp)
        offset = int(t * 100)
        stops.append(f'<stop offset="{offset}%" stop-color="{color}"/>')

    # Build legend
    return (
        f'<g class="heatmap-legend">'
        f'<defs>'
        f'<linearGradient id="temp-gradient" x1="0%" y1="100%" x2="0%" y2="0%">'
        f'{"".join(stops)}'
        f'</linearGradient>'
        f'</defs>'
        f'<rect x="{legend_x}" y="{legend_y}" '
        f'width="{legend_width}" height="{legend_height}" '
        f'fill="url(#temp-gradient)" stroke="#fff" stroke-width="1" opacity="0.9"/>'
        f'<text x="{legend_x + legend_width + 5}" y="{legend_y + 5}" '
        f'fill="#fff" font-size="10" font-family="monospace">{max_temp:.0f}°C</text>'
        f'<text x="{legend_x + legend_width + 5}" y="{legend_y + legend_height}" '
        f'fill="#fff" font-size="10" font-family="monospace">{min_temp:.0f}°C</text>'
        f'</g>'
    )


def _build_points_overlay(
    points: Sequence[tuple[float, float, float]],
    width: int,
    height: int,
    min_temp: float,
    max_temp: float,
) -> str:
    """Build overlay showing measurement point locations."""
    circles = []
    for px, py, temp in points:
        x = px * width
        y = py * height
        color = _temperature_to_color(temp, min_temp, max_temp)

        circles.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" '
            f'fill="{color}" stroke="#fff" stroke-width="1.5" opacity="0.9"/>'
        )

    return f'<g class="heatmap-points">{"".join(circles)}</g>'


def _empty_heatmap(width: int, height: int, class_name: str) -> str:
    """Return empty heat map placeholder."""
    return (
        f'<svg class="{class_name} heatmap--empty" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{width}" height="{height}" fill="#1e293b" opacity="0.3"/>'
        f'<text x="{width/2}" y="{height/2}" '
        f'text-anchor="middle" fill="#64748b" font-size="14" font-family="sans-serif">'
        f'Недостаточно данных для тепловой карты'
        f'</text>'
        f'</svg>'
    )
