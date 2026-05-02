from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.services.status_service import StatusService
from app.simulation.parameters import ControlMode
from app.simulation.state import OperationStatus, SimulationResult
from app.simulation.status_policy import max_status


class VisualElementState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    visual_id: str
    label: str
    value: str
    detail: str | None = None
    state: OperationStatus = OperationStatus.NORMAL
    active: bool = True
    alarm_text: str | None = None
    intensity: float | None = Field(default=None, ge=0.0, le=1.0)


class VisualizationSignalMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str | None = None
    scenario_title: str | None = None
    status: OperationStatus
    summary: str
    bindings_version: int = 2
    active_alarm_codes: list[str] = Field(default_factory=list)
    nodes: dict[str, VisualElementState] = Field(default_factory=dict)
    sensors: dict[str, VisualElementState] = Field(default_factory=dict)
    flows: dict[str, VisualElementState] = Field(default_factory=dict)
    room_sensors: dict[str, VisualElementState] = Field(default_factory=dict)
    room_story: str | None = None

    def all_visual_ids(self) -> set[str]:
        return set(self.nodes) | set(self.sensors) | set(self.flows)


def build_visualization_signal_map(
    result: SimulationResult,
    bindings_version: int = 2,
    room_context: dict[str, object] | None = None,
    status_service: StatusService | None = None,
) -> VisualizationSignalMap:
    status_service = status_service or StatusService()
    state = result.state
    parameters = result.parameters
    alarm_codes = {alarm.code for alarm in result.alarms}
    airflow_ratio = state.actual_airflow_m3_h / max(parameters.airflow_m3_h, 1.0)
    metric_map = status_service.build_metric_status_map(result)
    flow_status = metric_map["airflow"].status
    flow_intensity = _clamp(round(airflow_ratio, 2), lower=0.18, upper=1.0)
    control_label = "Ручной режим" if parameters.control_mode == ControlMode.MANUAL else "Авто"

    filter_state = metric_map["filter_pressure"].status
    heater_state = max_status(metric_map["supply_temp"].status, metric_map["heating_power"].status)
    fan_state = metric_map["airflow"].status
    supply_state = max_status(flow_status, heater_state)
    room_state = metric_map["room_temp"].status
    outdoor_state = status_service.outdoor_temp_status(result)

    nodes = {
        "outdoor_air": VisualElementState(
            visual_id="outdoor_air",
            label="Наружный воздух",
            value=_temperature(parameters.outdoor_temp_c),
            detail=f"После рекуперации {_temperature(state.recovered_air_temp_c)}",
            state=outdoor_state,
            alarm_text=_alarm_marker(outdoor_state),
        ),
        "filter_bank": VisualElementState(
            visual_id="filter_bank",
            label="Фильтр",
            value=_pressure(state.filter_pressure_drop_pa),
            detail=f"Загрязнение {parameters.filter_contamination * 100:.0f}%",
            state=filter_state,
            alarm_text=_alarm_marker(filter_state),
        ),
        "heater_coil": VisualElementState(
            visual_id="heater_coil",
            label="Нагреватель",
            value=_power(state.heating_power_kw),
            detail=f"Загрузка {state.heater_load_ratio * 100:.0f}%",
            state=heater_state,
            alarm_text=_alarm_marker(heater_state),
        ),
        "supply_fan": VisualElementState(
            visual_id="supply_fan",
            label="Вентилятор",
            value=_power(state.fan_power_kw),
            detail=control_label,
            state=fan_state,
            alarm_text=_alarm_marker(fan_state),
        ),
        "supply_duct": VisualElementState(
            visual_id="supply_duct",
            label="Приточный воздуховод",
            value=_airflow(state.actual_airflow_m3_h),
            detail=f"Приток {_temperature(state.supply_temp_c)}",
            state=supply_state,
            alarm_text=_alarm_marker(supply_state),
        ),
        "room_zone": VisualElementState(
            visual_id="room_zone",
            label="Помещение",
            value=_temperature(state.room_temp_c),
            detail=(
                f"Теплобаланс {state.heat_balance_kw:+.1f} кВт | "
                f"Объём {parameters.room_volume_m3:.0f} м³"
            ),
            state=room_state,
            alarm_text=_alarm_marker(room_state),
        ),
    }
    sensors = {
        "sensor_outdoor_temp": VisualElementState(
            visual_id="sensor_outdoor_temp",
            label="T наружного воздуха",
            value=_temperature(parameters.outdoor_temp_c),
            detail="датчик OA",
            state=outdoor_state,
            alarm_text=_alarm_marker(outdoor_state),
        ),
        "sensor_supply_temp": VisualElementState(
            visual_id="sensor_supply_temp",
            label="T притока",
            value=_temperature(state.supply_temp_c),
            detail=f"Уставка {_temperature(parameters.supply_temp_setpoint_c)}",
            state=heater_state,
            alarm_text=_alarm_marker(heater_state),
        ),
        "sensor_room_temp": VisualElementState(
            visual_id="sensor_room_temp",
            label="T помещения",
            value=_temperature(state.room_temp_c),
            detail=f"Теплопритоки {parameters.room_heat_gain_kw:.1f} кВт",
            state=room_state,
            alarm_text=_alarm_marker(room_state),
        ),
        "sensor_filter_pressure": VisualElementState(
            visual_id="sensor_filter_pressure",
            label="ΔP фильтра",
            value=_pressure(state.filter_pressure_drop_pa),
            detail="датчик DP",
            state=filter_state,
            alarm_text=_alarm_marker(filter_state),
        ),
        "sensor_airflow": VisualElementState(
            visual_id="sensor_airflow",
            label="Расход",
            value=_airflow(state.actual_airflow_m3_h),
            detail=f"{airflow_ratio * 100:.0f}% от задания",
            state=flow_status,
            alarm_text=_alarm_marker(flow_status),
        ),
    }
    flow_detail = f"{airflow_ratio * 100:.0f}% от задания"
    flows = {
        "flow_outdoor_to_filter": VisualElementState(
            visual_id="flow_outdoor_to_filter",
            label="Подача наружного воздуха",
            value=_airflow(state.actual_airflow_m3_h),
            detail=flow_detail,
            state=flow_status,
            active=state.actual_airflow_m3_h > 250.0,
            intensity=flow_intensity,
        ),
        "flow_filter_to_heater": VisualElementState(
            visual_id="flow_filter_to_heater",
            label="Поток после фильтра",
            value=_airflow(state.actual_airflow_m3_h),
            detail=flow_detail,
            state=max_status(flow_status, filter_state),
            active=state.actual_airflow_m3_h > 250.0,
            intensity=flow_intensity,
        ),
        "flow_heater_to_fan": VisualElementState(
            visual_id="flow_heater_to_fan",
            label="Поток после нагревателя",
            value=_temperature(state.supply_temp_c),
            detail=_airflow(state.actual_airflow_m3_h),
            state=max_status(flow_status, heater_state),
            active=state.actual_airflow_m3_h > 250.0,
            intensity=flow_intensity,
        ),
        "flow_fan_to_room": VisualElementState(
            visual_id="flow_fan_to_room",
            label="Подача в помещение",
            value=_temperature(state.supply_temp_c),
            detail=_airflow(state.actual_airflow_m3_h),
            state=supply_state,
            active=state.actual_airflow_m3_h > 250.0,
            intensity=flow_intensity,
        ),
    }
    room_sensors, room_story = _build_room_sensor_map(
        result,
        room_context or {},
        status_service=status_service,
    )
    scenario_title = result.scenario_title or "Пользовательский режим"
    summary = (
        f"{scenario_title}: {control_label.lower()}, приток {_temperature(state.supply_temp_c)}, "
        f"расход {_airflow(state.actual_airflow_m3_h)}, "
        f"суммарная мощность {_power(state.total_power_kw)}, "
        f"помещение {parameters.room_volume_m3:.0f} м³."
    )
    if room_context:
        room_mode_label = str(
            ((room_context or {}).get("active_preset") or {}).get("label")
            or ((room_context or {}).get("label") or "room-model")
        )
        summary = summary[:-1] + f", режим {room_mode_label.lower()}."
    if room_story:
        summary = f"{summary} {room_story}"

    return VisualizationSignalMap(
        scenario_id=result.scenario_id,
        scenario_title=result.scenario_title,
        status=state.status,
        summary=summary,
        bindings_version=bindings_version,
        active_alarm_codes=sorted(alarm_codes),
        nodes=nodes,
        sensors=sensors,
        flows=flows,
        room_sensors=room_sensors,
        room_story=room_story,
    )


