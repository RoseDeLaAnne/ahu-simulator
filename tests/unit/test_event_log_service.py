from pathlib import Path

from app.services.event_log_service import EventLogService
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


def test_event_log_service_records_simulation_and_artifact_events(tmp_path: Path) -> None:
    simulation_service = _build_service()
    event_log_service = EventLogService(project_root=tmp_path)

    previous_result = simulation_service.get_state()
    result = simulation_service.run_scenario("winter")
    simulation_event = event_log_service.record_simulation_event(
        result,
        previous_result=previous_result,
        trigger="scenario-select",
        source_type="dashboard",
    )

    assert simulation_event is not None
    assert (tmp_path / simulation_event.entry.file_path).exists()

    export_event = event_log_service.record_export_event(
        result,
        manifest_path="artifacts/exports/2026-04-04/pvu-export.manifest.json",
        source_type="dashboard",
    )

    snapshot = event_log_service.build_snapshot()
    assert export_event.entry.category.value == "export"
    assert snapshot.total_entries == 2
    assert snapshot.entries[0].artifact_path == export_event.entry.artifact_path
