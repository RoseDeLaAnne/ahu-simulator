import json
from pathlib import Path

from app.services.scenario_archive_service import ScenarioArchiveService
from app.services.simulation_service import SimulationService
from app.services.trend_service import TrendService
from app.simulation.state import OperationStatus
from app.simulation.scenarios import load_scenarios


def _build_simulation_service() -> SimulationService:
    scenario_path = Path(__file__).resolve().parents[2] / "data" / "scenarios" / "presets.json"
    return SimulationService(
        scenarios=load_scenarios(scenario_path),
        trend_service=TrendService(),
        default_scenario_id="midseason",
    )


def test_scenario_archive_snapshot_is_empty_before_save(tmp_path: Path) -> None:
    archive_service = ScenarioArchiveService(project_root=tmp_path)

    snapshot = archive_service.build_snapshot()

    assert snapshot.overall_status == OperationStatus.WARNING
    assert snapshot.total_entries == 0
    assert snapshot.latest_entry_path is None
    assert snapshot.entries == []


def test_scenario_archive_service_saves_and_lists_entries(tmp_path: Path) -> None:
    simulation_service = _build_simulation_service()
    archive_service = ScenarioArchiveService(project_root=tmp_path)

    scenario_result = simulation_service.preview_scenario("midseason")
    custom_result = simulation_service.preview(
        scenario_result.parameters.model_copy(update={"airflow_m3_h": 3150.0})
    )

    saved_scenario = archive_service.save_result(scenario_result)
    saved_custom = archive_service.save_result(custom_result)
    snapshot = archive_service.build_snapshot()

    assert (tmp_path / saved_scenario.entry.file_path).exists()
    assert (tmp_path / saved_custom.entry.file_path).exists()
    assert snapshot.overall_status == OperationStatus.NORMAL
    assert snapshot.total_entries == 2
    assert snapshot.latest_entry_path == saved_custom.entry.file_path
    assert snapshot.entries[0].source_type == "custom"
    assert snapshot.entries[1].source_type == "scenario"

    payload = json.loads((tmp_path / saved_scenario.entry.file_path).read_text(encoding="utf-8"))
    assert payload["result"]["scenario_id"] == "midseason"
    assert payload["result"]["state"]["status"] in {"normal", "warning", "alarm"}
