from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.infrastructure.runtime_paths import RuntimePathResolver
from app.services.pdf_text_renderer import to_ascii_text, write_text_pdf
from app.services.scenario_archive_service import (
    ArchivedScenarioRecord,
    ScenarioArchiveService,
)
from app.services.status_service import StatusService
from app.simulation.parameters import ControlMode
from app.simulation.state import OperationStatus, SimulationResult, SimulationSession

ACTIVE_RUN_REFERENCE_ID = "active-run"
ARCHIVE_REFERENCE_PREFIX = "archive:"
SNAPSHOT_REFERENCE_PREFIX = "snapshot:"
COMPARISON_SCHEMA_VERSION = "run-comparison.v2"
COMPARISON_SNAPSHOT_SCHEMA_VERSION = "run-comparison-snapshot.v1"
COMPARISON_SNAPSHOT_ROLES = ("before", "after")


class RunComparisonNamedSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = COMPARISON_SNAPSHOT_SCHEMA_VERSION
    snapshot_id: str
    role: str
    label: str
    notes: str = ""
    captured_at: datetime
    source_type: str
    source_id: str
    source_label: str
    scenario_id: str | None = None
    scenario_title: str | None = None
    parameter_hash: str
    compatibility_metadata: dict[str, object] = Field(default_factory=dict)
    result: SimulationResult


class RunComparisonSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_id: str
    source_type: str
    source_id: str | None = None
    source_label: str
    display_label: str
    captured_at: datetime
    role: str | None = None
    notes: str | None = None
    scenario_id: str | None = None
    scenario_title: str | None = None
    parameter_hash: str | None = None
    control_mode: ControlMode
    status: OperationStatus
    alarm_count: int
    step_minutes: int
    horizon_minutes: int
    point_count: int


class RunComparisonSnapshotSaveResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    summary: str
    snapshot: RunComparisonNamedSnapshot
    source: RunComparisonSource


