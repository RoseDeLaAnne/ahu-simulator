from datetime import datetime, timezone
from pathlib import Path

from app.services.comparison_service import (
    RunComparisonNamedSnapshot,
    RunComparisonExportEntry,
    RunComparisonSnapshot,
    RunComparisonSource,
)
from app.simulation.scenarios import load_scenarios
from app.services.simulation_service import SimulationService
from app.services.trend_service import TrendService
from app.simulation.parameters import ControlMode
from app.simulation.state import OperationStatus
from app.ui.viewmodels.run_comparison import build_run_comparison_view


def test_run_comparison_view_formats_sources_and_exports() -> None:
    simulation_service = SimulationService(
        scenarios=load_scenarios(Path("data/scenarios/presets.json")),
        trend_service=TrendService(),
        default_scenario_id="midseason",
    )
    result = simulation_service.preview_scenario("winter")
    snapshot = RunComparisonSnapshot(
        generated_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
        overall_status=OperationStatus.NORMAL,
        summary="Снимки готовы к сравнению.",
        note="Дельты считаются как после - до.",
        available_sources=[
            RunComparisonSource(
                reference_id="active-run",
                source_type="active",
                source_label="Пользовательский режим",
                display_label="Текущий прогон — Пользовательский режим",
                captured_at=datetime(2026, 4, 18, 11, 55, tzinfo=timezone.utc),
                control_mode=ControlMode.AUTO,
                status=OperationStatus.NORMAL,
                alarm_count=0,
                step_minutes=10,
                horizon_minutes=120,
                point_count=13,
            ),
            RunComparisonSource(
                reference_id="snapshot:before",
                source_type="snapshot",
                source_id="comparison-before",
                source_label="До очистки",
                display_label="До — До очистки",
                captured_at=datetime(2026, 4, 18, 11, 52, tzinfo=timezone.utc),
                role="before",
                scenario_id="winter",
                scenario_title="Зима",
                control_mode=ControlMode.AUTO,
                status=OperationStatus.NORMAL,
                alarm_count=0,
                step_minutes=10,
                horizon_minutes=120,
                point_count=13,
            ),
            RunComparisonSource(
                reference_id="archive:pvu-run-20260418-115000",
                source_type="archive",
                source_label="Зима (winter)",
                display_label="Архив сценариев — Зима (winter)",
                captured_at=datetime(2026, 4, 18, 11, 50, tzinfo=timezone.utc),
                scenario_id="winter",
                scenario_title="Зима",
                control_mode=ControlMode.AUTO,
                status=OperationStatus.WARNING,
                alarm_count=2,
                step_minutes=10,
                horizon_minutes=120,
                point_count=13,
            ),
        ],
        named_snapshots=[
            RunComparisonNamedSnapshot(
                snapshot_id="comparison-before",
                role="before",
                label="До очистки",
                captured_at=datetime(2026, 4, 18, 11, 52, tzinfo=timezone.utc),
                source_type="active",
                source_id="active-run",
                source_label="Зима (winter)",
                scenario_id="winter",
                scenario_title="Зима",
                parameter_hash="abc",
                compatibility_metadata={"step_minutes": 10},
                result=result,
            )
        ],
        default_before_reference_id="archive:pvu-run-20260418-115000",
        default_after_reference_id="active-run",
        latest_comparison_id="pvu-comparison-20260418-120000",
        latest_csv_path="artifacts/exports/2026-04-18/pvu-comparison-20260418-120000.csv",
        latest_pdf_path="artifacts/exports/2026-04-18/pvu-comparison-20260418-120000.pdf",
        latest_manifest_path="artifacts/exports/2026-04-18/pvu-comparison-20260418-120000.manifest.json",
        total_exports=1,
        entries=[
            RunComparisonExportEntry(
                comparison_id="pvu-comparison-20260418-120000",
                captured_at=datetime(2026, 4, 18, 12, 0, tzinfo=timezone.utc),
                before_label="Архив сценариев — Зима (winter)",
                after_label="Текущий прогон — Пользовательский режим",
                metric_count=12,
                trend_points=13,
                csv_path="artifacts/exports/2026-04-18/pvu-comparison-20260418-120000.csv",
                pdf_path="artifacts/exports/2026-04-18/pvu-comparison-20260418-120000.pdf",
                manifest_path="artifacts/exports/2026-04-18/pvu-comparison-20260418-120000.manifest.json",
            )
        ],
    )

    view = build_run_comparison_view(snapshot)

    assert view.status_text == "Норма"
    assert view.default_before_reference_id == "archive:pvu-run-20260418-115000"
    assert view.default_after_reference_id == "active-run"
    assert view.latest_comparison_id_text == "pvu-comparison-20260418-120000"
    assert view.source_options[0]["label"].startswith("Текущий прогон |")
    assert view.source_options[1]["label"].startswith("Снимок До/После |")
    assert view.source_options[2]["label"].startswith("Архив сценариев |")
    assert view.named_before_text.startswith("До: До очистки")
    assert view.named_after_text == "После: ещё не зафиксирован"
    assert view.entries[0].pair_text.endswith("Текущий прогон — Пользовательский режим")
    assert view.entries[0].formats_text == "CSV/PDF; метрик: 12; точек дельты: 13"
