"""Профиль сцены: «Базовый классический» — base_classic.

Ручки масштаба — transform.scale_multiplier, transform.lift_ratio,
room_zone.*_scale (см. `industrial_machinery_unit` для описания).
"""

from __future__ import annotations


PROFILE: dict[str, object] = {
    "theme": {
        "floor_color": "#143f39",
        "halo_color": "#22c55e",
        "particles_color": "#bbf7d0",
        "rim_color": "#86efac",
        "fill_color": "#ecfccb",
    },
    "room_zone": {
        "long_scale": 0.48,
        "vertical_scale": 0.3,
        "side_scale": 0.24,
    },
    "anchors": {
        "outdoor": {"long": 0.08, "vertical": 0.62, "side": -0.16},
        "filter": {"long": 0.23, "vertical": 0.62, "side": -0.06},
        "heater": {"long": 0.46, "vertical": 0.6, "side": 0.0},
        "fan": {"long": 0.66, "vertical": 0.62, "side": 0.1},
        "duct": {"long": 0.88, "vertical": 0.6, "side": 0.2},
        "room": {"long": 1.12, "vertical": 0.32, "side": 0.24},
        "room_sensor": {"long": 1.12, "vertical": 0.55, "side": 0.26},
    },
    "flows": {
        "outdoor_to_filter": [
            "outdoor",
            {"long": 0.14, "vertical": 0.62, "side": -0.12},
            "filter",
        ],
        "filter_to_heater": [
            "filter",
            {"long": 0.34, "vertical": 0.61, "side": -0.02},
            {"long": 0.4, "vertical": 0.6, "side": 0.0},
            "heater",
        ],
        "heater_to_fan": [
            "heater",
            {"long": 0.56, "vertical": 0.6, "side": 0.04},
            "fan",
        ],
        "fan_to_room": [
            "fan",
            {"long": 0.8, "vertical": 0.61, "side": 0.14},
            "duct",
            {"anchor": "room", "vertical_delta": 0.04},
        ],
    },
    "effects": {
        "intake_aura": {"anchor": "outdoor", "scale": 1.08},
        "filter_dust": {"anchor": "filter", "scale": 1.02},
        "heater_field": {"anchor": "heater", "scale": 1.08},
    },
    "camera": {
        "hero": {
            "distance": 1.72,
            "long": 0.94,
            "side": -0.52,
            "up": 0.42,
            "target": {"anchor": "heater", "vertical_delta": -0.02},
        },
        "service": {
            "distance": 1.68,
            "long": -0.96,
            "side": 0.42,
            "up": 0.46,
            "target": {"anchor": "fan", "vertical_delta": -0.02},
        },
        "top": {
            "distance": 1.48,
            "up": 1.52,
            "target": {"anchor": "heater", "vertical_delta": -0.02},
        },
    },
}
