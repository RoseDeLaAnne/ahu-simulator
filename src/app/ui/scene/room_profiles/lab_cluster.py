"""Профиль помещения: «Лабораторный блок» — lab_cluster.

Ручки масштаба/размещения — placement.target_long_ratio,
placement.scale_multiplier, placement.*_clearance_ratio, room_profile.*_scale
(см. `office_suite` для полного описания).
"""

from __future__ import annotations


META: dict[str, object] = {
    "id": "lab_cluster",
    "label": "Лабораторный блок",
    "description": (
        "Лаборатория с островом, стойками и вытяжным колпаком. Подходит для "
        "сценариев с оборудованием и локальными теплопритоками."
    ),
    "climate_note": (
        "Лаборатория интересна тем, что даже при малом числе людей воздух может "
        "ухудшаться из-за оборудования и повышенной влажностной нагрузки."
    ),
    "accent": "#f97316",
    "tone": "lab",
    "volume_m3": 320.0,
    "room_heat_gain_kw": 11.5,
    "room_thermal_capacity_kwh_per_k": 23.0,
    "room_loss_coeff_kw_per_k": 0.29,
    "room_profile": {
        "long_scale": 0.58,
        "vertical_scale": 0.38,
        "side_scale": 0.32,
    },
    "placement": {
        "anchor": "room",
        "long_delta": 0.36,
        "vertical_delta": 0.02,
        "side_delta": -0.08,
        "rotation_deg_y": 160.0,
        "scale_multiplier": 1.0,
        # Контекст-помещение меньше ПВУ, чтобы установка оставалась главным
        # объектом сцены (см. office_suite).
        "target_long_ratio": 0.9,
        "clearance_ratio": 0.26,
        "side_clearance_ratio": 0.12,
    },
    "design_occupancy_people": 14,
    "fresh_air_target_l_s_per_person": 16.0,
    "local_humidity_baseline_percent": 46.0,
    "presets": [
        {
            "id": "lab_calibrated",
            "label": "Калиброванный режим",
            "description": "Умеренная занятость и стабильная работа оборудования.",
            "outdoor_temp_c": 4.0,
            "airflow_m3_h": 3400.0,
            "supply_temp_setpoint_c": 19.5,
            "heat_recovery_efficiency": 0.5,
            "heater_power_kw": 22.0,
            "filter_contamination": 0.18,
            "fan_speed_ratio": 0.82,
            "room_temp_c": 21.5,
            "room_heat_gain_kw": 9.4,
            "occupancy_people": 6,
            "local_humidity_percent": 46.0,
            "explanation": (
                "Нормальный лабораторный цикл: room-датчики стабильны, "
                "но теплопритоки выше, чем в офисе."
            ),
        },
        {
            "id": "lab_equipment_peak",
            "label": "Пик оборудования",
            "description": "Максимальные теплопритоки и ухудшение качества воздуха.",
            "outdoor_temp_c": -14.0,
            "airflow_m3_h": 3800.0,
            "supply_temp_setpoint_c": 21.0,
            "heat_recovery_efficiency": 0.62,
            "heater_power_kw": 38.0,
            "filter_contamination": 0.42,
            "fan_speed_ratio": 1.0,
            "room_temp_c": 24.1,
            "room_heat_gain_kw": 15.8,
            "occupancy_people": 12,
            "local_humidity_percent": 54.0,
            "explanation": (
                "Оборудование и люди одновременно поднимают температуру, CO₂ и влажность. "
                "Визуально это должен быть самый тяжёлый room-сценарий."
            ),
        },
        {
            "id": "lab_purge_after_shift",
            "label": "Продувка после смены",
            "description": "Интенсивная подача при пустой лаборатории после работы.",
            "outdoor_temp_c": 1.0,
            "airflow_m3_h": 4800.0,
            "supply_temp_setpoint_c": 18.0,
            "heat_recovery_efficiency": 0.54,
            "heater_power_kw": 18.0,
            "filter_contamination": 0.24,
            "fan_speed_ratio": 1.06,
            "room_temp_c": 20.1,
            "room_heat_gain_kw": 5.2,
            "occupancy_people": 1,
            "local_humidity_percent": 43.0,
            "explanation": (
                "После смены людей почти нет, зато установка быстро вымывает остаточные "
                "загрязнения и возвращает room-датчики в комфорт."
            ),
        },
    ],
}

MODEL_OVERRIDES: tuple[str, ...] = (
    "models/rooms/lab_cluster.glb",
)
