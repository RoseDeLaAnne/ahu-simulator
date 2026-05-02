from pathlib import Path
import csv
import json

import pytest

from app.services.comparison_service import (
    ACTIVE_RUN_REFERENCE_ID,
    COMPARISON_SCHEMA_VERSION,
    RunComparisonCompatibilityError,
    RunComparisonService,
)
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


def test_run_comparison_snapshot_requires_archive_entry(tmp_path: Path) -> None:
    simulation_service = _build_simulation_service()
    archive_service = ScenarioArchiveService(project_root=tmp_path)
    comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=archive_service,
    )

    snapshot = comparison_service.build_snapshot(
        simulation_service.get_session().current_result,
        simulation_service.get_session(),
    )

    assert snapshot.overall_status == OperationStatus.WARNING
    assert snapshot.default_before_reference_id is None
    assert snapshot.default_after_reference_id == ACTIVE_RUN_REFERENCE_ID
    assert snapshot.available_sources[0].reference_id == ACTIVE_RUN_REFERENCE_ID


def test_run_comparison_builds_metric_and_trend_deltas(tmp_path: Path) -> None:
    simulation_service = _build_simulation_service()
    archive_service = ScenarioArchiveService(project_root=tmp_path)
    comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=archive_service,
    )
    archived_result = simulation_service.preview_scenario("winter")
    save_result = archive_service.save_result(archived_result)
    active_result = simulation_service.preview_scenario("midseason")

    comparison = comparison_service.build_comparison_from_references(
        f"archive:{save_result.entry.archive_id}",
        ACTIVE_RUN_REFERENCE_ID,
        active_result,
        simulation_service.get_session(),
    )

    assert comparison.compatibility.is_compatible is True
    assert comparison.before_source.source_type == "archive"
    assert comparison.after_source.source_type == "active"
    assert len(comparison.metric_deltas) == 12
    assert len(comparison.trend_deltas) == len(active_result.trend.points)
    assert any(metric.metric_id == "total_power_kw" for metric in comparison.metric_deltas)
    assert comparison.schema_version == COMPARISON_SCHEMA_VERSION
    assert comparison.comparison_status in {
        OperationStatus.NORMAL,
        OperationStatus.WARNING,
        OperationStatus.ALARM,
    }
    assert comparison.interpretation.top_deltas
    assert "Улучшилось" in comparison.interpretation.summary


def test_run_comparison_saves_named_before_after_snapshots(tmp_path: Path) -> None:
    simulation_service = _build_simulation_service()
    archive_service = ScenarioArchiveService(project_root=tmp_path)
    comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=archive_service,
    )

    before = comparison_service.save_before(
        simulation_service.preview_scenario("winter"),
        label="До очистки фильтра",
        notes="baseline",
    )
    after = comparison_service.save_after(
        simulation_service.preview_scenario("midseason"),
        label="После настройки",
    )
    snapshot = comparison_service.build_snapshot(
        simulation_service.preview_scenario("midseason"),
        simulation_service.get_session(),
    )

    assert before.snapshot.role == "before"
    assert before.snapshot.label == "До очистки фильтра"
    assert before.snapshot.notes == "baseline"
    assert before.snapshot.parameter_hash
    assert after.snapshot.role == "after"
    assert (tmp_path / "artifacts" / "comparison-snapshots" / "before.json").exists()
    assert snapshot.default_before_reference_id == "snapshot:before"
    assert snapshot.default_after_reference_id == "snapshot:after"
    assert [item.role for item in snapshot.named_snapshots] == ["before", "after"]
    assert snapshot.available_sources[0].reference_id == "snapshot:before"
    assert snapshot.available_sources[1].reference_id == "snapshot:after"


