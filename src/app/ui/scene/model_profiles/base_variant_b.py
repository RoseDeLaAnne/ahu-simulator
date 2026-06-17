"""Профиль сцены: «Базовый вариант Б» — base_variant_b.

Высокий корпус — обратите внимание на room_zone.vertical_scale (вытянут по
вертикали). Ручки масштаба — transform.scale_multiplier, transform.lift_ratio,
room_zone.*_scale (см. `industrial_machinery_unit` для описания).
"""

from __future__ import annotations


PROFILE: dict[str, object] = {
    "theme": {
        "floor_color": "#514006",
        "halo_color": "#eab308",
        "particles_color": "#fde68a",
        "rim_color": "#facc15",
    },
    "room_zone": {
        "long_scale": 0.44,
        "vertical_scale": 0.42,
        "side_scale": 0.22,
    },
    "anchors": {
        "outdoor": {"long": 0.08, "vertical": 0.68, "side": -0.1},
        "filter": {"long": 0.24, "vertical": 0.68, "side": -0.02},
        "heater": {"long": 0.46, "vertical": 0.69, "side": 0.02},
        "fan": {"long": 0.68, "vertical": 0.7, "side": 0.1},
        "duct": {"long": 0.9, "vertical": 0.66, "side": 0.18},
        "room": {"long": 1.1, "vertical": 0.38, "side": 0.24},
        "room_sensor": {"long": 1.12, "vertical": 0.62, "side": 0.24},
    },
    "flows": {
        "outdoor_to_filter": [
            "outdoor",
            {"long": 0.14, "vertical": 0.68, "side": -0.08},
            "filter",
        ],
        "filter_to_heater": [
            "filter",
            {"long": 0.34, "vertical": 0.69, "side": 0.0},
            {"long": 0.4, "vertical": 0.7, "side": 0.02},
            "heater",
        ],
        "heater_to_fan": [
            "heater",
            {"long": 0.56, "vertical": 0.7, "side": 0.04},
            "fan",
        ],
        "fan_to_room": [
            "fan",
            {"long": 0.82, "vertical": 0.68, "side": 0.14},
            "duct",
            {"anchor": "room", "vertical_delta": 0.08},
        ],
    },
    "effects": {
        "intake_aura": {"anchor": "outdoor", "scale": 0.96},
        "filter_dust": {"anchor": "filter", "scale": 1.06},
        "heater_field": {"anchor": "heater", "scale": 1.12},
    },
    "camera": {
        "hero": {
            "distance": 1.9,
            "long": 0.9,
            "side": -0.54,
            "up": 0.58,
            "target": {"anchor": "fan"},
        },
        "service": {
            "distance": 1.82,
            "long": -0.94,
            "side": 0.44,
            "up": 0.58,
            "target": {"anchor": "filter"},
        },
        "top": {
            "distance": 1.42,
            "up": 1.68,
            "target": {"anchor": "heater"},
        },
    },
}
