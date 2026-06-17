"""Профиль помещения: «Учебная аудитория» — classroom_wing.

Ручки масштаба/размещения — placement.target_long_ratio,
placement.scale_multiplier, placement.*_clearance_ratio, room_profile.*_scale
(см. `office_suite` для полного описания).
"""

from __future__ import annotations


META: dict[str, object] = {
    "id": "classroom_wing",
    "label": "Учебная аудитория",
    "description": (
        "Аудитория с рядом мест и доской. Хорошо показывает, как высокая "
        "занятость влияет на CO₂ и требует увеличения притока."
    ),
    "climate_note": (
        "Наглядный учебный сценарий: при заполнении аудитории локальные датчики "
        "сразу уходят из зелёной зоны, если притока не хватает."
    ),
    "accent": "#22c55e",
    "tone": "classroom",
    "volume_m3": 420.0,
    "room_heat_gain_kw": 8.6,
    "room_thermal_capacity_kwh_per_k": 19.0,
    "room_loss_coeff_kw_per_k": 0.24,
    "room_profile": {
        "long_scale": 0.68,
        "vertical_scale": 0.36,
        "side_scale": 0.34,
    },
    "placement": {
        "anchor": "room",
        "long_delta": 0.38,
        "vertical_delta": 0.02,
        "side_delta": -0.1,
        "rotation_deg_y": 172.0,
        "scale_multiplier": 1.0,
        # Контекст-помещение меньше ПВУ, чтобы установка оставалась главным
        # объектом сцены (см. office_suite). Класс крупнее офиса — ratio чуть
        # выше, но всё равно < 1.
        "target_long_ratio": 0.95,
        "clearance_ratio": 0.28,
        "side_clearance_ratio": 0.11,
    },
    "design_occupancy_people": 32,
    "fresh_air_target_l_s_per_person": 14.0,
    "local_humidity_baseline_percent": 44.0,
    "presets": [
        {
            "id": "classroom_before_lesson",
            "label": "Перед занятием",
            "description": "Аудитория почти пустая и продувается без нагрузки.",
            "outdoor_temp_c": 5.0,
            "airflow_m3_h": 3000.0,
            "supply_temp_setpoint_c": 19.0,
            "heat_recovery_efficiency": 0.48,
            "heater_power_kw": 16.0,
            "filter_contamination": 0.18,
            "fan_speed_ratio": 0.76,
            "room_temp_c": 20.4,
            "room_heat_gain_kw": 3.2,
            "occupancy_people": 5,
            "local_humidity_percent": 42.0,
            "explanation": (
                "До начала занятия воздух свежий, датчики CO₂ и влажности "
                "показывают запас по качеству воздуха."
            ),
        },
        {
            "id": "classroom_full_lesson",
            "label": "Полная аудитория",
            "description": "Максимально наглядный режим с полной посадкой.",
            "outdoor_temp_c": -10.0,
            "airflow_m3_h": 4200.0,
            "supply_temp_setpoint_c": 21.0,
            "heat_recovery_efficiency": 0.6,
            "heater_power_kw": 34.0,
            "filter_contamination": 0.36,
            "fan_speed_ratio": 1.0,
            "room_temp_c": 23.0,
            "room_heat_gain_kw": 10.8,
            "occupancy_people": 32,
            "local_humidity_percent": 51.0,
            "explanation": (
                "Это самый показательный пресет: в комнате много людей, "
                "поэтому room-датчики должны быстро показать ухудшение качества воздуха."
            ),
        },
        {
            "id": "classroom_recovery_flush",
            "label": "Проветривание после пары",
            "description": "Повышенная подача для быстрого снижения CO₂ после занятия.",
            "outdoor_temp_c": 0.0,
            "airflow_m3_h": 5200.0,
            "supply_temp_setpoint_c": 18.0,
            "heat_recovery_efficiency": 0.52,
            "heater_power_kw": 20.0,
            "filter_contamination": 0.22,
            "fan_speed_ratio": 1.08,
            "room_temp_c": 21.1,
            "room_heat_gain_kw": 4.4,
            "occupancy_people": 8,
            "local_humidity_percent": 45.0,
            "explanation": (
                "После занятия помещение почти пустое, но подача увеличена, "
                "чтобы быстро вывести накопившийся CO₂ и вернуть зелёную зону."
            ),
        },
    ],
}

MODEL_OVERRIDES: tuple[str, ...] = (
    "models/rooms/classroom_wing.glb",
)
