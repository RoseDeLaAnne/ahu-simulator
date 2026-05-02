from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from app.services.export_service import ResultExportEntry, ResultExportSnapshot
from app.ui.viewmodels.status_presenter import status_class_name, status_text


@dataclass(frozen=True)
class ResultExportEntryView:
    captured_at_text: str
    source_text: str
    status_text: str
    status_class_name: str
    formats_text: str
    csv_path_text: str
    pdf_path_text: str
    manifest_path_text: str
    csv_download_url: str
    pdf_download_url: str
    manifest_download_url: str


@dataclass(frozen=True)
class ResultExportView:
    status_text: str
    summary_text: str
    summary_class_name: str
    note: str
    generated_at_text: str
    target_directory_text: str
    latest_report_id_text: str
    latest_csv_text: str
    latest_pdf_text: str
    latest_manifest_text: str
    latest_csv_download_url: str
    latest_pdf_download_url: str
    latest_manifest_download_url: str
    preview_text: str
    total_entries_text: str
    entries: list[ResultExportEntryView]


def build_result_export_view(snapshot: ResultExportSnapshot) -> ResultExportView:
    return ResultExportView(
        status_text=status_text(snapshot.overall_status),
        summary_text=snapshot.summary,
        summary_class_name=status_class_name(snapshot.overall_status),
        note=snapshot.note,
        generated_at_text=snapshot.generated_at.isoformat(),
        target_directory_text=snapshot.target_directory,
        latest_report_id_text=snapshot.latest_report_id or "ещё не создан",
        latest_csv_text=snapshot.latest_csv_path or "ещё не создан",
        latest_pdf_text=snapshot.latest_pdf_path or "ещё не создан",
        latest_manifest_text=snapshot.latest_manifest_path or "ещё не создан",
        latest_csv_download_url=_build_download_url(snapshot.latest_csv_path),
        latest_pdf_download_url=_build_download_url(snapshot.latest_pdf_path),
        latest_manifest_download_url=_build_download_url(snapshot.latest_manifest_path),
        preview_text=(
            "Предпросмотр: отчёт будет собран в секциях metadata, findings, "
            "parameters, state, status_legend, status_events, trend."
        ),
        total_entries_text=str(snapshot.total_entries),
        entries=[_build_result_export_entry_view(entry) for entry in snapshot.entries],
    )


def _build_result_export_entry_view(entry: ResultExportEntry) -> ResultExportEntryView:
    csv_path = entry.csv_path
    pdf_path = entry.pdf_path
    manifest_path = entry.manifest_path
    return ResultExportEntryView(
        captured_at_text=entry.captured_at.isoformat(),
        source_text=entry.source_label,
        status_text=status_text(entry.status),
        status_class_name=status_class_name(entry.status),
        formats_text=(
            f"Форматы CSV и PDF; выводов: {entry.finding_count}; "
            f"таблиц: {entry.table_count}; трендовых точек: {entry.trend_points}"
        ),
        csv_path_text=csv_path,
        pdf_path_text=pdf_path,
        manifest_path_text=manifest_path,
        csv_download_url=_build_download_url(csv_path),
        pdf_download_url=_build_download_url(pdf_path),
        manifest_download_url=_build_download_url(manifest_path),
    )

def _build_download_url(path: str | None) -> str:
    if not path:
        return "#"
    return f"/exports/result/download?path={quote(path, safe='')}"
