from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from app.services.scenario_archive_service import (
    ScenarioArchiveEntry,
    ScenarioArchiveSnapshot,
)
from app.ui.viewmodels.status_presenter import status_class_name, status_text


@dataclass(frozen=True)
class ScenarioArchiveEntryView:
    captured_at_text: str
    source_text: str
    status_text: str
    status_class_name: str
    metrics_text: str
    alarms_text: str
    file_path_text: str
    file_download_url: str


@dataclass(frozen=True)
class ScenarioArchiveView:
    status_text: str
    summary_text: str
    summary_class_name: str
    note: str
    generated_at_text: str
    target_directory_text: str
    latest_entry_text: str
    total_entries_text: str
    entries: list[ScenarioArchiveEntryView]


def build_scenario_archive_view(
    snapshot: ScenarioArchiveSnapshot,
) -> ScenarioArchiveView:
    return ScenarioArchiveView(
        status_text=status_text(snapshot.overall_status),
        summary_text=snapshot.summary,
        summary_class_name=status_class_name(snapshot.overall_status),
        note=snapshot.note,
        generated_at_text=snapshot.generated_at.isoformat(),
        target_directory_text=snapshot.target_directory,
        latest_entry_text=snapshot.latest_entry_path or "ещё не сохранён",
        total_entries_text=str(snapshot.total_entries),
        entries=[
            ScenarioArchiveEntryView(
                captured_at_text=entry.captured_at.isoformat(),
                source_text=entry.source_label,
                status_text=status_text(entry.status),
                status_class_name=status_class_name(entry.status),
                metrics_text=_metrics_text(entry),
                alarms_text="нет" if entry.alarm_count == 0 else str(entry.alarm_count),
                file_path_text=entry.file_path,
                file_download_url=_build_download_url(entry.file_path),
            )
            for entry in snapshot.entries
        ],
    )

def _metrics_text(entry: ScenarioArchiveEntry) -> str:
    return (
        f"{entry.actual_airflow_m3_h:.0f} м³/ч | "
        f"{entry.supply_temp_c:.1f} °C | "
        f"{entry.total_power_kw:.1f} кВт"
    )


def _build_download_url(path: str) -> str:
    return f"/archive/scenarios/download?path={quote(path, safe='')}"
