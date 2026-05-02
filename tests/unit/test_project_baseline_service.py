from pathlib import Path

from app.services.project_baseline_service import ProjectBaselineService
from app.simulation.state import OperationStatus


def test_project_baseline_service_loads_locked_scope() -> None:
    project_root = Path(__file__).resolve().parents[2]

    snapshot = ProjectBaselineService(project_root=project_root).build_snapshot()

    assert snapshot.overall_status == OperationStatus.NORMAL
    assert snapshot.baseline_version == 1
    assert snapshot.subject.subject_id == "generalized_supply_ahu"
    assert len(snapshot.operator_inputs) == 10
    assert len(snapshot.fixed_model_inputs) == 5
    assert len(snapshot.outputs) == 10
    assert snapshot.defense_scenarios[-1].scenario_id == "manual_mode"
    assert any(layer.layer_id == "validation_basis" for layer in snapshot.validation_layers)
