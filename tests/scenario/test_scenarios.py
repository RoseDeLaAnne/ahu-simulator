from pathlib import Path

from app.services.simulation_service import SimulationService
from app.services.trend_service import TrendService
from app.simulation.scenarios import load_scenarios


def _build_service() -> SimulationService:
    scenario_path = Path(__file__).resolve().parents[2] / "data" / "scenarios" / "presets.json"
    return SimulationService(
        scenarios=load_scenarios(scenario_path),
        trend_service=TrendService(),
        default_scenario_id="midseason",
    )


def test_winter_scenario_produces_heating_load() -> None:
    service = _build_service()
    result = service.run_scenario("winter")

    assert result.state.heating_power_kw > 0
    assert result.state.supply_temp_c >= 18


def test_dirty_filter_scenario_contains_filter_alarm() -> None:
    service = _build_service()
    result = service.run_scenario("dirty_filter")

    assert any(alarm.code.startswith("FILTER") for alarm in result.alarms)


def test_manual_mode_scenario_marks_warning_state() -> None:
    service = _build_service()
    result = service.run_scenario("manual_mode")

    assert result.state.status == "warning"
    assert any(alarm.code == "MANUAL_MODE" for alarm in result.alarms)


def test_summer_scenario_requires_less_heating_than_winter() -> None:
    service = _build_service()
    winter = service.run_scenario("winter")
    summer = service.run_scenario("summer")

    assert summer.parameters.outdoor_temp_c > winter.parameters.outdoor_temp_c
    assert summer.state.heating_power_kw < winter.state.heating_power_kw


def test_peak_load_scenario_increases_total_power_vs_midseason() -> None:
    service = _build_service()
    midseason = service.run_scenario("midseason")
    peak_load = service.run_scenario("peak_load")

    assert peak_load.state.total_power_kw > midseason.state.total_power_kw
    assert peak_load.state.filter_pressure_drop_pa > midseason.state.filter_pressure_drop_pa
