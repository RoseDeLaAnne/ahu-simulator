from pathlib import Path

from app.services.simulation_service import SimulationService
from app.services.status_service import StatusService
from app.services.trend_service import TrendService
from app.simulation.scenarios import load_scenarios
from app.simulation.state import OperationStatus
from app.ui.viewmodels.concept03_kpi import build_concept03_kpi_view


PROJECT_ROOT = Path(__file__).resolve().parents[4]


def test_concept03_kpi_view_builds_six_operator_rows() -> None:
    result = _preview("baseline_office_winter")
    view = build_concept03_kpi_view(result)

    assert [row.kpi_id for row in view.rows] == [
        "kpi-row-airflow",
        "kpi-row-pressure",
        "kpi-row-supply-temp",
        "kpi-row-humidity",
        "kpi-row-recovery",
        "kpi-row-power",
    ]
    # «­» — мягкий перенос для мобильной KPI-плитки.
    assert view.rows[0].label == "Производи­тельность"
    assert view.rows[0].unit == "м³/ч"
    assert "Задание: 3 600 м³/ч" == view.rows[0].setpoint_text
    assert view.rows[3].state == "unavailable"
    assert view.rows[3].value_text == "Недоступно"


def test_concept03_kpi_view_maps_warning_alarm_and_progress() -> None:
    result = _preview("dirty_filter")
    view = build_concept03_kpi_view(result)
    rows = {row.kpi_id: row for row in view.rows}

    assert rows["kpi-row-airflow"].state == "warning"
    assert rows["kpi-row-pressure"].state == "alarm"
    assert "c03-kpi-row--warn" in rows["kpi-row-airflow"].class_name
    assert "c03-kpi-row--alarm" in rows["kpi-row-pressure"].class_name
    assert rows["kpi-row-pressure"].progress_style == {"width": "100%"}
    assert rows["kpi-row-supply-temp"].progress_style == {"width": "100%"}


def test_status_service_exposes_concept03_metric_status_ids() -> None:
    status_map = StatusService().build_metric_status_map_for_concept03(
        _preview("dirty_filter")
    )

    assert status_map["kpi-row-airflow"] == OperationStatus.WARNING
    assert status_map["kpi-row-pressure"] == OperationStatus.ALARM
    assert status_map["kpi-row-humidity"] == OperationStatus.NORMAL


def _preview(scenario_id: str):
    service = SimulationService(
        scenarios=load_scenarios(PROJECT_ROOT / "data" / "scenarios" / "presets.json"),
        trend_service=TrendService(),
        default_scenario_id="baseline_office_winter",
    )
    return service.preview_scenario(scenario_id)
