"""Профиль сцены: «Промышленный агрегат» — industrial_machinery_unit.

Это модель ПО УМОЛЧАНИЮ в селекторе сцены (см. model_catalog), поэтому её
масштаб служит эталоном пропорции «модель ↔ помещение».

Главные ручки масштаба:
  * transform.scale_multiplier — общий масштаб модели относительно сцены;
  * transform.lift_ratio       — подъём над полом (доля габарита по высоте);
  * room_zone.{long,vertical,side}_scale — размер «зоны помещения» относительно
    габарита модели (стеклянный короб вокруг агрегата).
Соответствующий масштаб реального помещения (office_suite/classroom_wing/...)
настраивается в `room_profiles/<id>.py` через placement.target_long_ratio.
"""

from __future__ import annotations


PROFILE: dict[str, object] = {
    "transform": {
        "rotation_deg": {"x": 0.0, "y": 0.0, "z": 0.0},
        "scale_multiplier": 1.0,
        "lift_ratio": 0.0,
    },
    "theme": {
        "floor_color": "#4a2412",
        "halo_color": "#f97316",
        "particles_color": "#fdba74",
        "rim_color": "#fb923c",
        "fill_color": "#ffedd5",
    },
    "room_zone": {
        "long_scale": 0.46,
        "vertical_scale": 0.34,
        "side_scale": 0.26,
    },
    "anchors": {
        "outdoor": {"long": 0.12, "vertical": 0.62, "side": -0.18},
        "filter": {"long": 0.31, "vertical": 0.6, "side": -0.04},
        "heater": {"long": 0.55, "vertical": 0.6, "side": 0.08},
        "fan": {"long": 0.72, "vertical": 0.61, "side": 0.16},
        "duct": {"long": 0.9, "vertical": 0.58, "side": 0.26},
        "room": {"long": 1.1, "vertical": 0.32, "side": 0.3},
        "room_sensor": {"long": 1.1, "vertical": 0.52, "side": 0.32},
    },
    "flows": {
        "outdoor_to_filter": [
            "outdoor",
            {"long": 0.18, "vertical": 0.63, "side": -0.14},
            {"long": 0.24, "vertical": 0.61, "side": -0.08},
            "filter",
        ],
        "filter_to_heater": [
            "filter",
            {"long": 0.42, "vertical": 0.6, "side": 0.0},
            "heater",
        ],
        "heater_to_fan": [
            "heater",
            {"long": 0.63, "vertical": 0.6, "side": 0.11},
            "fan",
        ],
        "fan_to_room": [
            "fan",
            {"long": 0.84, "vertical": 0.59, "side": 0.22},
            "duct",
            {"anchor": "room", "vertical_delta": 0.04},
        ],
    },
    "effects": {
        "filter_dust": {"anchor": "filter", "scale": 1.0},
        "heater_field": {"anchor": "heater", "scale": 1.15},
    },
    "camera": {
        "hero": {
            "distance": 1.76,
            "long": 0.9,
            "side": -0.62,
            "up": 0.46,
            "target": {"anchor": "heater"},
        },
        "service": {
            "distance": 1.72,
            "long": -0.98,
            "side": 0.56,
            "up": 0.52,
            "target": {"anchor": "fan", "vertical_delta": -0.02},
        },
    },
}
