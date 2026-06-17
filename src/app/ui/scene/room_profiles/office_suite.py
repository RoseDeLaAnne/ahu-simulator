"""Профиль помещения: «Офис open-space» — office_suite (по умолчанию).

Главные ручки масштаба/размещения помещения относительно модели ПВУ:
  * placement.target_long_ratio  — целевая длина помещения в долях длины модели
    (адаптивный масштаб подгоняет короб помещения под габарит модели);
  * placement.scale_multiplier   — дополнительный множитель поверх адаптивного;
  * placement.clearance_ratio / side_clearance_ratio / vertical_clearance_ratio
    — зазоры между моделью и стенами помещения;
  * placement.{long,vertical,side}_delta — смещение помещения относительно якоря;
  * placement.rotation_deg_y     — поворот помещения вокруг вертикали;
  * room_profile.{long,vertical,side}_scale — пропорции схематичной зоны.
Геометрия GLB берётся из `MODEL_OVERRIDES` (предпочтительные пути) с откатом на
`models/rooms/<имя>.glb`.
"""

from __future__ import annotations


META: dict[str, object] = {
    "id": "office_suite",
    "label": "Офис open-space",
    "description": (
        "Открытый офисный блок с рабочими столами и переговорной зоной. "
        "Подходит для базовой демонстрации комфорта и качества воздуха."
    ),
    "climate_note": (
        "Оптимален для объяснения обычному пользователю: мало людей — "
        "воздух чище, больше людей — CO₂ растёт, приток приходится повышать."
    ),
    "accent": "#38bdf8",
    "tone": "office",
    "volume_m3": 250.0,
    "room_heat_gain_kw": 4.2,
    "room_thermal_capacity_kwh_per_k": 14.0,
    "room_loss_coeff_kw_per_k": 0.18,
    "room_profile": {
        "long_scale": 0.52,
        "vertical_scale": 0.32,
        "side_scale": 0.3,
    },
    "placement": {
        "anchor": "room",
        "long_delta": 0.2,
        "vertical_delta": 0.02,
        "side_delta": -0.04,
        "rotation_deg_y": 170.0,
        "scale_multiplier": 1.0,
        # Помещение — это полупрозрачный пространственный КОНТЕКСТ сбоку от ПВУ,
        # а не объект изучения. Раньше короб помещения был длиннее модели
        # (ratio > 1), из-за чего мебель (стол/кресло) визуально перекрывала
        # установку — замечание про «мебель больше агрегата». Делаем контекст
        # заметно меньше ПВУ, чтобы установка читалась как главный объект.
        "target_long_ratio": 0.78,
        "clearance_ratio": 0.3,
        "side_clearance_ratio": 0.12,
    },
    "design_occupancy_people": 18,
    "fresh_air_target_l_s_per_person": 12.0,
    "local_humidity_baseline_percent": 42.0,
    "presets": [
        {
            "id": "office_focus",
            "label": "Тихий рабочий день",
            "description": "Небольшая загрузка и ровный комфорт без перегрева.",
            "outdoor_temp_c": 8.0,
            "airflow_m3_h": 2600.0,
            "supply_temp_setpoint_c": 19.0,
            "heat_recovery_efficiency": 0.42,
            "heater_power_kw": 12.0,
            "filter_contamination": 0.14,
            "fan_speed_ratio": 0.74,
            "room_temp_c": 21.1,
            "room_heat_gain_kw": 3.6,
            "occupancy_people": 7,
            "local_humidity_percent": 41.0,
            "explanation": (
                "Людей немного, поэтому CO₂ и влажность держатся в зелёной зоне, "
                "а установка работает мягко и без перегрузки."
            ),
        },
        {
            "id": "office_meeting_rush",
            "label": "Совещание на весь блок",
            "description": "Быстрый рост нагрузки и качества воздуха при высокой занятости.",
            "outdoor_temp_c": -6.0,
            "airflow_m3_h": 3600.0,
            "supply_temp_setpoint_c": 21.0,
            "heat_recovery_efficiency": 0.56,
            "heater_power_kw": 26.0,
            "filter_contamination": 0.28,
            "fan_speed_ratio": 0.94,
            "room_temp_c": 22.4,
            "room_heat_gain_kw": 7.4,
            "occupancy_people": 18,
            "local_humidity_percent": 47.0,
            "explanation": (
                "Помещение заполнено людьми, из-за этого растут CO₂ и теплопритоки. "
                "Сцена покажет более плотный поток и более активные room-эффекты."
            ),
        },
        {
            "id": "office_overtime",
            "label": "Вечерний минимум",
            "description": "Пониженный приток при почти пустом помещении.",
            "outdoor_temp_c": 2.0,
            "airflow_m3_h": 1800.0,
            "supply_temp_setpoint_c": 18.0,
            "heat_recovery_efficiency": 0.4,
            "heater_power_kw": 10.0,
            "filter_contamination": 0.2,
            "fan_speed_ratio": 0.58,
            "room_temp_c": 20.2,
            "room_heat_gain_kw": 1.8,
            "occupancy_people": 2,
            "local_humidity_percent": 38.0,
            "explanation": (
                "Нагрузка минимальна: установка переходит в спокойный режим, "
                "а помещение остаётся комфортным даже при сниженной подаче."
            ),
        },
    ],
}

MODEL_OVERRIDES: tuple[str, ...] = (
    "models/rooms/office_suite.glb",
)
