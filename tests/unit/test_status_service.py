from pathlib import Path

from app.services.simulation_service import SimulationService
from app.services.status_service import StatusService
from app.services.trend_service import TrendService
from app.simulation.scenarios import load_scenarios
from app.simulation.state import OperationStatus


def _build_service() -> SimulationService:
    scenario_path = Path(__file__).resolve().parents[2] / "data" / "scenarios" / "presets.json"
    return SimulationService(
        scenarios=load_scenarios(scenario_path),
        trend_service=TrendService(),
        default_scenario_id="midseason",
    )


def test_status_service_projects_warning_and_alarm_metrics_from_result() -> None:
    simulation_service = _build_service()
    status_service = StatusService()

    dirty_filter = simulation_service.preview_scenario("dirty_filter")
    dirty_metrics = status_service.build_metric_status_map(dirty_filter)

    assert dirty_metrics["filter_pressure"].status == OperationStatus.ALARM
    assert dirty_metrics["airflow"].status == OperationStatus.WARNING
    assert status_service.build_alert_block_status(dirty_filter) == OperationStatus.ALARM

    manual_mode = simulation_service.preview_scenario("manual_mode")
    manual_metrics = status_service.build_metric_status_map(manual_mode)

    assert manual_metrics["airflow"].status == OperationStatus.WARNING
    assert manual_metrics["total_power"].status == OperationStatus.WARNING
    assert status_service.build_alert_block_status(manual_mode) == OperationStatus.WARNING


def test_status_service_owns_user_facing_status_presentation() -> None:
    status_service = StatusService()

    expected = {
        OperationStatus.NORMAL: ("Норма", "status-pill status-normal", "#22c55e"),
        OperationStatus.WARNING: ("Риск", "status-pill status-warning", "#facc15"),
        OperationStatus.ALARM: ("Авария", "status-pill status-alarm", "#ef4444"),
    }

    for status, (label, class_name, color_hex) in expected.items():
        assert status_service.status_label(status) == label
        assert status_service.status_class_name(status) == class_name
        assert status_service.status_color(status) == color_hex
        assert status_service.status_summary(status)

    legend = {entry.status: entry for entry in status_service.build_status_legend()}
    assert set(legend) == set(expected)
    for status, entry in legend.items():
        label, class_name, color_hex = expected[status]
        assert entry.label == label
        assert entry.class_name == class_name
        assert entry.color_hex == color_hex
        assert entry.summary == status_service.status_summary(status)