class RunComparisonCompatibility(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_compatible: bool
    status: OperationStatus
    summary: str
    issues: list[str] = Field(default_factory=list)
    validated_rules: list[str] = Field(default_factory=list)


class ComparisonMetricDelta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: str
    title: str
    unit: str
    before_value: float
    after_value: float
    delta_value: float


class ComparisonTrendDeltaPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minute: int
    supply_temp_delta_c: float
    room_temp_delta_c: float
    total_power_delta_kw: float
    airflow_delta_m3_h: float
    filter_pressure_drop_delta_pa: float


class ComparisonInterpretation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: OperationStatus
    summary: str
    improved_metrics: list[str] = Field(default_factory=list)
    worsened_metrics: list[str] = Field(default_factory=list)
    unchanged_metrics: list[str] = Field(default_factory=list)
    top_deltas: list[ComparisonMetricDelta] = Field(default_factory=list)


class RunComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = COMPARISON_SCHEMA_VERSION
    generated_at: datetime
    comparison_id: str
    comparison_status: OperationStatus
    summary: str
    note: str
    before_source: RunComparisonSource
    after_source: RunComparisonSource
    compatibility: RunComparisonCompatibility
    interpretation: ComparisonInterpretation
    metric_deltas: list[ComparisonMetricDelta] = Field(default_factory=list)
    trend_deltas: list[ComparisonTrendDeltaPoint] = Field(default_factory=list)


class RunComparisonExportArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    label: str
    path: str
    exists: bool


class RunComparisonExportEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = COMPARISON_SCHEMA_VERSION
    comparison_id: str
    captured_at: datetime
    comparison_status: OperationStatus = OperationStatus.NORMAL
    before_reference_id: str | None = None
    before_label: str
    after_reference_id: str | None = None
    after_label: str
    compatibility_summary: str | None = None
    interpretation_summary: str | None = None
    metric_count: int
    trend_points: int
    csv_path: str
    pdf_path: str
    manifest_path: str


class RunComparisonExportManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = COMPARISON_SCHEMA_VERSION
    generated_at: datetime
    entry: RunComparisonExportEntry
    comparison: RunComparison
    artifacts: list[RunComparisonExportArtifact] = Field(default_factory=list)
    artifact_sizes: dict[str, int] = Field(default_factory=dict)


class RunComparisonSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    overall_status: OperationStatus
    summary: str
    note: str
    available_sources: list[RunComparisonSource] = Field(default_factory=list)
    named_snapshots: list[RunComparisonNamedSnapshot] = Field(default_factory=list)
    default_before_reference_id: str | None = None
    default_after_reference_id: str | None = None
    latest_comparison_id: str | None = None
    latest_csv_path: str | None = None
    latest_pdf_path: str | None = None
    latest_manifest_path: str | None = None
    total_exports: int
    entries: list[RunComparisonExportEntry] = Field(default_factory=list)


class RunComparisonExportBuildResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    summary: str
    entry: RunComparisonExportEntry
    comparison: RunComparison


class RunComparisonCompatibilityError(ValueError):
    def __init__(self, issues: list[str]) -> None:
        self.issues = issues
        super().__init__("; ".join(issues))


class RunComparisonService:
    _METRIC_CATALOG: tuple[tuple[str, str, str], ...] = (
        ("supply_temp_c", "Приточный воздух", "°C"),
        ("room_temp_c", "Температура помещения", "°C"),
        ("actual_airflow_m3_h", "Фактический расход", "м³/ч"),
        ("heating_power_kw", "Мощность нагревателя", "кВт"),
        ("fan_power_kw", "Мощность вентилятора", "кВт"),
        ("total_power_kw", "Суммарная мощность", "кВт"),
        ("filter_pressure_drop_pa", "ΔP фильтра", "Па"),
        ("energy_intensity_kw_per_1000_m3_h", "Удельная мощность", "кВт/1000 м³/ч"),
        ("heat_balance_kw", "Тепловой баланс", "кВт"),
        ("mixed_air_temp_c", "Смесительная камера", "°C"),
        ("recovered_air_temp_c", "После рекуперации", "°C"),
        ("alarm_count", "Количество тревог", "шт"),
    )

    def __init__(
        self,
        project_root: Path,
        scenario_archive_service: ScenarioArchiveService,
        status_service: StatusService | None = None,
        path_resolver: RuntimePathResolver | None = None,
    ) -> None:
        self._project_root = project_root
        self._scenario_archive_service = scenario_archive_service
        self._status_service = status_service or StatusService()
        self._path_resolver = path_resolver or RuntimePathResolver(project_root)

    @property
    def path_resolver(self) -> RuntimePathResolver:
        return self._path_resolver

    def save_before(
        self,
        result: SimulationResult,
        *,
        label: str | None = None,
        notes: str = "",
        source_id: str = ACTIVE_RUN_REFERENCE_ID,
        source_type: str = "active",
    ) -> RunComparisonSnapshotSaveResult:
        return self._save_named_snapshot(
            "before",
            result,
            label=label,
            notes=notes,
            source_id=source_id,
            source_type=source_type,
        )

    def save_after(
        self,
        result: SimulationResult,
        *,
        label: str | None = None,
        notes: str = "",
        source_id: str = ACTIVE_RUN_REFERENCE_ID,
        source_type: str = "active",
    ) -> RunComparisonSnapshotSaveResult:
        return self._save_named_snapshot(
            "after",
            result,
            label=label,
            notes=notes,
            source_id=source_id,
            source_type=source_type,
        )

    def build_snapshot(
        self,
        active_result: SimulationResult,
        active_session: SimulationSession | None = None,
        *,
        limit: int = 8,
    ) -> RunComparisonSnapshot:
        active_source = self._build_active_source(active_result, active_session)
        named_snapshots = self._load_named_snapshots()
        snapshot_sources = [
            self._build_named_snapshot_source(snapshot)
            for snapshot in named_snapshots
        ]
        archive_sources = [
            self._build_archive_source(record)
            for record in self._scenario_archive_service.list_records(limit=limit)
        ]
        available_sources = [*snapshot_sources, active_source, *archive_sources]
        export_entries = self._load_export_entries()
        visible_entries = export_entries[:limit]
        latest_entry = visible_entries[0] if visible_entries else None
        before_snapshot = self._find_named_snapshot(named_snapshots, "before")
        after_snapshot = self._find_named_snapshot(named_snapshots, "after")

        if before_snapshot and after_snapshot:
            overall_status = OperationStatus.NORMAL
            summary = (
                "Именованные снимки До и После готовы; они выбраны по умолчанию "
                "для сравнения, архивные прогоны сохранены как дополнительные источники."
            )
        elif before_snapshot or after_snapshot:
            overall_status = OperationStatus.WARNING
            summary = (
                "Зафиксирован один именованный снимок; сохраните вторую сторону "
                "До/После или выберите архивный/активный прогон."
            )
        elif not archive_sources:
            overall_status = OperationStatus.WARNING
            summary = (
                "Сохраните снимок До/После или хотя бы один прогон в архив сценариев, "
                "чтобы сравнить его с текущим прогоном."
            )
        elif visible_entries and all(self._entry_files_exist(entry) for entry in visible_entries):
            overall_status = OperationStatus.NORMAL
            summary = (
                f"Для сравнения доступны текущий прогон и {len(archive_sources)} архивных "
                f"снимков; последний манифест сравнения: {visible_entries[0].manifest_path}."
            )
        elif visible_entries:
            overall_status = OperationStatus.WARNING
            summary = (
                f"Для сравнения доступны текущий прогон и {len(archive_sources)} архивных "
                "снимков, но часть последних файлов экспорта сравнения отсутствует."
            )
        else:
            overall_status = OperationStatus.NORMAL
            summary = (
                f"Для сравнения доступны текущий прогон и {len(archive_sources)} архивных "
                "снимков; выберите пару до/после и при необходимости соберите CSV/PDF."
            )

        return RunComparisonSnapshot(
            generated_at=datetime.now(timezone.utc),
            overall_status=overall_status,
            summary=summary,
            note=(
                "Сравнение разрешается только для совместимых пар: одинаковый шаг, "
                "одинаковый горизонт и совпадающая временная сетка тренда. Все дельты "
                "считаются как после - до."
            ),
            available_sources=available_sources,
            named_snapshots=named_snapshots,
            default_before_reference_id=(
                f"{SNAPSHOT_REFERENCE_PREFIX}before"
                if before_snapshot
                else archive_sources[0].reference_id if archive_sources else None
            ),
            default_after_reference_id=(
                f"{SNAPSHOT_REFERENCE_PREFIX}after"
                if after_snapshot
                else active_source.reference_id
            ),
            latest_comparison_id=latest_entry.comparison_id if latest_entry else None,
            latest_csv_path=latest_entry.csv_path if latest_entry else None,
            latest_pdf_path=latest_entry.pdf_path if latest_entry else None,
            latest_manifest_path=latest_entry.manifest_path if latest_entry else None,
            total_exports=len(export_entries),
            entries=visible_entries,
        )

    def build_comparison_from_references(
        self,
        before_reference_id: str,
        after_reference_id: str,
        active_result: SimulationResult,
        active_session: SimulationSession | None = None,
        *,
        generated_at: datetime | None = None,
        comparison_id: str | None = None,
    ) -> RunComparison:
        before_source, before_result = self._resolve_reference(
            before_reference_id,
            active_result,
            active_session,
        )
        after_source, after_result = self._resolve_reference(
            after_reference_id,
            active_result,
            active_session,
        )
        return self.build_comparison(
            before_result,
            after_result,
            before_source=before_source,
            after_source=after_source,
            generated_at=generated_at,
            comparison_id=comparison_id,
        )

    def build_comparison(
        self,
        before_result: SimulationResult,
        after_result: SimulationResult,
        *,
        before_source: RunComparisonSource,
        after_source: RunComparisonSource,
        generated_at: datetime | None = None,
        comparison_id: str | None = None,
    ) -> RunComparison:
        generated_at = generated_at or datetime.now(timezone.utc)
        comparison_id = (
            comparison_id
            or f"pvu-comparison-{generated_at.astimezone():%Y%m%d-%H%M%S}"
        )
        compatibility = self._build_compatibility(
            before_result,
            after_result,
            before_source=before_source,
            after_source=after_source,
        )
        metric_deltas = (
            self._build_metric_deltas(before_result, after_result)
            if compatibility.is_compatible
            else []
        )
        interpretation = self._build_interpretation(
            metric_deltas,
            compatibility=compatibility,
            before_status=before_source.status,
            after_status=after_source.status,
        )
        comparison_status = self._derive_comparison_status(
            compatibility=compatibility,
            interpretation=interpretation,
            before_status=before_source.status,
            after_status=after_source.status,
        )
        trend_deltas = (
            self._build_trend_deltas(before_result, after_result)
            if compatibility.is_compatible
            else []
        )
        return RunComparison(
            generated_at=generated_at,
            comparison_id=comparison_id,
            comparison_status=comparison_status,
            summary=(
                f"{before_source.display_label} -> {after_source.display_label}"
            ),
            note="Все численные дельты рассчитаны как после - до.",
            before_source=before_source,
            after_source=after_source,
            compatibility=compatibility,
            interpretation=interpretation,
            metric_deltas=metric_deltas,
            trend_deltas=trend_deltas,
        )

    def export_comparison(
        self,
        comparison: RunComparison,
    ) -> RunComparisonExportBuildResult:
        if not comparison.compatibility.is_compatible:
            raise RunComparisonCompatibilityError(comparison.compatibility.issues)

        generated_at = datetime.now(timezone.utc)
        target_directory = self._export_directory(generated_at)
        target_directory.mkdir(parents=True, exist_ok=True)

        comparison_stem = f"pvu-comparison-{generated_at.astimezone():%Y%m%d-%H%M%S}"
        csv_path = target_directory / f"{comparison_stem}.csv"
        sequence = 2
        while csv_path.exists():
            csv_path = target_directory / f"{comparison_stem}-{sequence}.csv"
            sequence += 1

        comparison_stem = csv_path.stem
        pdf_path = target_directory / f"{comparison_stem}.pdf"
        manifest_path = target_directory / f"{comparison_stem}.manifest.json"
        comparison = comparison.model_copy(
            update={
                "generated_at": generated_at,
                "comparison_id": comparison_stem,
            }
        )

        self._write_csv(comparison, csv_path)
        self._write_pdf(comparison, pdf_path)

        entry = RunComparisonExportEntry(
            comparison_id=comparison.comparison_id,
            captured_at=generated_at,
            comparison_status=comparison.comparison_status,
            before_reference_id=comparison.before_source.reference_id,
            before_label=comparison.before_source.display_label,
            after_reference_id=comparison.after_source.reference_id,
            after_label=comparison.after_source.display_label,
            compatibility_summary=comparison.compatibility.summary,
            interpretation_summary=comparison.interpretation.summary,
            metric_count=len(comparison.metric_deltas),
            trend_points=len(comparison.trend_deltas),
            csv_path=self._relative_path(csv_path),
            pdf_path=self._relative_path(pdf_path),
            manifest_path=self._relative_path(manifest_path),
        )
        manifest = RunComparisonExportManifest(
            generated_at=generated_at,
            entry=entry,
            comparison=comparison,
            artifacts=[
                RunComparisonExportArtifact(
                    artifact_id="csv",
                    label="CSV сравнения",
                    path=entry.csv_path,
                    exists=True,
                ),
                RunComparisonExportArtifact(
                    artifact_id="pdf",
                    label="PDF сравнения",
                    path=entry.pdf_path,
                    exists=True,
                ),
                RunComparisonExportArtifact(
                    artifact_id="manifest",
                    label="Манифест",
                    path=entry.manifest_path,
                    exists=True,
                ),
            ],
            artifact_sizes={
                "csv": csv_path.stat().st_size,
                "pdf": pdf_path.stat().st_size,
            },
        )
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        manifest = manifest.model_copy(
            update={
                "artifact_sizes": {
                    **manifest.artifact_sizes,
                    "manifest": manifest_path.stat().st_size,
                }
            }
        )
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

        return RunComparisonExportBuildResult(
            generated_at=generated_at,
            summary=(
                "Сравнение до/после сохранено в CSV/PDF + манифест "
                f"в {self._relative_path(target_directory)}."
            ),
            entry=entry,
            comparison=comparison,
        )

    def _resolve_reference(
        self,
        reference_id: str,
        active_result: SimulationResult,
        active_session: SimulationSession | None,
    ) -> tuple[RunComparisonSource, SimulationResult]:
        if reference_id == ACTIVE_RUN_REFERENCE_ID:
            source = self._build_active_source(active_result, active_session)
            return source, active_result
        if reference_id.startswith(ARCHIVE_REFERENCE_PREFIX):
            archive_id = reference_id.removeprefix(ARCHIVE_REFERENCE_PREFIX)
            record = self._scenario_archive_service.get_record(archive_id)
            if record is None:
                raise KeyError(f"Архивный прогон '{archive_id}' не найден")
            source = self._build_archive_source(record)
            return source, record.result
        if reference_id.startswith(SNAPSHOT_REFERENCE_PREFIX):
            role = reference_id.removeprefix(SNAPSHOT_REFERENCE_PREFIX)
            snapshot = self._load_named_snapshot(role)
            if snapshot is None:
                raise KeyError(f"Снимок сравнения '{role}' не найден")
            source = self._build_named_snapshot_source(snapshot)
            return source, snapshot.result
        raise KeyError(f"Неизвестный источник сравнения '{reference_id}'")

    def _build_active_source(
        self,
        result: SimulationResult,
        session: SimulationSession | None,
    ) -> RunComparisonSource:
        source_label = self._source_label(result)
        captured_at = session.updated_at if session else result.timestamp
        return RunComparisonSource(
            reference_id=ACTIVE_RUN_REFERENCE_ID,
            source_type="active",
            source_id=ACTIVE_RUN_REFERENCE_ID,
            source_label=source_label,
            display_label=f"Текущий прогон — {source_label}",
            captured_at=captured_at,
            scenario_id=result.scenario_id,
            scenario_title=result.scenario_title,
            parameter_hash=self._parameter_hash(result),
            control_mode=result.parameters.control_mode,
            status=result.state.status,
            alarm_count=len(result.alarms),
            step_minutes=result.trend.step_minutes,
            horizon_minutes=result.trend.horizon_minutes,
            point_count=len(result.trend.points),
        )

    def _build_archive_source(
        self,
        record: ArchivedScenarioRecord,
    ) -> RunComparisonSource:
        result = record.result
        return RunComparisonSource(
            reference_id=f"{ARCHIVE_REFERENCE_PREFIX}{record.archive_id}",
            source_type="archive",
            source_id=record.archive_id,
            source_label=record.source_label,
            display_label=f"Архив сценариев — {record.source_label}",
            captured_at=record.captured_at,
            scenario_id=result.scenario_id,
            scenario_title=result.scenario_title,
            parameter_hash=self._parameter_hash(result),
            control_mode=result.parameters.control_mode,
            status=result.state.status,
            alarm_count=len(result.alarms),
            step_minutes=result.trend.step_minutes,
            horizon_minutes=result.trend.horizon_minutes,
            point_count=len(result.trend.points),
        )

    def _build_named_snapshot_source(
        self,
        snapshot: RunComparisonNamedSnapshot,
    ) -> RunComparisonSource:
        result = snapshot.result
        role_label = "До" if snapshot.role == "before" else "После"
        return RunComparisonSource(
            reference_id=f"{SNAPSHOT_REFERENCE_PREFIX}{snapshot.role}",
            source_type="snapshot",
            source_id=snapshot.snapshot_id,
            source_label=snapshot.label,
            display_label=f"{role_label} — {snapshot.label}",
            captured_at=snapshot.captured_at,
            role=snapshot.role,
            notes=snapshot.notes,
            scenario_id=snapshot.scenario_id,
            scenario_title=snapshot.scenario_title,
            parameter_hash=snapshot.parameter_hash,
            control_mode=result.parameters.control_mode,
            status=result.state.status,
            alarm_count=len(result.alarms),
            step_minutes=result.trend.step_minutes,
            horizon_minutes=result.trend.horizon_minutes,
            point_count=len(result.trend.points),
        )

    def _save_named_snapshot(
        self,
        role: str,
        result: SimulationResult,
        *,
        label: str | None,
        notes: str,
        source_id: str,
        source_type: str,
    ) -> RunComparisonSnapshotSaveResult:
        if role not in COMPARISON_SNAPSHOT_ROLES:
            raise ValueError(f"Unsupported comparison snapshot role: {role}")

        generated_at = datetime.now(timezone.utc)
        source_label = self._source_label(result)
        role_label = "До" if role == "before" else "После"
        snapshot = RunComparisonNamedSnapshot(
            snapshot_id=f"comparison-{role}",
            role=role,
            label=(label or f"{role_label}: {source_label}").strip(),
            notes=notes.strip(),
            captured_at=generated_at,
            source_type=source_type,
            source_id=source_id,
            source_label=source_label,
            scenario_id=result.scenario_id,
            scenario_title=result.scenario_title,
            parameter_hash=self._parameter_hash(result),
            compatibility_metadata=self._compatibility_metadata(result),
            result=result,
        )
        snapshot_path = self._named_snapshot_path(role)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
        source = self._build_named_snapshot_source(snapshot)
        return RunComparisonSnapshotSaveResult(
            generated_at=generated_at,
            summary=(
                f"Снимок {role_label} сохранён как {snapshot.label}. "
                f"Статус: {self._status_service.status_label(result.state.status)}."
            ),
            snapshot=snapshot,
            source=source,
        )

    def _load_named_snapshots(self) -> list[RunComparisonNamedSnapshot]:
        snapshots = [
            snapshot
            for role in COMPARISON_SNAPSHOT_ROLES
            if (snapshot := self._load_named_snapshot(role)) is not None
        ]
        return snapshots

    def _load_named_snapshot(self, role: str) -> RunComparisonNamedSnapshot | None:
        if role not in COMPARISON_SNAPSHOT_ROLES:
            return None
        snapshot_path = self._named_snapshot_path(role)
        if not snapshot_path.exists():
            return None
        try:
            snapshot = RunComparisonNamedSnapshot.model_validate_json(
                snapshot_path.read_text(encoding="utf-8")
            )
        except ValueError:
            return None
        if snapshot.schema_version != COMPARISON_SNAPSHOT_SCHEMA_VERSION:
            return None
        if snapshot.role != role:
            return None
        return snapshot

    def _find_named_snapshot(
        self,
        snapshots: list[RunComparisonNamedSnapshot],
        role: str,
    ) -> RunComparisonNamedSnapshot | None:
        return next((snapshot for snapshot in snapshots if snapshot.role == role), None)

    def _build_compatibility(
        self,
        before_result: SimulationResult,
        after_result: SimulationResult,
        *,
        before_source: RunComparisonSource,
        after_source: RunComparisonSource,
    ) -> RunComparisonCompatibility:
        issues: list[str] = []
        validated_rules: list[str] = []

        if before_source.reference_id == after_source.reference_id:
            issues.append("Для сравнения нужно выбрать два разных прогона.")

        if before_result.trend.step_minutes != after_result.trend.step_minutes:
            issues.append(
                "Шаг времени различается: "
                f"{before_result.trend.step_minutes} против {after_result.trend.step_minutes} мин."
            )
        else:
            validated_rules.append(
                f"шаг времени совпадает ({before_result.trend.step_minutes} мин)"
            )

        if before_result.trend.horizon_minutes != after_result.trend.horizon_minutes:
            issues.append(
                "Горизонт тренда различается: "
                f"{before_result.trend.horizon_minutes} против {after_result.trend.horizon_minutes} мин."
            )
        else:
            validated_rules.append(
                f"горизонт совпадает ({before_result.trend.horizon_minutes} мин)"
            )

        if len(before_result.trend.points) != len(after_result.trend.points):
            issues.append(
                "Количество точек тренда различается: "
                f"{len(before_result.trend.points)} против {len(after_result.trend.points)}."
            )
        else:
            validated_rules.append(
                f"количество точек совпадает ({len(before_result.trend.points)})"
            )

        before_minutes = [point.minute for point in before_result.trend.points]
        after_minutes = [point.minute for point in after_result.trend.points]
        if before_minutes != after_minutes:
            issues.append("Временная сетка тренда не совпадает.")
        else:
            validated_rules.append("временная сетка тренда совпадает")

        before_state_fields = set(before_result.state.model_dump(mode="json"))
        after_state_fields = set(after_result.state.model_dump(mode="json"))
        if before_state_fields != after_state_fields:
            issues.append("Набор итоговых метрик состояния отличается между прогонами.")
        else:
            validated_rules.append("набор KPI и диагностических метрик совпадает")

        if issues:
            return RunComparisonCompatibility(
                is_compatible=False,
                status=OperationStatus.WARNING,
                summary="Сравнение заблокировано: " + " ".join(issues),
                issues=issues,
                validated_rules=validated_rules,
            )

        return RunComparisonCompatibility(
            is_compatible=True,
            status=OperationStatus.NORMAL,
            summary=(
                "Совместимость подтверждена: "
                + ", ".join(validated_rules)
                + "."
            ),
            validated_rules=validated_rules,
        )

    def _build_metric_deltas(
        self,
        before_result: SimulationResult,
        after_result: SimulationResult,
    ) -> list[ComparisonMetricDelta]:
        metric_deltas: list[ComparisonMetricDelta] = []
        for metric_id, title, unit in self._METRIC_CATALOG:
            before_value = self._metric_value(before_result, metric_id)
            after_value = self._metric_value(after_result, metric_id)
            metric_deltas.append(
                ComparisonMetricDelta(
                    metric_id=metric_id,
                    title=title,
                    unit=unit,
                    before_value=before_value,
                    after_value=after_value,
                    delta_value=after_value - before_value,
                )
            )
        return metric_deltas

    def _build_interpretation(
        self,
        metric_deltas: list[ComparisonMetricDelta],
        *,
        compatibility: RunComparisonCompatibility,
        before_status: OperationStatus,
        after_status: OperationStatus,
    ) -> ComparisonInterpretation:
        if not compatibility.is_compatible:
            return ComparisonInterpretation(
                status=OperationStatus.WARNING,
                summary=(
                    "Интерпретация недоступна, пока пара несовместима: "
                    + " ".join(compatibility.issues)
                ),
            )

        improved: list[str] = []
        worsened: list[str] = []
        unchanged: list[str] = []
        for metric in metric_deltas:
            direction = self._metric_improvement_direction(metric.metric_id)
            tolerance = self._metric_tolerance(metric)
            if abs(metric.delta_value) <= tolerance:
                unchanged.append(metric.title)
                continue
            if direction == 0:
                unchanged.append(metric.title)
                continue
            if metric.delta_value * direction > 0:
                improved.append(metric.title)
            else:
                worsened.append(metric.title)

        top_deltas = sorted(
            metric_deltas,
            key=lambda metric: abs(metric.delta_value),
            reverse=True,
        )[:5]
        status = self._interpretation_status(
            improved,
            worsened,
            before_status=before_status,
            after_status=after_status,
        )
        summary = (
            f"Улучшилось: {len(improved)}; ухудшилось: {len(worsened)}; "
            f"без существенных изменений: {len(unchanged)}. "
            f"Статус пары: {self._status_service.status_label(status)}."
        )
        if top_deltas:
            summary += " Крупнейшая дельта: " + (
                f"{top_deltas[0].title} {top_deltas[0].delta_value:+.2f} "
                f"{top_deltas[0].unit}."
            )
        return ComparisonInterpretation(
            status=status,
            summary=summary,
            improved_metrics=improved,
            worsened_metrics=worsened,
            unchanged_metrics=unchanged,
            top_deltas=top_deltas,
        )

    def _derive_comparison_status(
        self,
        *,
        compatibility: RunComparisonCompatibility,
        interpretation: ComparisonInterpretation,
        before_status: OperationStatus,
        after_status: OperationStatus,
    ) -> OperationStatus:
        if not compatibility.is_compatible:
            return OperationStatus.WARNING
        worst_status = max(
            before_status,
            after_status,
            key=self._status_severity,
        )
        if self._status_severity(worst_status) >= self._status_severity(OperationStatus.ALARM):
            return OperationStatus.ALARM
        if (
            worst_status == OperationStatus.WARNING
            or interpretation.status == OperationStatus.WARNING
        ):
            return OperationStatus.WARNING
        return OperationStatus.NORMAL

    def _interpretation_status(
        self,
        improved: list[str],
        worsened: list[str],
        *,
        before_status: OperationStatus,
        after_status: OperationStatus,
    ) -> OperationStatus:
        if self._status_severity(after_status) > self._status_severity(before_status):
            return OperationStatus.WARNING
        if len(worsened) > len(improved):
            return OperationStatus.WARNING
        return OperationStatus.NORMAL

    def _metric_improvement_direction(self, metric_id: str) -> int:
        lower_is_better = {
            "heating_power_kw",
            "fan_power_kw",
            "total_power_kw",
            "filter_pressure_drop_pa",
            "energy_intensity_kw_per_1000_m3_h",
            "alarm_count",
        }
        higher_is_better = {"actual_airflow_m3_h"}
        if metric_id in lower_is_better:
            return -1
        if metric_id in higher_is_better:
            return 1
        return 0

    def _metric_tolerance(self, metric: ComparisonMetricDelta) -> float:
        return max(abs(metric.before_value) * 0.005, 0.01)

    def _status_severity(self, status: OperationStatus) -> int:
        severity = {
            OperationStatus.NORMAL: 0,
            OperationStatus.WARNING: 1,
            OperationStatus.ALARM: 2,
        }
        return severity[status]

    def _build_trend_deltas(
        self,
        before_result: SimulationResult,
        after_result: SimulationResult,
    ) -> list[ComparisonTrendDeltaPoint]:
        return [
            ComparisonTrendDeltaPoint(
                minute=after_point.minute,
                supply_temp_delta_c=after_point.supply_temp_c - before_point.supply_temp_c,
                room_temp_delta_c=after_point.room_temp_c - before_point.room_temp_c,
                total_power_delta_kw=after_point.total_power_kw - before_point.total_power_kw,
                airflow_delta_m3_h=after_point.airflow_m3_h - before_point.airflow_m3_h,
                filter_pressure_drop_delta_pa=(
                    after_point.filter_pressure_drop_pa
                    - before_point.filter_pressure_drop_pa
                ),
            )
            for before_point, after_point in zip(
                before_result.trend.points,
                after_result.trend.points,
                strict=True,
            )
        ]

    def _metric_value(self, result: SimulationResult, metric_id: str) -> float:
        if metric_id == "alarm_count":
            return float(len(result.alarms))
        return float(getattr(result.state, metric_id))

    def _load_export_entries(self) -> list[RunComparisonExportEntry]:
        export_root = self._export_root()
        if not export_root.exists():
            return []

        manifest_paths = sorted(
            (
                path
                for path in export_root.rglob("pvu-comparison-*.manifest.json")
                if path.is_file()
            ),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
        entries: list[RunComparisonExportEntry] = []
        for manifest_path in manifest_paths:
            entry = self._load_entry_from_manifest(manifest_path)
            if entry is not None:
                entries.append(entry)
        entries.sort(
            key=lambda entry: (entry.captured_at, entry.comparison_id),
            reverse=True,
        )
        return entries

    def _load_entry_from_manifest(
        self,
        manifest_path: Path,
    ) -> RunComparisonExportEntry | None:
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except ValueError:
            return None

        entry_payload = payload.get("entry")
        if not isinstance(entry_payload, dict):
            return None

        normalized_payload = dict(entry_payload)
        normalized_payload["manifest_path"] = self._relative_path(manifest_path)
        try:
            return RunComparisonExportEntry.model_validate(normalized_payload)
        except ValueError:
            return None

    def _entry_files_exist(self, entry: RunComparisonExportEntry) -> bool:
        return all(
            self._path_resolver.resolve_display_path(relative_path).exists()
            for relative_path in [
                entry.csv_path,
                entry.pdf_path,
                entry.manifest_path,
            ]
        )

    def _write_csv(self, comparison: RunComparison, target_path: Path) -> None:
        with target_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["раздел", "ключ", "значение"])
            metadata_rows = [
                ["schema_version", comparison.schema_version],
                ["идентификатор_сравнения", comparison.comparison_id],
                ["время_формирования", comparison.generated_at.isoformat()],
                ["идентификатор_источника_до", comparison.before_source.reference_id],
                ["source_id_до", comparison.before_source.source_id or ""],
                ["источник_до", comparison.before_source.display_label],
                ["статус_до", self._status_service.status_label(comparison.before_source.status)],
                ["идентификатор_источника_после", comparison.after_source.reference_id],
                ["source_id_после", comparison.after_source.source_id or ""],
                ["источник_после", comparison.after_source.display_label],
                ["статус_после", self._status_service.status_label(comparison.after_source.status)],
                ["статус_сравнения", self._status_service.status_label(comparison.comparison_status)],
                ["совместимо", "да" if comparison.compatibility.is_compatible else "нет"],
                ["статус_совместимости", self._status_service.status_label(comparison.compatibility.status)],
                ["интерпретация", comparison.interpretation.summary],
            ]
            for key, value in metadata_rows:
                writer.writerow(["метаданные", key, value])

            writer.writerow([])
            writer.writerow(["раздел", "статус", "сводка"])
            writer.writerow(
                [
                    "совместимость",
                    self._status_service.status_label(comparison.compatibility.status),
                    comparison.compatibility.summary,
                ]
            )
            for issue in comparison.compatibility.issues:
                writer.writerow(["проблема_совместимости", "проблема", issue])
            for rule in comparison.compatibility.validated_rules:
                writer.writerow(["правило_совместимости", "правило", rule])

            writer.writerow([])
            writer.writerow(["раздел", "категория", "метрика"])
            for metric_title in comparison.interpretation.improved_metrics:
                writer.writerow(["интерпретация", "улучшилось", metric_title])
            for metric_title in comparison.interpretation.worsened_metrics:
                writer.writerow(["интерпретация", "ухудшилось", metric_title])
            for metric_title in comparison.interpretation.unchanged_metrics:
                writer.writerow(["интерпретация", "без_изменений", metric_title])
            for metric in comparison.interpretation.top_deltas:
                writer.writerow(
                    [
                        "top_delta",
                        metric.metric_id,
                        f"{metric.title}: {metric.delta_value:+.2f} {metric.unit}",
                    ]
                )

            writer.writerow([])
            writer.writerow(
                [
                    "идентификатор_метрики",
                    "метрика",
                    "единица",
                    "значение_до",
                    "значение_после",
                    "дельта",
                ]
            )
            for metric in comparison.metric_deltas:
                writer.writerow(
                    [
                        metric.metric_id,
                        metric.title,
                        metric.unit,
                        self._format_float(metric.before_value),
                        self._format_float(metric.after_value),
                        self._format_float(metric.delta_value),
                    ]
                )

            writer.writerow([])
            writer.writerow(
                [
                    "минута",
                    "дельта_притока_с",
                    "дельта_помещения_с",
                    "дельта_мощности_квт",
                    "дельта_расхода_м3_ч",
                    "дельта_перепада_фильтра_па",
                ]
            )
            for point in comparison.trend_deltas:
                writer.writerow(
                    [
                        str(point.minute),
                        self._format_float(point.supply_temp_delta_c),
                        self._format_float(point.room_temp_delta_c),
                        self._format_float(point.total_power_delta_kw),
                        self._format_float(point.airflow_delta_m3_h),
                        self._format_float(point.filter_pressure_drop_delta_pa),
                    ]
                )

    def _write_pdf(self, comparison: RunComparison, target_path: Path) -> None:
        lines = self._build_pdf_lines(comparison)
        if write_text_pdf(target_path, lines, title="Сравнение прогонов"):
            return
        fallback_lines = [to_ascii_text(line) for line in lines]
        target_path.write_bytes(self._build_pdf_document(fallback_lines))

    def _build_pdf_lines(self, comparison: RunComparison) -> list[str]:
        lines = [
            "Сравнение прогонов ПВУ",
            "",
            f"Версия схемы: {comparison.schema_version}",
            f"Идентификатор сравнения: {comparison.comparison_id}",
            f"До: {comparison.before_source.display_label}",
            f"Источник до: {comparison.before_source.reference_id}",
            f"Статус до: {self._status_service.status_label(comparison.before_source.status)}",
            f"После: {comparison.after_source.display_label}",
            f"Источник после: {comparison.after_source.reference_id}",
            f"Статус после: {self._status_service.status_label(comparison.after_source.status)}",
            f"Статус сравнения: {self._status_service.status_label(comparison.comparison_status)}",
            f"Совместимость: {comparison.compatibility.summary}",
            f"Интерпретация: {comparison.interpretation.summary}",
        ]
        if comparison.compatibility.issues:
            lines.append("Проблемы:")
            lines.extend(f"- {issue}" for issue in comparison.compatibility.issues)

        lines.extend(["", "Дельты метрик"])
        for metric in comparison.metric_deltas:
            lines.append(
                f"{metric.title}: {metric.before_value:.2f} -> {metric.after_value:.2f} "
                f"({metric.delta_value:+.2f} {metric.unit})"
            )

        lines.extend(["", "Top deltas"])
        for metric in comparison.interpretation.top_deltas:
            lines.append(f"{metric.title}: {metric.delta_value:+.2f} {metric.unit}")

        lines.extend(["", "Дельты трендов"])
        for point in comparison.trend_deltas:
            lines.append(
                f"t={point.minute}: приток {point.supply_temp_delta_c:+.2f} °C, "
                f"помещение {point.room_temp_delta_c:+.2f} °C, "
                f"мощность {point.total_power_delta_kw:+.2f} кВт, "
                f"расход {point.airflow_delta_m3_h:+.2f} м³/ч."
            )
        return lines

    def _build_pdf_document(self, lines: list[str]) -> bytes:
        lines_per_page = 44
        pages = [
            lines[index : index + lines_per_page]
            for index in range(0, len(lines), lines_per_page)
        ] or [[]]
        page_object_ids = [4 + index for index in range(len(pages))]
        content_object_ids = [
            4 + len(pages) + index for index in range(len(pages))
        ]
        objects: list[bytes] = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            (
                "<< /Type /Pages /Count {count} /Kids [{kids}] >>".format(
                    count=len(pages),
                    kids=" ".join(f"{object_id} 0 R" for object_id in page_object_ids),
                )
            ).encode("ascii"),
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]

        for content_object_id in content_object_ids:
            objects.append(
                (
                    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                    "/Resources << /Font << /F1 3 0 R >> >> /Contents "
                    f"{content_object_id} 0 R >>"
                ).encode("ascii")
            )

        for page_lines in pages:
            content_lines = [
                "BT",
                "/F1 11 Tf",
                "72 760 Td",
                "14 TL",
            ]
            for index, line in enumerate(page_lines):
                escaped = (
                    line.replace("\\", "\\\\")
                    .replace("(", "\\(")
                    .replace(")", "\\)")
                )
                if index == 0:
                    content_lines.append(f"({escaped}) Tj")
                else:
                    content_lines.append(f"T* ({escaped}) Tj")
            content_lines.append("ET")
            content_stream = "\n".join(content_lines).encode("ascii")
            objects.append(
                (
                    f"<< /Length {len(content_stream)} >>\nstream\n".encode("ascii")
                    + content_stream
                    + b"\nendstream"
                )
            )

        header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
        buffer = bytearray(header)
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(buffer))
            buffer.extend(f"{index} 0 obj\n".encode("ascii"))
            buffer.extend(obj)
            buffer.extend(b"\nendobj\n")

        xref_offset = len(buffer)
        buffer.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        buffer.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            buffer.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        buffer.extend(
            (
                f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
                f"startxref\n{xref_offset}\n%%EOF\n"
            ).encode("ascii")
        )
        return bytes(buffer)

    def _source_label(self, result: SimulationResult) -> str:
        if result.scenario_id and result.scenario_title:
            return f"{result.scenario_title} ({result.scenario_id})"
        return "Пользовательский режим"

    def _export_root(self) -> Path:
        return self._path_resolver.runtime_directories.exports

    def _snapshot_root(self) -> Path:
        return (
            self._path_resolver.runtime_directories.comparison_snapshots
            or self._path_resolver.runtime_directories.root / "comparison-snapshots"
        )

    def _named_snapshot_path(self, role: str) -> Path:
        return self._snapshot_root() / f"{role}.json"

    def _export_directory(self, generated_at: datetime) -> Path:
        return self._export_root() / generated_at.astimezone().strftime("%Y-%m-%d")

    def _relative_path(self, absolute_path: Path) -> str:
        return self._path_resolver.to_display_path(absolute_path)

    def _format_float(self, value: float) -> str:
        return f"{value:.2f}"

    def _parameter_hash(self, result: SimulationResult) -> str:
        payload = {
            "parameters": result.parameters.model_dump(mode="json"),
            "trend": self._compatibility_metadata(result),
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _compatibility_metadata(self, result: SimulationResult) -> dict[str, object]:
        return {
            "step_minutes": result.trend.step_minutes,
            "horizon_minutes": result.trend.horizon_minutes,
            "point_minutes": [point.minute for point in result.trend.points],
            "state_fields": sorted(result.state.model_dump(mode="json")),
        }
