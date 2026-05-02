from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.infrastructure.runtime_paths import RuntimePathResolver
from app.services.status_service import StatusService
from app.simulation.parameters import ControlMode
from app.simulation.state import (
    AlarmLevel,
    OperationStatus,
    SimulationResult,
    SimulationSession,
)


class EventCategory(StrEnum):
    SIMULATION = "simulation"
    CONTROL = "control"
    EXPORT = "export"
    ARCHIVE = "archive"


class EventLogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    captured_at: datetime
    category: EventCategory
    level: AlarmLevel
    title: str
    summary: str
    source_type: str
    source_label: str
    trigger: str | None = None
    scenario_id: str | None = None
    scenario_title: str | None = None
    control_mode: ControlMode
    status: OperationStatus
    details: list[str] = Field(default_factory=list)
    artifact_path: str | None = None
    file_path: str


class EventLogSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    overall_status: OperationStatus
    summary: str
    note: str
    target_directory: str
    latest_entry_path: str | None = None
    total_entries: int
    entries: list[EventLogEntry] = Field(default_factory=list)


class EventLogRecordResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    summary: str
    entry: EventLogEntry


class EventLogService:
    def __init__(
        self,
        project_root: Path,
        status_service: StatusService | None = None,
        path_resolver: RuntimePathResolver | None = None,
    ) -> None:
        self._project_root = project_root
        self._status_service = status_service or StatusService()
        self._path_resolver = path_resolver or RuntimePathResolver(project_root)

    @property
    def path_resolver(self) -> RuntimePathResolver:
        return self._path_resolver

    def build_snapshot(self, limit: int = 10) -> EventLogSnapshot:
        entries = self._load_entries()
        visible_entries = entries[:limit]

        if not visible_entries:
            overall_status = OperationStatus.WARNING
            summary = (
                "Журнал пока пуст; выполните запуск сценария, экспорт или сохранение, "
                "чтобы зафиксировать события проекта."
            )
        else:
            overall_status = self._overall_status(visible_entries)
            summary = (
                f"В журнале {len(entries)} событий; последнее сохранено как "
                f"{visible_entries[0].file_path}."
            )

        return EventLogSnapshot(
            generated_at=datetime.now(timezone.utc),
            overall_status=overall_status,
            summary=summary,
            note=(
                "Журнал событий хранит отдельные JSON-записи в artifacts/event-log и "
                "фиксирует расчётные переходы, смену режима управления, локальные "
                "экспорты и сохранения в архив."
            ),
            target_directory="artifacts/event-log",
            latest_entry_path=visible_entries[0].file_path if visible_entries else None,
            total_entries=len(entries),
            entries=visible_entries,
        )

    def record_simulation_event(
        self,
        result: SimulationResult,
        *,
        previous_result: SimulationResult | None = None,
        trigger: str | None = None,
        source_type: str,
    ) -> EventLogRecordResult | None:
        if previous_result is not None and not self._is_significant_change(
            previous_result,
            result,
        ):
            return None

        category = self._simulation_category(previous_result, result)
        title = self._simulation_title(previous_result, result)
        details = self._simulation_details(previous_result, result, trigger)
        entry = self._write_entry(
            category=category,
            level=self._level_from_status(result.state.status),
            title=title,
            summary=self._simulation_summary(result),
            source_type=source_type,
            source_label=self._source_label(result),
            trigger=trigger,
            result=result,
            details=details,
        )
        return EventLogRecordResult(
            generated_at=entry.captured_at,
            summary=f"{entry.title}: {entry.summary}",
            entry=entry,
        )

    def record_session_event(
        self,
        session: SimulationSession,
        *,
        trigger: str,
        source_type: str,
    ) -> EventLogRecordResult:
        result = session.current_result
        title = self._session_event_title(session.last_command or trigger)
        entry = self._write_entry(
            category=EventCategory.SIMULATION,
            level=self._level_from_status(result.state.status),
            title=title,
            summary=(
                f"{self._source_label(result)}: {session.elapsed_minutes} из "
                f"{result.parameters.horizon_minutes} мин, "
                f"тик {session.tick_count} из {session.max_ticks}."
            ),
            source_type=source_type,
            source_label=self._source_label(result),
            trigger=trigger,
            result=result,
            details=[
                f"Состояние сессии: {session.status.value}.",
                f"Скорость воспроизведения: x{session.playback_speed:g}.",
                f"Горизонт достигнут: {'да' if session.horizon_reached else 'нет'}.",
                f"Действие: {session.last_command or trigger}.",
            ],
        )
        return EventLogRecordResult(
            generated_at=entry.captured_at,
            summary=f"{entry.title}: {entry.summary}",
            entry=entry,
        )

    def record_export_event(
        self,
        result: SimulationResult,
        *,
        manifest_path: str,
        source_type: str,
    ) -> EventLogRecordResult:
        entry = self._write_entry(
            category=EventCategory.EXPORT,
            level=self._level_from_status(result.state.status),
            title="Собран сценарный отчёт",
            summary=(
                "Текущий прогон сохранён в CSV/PDF с манифестом для "
                "повторяемой офлайн-проверки."
            ),
            source_type=source_type,
            source_label=self._source_label(result),
            result=result,
            details=[
                f"Статус режима: {self._status_label(result.state.status)}.",
                f"Количество тревог: {len(result.alarms)}.",
                f"Манифест: {manifest_path}.",
            ],
            artifact_path=manifest_path,
        )
        return EventLogRecordResult(
            generated_at=entry.captured_at,
            summary=f"{entry.title}: {entry.summary}",
            entry=entry,
        )

    def record_archive_event(
        self,
        result: SimulationResult,
        *,
        archive_path: str,
        source_type: str,
    ) -> EventLogRecordResult:
        entry = self._write_entry(
            category=EventCategory.ARCHIVE,
            level=self._level_from_status(result.state.status),
            title="Сохранён прогон в архив сценариев",
            summary=(
                "Текущий прогон зафиксирован как отдельный JSON-снимок для "
                "повторного разбора или защиты."
            ),
            source_type=source_type,
            source_label=self._source_label(result),
            result=result,
            details=[
                f"Статус режима: {self._status_label(result.state.status)}.",
                f"Количество тревог: {len(result.alarms)}.",
                f"Файл архива: {archive_path}.",
            ],
            artifact_path=archive_path,
        )
        return EventLogRecordResult(
            generated_at=entry.captured_at,
            summary=f"{entry.title}: {entry.summary}",
            entry=entry,
        )

    def _load_entries(self) -> list[EventLogEntry]:
        event_root = self._event_root()
        if not event_root.exists():
            return []

        file_paths = sorted(
            (
                path
                for path in event_root.rglob("*.json")
                if path.is_file() and path.name != "README.md"
            ),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )

        entries: list[EventLogEntry] = []
        for file_path in file_paths:
            try:
                entry = EventLogEntry.model_validate_json(
                    file_path.read_text(encoding="utf-8")
                )
            except ValueError:
                continue
            entries.append(
                entry.model_copy(update={"file_path": self._relative_path(file_path)})
            )

        entries.sort(key=lambda entry: (entry.captured_at, entry.event_id), reverse=True)
        return entries

    def _write_entry(
        self,
        *,
        category: EventCategory,
        level: AlarmLevel,
        title: str,
        summary: str,
        source_type: str,
        source_label: str,
        result: SimulationResult,
        details: list[str],
        trigger: str | None = None,
        artifact_path: str | None = None,
    ) -> EventLogEntry:
        captured_at = datetime.now(timezone.utc)
        target_directory = self._event_directory(captured_at)
        target_directory.mkdir(parents=True, exist_ok=True)

        event_stem = f"pvu-event-{captured_at.astimezone():%Y%m%d-%H%M%S}"
        file_path = target_directory / f"{event_stem}.json"
        sequence = 2
        while file_path.exists():
            file_path = target_directory / f"{event_stem}-{sequence}.json"
            sequence += 1

        entry = EventLogEntry(
            event_id=file_path.stem,
            captured_at=captured_at,
            category=category,
            level=level,
            title=title,
            summary=summary,
            source_type=source_type,
            source_label=source_label,
            trigger=trigger,
            scenario_id=result.scenario_id,
            scenario_title=result.scenario_title,
            control_mode=result.parameters.control_mode,
            status=result.state.status,
            details=details,
            artifact_path=artifact_path,
            file_path=self._relative_path(file_path),
        )
        file_path.write_text(entry.model_dump_json(indent=2), encoding="utf-8")
        return entry

    def _is_significant_change(
        self,
        previous_result: SimulationResult,
        result: SimulationResult,
    ) -> bool:
        previous_alarm_codes = {alarm.code for alarm in previous_result.alarms}
        current_alarm_codes = {alarm.code for alarm in result.alarms}
        return any(
            [
                previous_result.scenario_id != result.scenario_id,
                previous_result.parameters.control_mode != result.parameters.control_mode,
                previous_result.state.status != result.state.status,
                previous_alarm_codes != current_alarm_codes,
                abs(
                    previous_result.state.supply_temp_c - result.state.supply_temp_c
                )
                >= 0.5,
                abs(
                    previous_result.state.actual_airflow_m3_h
                    - result.state.actual_airflow_m3_h
                )
                >= 150.0,
                abs(
                    previous_result.state.total_power_kw - result.state.total_power_kw
                )
                >= 0.75,
            ]
        )

    def _simulation_category(
        self,
        previous_result: SimulationResult | None,
        result: SimulationResult,
    ) -> EventCategory:
        if (
            previous_result is not None
            and previous_result.parameters.control_mode != result.parameters.control_mode
        ):
            return EventCategory.CONTROL
        return EventCategory.SIMULATION

    def _simulation_title(
        self,
        previous_result: SimulationResult | None,
        result: SimulationResult,
    ) -> str:
        if previous_result is None:
            return "Зафиксирован первый расчёт"
        if previous_result.parameters.control_mode != result.parameters.control_mode:
            return "Сменён режим управления"
        if result.scenario_id and result.scenario_id != previous_result.scenario_id:
            return f"Запущен сценарий {result.scenario_title or result.scenario_id}"
        if result.scenario_id:
            return f"Обновлён сценарий {result.scenario_title or result.scenario_id}"
        return "Пересчитан пользовательский режим"

    def _simulation_summary(self, result: SimulationResult) -> str:
        return (
            f"{self._source_label(result)}: приток {result.state.supply_temp_c:.1f} °C, "
            f"расход {result.state.actual_airflow_m3_h:.0f} м³/ч, "
            f"суммарная мощность {result.state.total_power_kw:.1f} кВт."
        )

    def _simulation_details(
        self,
        previous_result: SimulationResult | None,
        result: SimulationResult,
        trigger: str | None,
    ) -> list[str]:
        details = [
            f"Режим управления: {self._control_mode_label(result.parameters.control_mode)}.",
            f"Статус: {self._status_label(result.state.status)}.",
            f"Тревоги: {self._alarm_codes_text(result)}.",
            (
                f"Контур: {result.control.summary}"
                if result.control is not None
                else "Контур: диагностика не построена."
            ),
        ]
        if trigger:
            details.insert(0, f"Триггер интерфейса/API: {trigger}.")
        if previous_result is None:
            return details

        if previous_result.parameters.control_mode != result.parameters.control_mode:
            details.append(
                "Смена режима управления: "
                f"{self._control_mode_label(previous_result.parameters.control_mode)} -> "
                f"{self._control_mode_label(result.parameters.control_mode)}."
            )
        if previous_result.state.status != result.state.status:
            details.append(
                f"Смена статуса: {self._status_label(previous_result.state.status)} -> "
                f"{self._status_label(result.state.status)}."
            )
        details.append(
            f"Δ притока: {result.state.supply_temp_c - previous_result.state.supply_temp_c:+.1f} °C."
        )
        details.append(
            "Δ расхода: "
            f"{result.state.actual_airflow_m3_h - previous_result.state.actual_airflow_m3_h:+.0f} м³/ч."
        )
        details.append(
            f"Δ мощности: {result.state.total_power_kw - previous_result.state.total_power_kw:+.1f} кВт."
        )
        return details

    def _event_root(self) -> Path:
        return self._path_resolver.runtime_directories.event_log

    def _event_directory(self, captured_at: datetime) -> Path:
        return self._event_root() / captured_at.astimezone().strftime("%Y-%m-%d")

    def _relative_path(self, absolute_path: Path) -> str:
        return self._path_resolver.to_display_path(absolute_path)

    def _source_label(self, result: SimulationResult) -> str:
        if result.scenario_id and result.scenario_title:
            return f"{result.scenario_title} ({result.scenario_id})"
        return "Пользовательский режим"

    def _control_mode_label(self, control_mode: ControlMode) -> str:
        control_mode_labels = {
            ControlMode.AUTO: "Авто",
            ControlMode.MANUAL: "Ручной",
        }
        return control_mode_labels.get(control_mode, control_mode.value)

    def _status_label(self, status: OperationStatus) -> str:
        return self._status_service.status_label(status)

    def _session_event_title(self, command: str) -> str:
        mapping = {
            "start": "Сессия симуляции запущена",
            "resume": "Сессия симуляции продолжена",
            "pause": "Сессия симуляции поставлена на паузу",
            "tick": "Выполнен шаг сессии симуляции",
            "reset": "Сессия симуляции сброшена",
            "completed": "Горизонт сессии симуляции достигнут",
            "speed": "Скорость сессии симуляции обновлена",
        }
        return mapping.get(command, "Обновлена сессия симуляции")

    def _alarm_codes_text(self, result: SimulationResult) -> str:
        return ", ".join(alarm.code for alarm in result.alarms) or "нет активных тревог"

    def _overall_status(self, entries: list[EventLogEntry]) -> OperationStatus:
        if any(entry.level == AlarmLevel.CRITICAL for entry in entries):
            return OperationStatus.ALARM
        if any(entry.level == AlarmLevel.WARNING for entry in entries):
            return OperationStatus.WARNING
        return OperationStatus.NORMAL

    def _level_from_status(self, status: OperationStatus) -> AlarmLevel:
        mapping = {
            OperationStatus.NORMAL: AlarmLevel.INFO,
            OperationStatus.WARNING: AlarmLevel.WARNING,
            OperationStatus.ALARM: AlarmLevel.CRITICAL,
        }
        return mapping[status]