def test_run_comparison_builds_from_named_snapshots(tmp_path: Path) -> None:
    simulation_service = _build_simulation_service()
    archive_service = ScenarioArchiveService(project_root=tmp_path)
    comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=archive_service,
    )
    comparison_service.save_before(simulation_service.preview_scenario("winter"))
    comparison_service.save_after(simulation_service.preview_scenario("midseason"))

    comparison = comparison_service.build_comparison_from_references(
        "snapshot:before",
        "snapshot:after",
        simulation_service.preview_scenario("midseason"),
        simulation_service.get_session(),
    )

    assert comparison.before_source.source_type == "snapshot"
    assert comparison.before_source.role == "before"
    assert comparison.after_source.role == "after"
    assert comparison.compatibility.is_compatible is True
    assert comparison.interpretation.summary.startswith("Улучшилось")


def test_run_comparison_detects_incompatible_pairs(tmp_path: Path) -> None:
    simulation_service = _build_simulation_service()
    archive_service = ScenarioArchiveService(project_root=tmp_path)
    comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=archive_service,
    )
    archived_result = simulation_service.preview(
        simulation_service.get_scenario("winter").parameters.model_copy(
            update={"step_minutes": 5}
        )
    )
    save_result = archive_service.save_result(archived_result)

    comparison = comparison_service.build_comparison_from_references(
        f"archive:{save_result.entry.archive_id}",
        ACTIVE_RUN_REFERENCE_ID,
        simulation_service.preview_scenario("winter"),
        simulation_service.get_session(),
    )

    assert comparison.compatibility.is_compatible is False
    assert comparison.metric_deltas == []
    assert any("Шаг времени" in issue for issue in comparison.compatibility.issues)


def test_run_comparison_export_creates_csv_pdf_and_manifest(tmp_path: Path) -> None:
    simulation_service = _build_simulation_service()
    archive_service = ScenarioArchiveService(project_root=tmp_path)
    comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=archive_service,
    )
    save_result = archive_service.save_result(
        simulation_service.preview_scenario("winter")
    )
    comparison = comparison_service.build_comparison_from_references(
        f"archive:{save_result.entry.archive_id}",
        ACTIVE_RUN_REFERENCE_ID,
        simulation_service.preview_scenario("midseason"),
        simulation_service.get_session(),
    )

    export_result = comparison_service.export_comparison(comparison)
    snapshot = comparison_service.build_snapshot(
        simulation_service.preview_scenario("midseason"),
        simulation_service.get_session(),
    )

    assert (tmp_path / export_result.entry.csv_path).exists()
    assert (tmp_path / export_result.entry.pdf_path).exists()
    assert (tmp_path / export_result.entry.manifest_path).exists()
    assert snapshot.latest_comparison_id == export_result.entry.comparison_id
    assert snapshot.total_exports == 1
    manifest = json.loads((tmp_path / export_result.entry.manifest_path).read_text(encoding="utf-8"))
    assert manifest["schema_version"] == COMPARISON_SCHEMA_VERSION
    assert manifest["entry"]["schema_version"] == COMPARISON_SCHEMA_VERSION
    assert manifest["entry"]["before_reference_id"].startswith("archive:")
    assert manifest["entry"]["after_reference_id"] == ACTIVE_RUN_REFERENCE_ID
    assert manifest["entry"]["interpretation_summary"]
    assert manifest["artifact_sizes"]["csv"] > 0
    with (tmp_path / export_result.entry.csv_path).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert ["метаданные", "schema_version", COMPARISON_SCHEMA_VERSION] in rows
    assert any(row[:2] == ["интерпретация", "улучшилось"] for row in rows)


def test_run_comparison_export_rejects_incompatible_pair(tmp_path: Path) -> None:
    simulation_service = _build_simulation_service()
    archive_service = ScenarioArchiveService(project_root=tmp_path)
    comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=archive_service,
    )
    save_result = archive_service.save_result(
        simulation_service.preview(
            simulation_service.get_scenario("winter").parameters.model_copy(
                update={"step_minutes": 5}
            )
        )
    )
    comparison = comparison_service.build_comparison_from_references(
        f"archive:{save_result.entry.archive_id}",
        ACTIVE_RUN_REFERENCE_ID,
        simulation_service.preview_scenario("winter"),
        simulation_service.get_session(),
    )

    with pytest.raises(RunComparisonCompatibilityError):
        comparison_service.export_comparison(comparison)
