import pytest

from app.simulation.equations import calculate_operating_point
from app.simulation.parameters import SimulationParameters


def test_heater_hits_setpoint_when_capacity_is_sufficient() -> None:
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
    )

    operating_point = calculate_operating_point(parameters, step_minutes=10)

    assert operating_point.supply_temp_c == pytest.approx(20.0, abs=0.3)
    assert operating_point.heating_power_kw > 0


def test_dirty_filter_reduces_airflow_and_raises_pressure_drop() -> None:
    clean = calculate_operating_point(
        SimulationParameters(filter_contamination=0.0, fan_speed_ratio=1.0),
        step_minutes=10,
    )
    dirty = calculate_operating_point(
        SimulationParameters(filter_contamination=0.95, fan_speed_ratio=1.0),
        step_minutes=10,
    )

    assert dirty.actual_airflow_m3_h < clean.actual_airflow_m3_h
    assert dirty.filter_pressure_drop_pa > clean.filter_pressure_drop_pa
