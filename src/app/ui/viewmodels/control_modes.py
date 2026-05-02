from __future__ import annotations

from dataclasses import dataclass

from app.simulation.control import ControlDiagnostics, ControlTargetState
from app.simulation.parameters import ControlMode


@dataclass(frozen=True)
class ControlModeView:
    mode_text: str
    target_status_text: str
    target_status_class_name: str
    summary: str
    setpoint_gap_text: str
    airflow_gap_text: str
    heater_band_text: str
    fan_command_text: str


def build_control_mode_view(control: ControlDiagnostics | None) -> ControlModeView:
    if control is None:
        return ControlModeView(
            mode_text="Не рассчитан",
            target_status_text="Нет данных",
            target_status_class_name="status-pill status-warning",
            summary="Контур управления ещё не был рассчитан.",
            setpoint_gap_text="—",
            airflow_gap_text="—",
            heater_band_text="—",
            fan_command_text="—",
        )

    return ControlModeView(
        mode_text="Ручной" if control.mode == ControlMode.MANUAL else "Автоматический",
        target_status_text=_target_status_text(control.target_state),
        target_status_class_name=_target_status_class_name(control.target_state),
        summary=control.summary,
        setpoint_gap_text=f"{control.setpoint_gap_c:+.2f} °C",
        airflow_gap_text=f"{control.airflow_gap_m3_h:+.0f} м³/ч",
        heater_band_text=(
            f"нужно {control.required_heating_kw:.2f} кВт / "
            f"доступно {control.available_heater_kw:.2f} кВт"
        ),
        fan_command_text=(
            f"{control.commanded_fan_speed_ratio:.2f} отн. ед. при задании "
            f"{control.requested_airflow_m3_h:.0f} м³/ч"
        ),
    )


def _target_status_text(state: ControlTargetState) -> str:
    mapping = {
        ControlTargetState.TRACKING: "Tracking",
        ControlTargetState.LIMITED: "Limited",
        ControlTargetState.OVERRIDE: "Override",
    }
    return mapping[state]


def _target_status_class_name(state: ControlTargetState) -> str:
    mapping = {
        ControlTargetState.TRACKING: "status-pill status-normal",
        ControlTargetState.LIMITED: "status-pill status-warning",
        ControlTargetState.OVERRIDE: "status-pill status-warning",
    }
    return mapping[state]
