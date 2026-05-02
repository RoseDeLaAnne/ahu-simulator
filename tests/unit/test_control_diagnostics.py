import pytest

from app.simulation.control import ControlTargetState, build_control_diagnostics
from app.simulation.equations import calculate_operating_point
from app.simulation.parameters import ControlMode, SimulationParameters


def test_auto_control_diagnostics_tracks_setpoint() -> None:
    parameters = SimulationParameters(
        outdoor_temp_c=-10,
        airflow_m3_h=2800,
        supply_temp_setpoint_c=20,
        heat_recovery_efficiency=0.55,
        heater_power_kw=40,
        filter_contamination=0.1,
        fan_speed_ratio=1.0,
        room_temp_c=21,
        room_heat_gain_kw=4,
        control_mode=ControlMode.AUTO,
    )

    operating_point = calculate_operating_point(parameters, step_minutes=10)
    diagnostics = build_control_diagnostics(parameters, operating_point)

    assert diagnostics.mode == ControlMode.AUTO
    assert diagnostics.target_state == ControlTargetState.TRACKING
    assert diagnostics.setpoint_gap_c == pytest.approx(0.0, abs=0.3)
    assert diagnostics.available_heater_kw >= diagnostics.required_heating_kw


def test_manual_control_diagnostics_marks_operator_override() -> None:
    parameters = SimulationParameters(
        outdoor_temp_c=-18,
        airflow_m3_h=3200,
        supply_temp_setpoint_c=22,
        heat_recovery_efficiency=0.5,
        heater_power_kw=20,
        filter_contamination=0.35,
        fan_speed_ratio=0.82,
        room_temp_c=21,
        room_heat_gain_kw=2.5,
        control_mode=ControlMode.MANUAL,
    )

    operating_point = calculate_operating_point(parameters, step_minutes=10)
    diagnostics = build_control_diagnostics(parameters, operating_point)

    assert diagnostics.mode == ControlMode.MANUAL
    assert diagnostics.target_state == ControlTargetState.OVERRIDE
    assert "вмешательство оператора" in diagnostics.summary
    assert diagnostics.commanded_fan_speed_ratio == pytest.approx(0.82, abs=0.01)
