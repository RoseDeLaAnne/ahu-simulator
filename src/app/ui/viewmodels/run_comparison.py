from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from app.services.comparison_service import (
    RunComparisonExportEntry,
    RunComparisonSnapshot,
    RunComparisonSource,
)
from app.simulation.state import OperationStatus
from app.ui.viewmodels.status_presenter import status_class_name, status_text


@dataclass(frozen=True)
class RunComparisonEntryView:
    captured_at_text: str
    pair_text: str
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
class RunComparisonView:
    status_text: str
    summary_text: str
    summary_class_name: str
    note: str
    generated_at_text: str
    latest_comparison_id_text: str
    latest_csv_text: str
    latest_pdf_text: str
    latest_manifest_text: str
    total_exports_text: str
    source_options: list[dict[str, str]]
    default_before_reference_id: str | None
    default_after_reference_id: str | None
    named_before_text: str
    named_after_text: str
    entries: list[RunComparisonEntryView]


def build_run_comparison_view(snapshot: RunComparisonSnapshot) -> RunComparisonView:
    return RunComparisonView(
        status_text=status_text(snapshot.overall_status),
        summary_text=snapshot.summary,
        summary_class_name=status_class_name(snapshot.overall_status),
        note=snapshot.note,
        generated_at_text=snapshot.generated_at.isoformat(),
        latest_comparison_id_text=snapshot.latest_comparison_id or "ещё не создан",
        latest_csv_text=snapshot.latest_csv_path or "ещё не создан",
        latest_pdf_text=snapshot.latest_pdf_path or "ещё не создан",
        latest_manifest_text=snapshot.latest_manifest_path or "ещё не создан",
        total_exports_text=str(snapshot.total_exports),
        source_options=[
            {
                "label": _source_option_label(source),
                "value": source.reference_id,
            }
            for source in snapshot.available_sources
        ],
        default_before_reference_id=snapshot.default_before_reference_id,
        default_after_reference_id=snapshot.default_after_reference_id,
        named_before_text=_named_snapshot_text(snapshot, "before"),
        named_after_text=_named_snapshot_text(snapshot, "after"),
        entries=[_build_entry_view(entry) for entry in snapshot.entries],
    )


def _build_entry_view(entry: RunComparisonExportEntry) -> RunComparisonEntryView:
    return RunComparisonEntryView(
        captured_at_text=entry.captured_at.isoformat(),
        pair_text=f"{entry.before_label} -> {entry.after_label}",
        status_text=status_text(OperationStatus.NORMAL),
        status_class_name=status_class_name(OperationStatus.NORMAL),
        formats_text=(
            f"CSV/PDF; метрик: {entry.metric_count}; "
            f"точек дельты: {entry.trend_points}"
        ),
        csv_path_text=entry.csv_path,
        pdf_path_text=entry.pdf_path,
        manifest_path_text=entry.manifest_path,
        csv_download_url=_build_download_url(entry.csv_path),
        pdf_download_url=_build_download_url(entry.pdf_path),
        manifest_download_url=_build_download_url(entry.manifest_path),
    )


def _source_option_label(source: RunComparisonSource) -> str:
    source_prefix = {
        "active": "Текущий прогон",
        "archive": "Архив сценариев",
        "snapshot": "Снимок До/После",
    }.get(source.source_type, source.source_type)
    return (
        f"{source_prefix} | {source.source_label} | "
        f"статус {status_text(source.status)} | "
        f"{source.captured_at.isoformat()} | шаг {source.step_minutes} мин | "
        f"{source.point_count} точек"
    )


def _build_download_url(path: str) -> str:
    return f"/comparison/runs/download?path={quote(path, safe='')}"


def _named_snapshot_text(snapshot: RunComparisonSnapshot, role: str) -> str:
    role_label = "До" if role == "before" else "После"
    for named_snapshot in snapshot.named_snapshots:
        if named_snapshot.role == role:
            return (
                f"{role_label}: {named_snapshot.label} | "
                f"{named_snapshot.captured_at.isoformat()}"
            )
    return f"{role_label}: ещё не зафиксирован"
