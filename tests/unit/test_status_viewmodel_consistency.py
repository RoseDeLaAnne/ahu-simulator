from datetime import datetime, timezone

from app.services.export_service import ResultExportEntry, ResultExportSnapshot
from app.services.scenario_archive_service import ScenarioArchiveEntry, ScenarioArchiveSnapshot
from app.services.status_service import StatusService
from app.simulation.state import OperationStatus
from app.ui.viewmodels.export_pack import build_result_export_view
from app.ui.viewmodels.scenario_archive import build_scenario_archive_view
from app.ui.viewmodels.status_presenter import (
    status_class_name,
    status_color,
    status_summary,
    status_text,
)


def test_status_presenter_uses_normal_risk_alarm_contract() -> None:
    status_service = StatusService()

    for status in OperationStatus:
        assert status_text(status) == status_service.status_label(status)
        assert status_class_name(status) == status_service.status_class_name(status)
        assert status_color(status) == status_service.status_color(status)
        assert status_summary(status) == status_service.status_summary(status)


def test_export_and_archive_viewmodels_share_warning_presentation() -> None:
    captured_at = datetime(2026, 4, 18, 18, 10, tzinfo=timezone.utc)

    export_view = build_result_export_view(
        ResultExportSnapshot(
            generated_at=captured_at,
            overall_status=OperationStatus.WARNING,
            summary="Есть риск по статусам.",
            note="Status export note.",
            target_directory="artifacts/exports",
            latest_report_id="pvu-report-20260418-181000",
            latest_csv_path="artifacts/exports/2026-04-18/pvu-report.csv",
            latest_pdf_path="artifacts/exports/2026-04-18/pvu-report.pdf",
            latest_manifest_path="artifacts/exports/2026-04-18/pvu-report.manifest.json",
            total_entries=1,
            entries=[
                ResultExportEntry(
                    report_id="pvu-report-20260418-181000",
                    captured_at=captured_at,
                    source_type="scenario",
                    source_label="Ручной режим",
                    scenario_id="manual_mode",
                    scenario_title="Ручной режим",
                    status=OperationStatus.WARNING,
                    alarm_count=2,
                    trend_points=13,
                    finding_count=4,
                    table_count=7,
                    csv_path="artifacts/exports/2026-04-18/pvu-report.csv",
                    pdf_path="artifacts/exports/2026-04-18/pvu-report.pdf",
                    manifest_path="artifacts/exports/2026-04-18/pvu-report.manifest.json",
                )
            ],
        )
    )
    archive_view = build_scenario_archive_view(
        ScenarioArchiveSnapshot(
            generated_at=captured_at,
            overall_status=OperationStatus.WARNING,
            summary="Архив содержит риск-снимок.",
            note="Archive status note.",
            target_directory="artifacts/scenario-archive",
            latest_entry_path="artifacts/scenario-archive/2026-04-18/pvu-run-20260418-181000.json",
            total_entries=1,
            entries=[
                ScenarioArchiveEntry(
                    archive_id="pvu-run-20260418-181000",
                    captured_at=captured_at,
                    source_type="scenario",
                    source_label="Ручной режим",
                    scenario_id="manual_mode",
                    scenario_title="Ручной режим",
                    status=OperationStatus.WARNING,
                    alarm_count=2,
                    supply_temp_c=22.0,
                    room_temp_c=21.0,
                    actual_airflow_m3_h=2302.56,
                    total_power_kw=16.76,
                    file_path="artifacts/scenario-archive/2026-04-18/pvu-run-20260418-181000.json",
                )
            ],
        )
    )

    assert export_view.entries[0].status_text == "Риск"
    assert archive_view.entries[0].status_text == "Риск"
    assert export_view.entries[0].status_class_name == archive_view.entries[0].status_class_name
    assert export_view.status_text == "Риск"
    assert archive_view.status_text == "Риск"
