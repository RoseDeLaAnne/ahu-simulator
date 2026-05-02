from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from app.services.event_log_service import EventLogEntry, EventLogSnapshot
from app.simulation.state import AlarmLevel, OperationStatus
from app.ui.viewmodels.status_presenter import status_class_name, status_text


@dataclass(frozen=True)
class EventLogEntryView:
    captured_at_text: str
    category_text: str
    level_text: str
    level_class_name: str
    source_text: str
    summary_text: str
    details_text: str
    artifact_path_text: str
    file_path_text: str
    artifact_download_url: str | None
    file_download_url: str


@dataclass(frozen=True)
class EventLogView:
    status_text: str
    summary_text: str
    summary_class_name: str
    note: str
    generated_at_text: str
    target_directory_text: str
    latest_entry_text: str
    total_entries_text: str
    entries: list[EventLogEntryView]


def build_event_log_view(snapshot: EventLogSnapshot) -> EventLogView:
    return EventLogView(
        status_text=status_text(snapshot.overall_status),
        summary_text=snapshot.summary,
        summary_class_name=status_class_name(snapshot.overall_status),
        note=snapshot.note,
        generated_at_text=snapshot.generated_at.isoformat(),
        target_directory_text=snapshot.target_directory,
        latest_entry_text=snapshot.latest_entry_path or "ещё нет записей",
        total_entries_text=str(snapshot.total_entries),
        entries=[_build_event_log_entry_view(entry) for entry in snapshot.entries],
    )


def _build_event_log_entry_view(entry: EventLogEntry) -> EventLogEntryView:
    return EventLogEntryView(
        captured_at_text=entry.captured_at.isoformat(),
        category_text=_category_text(entry),
        level_text=_level_text(entry.level),
        level_class_name=_level_class_name(entry.level),
        source_text=entry.source_label,
        summary_text=entry.summary,
        details_text=" ".join(entry.details) if entry.details else "—",
        artifact_path_text=entry.artifact_path or "—",
        file_path_text=entry.file_path,
        artifact_download_url=(
            _build_download_url(entry.artifact_path)
            if entry.artifact_path
            else None
        ),
        file_download_url=_build_download_url(entry.file_path),
    )


def _category_text(entry: EventLogEntry) -> str:
    category_labels = {
        "simulation": "Симуляция",
        "control": "Управление",
        "export": "Экспорт",
        "archive": "Архив",
    }
    category_text = category_labels.get(entry.category.value, entry.category.value)
    return f"{category_text} / {entry.title}"


def _level_text(level: AlarmLevel) -> str:
    return status_text(_status_from_level(level))


def _level_class_name(level: AlarmLevel) -> str:
    return status_class_name(_status_from_level(level))


def _status_from_level(level: AlarmLevel) -> OperationStatus:
    mapping = {
        AlarmLevel.INFO: OperationStatus.NORMAL,
        AlarmLevel.WARNING: OperationStatus.WARNING,
        AlarmLevel.CRITICAL: OperationStatus.ALARM,
    }
    return mapping[level]


def _build_download_url(path: str) -> str:
    return f"/events/log/download?path={quote(path, safe='')}"
