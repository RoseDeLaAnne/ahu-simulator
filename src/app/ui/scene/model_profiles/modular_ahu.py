"""Профиль сцены: «Флагманская ПВУ (детализированная)» — modular_ahu.

Тонкая настройка масштаба и компоновки этой модели. Главные ручки масштаба:
  * transform.scale_multiplier — общий масштаб модели относительно сцены;
  * transform.lift_ratio       — подъём над полом (доля габарита по высоте);
  * room_zone.{long,vertical,side}_scale — размер стеклянной «зоны помещения»
    относительно габарита модели;
  * sizing.* (в _base) — масштаб маркеров/потоков/коннекторов/эффектов.
Якоря узлов (anchors) и потоки (flows) заданы в долях габарита модели и
переопределяют значения из `_base.DEFAULT_SCENE_PROFILE`.
"""

from __future__ import annotations


PROFILE: dict[str, object] = {
    "theme": {
        "floor_color": "#0b4664",
        "halo_color": "#38bdf8",
        "particles_color": "#c6ecff",
        "rim_color": "#7dd3fc",
    },
    "room_zone": {
        "long_scale": 0.42,
        "vertical_scale": 0.28,
        "side_scale": 0.22,
    },
    "anchors": {
        "outdoor": {"long": 0.08, "vertical": 0.68, "side": -0.22},
        "filter": {"long": 0.28, "vertical": 0.68, "side": -0.04},
        "heater": {"long": 0.62, "vertical": 0.58, "side": 0.12},
        "fan": {"long": 0.78, "vertical": 0.58, "side": 0.14},
        "duct": {"long": 0.95, "vertical": 0.58, "side": 0.24},
        "room": {"long": 1.16, "vertical": 0.28, "side": 0.28},
        "room_sensor": {"long": 1.16, "vertical": 0.52, "side": 0.32},
    },
    "flows": {
        "outdoor_to_filter": [
            "outdoor",
            {"long": 0.16, "vertical": 0.68, "side": -0.18},
            {"long": 0.22, "vertical": 0.67, "side": -0.08},
            "filter",
        ],
        "filter_to_heater": [
            "filter",
            {"long": 0.42, "vertical": 0.66, "side": -0.02},
            {"long": 0.54, "vertical": 0.62, "side": 0.08},
            "heater",
        ],
        "heater_to_fan": [
            "heater",
            {"long": 0.7, "vertical": 0.58, "side": 0.12},
            "fan",
        ],
        "fan_to_room": [
            "fan",
            "duct",
            {"long": 1.02, "vertical": 0.52, "side": 0.28},
            {"anchor": "room", "vertical_delta": 0.06},
        ],
    },
    "dampers": {
        "bedroom_north": {"anchor": "duct", "side_delta": 0.06},
        "bedroom_south": {"anchor": "duct", "side_delta": -0.06},
        "study": {"anchor": "duct", "vertical_delta": 0.06, "side_delta": 0.12},
        "kitchen": {"anchor": "duct", "vertical_delta": -0.06, "side_delta": -0.12},
    },
    "effects": {
        "filter_dust": {"anchor": "filter", "scale": 1.15},
        "heater_field": {"anchor": "heater", "scale": 1.2},
    },
    "camera": {
        "hero": {
            "distance": 1.82,
            "long": 1.06,
            "side": -0.62,
            "up": 0.44,
            "target": {"anchor": "heater", "vertical_delta": -0.02},
        },
        "service": {
            "distance": 1.7,
            "long": -1.0,
            "side": 0.5,
            "up": 0.5,
            "target": {"anchor": "fan", "vertical_delta": -0.03},
        },
    },
}
