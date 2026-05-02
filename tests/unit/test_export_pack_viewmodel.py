from datetime import datetime, timezone

from app.services.export_service import ResultExportEntry, ResultExportSnapshot
from app.simulation.state import OperationStatus
from app.ui.viewmodels.export_pack import build_result_export_view


def test_result_export_view_formats_snapshot() -> None:
    snapshot = ResultExportSnapshot(
        generated_at=datetime(2026, 4, 4, 22, 10, tzinfo=timezone.utc),
        overall_status=OperationStatus.NORMAL,
        summary="Собран 1 сценарный отчёт.",
        note="CSV/PDF доступны в локальной структуре артефактов.",
        target_directory="artifacts/exports",
        latest_report_id="pvu-report-20260404-221000",
        latest_csv_path="artifacts/exports/2026-04-04/pvu-export.csv",
        latest_pdf_path="artifacts/exports/2026-04-04/pvu-export.pdf",
        latest_manifest_path="artifacts/exports/2026-04-04/pvu-export.manifest.json",
        total_entries=1,
        entries=[
            ResultExportEntry(
                report_id="pvu-report-20260404-221000",
                captured_at=datetime(2026, 4, 4, 22, 10, tzinfo=timezone.utc),
                source_type="scenario",
                source_label="Межсезонье (midseason)",
                scenario_id="midseason",
                scenario_title="Межсезонье",
                status=OperationStatus.NORMAL,
                alarm_count=0,
                trend_points=13,
                finding_count=4,
                table_count=7,
                csv_path="artifacts/exports/2026-04-04/pvu-export.csv",
                pdf_path="artifacts/exports/2026-04-04/pvu-export.pdf",
                manifest_path="artifacts/exports/2026-04-04/pvu-export.manifest.json",
            )
        ],
    )

    view = build_result_export_view(snapshot)

    assert view.status_text == "Норма"
    assert view.summary_class_name == "status-pill status-normal"
    assert view.latest_report_id_text == "pvu-report-20260404-221000"
    assert view.latest_pdf_text.endswith(".pdf")
    assert view.latest_csv_download_url.startswith("/exports/result/download?path=")
    assert view.latest_pdf_download_url.startswith("/exports/result/download?path=")
    assert view.latest_manifest_download_url.startswith("/exports/result/download?path=")
    assert "metadata" in view.preview_text
    assert view.entries[0].status_text == "Норма"
    assert (
        view.entries[0].formats_text
        == "Форматы CSV и PDF; выводов: 4; таблиц: 7; трендовых точек: 13"
    )


def test_result_export_view_formats_empty_state() -> None:
    snapshot = ResultExportSnapshot(
        generated_at=datetime(2026, 4, 4, 22, 20, tzinfo=timezone.utc),
        overall_status=OperationStatus.WARNING,
        summary="Экспортов пока нет.",
        note="Соберите первый export-набор.",
        target_directory="artifacts/exports",
        total_entries=0,
        entries=[],
    )

    view = build_result_export_view(snapshot)

    assert view.status_text == "Риск"
    assert view.latest_report_id_text == "ещё не создан"
    assert view.latest_csv_text == "ещё не создан"
    assert view.latest_csv_download_url == "#"
    assert view.total_entries_text == "0"
    assert view.entries == []
