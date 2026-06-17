"""Базовый профиль сцены 3D-модели.

`DEFAULT_SCENE_PROFILE` задаёт значения по умолчанию для всех моделей: трансформ
(масштаб/наклон/подъём), тему освещения, масштаб зоны помещения, размеры
маркеров, якоря узлов, датчики, потоки воздуха, клапаны, эффекты и пресеты
камеры. Профиль конкретной модели (`model_profiles/<id>.py`) переопределяет
только нужные ветви — слияние выполняет `build_scene_profile`.
"""

from __future__ import annotations


DEFAULT_SCENE_PROFILE: dict[str, object] = {
    "transform": {
        "rotation_deg": {"x": 0.0, "y": 0.0, "z": 0.0},
        # target_long — целевой габарит модели по самой длинной ГОРИЗОНТАЛЬНОЙ
        # оси в единицах сцены. GLB-модели приходят в разных единицах (родной
        # габарит варьируется от ~1 до ~13), поэтому без нормализации масштаб
        # модели и зависящие от него размеры (маркеры, потоки, зона помещения)
        # «плавали» от модели к модели. Нормализация к target_long делает
        # масштаб детерминированным и единообразным; per-model профиль может его
        # переопределить, а scale_multiplier остаётся тонкой подстройкой сверху.
        # 0/None — отключить нормализацию (использовать только scale_multiplier).
        "target_long": 3.4,
        "scale_multiplier": 1.0,
        "lift_ratio": 0.0,
    },
    "theme": {
        "floor_color": "#0f3d4c",
        "halo_color": "#14b8a6",
        "far_ring_color": "#1e293b",
        "particles_color": "#9dd8ff",
        "ambient_color": "#e6f3ff",
        "key_color": "#ffffff",
        "rim_color": "#7dd3fc",
        "fill_color": "#fef3c7",
    },
    "room_zone": {
        "long_scale": 0.52,
        "vertical_scale": 0.36,
        "side_scale": 0.28,
    },
    "sizing": {
        "marker_scale": 1.55,
        "flow_scale": 1.42,
        "connector_scale": 1.32,
        "effect_scale": 1.2,
    },
    "anchors": {
        "outdoor": {"long": 0.06, "vertical": 0.72, "side": -0.28},
        "filter": {"long": 0.24, "vertical": 0.74, "side": -0.12},
        "heater": {"long": 0.46, "vertical": 0.74, "side": 0.0},
        "fan": {"long": 0.68, "vertical": 0.74, "side": 0.14},
        "duct": {"long": 0.88, "vertical": 0.72, "side": 0.24},
        "room": {"long": 1.12, "vertical": 0.36, "side": 0.26},
        "room_sensor": {"long": 1.12, "vertical": 0.58, "side": 0.26},
    },
    "sensors": {
        "outdoor": {"anchor": "outdoor", "vertical_delta": 0.09},
        "filter_pressure": {"anchor": "filter", "vertical_delta": 0.08},
        "supply_temp": {"anchor": "heater", "vertical_delta": 0.08},
        "airflow": {"anchor": "duct", "vertical_delta": 0.08},
        "room_temp": {"anchor": "room_sensor"},
    },
    "flows": {
        "outdoor_to_filter": [
            "outdoor",
            {"long": 0.13, "vertical": 0.72, "side": -0.24},
            "filter",
        ],
        "filter_to_heater": [
            "filter",
            {"long": 0.34, "vertical": 0.72, "side": -0.06},
            "heater",
        ],
        "heater_to_fan": [
            "heater",
            {"long": 0.56, "vertical": 0.72, "side": 0.08},
            "fan",
        ],
        "fan_to_room": [
            "fan",
            "duct",
            {"long": 0.98, "vertical": 0.64, "side": 0.28},
            {"anchor": "room", "vertical_delta": 0.04},
        ],
        "extract_context": [
            {"anchor": "room", "vertical_delta": 0.04},
            {"anchor": "room", "vertical_delta": 0.18, "side_delta": -0.12},
            {"anchor": "room", "vertical_delta": 0.34, "side_delta": -0.28},
        ],
    },
    "dampers": {
        "intake": {"anchor": "outdoor", "vertical_delta": -0.03},
        "living": {"anchor": "duct", "vertical_delta": -0.02},
        "bedroom_north": {"anchor": "duct", "side_delta": 0.08},
        "bedroom_south": {"anchor": "duct", "side_delta": -0.08},
        "study": {"anchor": "duct", "vertical_delta": 0.04, "side_delta": 0.16},
        "kitchen": {"anchor": "duct", "vertical_delta": -0.04, "side_delta": -0.16},
    },
    "effects": {
        "intake_aura": {"anchor": "outdoor", "scale": 1.0},
        "filter_dust": {"anchor": "filter", "scale": 0.95},
        "heater_field": {"anchor": "heater", "scale": 1.0},
    },
    "camera": {
        "hero": {
            "distance": 1.9,
            "long": 0.95,
            "side": -0.5,
            "up": 0.4,
            "target": {"anchor": "heater", "vertical_delta": -0.02},
        },
        "service": {
            "distance": 1.82,
            "long": -0.95,
            "side": 0.42,
            "up": 0.46,
            "target": {"anchor": "fan", "vertical_delta": -0.02},
        },
        "top": {
            "distance": 1.55,
            "up": 1.55,
            "target": {"anchor": "heater", "vertical_delta": -0.04},
        },
    },
}
