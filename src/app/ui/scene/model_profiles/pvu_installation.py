"""Профиль сцены: «Учебная ПВУ (СП 60.13330.2020)» — pvu_installation.

Учебная процедурная ПВУ. GLB сохраняет иерархию секций
(intake/filter/silencer/heater/fan/duct) и ставит их в ряд по длине корпуса.
Размер модели — около 6×2×1.4 м, что помогает камере «лечь» на линию секций.

Ручки масштаба — transform.scale_multiplier, transform.lift_ratio,
room_zone.*_scale (см. `industrial_machinery_unit` для описания).
"""

from __future__ import annotations


PROFILE: dict[str, object] = {
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
}
