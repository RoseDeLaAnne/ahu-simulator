"""Профиль сцены: «Промышленная ПВУ» — industrial_hvac_unit.

Главные ручки масштаба — transform.scale_multiplier, transform.lift_ratio,
room_zone.*_scale; см. модуль `modular_ahu` для полного описания. Якоря узлов
заданы в долях габарита модели.
"""

from __future__ import annotations


PROFILE: dict[str, object] = {
    "theme": {
        "floor_color": "#0d4b45",
        "halo_color": "#14b8a6",
        "particles_color": "#a7f3d0",
        "rim_color": "#5eead4",
    },
    "anchors": {
        "outdoor": {"long": 0.1, "vertical": 0.58, "side": -0.08},
        "filter": {"long": 0.26, "vertical": 0.56, "side": 0.0},
        "heater": {"long": 0.47, "vertical": 0.55, "side": 0.05},
        "fan": {"long": 0.67, "vertical": 0.55, "side": 0.08},
        "duct": {"long": 0.86, "vertical": 0.56, "side": 0.16},
        "room": {"long": 1.12, "vertical": 0.34, "side": 0.22},
        "room_sensor": {"long": 1.12, "vertical": 0.52, "side": 0.24},
    },
    "flows": {
        "filter_to_heater": [
            "filter",
            {"long": 0.36, "vertical": 0.56, "side": 0.02},
            "heater",
        ],
        "heater_to_fan": [
            "heater",
            {"long": 0.58, "vertical": 0.56, "side": 0.06},
            "fan",
        ],
        "fan_to_room": [
            "fan",
            {"long": 0.82, "vertical": 0.57, "side": 0.12},
            "duct",
            {"anchor": "room", "vertical_delta": 0.03},
        ],
    },
    "camera": {
        "hero": {
            "distance": 1.72,
            "long": 0.96,
            "side": -0.48,
            "up": 0.38,
            "target": {"anchor": "fan"},
        },
        "service": {
            "distance": 1.64,
            "long": -0.88,
            "side": 0.36,
            "up": 0.42,
            "target": {"anchor": "filter"},
        },
    },
}
