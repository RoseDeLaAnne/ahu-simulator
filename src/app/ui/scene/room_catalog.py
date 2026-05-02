from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field

from app.infrastructure.settings import get_project_root


class RoomScenePlacement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    anchor: str = Field(default="room", min_length=1)
    long_delta: float = 0.0
    vertical_delta: float = 0.0
    side_delta: float = 0.0
    rotation_deg_y: float = 0.0
    scale_multiplier: float = Field(default=1.0, gt=0.0, le=3.0)
    target_long_ratio: float = Field(default=1.5, gt=0.3, le=6.0)
    clearance_ratio: float = Field(default=0.24, gt=0.0, le=2.0)
    side_clearance_ratio: float = Field(default=0.1, ge=0.0, le=1.0)
    vertical_clearance_ratio: float = Field(default=0.03, ge=0.0, le=1.0)
    max_auto_shift_ratio: float = Field(default=3.2, gt=0.5, le=10.0)


class RoomDemoPresetDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    description: str = Field(min_length=1)
    outdoor_temp_c: float = Field(ge=-45.0, le=45.0)
    airflow_m3_h: float = Field(ge=200.0, le=8000.0)
    supply_temp_setpoint_c: float = Field(ge=10.0, le=35.0)
    heat_recovery_efficiency: float = Field(ge=0.0, le=0.85)
    heater_power_kw: float = Field(ge=0.0, le=120.0)
    filter_contamination: float = Field(ge=0.0, le=1.0)
    fan_speed_ratio: float = Field(ge=0.2, le=1.2)
    room_temp_c: float = Field(ge=5.0, le=40.0)
    room_heat_gain_kw: float = Field(ge=-10.0, le=40.0)
    occupancy_people: int = Field(ge=0, le=200)
    local_humidity_percent: float = Field(ge=20.0, le=85.0)
    explanation: str = Field(min_length=1)


class RoomCatalogDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    description: str = Field(min_length=1)
    climate_note: str = Field(min_length=1)
    model_path: str = Field(min_length=1)
    model_url: str = Field(min_length=1)
    accent: str = Field(default="#38bdf8", pattern=r"^#[0-9a-fA-F]{6}$")
    tone: str = Field(default="room", min_length=1)
    volume_m3: float = Field(gt=0)
    room_heat_gain_kw: float = Field(ge=-10.0, le=40.0)
    room_thermal_capacity_kwh_per_k: float = Field(gt=0)
    room_loss_coeff_kw_per_k: float = Field(gt=0)
    room_profile: dict[str, float] = Field(default_factory=dict)
    placement: RoomScenePlacement = Field(default_factory=RoomScenePlacement)
    design_occupancy_people: int = Field(ge=1, le=200)
    fresh_air_target_l_s_per_person: float = Field(gt=1.0, le=30.0)
    outdoor_co2_ppm: int = Field(default=430, ge=350, le=700)
    local_humidity_baseline_percent: float = Field(default=42.0, ge=20.0, le=80.0)
    default_preset_id: str | None = None
    presets: list[RoomDemoPresetDescriptor] = Field(default_factory=list)


class RoomCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_room_id: str | None = None
    rooms: list[RoomCatalogDescriptor] = Field(default_factory=list)


_ROOM_META: dict[str, dict[str, object]] = {
    "office_suite.glb": {
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
            "long_delta": 0.32,
            "vertical_delta": 0.02,
            "side_delta": -0.06,
            "rotation_deg_y": 170.0,
            "scale_multiplier": 1.0,
            "target_long_ratio": 1.42,
            "clearance_ratio": 0.24,
            "side_clearance_ratio": 0.1,
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
    },
    "classroom_wing.glb": {
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
            "target_long_ratio": 1.58,
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
    },
    "lab_cluster.glb": {
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
            "target_long_ratio": 1.5,
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
    },
}

_ROOM_MODEL_OVERRIDES: dict[str, tuple[str, ...]] = {
    "office_suite.glb": (
        "models/rooms/office_suite.glb",
    ),
    "classroom_wing.glb": (
        "models/rooms/classroom_wing.glb",
    ),
    "lab_cluster.glb": (
        "models/rooms/lab_cluster.glb",
    ),
}


