from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field

from app.infrastructure.settings import get_project_root
from app.ui.scene.room_profiles import ROOM_META, ROOM_MODEL_OVERRIDES


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


def build_room_catalog(project_root: Path | None = None) -> RoomCatalog:
    root = project_root or get_project_root()
    rooms: list[RoomCatalogDescriptor] = []
    for model_name, meta in ROOM_META.items():
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
    for relative_override_path in ROOM_MODEL_OVERRIDES.get(legacy_room_model_name, ()):
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
