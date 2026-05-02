from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.infrastructure.runtime_paths import RuntimePathResolver
from app.services.status_service import StatusService
from app.simulation.state import OperationStatus, SimulationResult


class ScenarioArchiveEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    archive_id: str
    captured_at: datetime
    source_type: str
    source_label: str
    scenario_id: str | None = None
    scenario_title: str | None = None
    status: OperationStatus
    alarm_count: int
    supply_temp_c: float
    room_temp_c: float
    actual_airflow_m3_h: float
    total_power_kw: float
    file_path: str


class ScenarioArchiveSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    overall_status: OperationStatus
    summary: str
    note: str
    target_directory: str
    latest_entry_path: str | None = None
    total_entries: int
    entries: list[ScenarioArchiveEntry] = Field(default_factory=list)


class ScenarioArchiveSaveResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    summary: str
    entry: ScenarioArchiveEntry


class ArchivedScenarioRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    archive_id: str
    captured_at: datetime
    source_type: str
    source_label: str
    note: str
    result: SimulationResult


class ScenarioArchiveService:
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

    def build_snapshot(self, limit: int = 8) -> ScenarioArchiveSnapshot:
        records = self._load_records()
        entries = [
            self._entry_from_record(record, file_path)
            for record, file_path in records[:limit]
        ]

        if entries:
            overall_status = OperationStatus.NORMAL
            summary = (
                f"Сохранено {len(records)} снимков; последний доступен как "
                f"{entries[0].file_path}."
            )
        else:
            overall_status = OperationStatus.WARNING
            summary = (
                "Архив пока пуст; сохраните текущий прогон, чтобы зафиксировать "
                "сценарий для защиты или сравнения."
            )

        return ScenarioArchiveSnapshot(
            generated_at=datetime.now(timezone.utc),
            overall_status=overall_status,
            summary=summary,
            note=(
                "Каждый снимок сохраняется отдельным JSON-файлом в artifacts/scenario-archive "
                "и фиксирует полный SimulationResult вместе со статусом, тревогами и "
                "ключевыми метриками."
            ),
            target_directory="artifacts/scenario-archive",
            latest_entry_path=entries[0].file_path if entries else None,
            total_entries=len(records),
            entries=entries,
        )

    def save_result(self, result: SimulationResult) -> ScenarioArchiveSaveResult:
        generated_at = datetime.now(timezone.utc)
        source_type, source_label, note = self._source_metadata(result)

        target_directory = self._archive_directory(generated_at)
        target_directory.mkdir(parents=True, exist_ok=True)
        archive_stem = f"pvu-run-{generated_at.astimezone():%Y%m%d-%H%M%S}"
        file_path = target_directory / f"{archive_stem}.json"
        sequence = 2
        while file_path.exists():
            file_path = target_directory / f"{archive_stem}-{sequence}.json"
            sequence += 1

        record = ArchivedScenarioRecord(
            archive_id=file_path.stem,
            captured_at=generated_at,
            source_type=source_type,
            source_label=source_label,
            note=note,
            result=result,
        )
        file_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")

        entry = self._entry_from_record(record, file_path)
        return ScenarioArchiveSaveResult(
            generated_at=generated_at,
            summary=(
                f"Снимок {source_label} сохранён в {entry.file_path}. "
                f"Статус: {self._status_service.status_label(entry.status)}."
            ),
            entry=entry,
        )

    def list_records(self, limit: int | None = None) -> list[ArchivedScenarioRecord]:
        records = [record for record, _ in self._load_records()]
        if limit is None:
            return records
        return records[:limit]

    def get_record(self, archive_id: str) -> ArchivedScenarioRecord | None:
        for record, _file_path in self._load_records():
            if record.archive_id == archive_id:
                return record
        return None

    def _load_records(self) -> list[tuple[ArchivedScenarioRecord, Path]]:
        archive_root = self._archive_root()
        if not archive_root.exists():
            return []

        file_paths = sorted(
            (
                path
                for path in archive_root.rglob("*.json")
                if path.is_file()
            ),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
        records: list[tuple[ArchivedScenarioRecord, Path]] = []
        for file_path in file_paths:
            try:
                record = ArchivedScenarioRecord.model_validate_json(
                    file_path.read_text(encoding="utf-8")
                )
            except ValueError:
                continue
            records.append((record, file_path))
        records.sort(
            key=lambda item: (item[0].captured_at, item[1].name),
            reverse=True,
        )
        return records

    def _entry_from_record(
        self,
        record: ArchivedScenarioRecord,
        file_path: Path,
    ) -> ScenarioArchiveEntry:
        result = record.result
        return ScenarioArchiveEntry(
            archive_id=record.archive_id,
            captured_at=record.captured_at,
            source_type=record.source_type,
            source_label=record.source_label,
            scenario_id=result.scenario_id,
            scenario_title=result.scenario_title,
            status=result.state.status,
            alarm_count=len(result.alarms),
            supply_temp_c=result.state.supply_temp_c,
            room_temp_c=result.state.room_temp_c,
            actual_airflow_m3_h=result.state.actual_airflow_m3_h,
            total_power_kw=result.state.total_power_kw,
            file_path=self._relative_path(file_path),
        )

    def _source_metadata(self, result: SimulationResult) -> tuple[str, str, str]:
        if result.scenario_id and result.scenario_title:
            return (
                "scenario",
                f"{result.scenario_title} ({result.scenario_id})",
                "Снимок сохранён из готового сценария.",
            )

        return (
            "custom",
            "Пользовательский режим",
            "Снимок сохранён из пользовательского набора параметров.",
        )

    def _archive_root(self) -> Path:
        return self._path_resolver.runtime_directories.scenario_archive

    def _archive_directory(self, generated_at: datetime) -> Path:
        return self._archive_root() / generated_at.astimezone().strftime("%Y-%m-%d")

    def _relative_path(self, absolute_path: Path) -> str:
        return self._path_resolver.to_display_path(absolute_path)