def build_room_catalog(project_root: Path | None = None) -> RoomCatalog:
    root = project_root or get_project_root()
    rooms: list[RoomCatalogDescriptor] = []
    for model_name, meta in _ROOM_META.items():
        model_path = _resolve_room_model_path(root, model_name)
        if model_path is None:
            continue
        descriptor = RoomCatalogDescriptor(
            id=str(meta["id"]),
            label=str(meta["label"]),
            description=str(meta["description"]),
            climate_note=str(meta["climate_note"]),
            model_path=model_path.relative_to(root).as_posix(),
            model_url="/" + quote(model_path.relative_to(root).as_posix()),
            accent=str(meta["accent"]),
            tone=str(meta["tone"]),
            volume_m3=float(meta["volume_m3"]),
            room_heat_gain_kw=float(meta["room_heat_gain_kw"]),
            room_thermal_capacity_kwh_per_k=float(meta["room_thermal_capacity_kwh_per_k"]),
            room_loss_coeff_kw_per_k=float(meta["room_loss_coeff_kw_per_k"]),
            room_profile=dict(meta.get("room_profile") or {}),
            placement=RoomScenePlacement.model_validate(meta.get("placement") or {}),
            design_occupancy_people=int(meta["design_occupancy_people"]),
            fresh_air_target_l_s_per_person=float(meta["fresh_air_target_l_s_per_person"]),
            outdoor_co2_ppm=int(meta.get("outdoor_co2_ppm", 430)),
            local_humidity_baseline_percent=float(meta["local_humidity_baseline_percent"]),
            presets=[
                RoomDemoPresetDescriptor.model_validate(item)
                for item in (meta.get("presets") or [])
            ],
            default_preset_id=(
                str((meta.get("presets") or [{}])[0].get("id"))
                if meta.get("presets")
                else None
            ),
        )
        rooms.append(descriptor)

    default_room_id = rooms[0].id if rooms else None
    return RoomCatalog(default_room_id=default_room_id, rooms=rooms)


def _resolve_room_model_path(
    project_root: Path,
    legacy_room_model_name: str,
) -> Path | None:
    for relative_override_path in _ROOM_MODEL_OVERRIDES.get(legacy_room_model_name, ()):
        override_candidate = project_root / relative_override_path
        if override_candidate.exists():
            return override_candidate

    fallback_path = project_root / "models" / "rooms" / legacy_room_model_name
    if fallback_path.exists():
        return fallback_path
    return None


def resolve_room_descriptor(
    catalog: RoomCatalog,
    room_id: str | None,
) -> RoomCatalogDescriptor | None:
    if not catalog.rooms:
        return None
    target_id = room_id or catalog.default_room_id or catalog.rooms[0].id
    for room in catalog.rooms:
        if room.id == target_id:
            return room
    return catalog.rooms[0]


def resolve_room_preset(
    room: RoomCatalogDescriptor,
    preset_id: str | None,
) -> RoomDemoPresetDescriptor | None:
    if not room.presets:
        return None
    target_id = preset_id or room.default_preset_id or room.presets[0].id
    for preset in room.presets:
        if preset.id == target_id:
            return preset
    return room.presets[0]


def build_room_runtime_payload(
    room: RoomCatalogDescriptor,
    *,
    preset_id: str | None = None,
    occupancy_people: int | None = None,
    local_humidity_percent: float | None = None,
) -> dict[str, object]:
    preset = resolve_room_preset(room, preset_id)
    runtime_payload = room.model_dump(mode="json")
    runtime_payload["active_preset"] = preset.model_dump(mode="json") if preset else None
    runtime_payload["active_preset_id"] = preset.id if preset else None
    runtime_payload["occupancy_people"] = (
        int(occupancy_people)
        if occupancy_people is not None
        else int(preset.occupancy_people if preset else room.design_occupancy_people)
    )
    runtime_payload["local_humidity_percent"] = (
        float(local_humidity_percent)
        if local_humidity_percent is not None
        else float(
            preset.local_humidity_percent
            if preset
            else room.local_humidity_baseline_percent
        )
    )
    runtime_payload["preset_summary"] = preset.explanation if preset else room.climate_note
    return runtime_payload
