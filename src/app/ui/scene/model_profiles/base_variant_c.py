"""Профиль сцены: «Базовый вариант C» — base_variant_c.

Ручки масштаба — transform.scale_multiplier, transform.lift_ratio,
room_zone.*_scale (см. `industrial_machinery_unit` для описания).
"""

from __future__ import annotations


PROFILE: dict[str, object] = {
    "theme": {
        "floor_color": "#0b4852",
        "halo_color": "#06b6d4",
        "particles_color": "#a5f3fc",
        "rim_color": "#67e8f9",
        "fill_color": "#cffafe",
    },
    "transform": {
        "rotation_deg": {"x": 0.0, "y": 0.0, "z": 0.0},
        "scale_multiplier": 1.02,
        "lift_ratio": 0.0,
    },
    "room_zone": {
        "long_scale": 0.5,
        "vertical_scale": 0.34,
        "side_scale": 0.24,
    },
    "anchors": {
        "outdoor": {"long": 0.1, "vertical": 0.64, "side": -0.2},
        "filter": {"long": 0.26, "vertical": 0.64, "side": -0.08},
        "heater": {"long": 0.5, "vertical": 0.63, "side": 0.02},
        "fan": {"long": 0.7, "vertical": 0.64, "side": 0.12},
        "duct": {"long": 0.9, "vertical": 0.62, "side": 0.22},
        "room": {"long": 1.14, "vertical": 0.34, "side": 0.26},
        "room_sensor": {"long": 1.14, "vertical": 0.56, "side": 0.28},
    },
    "flows": {
        "outdoor_to_filter": [
            "outdoor",
            {"long": 0.18, "vertical": 0.64, "side": -0.14},
            "filter",
        ],
        "filter_to_heater": [
            "filter",
            {"long": 0.38, "vertical": 0.64, "side": -0.02},
            "heater",
        ],
        "heater_to_fan": [
            "heater",
            {"long": 0.6, "vertical": 0.64, "side": 0.08},
            "fan",
        ],
        "fan_to_room": [
            "fan",
            {"long": 0.82, "vertical": 0.62, "side": 0.18},
            "duct",
            {"anchor": "room", "vertical_delta": 0.05},
        ],
    },
    "camera": {
        "hero": {
            "distance": 1.8,
            "long": 0.98,
            "side": -0.56,
            "up": 0.46,
            "target": {"anchor": "heater"},
        },
        "service": {
            "distance": 1.74,
            "long": -1.0,
            "side": 0.48,
            "up": 0.5,
            "target": {"anchor": "fan", "vertical_delta": -0.02},
        },
        "top": {
            "distance": 1.5,
            "up": 1.58,
            "target": {"anchor": "heater", "vertical_delta": -0.02},
        },
    },
}