def _alarm_marker(status: OperationStatus) -> str | None:
    return "!" if status != OperationStatus.NORMAL else None


def _temperature(value: float) -> str:
    return f"{value:.1f} °C"


def _power(value: float) -> str:
    return f"{value:.1f} кВт"


def _pressure(value: float) -> str:
    return f"{value:.0f} Па"


def _airflow(value: float) -> str:
    return f"{value:.0f} м³/ч"


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def _build_room_sensor_map(
    result: SimulationResult,
    room_context: dict[str, object],
    status_service: StatusService | None = None,
) -> tuple[dict[str, VisualElementState], str | None]:
    status_service = status_service or StatusService()
    state = result.state
    parameters = result.parameters
    if not room_context:
        return {}, None

    occupancy_people = int(room_context.get("occupancy_people") or 0)
    design_occupancy = max(int(room_context.get("design_occupancy_people") or 1), 1)
    humidity_baseline = float(
        room_context.get("local_humidity_percent")
        or room_context.get("local_humidity_baseline_percent")
        or 42.0
    )
    fresh_air_target = max(
        float(room_context.get("fresh_air_target_l_s_per_person") or 12.0),
        1.0,
    )
    outdoor_co2_ppm = int(room_context.get("outdoor_co2_ppm") or 430)

    supply_l_s = state.actual_airflow_m3_h / 3.6
    occupancy_ratio = occupancy_people / design_occupancy
    fresh_air_l_s_person = supply_l_s / max(occupancy_people, 1)
    ventilation_ratio = fresh_air_l_s_person / fresh_air_target

    co2_ppm = outdoor_co2_ppm + 520.0 * occupancy_ratio + 700.0 * max(0.0, 1.0 - min(ventilation_ratio, 1.55))
    if occupancy_people == 0:
        co2_ppm = float(outdoor_co2_ppm) + 15.0
    co2_ppm += max(0.0, state.room_temp_c - 22.0) * 28.0

    humidity_percent = humidity_baseline
    humidity_percent += occupancy_ratio * 7.5
    humidity_percent += max(0.0, 1.0 - min(ventilation_ratio, 1.45)) * 10.0
    humidity_percent += max(0.0, parameters.room_heat_gain_kw - 6.0) * 0.25
    humidity_percent = _clamp(humidity_percent, 28.0, 82.0)

    room_statuses = status_service.build_room_sensor_statuses(
        co2_ppm=co2_ppm,
        humidity_percent=humidity_percent,
        occupancy_ratio=occupancy_ratio,
    )
    co2_metric_status = room_statuses["co2"]
    humidity_metric_status = room_statuses["humidity"]
    occupancy_metric_status = room_statuses["occupancy"]
    air_quality_status = room_statuses["air_quality"]
    active_preset = (room_context.get("active_preset") or {}).get("label")

    room_sensors = {
        "sensor_room_co2": VisualElementState(
            visual_id="sensor_room_co2",
            label="CO₂ помещения",
            value=f"{co2_ppm:.0f} ppm",
            detail=f"{fresh_air_l_s_person:.1f} л/с на человека",
            state=co2_metric_status,
            alarm_text=_alarm_marker(co2_metric_status),
        ),
        "sensor_room_humidity": VisualElementState(
            visual_id="sensor_room_humidity",
            label="Влажность помещения",
            value=f"{humidity_percent:.0f} %",
            detail=f"База {humidity_baseline:.0f}% | Комфорт 40–60%",
            state=humidity_metric_status,
            alarm_text=_alarm_marker(humidity_metric_status),
        ),
        "sensor_room_occupancy": VisualElementState(
            visual_id="sensor_room_occupancy",
            label="Занятость помещения",
            value=f"{occupancy_people} чел.",
            detail=f"{occupancy_ratio * 100:.0f}% от проектной загрузки",
            state=occupancy_metric_status,
            alarm_text=_alarm_marker(occupancy_metric_status),
        ),
        "sensor_room_air_quality": VisualElementState(
            visual_id="sensor_room_air_quality",
            label="Качество воздуха",
            value={
                OperationStatus.ALARM: "Плохо",
                OperationStatus.WARNING: "Под наблюдением",
                OperationStatus.NORMAL: "Комфортно",
            }[air_quality_status],
            detail=f"Режим {active_preset or 'Пользовательский'}",
            state=air_quality_status,
            alarm_text=_alarm_marker(air_quality_status),
        ),
    }

    if co2_metric_status == OperationStatus.ALARM:
        story = (
            "CO₂ вышел в красную зону: людей много, а свежего воздуха на человека уже не хватает."
        )
    elif humidity_metric_status != OperationStatus.NORMAL:
        story = (
            "Влажность подросла: помещение нужно активнее продувать, иначе комфорт начнёт падать."
        )
    elif occupancy_metric_status != OperationStatus.NORMAL:
        story = (
            "Помещение почти заполнено: пока комфорт держится, но запас по качеству воздуха сокращается."
        )
    else:
        story = "Комната в зелёной зоне: воздуха на человека достаточно, локальные датчики спокойны."

    return room_sensors, story
