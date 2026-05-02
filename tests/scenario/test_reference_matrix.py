import json
from pathlib import Path

import pytest

from app.services.simulation_service import SimulationService
from app.services.trend_service import TrendService
from app.simulation.parameters import SimulationParameters
from app.simulation.scenarios import load_scenarios


def _build_service() -> SimulationService:
    scenario_path = Path(__file__).resolve().parents[2] / "data" / "scenarios" / "presets.json"
    return SimulationService(
        scenarios=load_scenarios(scenario_path),
        trend_service=TrendService(),
        default_scenario_id="midseason",
    )


def _load_reference_matrix() -> list[dict]:
    matrix_path = Path(__file__).resolve().parents[2] / "data" / "validation" / "reference_points.json"
    return json.loads(matrix_path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", _load_reference_matrix(), ids=lambda case: case["id"])
def test_reference_operating_points(case: dict) -> None:
    service = _build_service()
    parameters = SimulationParameters.model_validate(case["parameters"])

    result = service.run(parameters)
    expected = case["expected"]
    alarm_codes = {alarm.code for alarm in result.alarms}

    assert result.state.status == expected["status"]
    assert expected["supply_temp_c"][0] <= result.state.supply_temp_c <= expected["supply_temp_c"][1]
    assert expected["room_temp_c"][0] <= result.state.room_temp_c <= expected["room_temp_c"][1]
    assert (
        expected["actual_airflow_m3_h"][0]
        <= result.state.actual_airflow_m3_h
        <= expected["actual_airflow_m3_h"][1]
    )
    assert expected["total_power_kw"][0] <= result.state.total_power_kw <= expected["total_power_kw"][1]
    assert set(expected["alarm_codes"]).issubset(alarm_codes)
