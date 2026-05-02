import csv
import hashlib
import json
from pathlib import Path

from app.services.export_service import ExportService
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


def test_export_snapshot_is_empty_before_build(tmp_path: Path) -> None:
    export_service = ExportService(project_root=tmp_path)

    snapshot = export_service.build_snapshot()

    assert snapshot.overall_status == OperationStatus.WARNING
    assert snapshot.total_entries == 0
    assert snapshot.latest_manifest_path is None
    assert snapshot.entries == []


def test_export_service_builds_report_contract(tmp_path: Path) -> None:
    simulation_service = _build_simulation_service()
    export_service = ExportService(project_root=tmp_path)
    result = simulation_service.preview_scenario("midseason")

    report = export_service.build_report(result, simulation_service.get_session())

    assert report.schema_version == "scenario-report.v2"
    assert report.metadata.report_id.startswith("pvu-report-")
    assert report.metadata.status == result.state.status
    assert [section.section_id for section in report.sections] == [
        "metadata",
        "findings",
        "parameters",
        "state",
        "status_legend",
        "status_events",
        "trend",
    ]
    assert report.chart_specs[0].chart_id == "trend_temperature_power"
    assert len(report.findings) == 4
    assert report.tables[0].table_id == "summary"
    assert report.tables[1].table_id == "status"
    assert report.tables[2].table_id == "status_legend"
    assert report.tables[-1].table_id == "trend"


def test_export_service_creates_csv_pdf_and_manifest(tmp_path: Path) -> None:
    simulation_service = _build_simulation_service()
    export_service = ExportService(project_root=tmp_path)
    result = simulation_service.preview_scenario("midseason")

    build_result = export_service.export_result(result, simulation_service.get_session())
    snapshot = export_service.build_snapshot()

    csv_path = tmp_path / build_result.entry.csv_path
    pdf_path = tmp_path / build_result.entry.pdf_path
    manifest_path = tmp_path / build_result.entry.manifest_path

    assert csv_path.exists()
    assert pdf_path.exists()
    assert manifest_path.exists()
    assert snapshot.overall_status == OperationStatus.NORMAL
    assert snapshot.total_entries == 1
    assert snapshot.latest_report_id == build_result.entry.report_id
    assert snapshot.latest_csv_path == build_result.entry.csv_path
    assert snapshot.entries[0].source_type == "scenario"

    csv_text = csv_path.read_text(encoding="utf-8")
    csv_rows = list(csv.reader(csv_text.splitlines()))
    section_markers = [
        row[1]
        for row in csv_rows
        if len(row) >= 3
        and row[0] == "section"
        and row[1] in {"parameters", "state", "status_legend", "status_events", "trend"}
    ]
    assert csv_rows[0] == ["section", "key", "value"]
    assert ["metadata", "schema_version", "scenario-report.v2"] in csv_rows
    assert section_markers == [
        "parameters",
        "state",
        "status_legend",
        "status_events",
        "trend",
    ]
    assert any(row[:2] == ["metadata", "идентификатор_отчёта"] for row in csv_rows)
    assert any(row[:2] == ["status_legend", "Норма"] for row in csv_rows)
    assert "Предупреждение" not in csv_text
    assert "[warning]" not in csv_text
    assert "normal" not in csv_text
    assert "warning" not in csv_text
    assert "alarm" not in csv_text

    pdf_bytes = pdf_path.read_bytes()
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 4_000

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "scenario-report.v2"
    assert manifest["report_id"] == build_result.entry.report_id
    assert manifest["entry"]["report_id"] == build_result.entry.report_id
    assert manifest["entry"]["schema_version"] == "scenario-report.v2"
    assert manifest["report"]["schema_version"] == "scenario-report.v2"
    assert manifest["report"]["metadata"]["report_id"] == build_result.entry.report_id
    assert manifest["artifact_checksums"]["csv"] == _sha256(csv_path)
    assert manifest["artifact_checksums"]["pdf"] == _sha256(pdf_path)
    assert manifest["artifact_sizes"]["manifest"] == manifest_path.stat().st_size
    assert manifest["artifacts"][-1]["artifact_id"] == "manifest"
    assert manifest["artifacts"][0]["size_bytes"] == csv_path.stat().st_size


def test_export_service_builds_preview_without_writing_files(tmp_path: Path) -> None:
    simulation_service = _build_simulation_service()
    export_service = ExportService(project_root=tmp_path)
    result = simulation_service.preview_scenario("midseason")

    preview = export_service.preview_result(result, simulation_service.get_session())

    assert preview.report.schema_version == "scenario-report.v2"
    assert preview.planned_sections == [
        "metadata",
        "findings",
        "parameters",
        "state",
        "status_legend",
        "status_events",
        "trend",
    ]
    assert preview.planned_artifacts == ["csv", "pdf", "manifest"]
    assert "Предпросмотр отчёта" in preview.summary
    assert not (tmp_path / "artifacts" / "exports").exists()


def test_export_service_respects_runtime_directory_override(
    monkeypatch,
    tmp_path: Path,
) -> None:
    simulation_service = _build_simulation_service()
    runtime_root = tmp_path / "runtime"
    monkeypatch.setenv("AHU_SIMULATOR_RUNTIME_DIR", str(runtime_root))
    export_service = ExportService(project_root=tmp_path)
    result = simulation_service.preview_scenario("midseason")

    build_result = export_service.export_result(result, simulation_service.get_session())

    assert build_result.entry.csv_path.startswith("artifacts/exports/")
    assert (runtime_root / "exports").exists()
    assert export_service.build_snapshot().latest_csv_path == build_result.entry.csv_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
