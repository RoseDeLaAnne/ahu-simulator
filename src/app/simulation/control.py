from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.simulation.equations import OperatingPoint
from app.simulation.parameters import ControlMode, SimulationParameters


class ControlTargetState(StrEnum):
    TRACKING = "tracking"
    LIMITED = "limited"
    OVERRIDE = "override"


class ControlDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: ControlMode
    target_state: ControlTargetState
    summary: str
    setpoint_gap_c: float
    airflow_gap_m3_h: float
    required_heating_kw: float
    available_heater_kw: float
    commanded_fan_speed_ratio: float
    requested_airflow_m3_h: float


def build_control_diagnostics(
    parameters: SimulationParameters,
    operating_point: OperatingPoint,
) -> ControlDiagnostics:
    setpoint_gap_c = round(
        parameters.supply_temp_setpoint_c - operating_point.supply_temp_c,
        2,
    )
    airflow_gap_m3_h = round(
        parameters.airflow_m3_h - operating_point.actual_airflow_m3_h,
        2,
    )

    if parameters.control_mode == ControlMode.MANUAL:
        target_state = ControlTargetState.OVERRIDE
        summary = (
            "Ручной режим фиксирует вмешательство оператора: оператор сам задаёт "
            "уставку и скорость вентилятора, а система лишь показывает фактический "
            "результат без автоматической перенастройки сценария."
        )
    elif setpoint_gap_c <= 0.3:
        target_state = ControlTargetState.TRACKING
        summary = (
            "Автоматический режим удерживает температуру притока около уставки; "
            "доступный запас нагревателя можно использовать как резерв."
        )
    else:
        target_state = ControlTargetState.LIMITED
        summary = (
            "Автоматический режим пытается удерживать уставку, но упирается "
            "в доступную мощность нагревателя или текущие ограничения режима."
        )

    return ControlDiagnostics(
        mode=parameters.control_mode,
        target_state=target_state,
        summary=summary,
        setpoint_gap_c=setpoint_gap_c,
        airflow_gap_m3_h=airflow_gap_m3_h,
        required_heating_kw=operating_point.required_heating_kw,
        available_heater_kw=operating_point.available_heater_kw,
        commanded_fan_speed_ratio=round(parameters.fan_speed_ratio, 2),
        requested_airflow_m3_h=round(parameters.airflow_m3_h, 2),
    )
