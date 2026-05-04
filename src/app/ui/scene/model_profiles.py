from __future__ import annotations

from copy import deepcopy


DEFAULT_SCENE_PROFILE: dict[str, object] = {
    "transform": {
        "rotation_deg": {"x": 0.0, "y": 0.0, "z": 0.0},
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

MODEL_SCENE_PROFILES: dict[str, dict[str, object]] = {
    "modular_ahu": {
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
    },
    "industrial_hvac_unit": {
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
    },
    "industrial_machinery_unit": {
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
    },
    "base_classic": {
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
    },
    "base_variant_a": {
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
    },
    "base_variant_b": {
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
    },
    "base_variant_c": {
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
    },
    # Учебная процедурная ПВУ (СП 60.13330.2020). GLB сохраняет иерархию
    # секций (intake/filter/silencer/heater/fan/duct) и ставит их в ряд по
    # длине корпуса. Размер модели — около 6×2×1.4 м, helping the camera
    # rest on the section line.
    "pvu_installation": {
        "theme": {
            "floor_color": "#0d3a4a",
            "halo_color": "#22d3ee",
            "particles_color": "#a5f3fc",
            "rim_color": "#7dd3fc",
            "fill_color": "#fef3c7",
        },
        "transform": {
            "rotation_deg": {"x": 0.0, "y": 0.0, "z": 0.0},
            "scale_multiplier": 1.0,
            "lift_ratio": 0.0,
        },
        "room_zone": {
            "long_scale": 0.42,
            "vertical_scale": 0.28,
            "side_scale": 0.22,
        },
        "anchors": {
            "outdoor": {"long": 0.06, "vertical": 0.66, "side": -0.28},
            "filter": {"long": 0.24, "vertical": 0.66, "side": -0.12},
            "heater": {"long": 0.46, "vertical": 0.66, "side": 0.0},
            "fan": {"long": 0.7, "vertical": 0.66, "side": 0.12},
            "duct": {"long": 0.92, "vertical": 0.62, "side": 0.22},
            "room": {"long": 1.18, "vertical": 0.32, "side": 0.28},
            "room_sensor": {"long": 1.18, "vertical": 0.55, "side": 0.3},
        },
        "camera": {
            "hero": {
                "distance": 1.78,
                "long": 0.94,
                "side": -0.5,
                "up": 0.42,
                "target": {"anchor": "heater"},
            },
            "service": {
                "distance": 1.72,
                "long": -0.94,
                "side": 0.46,
                "up": 0.46,
                "target": {"anchor": "fan", "vertical_delta": -0.02},
            },
            "top": {
                "distance": 1.5,
                "up": 1.55,
                "target": {"anchor": "heater", "vertical_delta": -0.02},
            },
        },
    },
}


def build_scene_profile(model_id: str | None) -> dict[str, object]:
    profile = deepcopy(DEFAULT_SCENE_PROFILE)
    _deep_merge(profile, MODEL_SCENE_PROFILES.get(model_id or "", {}))
    return profile


def _deep_merge(target: dict[str, object], updates: dict[str, object]) -> None:
    for key, value in updates.items():
        if (
            key in target
            and isinstance(target[key], dict)
            and isinstance(value, dict)
        ):
            _deep_merge(target[key], value)
            continue
        target[key] = deepcopy(value)
