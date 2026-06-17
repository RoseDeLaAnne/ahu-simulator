"""Профиль сцены: «Базовый вариант A» — base_variant_a.

Ручки масштаба — transform.scale_multiplier, transform.lift_ratio,
room_zone.*_scale (см. `industrial_machinery_unit` для описания).
"""

from __future__ import annotations


PROFILE: dict[str, object] = {
    "theme": {
        "floor_color": "#4b2618",
        "halo_color": "#fb923c",
        "particles_color": "#fed7aa",
        "rim_color": "#fdba74",
        "fill_color": "#ffedd5",
    },
    "transform": {
        "rotation_deg": {"x": 0.0, "y": 0.0, "z": 0.0},
        "scale_multiplier": 1.04,
        "lift_ratio": 0.01,
    },
    "room_zone": {
        "long_scale": 0.56,
        "vertical_scale": 0.34,
        "side_scale": 0.26,
    },
    "anchors": {
        "outdoor": {"long": 0.1, "vertical": 0.66, "side": -0.22},
        "filter": {"long": 0.28, "vertical": 0.65, "side": -0.08},
        "heater": {"long": 0.5, "vertical": 0.63, "side": 0.04},
        "fan": {"long": 0.7, "vertical": 0.64, "side": 0.16},
        "duct": {"long": 0.9, "vertical": 0.62, "side": 0.24},
        "room": {"long": 1.16, "vertical": 0.34, "side": 0.28},
        "room_sensor": {"long": 1.16, "vertical": 0.58, "side": 0.3},
    },
    "flows": {
        "outdoor_to_filter": [
            "outdoor",
            {"long": 0.18, "vertical": 0.66, "side": -0.18},
            "filter",
        ],
        "filter_to_heater": [
            "filter",
            {"long": 0.38, "vertical": 0.65, "side": -0.02},
            {"long": 0.44, "vertical": 0.64, "side": 0.02},
            "heater",
        ],
        "heater_to_fan": [
            "heater",
            {"long": 0.62, "vertical": 0.64, "side": 0.1},
            "fan",
        ],
        "fan_to_room": [
            "fan",
            {"long": 0.82, "vertical": 0.63, "side": 0.2},
            "duct",
            {"anchor": "room", "vertical_delta": 0.05},
        ],
    },
    "effects": {
        "intake_aura": {"anchor": "outdoor", "scale": 1.12},
        "filter_dust": {"anchor": "filter", "scale": 0.96},
        "heater_field": {"anchor": "heater", "scale": 1.18},
    },
    "camera": {
        "hero": {
            "distance": 1.82,
            "long": 1.02,
            "side": -0.58,
            "up": 0.46,
            "target": {"anchor": "heater"},
        },
        "service": {
            "distance": 1.74,
            "long": -1.02,
            "side": 0.52,
            "up": 0.5,
            "target": {"anchor": "fan", "vertical_delta": -0.03},
        },
        "top": {
            "distance": 1.52,
            "up": 1.58,
            "target": {"anchor": "heater", "vertical_delta": -0.04},
        },
    },
}
