from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.infrastructure.runtime_paths import RuntimePathResolver
from app.services.pdf_text_renderer import to_ascii_text, write_text_pdf
from app.services.status_service import StatusService
from app.simulation.state import (
    OperationStatus,
    SimulationResult,
    SimulationSession,
)
from app.simulation.status_policy import evaluate_upper_threshold


REPORT_SCHEMA_VERSION = "scenario-report.v2"
REPORT_SECTION_ORDER = (
    "metadata",
    "findings",
    "parameters",
    "state",
    "status_legend",
    "status_events",
    "trend",
)


class ReportSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: str
    title: str
    table_ids: list[str] = Field(default_factory=list)
    required: bool = True


class ReportChartSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chart_id: str
    title: str
    source_table_id: str
    x_axis: str
    y_axes: list[str] = Field(default_factory=list)
    chart_type: str = "line"


class ScenarioReportMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str
    generated_at: datetime
    source_type: str
    source_label: str
    scenario_id: str | None = None
    scenario_title: str | None = None
    control_mode: str
    status: OperationStatus
    alarm_count: int
    trend_points: int
    horizon_minutes: int
    step_minutes: int
    session_id: str | None = None
    session_status: str | None = None
    elapsed_minutes: int | None = None


class ScenarioReportFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str
    title: str
    severity: OperationStatus
    conclusion: str


class ScenarioReportTable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table_id: str
    title: str
    columns: list[str]
    rows: list[list[str]] = Field(default_factory=list)


class ScenarioReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = REPORT_SCHEMA_VERSION
    metadata: ScenarioReportMetadata
    findings: list[ScenarioReportFinding] = Field(default_factory=list)
    tables: list[ScenarioReportTable] = Field(default_factory=list)
    sections: list[ReportSection] = Field(default_factory=list)
    chart_specs: list[ReportChartSpec] = Field(default_factory=list)


class ResultExportArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    label: str
    path: str
    exists: bool
    size_bytes: int | None = None
    sha256: str | None = None


class ResultExportEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = REPORT_SCHEMA_VERSION
    report_id: str
    captured_at: datetime
    source_type: str
    source_label: str
    scenario_id: str | None = None
    scenario_title: str | None = None
    status: OperationStatus
    alarm_count: int
    trend_points: int
    finding_count: int = 0
    table_count: int = 0
    csv_path: str
    pdf_path: str
    manifest_path: str


class ResultExportManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = REPORT_SCHEMA_VERSION
    report_id: str
    generated_at: datetime
    entry: ResultExportEntry
    report: ScenarioReport
    artifact_checksums: dict[str, str] = Field(default_factory=dict)
    artifact_sizes: dict[str, int] = Field(default_factory=dict)
    artifacts: list[ResultExportArtifact] = Field(default_factory=list)


class ResultExportSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    overall_status: OperationStatus
    summary: str
    note: str
    target_directory: str
    latest_report_id: str | None = None
    latest_csv_path: str | None = None
    latest_pdf_path: str | None = None
    latest_manifest_path: str | None = None
    total_entries: int
    entries: list[ResultExportEntry] = Field(default_factory=list)


class ResultExportBuildResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    summary: str
    entry: ResultExportEntry
    report: ScenarioReport


class ResultExportPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    summary: str
    report: ScenarioReport
    planned_sections: list[str] = Field(default_factory=list)
    planned_artifacts: list[str] = Field(default_factory=list)


class ResultExportBatchBuildResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    summary: str
    entries: list[ResultExportEntry] = Field(default_factory=list)


class ExportService:
    _CYRILLIC_TO_ASCII = str.maketrans(
        {
            "А": "A",
            "Б": "B",
            "В": "V",
            "Г": "G",
            "Д": "D",
            "Е": "E",
            "Ё": "E",
            "Ж": "Zh",
            "З": "Z",
            "И": "I",
            "Й": "Y",
            "К": "K",
            "Л": "L",
            "М": "M",
            "Н": "N",
            "О": "O",
            "П": "P",
            "Р": "R",
            "С": "S",
            "Т": "T",
            "У": "U",
            "Ф": "F",
            "Х": "Kh",
            "Ц": "Ts",
            "Ч": "Ch",
            "Ш": "Sh",
            "Щ": "Shch",
            "Ъ": "",
            "Ы": "Y",
            "Ь": "",
            "Э": "E",
            "Ю": "Yu",
            "Я": "Ya",
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ё": "e",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "й": "y",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "kh",
            "ц": "ts",
            "ч": "ch",
            "ш": "sh",
            "щ": "shch",
            "ъ": "",
            "ы": "y",
            "ь": "",
            "э": "e",
            "ю": "yu",
            "я": "ya",
        }
    )

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

    def build_snapshot(self, limit: int = 8) -> ResultExportSnapshot:
        entries = self._load_entries()
        visible_entries = entries[:limit]

        if not visible_entries:
            overall_status = OperationStatus.WARNING
            summary = (
                "Сценарные отчёты пока не собирались; сформируйте единый PDF/CSV-отчёт, "
                "чтобы зафиксировать активный режим."
            )
        elif all(self._entry_files_exist(entry) for entry in visible_entries):
            overall_status = OperationStatus.NORMAL
            summary = (
                f"Собрано {len(entries)} отчётов; последний манифест доступен как "
                f"{visible_entries[0].manifest_path}."
            )
        else:
            overall_status = OperationStatus.WARNING
            summary = (
                f"Собрано {len(entries)} отчётов, но часть файлов в последних "
                "записях отсутствует."
            )

        latest_entry = visible_entries[0] if visible_entries else None
        return ResultExportSnapshot(
            generated_at=datetime.now(timezone.utc),
            overall_status=overall_status,
            summary=summary,
            note=(
                "Каждый отчёт строится из единого контракта сценарного отчёта: "
                "метаданные прогона, ключевые выводы, таблицы статусов, легенды "
                "статусов, параметров, состояния, тревог и тренда, а также "
                "манифест в artifacts/exports."
            ),
            target_directory="artifacts/exports",
            latest_report_id=latest_entry.report_id if latest_entry else None,
            latest_csv_path=latest_entry.csv_path if latest_entry else None,
            latest_pdf_path=latest_entry.pdf_path if latest_entry else None,
            latest_manifest_path=latest_entry.manifest_path if latest_entry else None,
            total_entries=len(entries),
            entries=visible_entries,
        )

    def build_report(
        self,
        result: SimulationResult,
        session: SimulationSession | None = None,
        *,
        generated_at: datetime | None = None,
        report_id: str | None = None,
    ) -> ScenarioReport:
        generated_at = generated_at or datetime.now(timezone.utc)
        source_type, source_label = self._source_metadata(result)
        report_id = report_id or f"pvu-report-{generated_at.astimezone():%Y%m%d-%H%M%S}"

        metadata = ScenarioReportMetadata(
            report_id=report_id,
            generated_at=generated_at,
            source_type=source_type,
            source_label=source_label,
            scenario_id=result.scenario_id,
            scenario_title=result.scenario_title,
            control_mode=result.parameters.control_mode.value,
            status=result.state.status,
            alarm_count=len(result.alarms),
            trend_points=len(result.trend.points),
            horizon_minutes=result.trend.horizon_minutes,
            step_minutes=result.trend.step_minutes,
            session_id=session.session_id if session else None,
            session_status=session.status.value if session else None,
            elapsed_minutes=session.elapsed_minutes if session else None,
        )
        return ScenarioReport(
            metadata=metadata,
            findings=self._build_findings(result),
            tables=self._build_tables(result, metadata),
            sections=self._build_sections(),
            chart_specs=self._build_chart_specs(),
        )

    def preview_result(
        self,
        result: SimulationResult,
        session: SimulationSession | None = None,
    ) -> ResultExportPreview:
        generated_at = datetime.now(timezone.utc)
        report = self.build_report(result, session, generated_at=generated_at)
        return ResultExportPreview(
            generated_at=generated_at,
            summary=(
                f"Предпросмотр отчёта для {report.metadata.source_label}: "
                f"{len(report.sections)} разделов, {len(report.chart_specs)} график, "
                "артефакты CSV/PDF/manifest будут созданы при сборке."
            ),
            report=report,
            planned_sections=[section.section_id for section in report.sections],
            planned_artifacts=["csv", "pdf", "manifest"],
        )

    def export_result(
        self,
        result: SimulationResult,
        session: SimulationSession | None = None,
    ) -> ResultExportBuildResult:
        generated_at = datetime.now(timezone.utc)
        target_directory = self._export_directory(generated_at)
        target_directory.mkdir(parents=True, exist_ok=True)

        report_stem = f"pvu-report-{generated_at.astimezone():%Y%m%d-%H%M%S}"
        csv_path = target_directory / f"{report_stem}.csv"
        sequence = 2
        while csv_path.exists():
            csv_path = target_directory / f"{report_stem}-{sequence}.csv"
            sequence += 1

        report_stem = csv_path.stem
        pdf_path = target_directory / f"{report_stem}.pdf"
        manifest_path = target_directory / f"{report_stem}.manifest.json"

        report = self.build_report(
            result,
            session,
            generated_at=generated_at,
            report_id=report_stem,
        )
        self._write_csv(report, csv_path)
        self._write_pdf(report, pdf_path)

        entry = ResultExportEntry(
            report_id=report.metadata.report_id,
            captured_at=generated_at,
            source_type=report.metadata.source_type,
            source_label=report.metadata.source_label,
            scenario_id=result.scenario_id,
            scenario_title=result.scenario_title,
            status=result.state.status,
            alarm_count=len(result.alarms),
            trend_points=len(result.trend.points),
            finding_count=len(report.findings),
            table_count=len(report.tables),
            csv_path=self._relative_path(csv_path),
            pdf_path=self._relative_path(pdf_path),
            manifest_path=self._relative_path(manifest_path),
        )
        artifact_validations = {
            "csv": self._artifact_validation(
                "csv",
                "CSV отчёт",
                csv_path,
            ),
            "pdf": self._artifact_validation(
                "pdf",
                "PDF отчёт",
                pdf_path,
            ),
        }
        manifest = ResultExportManifest(
            report_id=report.metadata.report_id,
            generated_at=generated_at,
            entry=entry,
            report=report,
            artifact_checksums={
                artifact_id: artifact.sha256 or ""
                for artifact_id, artifact in artifact_validations.items()
            },
            artifact_sizes={
                artifact_id: artifact.size_bytes or 0
                for artifact_id, artifact in artifact_validations.items()
            },
            artifacts=list(artifact_validations.values()),
        )
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        manifest_artifact = self._artifact_validation(
            "manifest",
            "Манифест",
            manifest_path,
        )
        for _ in range(3):
            manifest = manifest.model_copy(
                update={
                    "artifact_sizes": {
                        **manifest.artifact_sizes,
                        "manifest": manifest_artifact.size_bytes or 0,
                    },
                    "artifacts": [
                        *manifest.artifacts[:2],
                        manifest_artifact,
                    ],
                }
            )
            manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
            current_size = manifest_path.stat().st_size
            if current_size == manifest_artifact.size_bytes:
                break
            manifest_artifact = manifest_artifact.model_copy(
                update={"size_bytes": current_size}
            )

        return ResultExportBuildResult(
            generated_at=generated_at,
            summary=(
                f"Сценарный отчёт для {report.metadata.source_label} сохранён: "
                f"CSV/PDF + манифест в {self._relative_path(target_directory)}."
            ),
            entry=entry,
            report=report,
        )

    def export_results(
        self,
        items: list[tuple[SimulationResult, SimulationSession | None]],
    ) -> ResultExportBatchBuildResult:
        generated_at = datetime.now(timezone.utc)
        entries = [
            self.export_result(result, session).entry
            for result, session in items
        ]
        return ResultExportBatchBuildResult(
            generated_at=generated_at,
            summary=f"Собрано {len(entries)} сценарных отчётов CSV/PDF/manifest.",
            entries=entries,
        )

    def _load_entries(self) -> list[ResultExportEntry]:
        export_root = self._export_root()
        if not export_root.exists():
            return []

        manifest_paths = sorted(
            (
                path
                for path in export_root.rglob("*.manifest.json")
                if path.is_file()
            ),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
        entries: list[ResultExportEntry] = []
        for manifest_path in manifest_paths:
            entry = self._load_entry_from_manifest(manifest_path)
            if entry is None:
                continue
            entries.append(entry)
        entries.sort(key=lambda entry: (entry.captured_at, entry.report_id), reverse=True)
        return entries

    def _load_entry_from_manifest(
        self,
        manifest_path: Path,
    ) -> ResultExportEntry | None:
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except ValueError:
            return None

        if not isinstance(payload, dict):
            return None

        entry_payload = payload.get("entry", payload)
        if not isinstance(entry_payload, dict):
            return None

        normalized_payload = dict(entry_payload)
        legacy_export_id = normalized_payload.pop("export_id", None)
        normalized_payload.pop("xlsx_path", None)
        normalized_payload.setdefault("report_id", legacy_export_id)
        normalized_payload.setdefault("schema_version", REPORT_SCHEMA_VERSION)
        normalized_payload.setdefault("finding_count", 0)
        normalized_payload.setdefault("table_count", 0)
        normalized_payload["manifest_path"] = self._relative_path(manifest_path)

        if normalized_payload.get("report_id") is None:
            return None

        try:
            return ResultExportEntry.model_validate(normalized_payload)
        except ValueError:
            return None

    def _entry_files_exist(self, entry: ResultExportEntry) -> bool:
        return all(
            self._path_resolver.resolve_display_path(relative_path).exists()
            for relative_path in [
                entry.csv_path,
                entry.pdf_path,
                entry.manifest_path,
            ]
        )

    def _build_findings(
        self,
        result: SimulationResult,
    ) -> list[ScenarioReportFinding]:
        supply_gap = result.state.supply_temp_c - result.parameters.supply_temp_setpoint_c
        room_delta = (
            result.trend.points[-1].room_temp_c - result.trend.points[0].room_temp_c
            if result.trend.points
            else 0.0
        )
        findings = [
            ScenarioReportFinding(
                finding_id="operating-status",
                title="Общий режим установки",
                severity=result.state.status,
                conclusion=(
                    f"Статус режима: {self._status_service.status_label(result.state.status)}; "
                    f"активных тревог: {len(result.alarms)}."
                ),
            ),
            ScenarioReportFinding(
                finding_id="supply-gap",
                title="Отклонение притока от уставки",
                severity=evaluate_upper_threshold(
                    abs(supply_gap),
                    self._status_service.thresholds.supply_temp_gap_c,
                ),
                conclusion=(
                    f"Фактический приток {result.state.supply_temp_c:.2f} °C, "
                    f"уставка {result.parameters.supply_temp_setpoint_c:.2f} °C, "
                    f"отклонение {supply_gap:+.2f} °C."
                ),
            ),
            ScenarioReportFinding(
                finding_id="energy-balance",
                title="Энергетическая нагрузка",
                severity=result.state.status,
                conclusion=(
                    f"Суммарная мощность {result.state.total_power_kw:.2f} кВт, "
                    f"нагреватель {result.state.heating_power_kw:.2f} кВт, "
                    f"вентилятор {result.state.fan_power_kw:.2f} кВт."
                ),
            ),
            ScenarioReportFinding(
                finding_id="room-trend",
                title="Динамика помещения",
                severity=evaluate_upper_threshold(
                    abs(room_delta),
                    self._status_service.thresholds.supply_temp_gap_c,
                ),
                conclusion=(
                    f"Температура помещения изменилась на {room_delta:+.2f} °C "
                    f"за {result.trend.horizon_minutes} мин "
                    f"при шаге {result.trend.step_minutes} мин."
                ),
            ),
        ]
        return findings

    def _build_tables(
        self,
        result: SimulationResult,
        metadata: ScenarioReportMetadata,
    ) -> list[ScenarioReportTable]:
        return [
            ScenarioReportTable(
                table_id="summary",
                title="Сводка прогона",
                columns=["Показатель", "Значение"],
                rows=self._summary_rows(metadata),
            ),
            ScenarioReportTable(
                table_id="status",
                title="Статусы KPI и блока тревог",
                columns=["Зона", "Статус", "Основание"],
                rows=self._status_service.build_export_status_rows(result),
            ),
            ScenarioReportTable(
                table_id="status_legend",
                title="Легенда статусов",
                columns=["Статус", "Цвет", "Правило"],
                rows=self._status_service.build_export_legend_rows(),
            ),
            ScenarioReportTable(
                table_id="parameters",
                title="Параметры сценария",
                columns=["Параметр", "Значение"],
                rows=self._field_rows(result.parameters.model_dump(mode="json")),
            ),
            ScenarioReportTable(
                table_id="state",
                title="Итоговое состояние",
                columns=["Показатель", "Значение"],
                rows=self._field_rows(result.state.model_dump(mode="json")),
            ),
            ScenarioReportTable(
                table_id="status_events",
                title="Статусные события",
                columns=["Код", "Уровень", "Сообщение"],
                rows=(
                    [
                        [
                            alarm.code,
                            self._alarm_level_label(alarm.level.value),
                            alarm.message,
                    ]
                    for alarm in result.alarms
                ]
                    or [["-", "Норма", "Активных статусных событий нет."]]
                ),
            ),
            ScenarioReportTable(
                table_id="trend",
                title="Тренд по шагам",
                columns=[
                    "Минута",
                    "Наружная, °C",
                    "Приток, °C",
                    "Помещение, °C",
                    "Нагрев, кВт",
                    "Суммарная мощность, кВт",
                    "Расход, м³/ч",
                    "ΔP фильтра, Па",
                ],
                rows=[
                    [
                        str(point.minute),
                        self._format_float(point.outdoor_temp_c),
                        self._format_float(point.supply_temp_c),
                        self._format_float(point.room_temp_c),
                        self._format_float(point.heating_power_kw),
                        self._format_float(point.total_power_kw),
                        self._format_float(point.airflow_m3_h),
                        self._format_float(point.filter_pressure_drop_pa),
                    ]
                    for point in result.trend.points
                ],
            ),
        ]

    def _build_sections(self) -> list[ReportSection]:
        return [
            ReportSection(
                section_id="metadata",
                title="Метаданные",
                table_ids=["summary", "status"],
            ),
            ReportSection(section_id="findings", title="Ключевые выводы"),
            ReportSection(
                section_id="parameters",
                title="Параметры сценария",
                table_ids=["parameters"],
            ),
            ReportSection(
                section_id="state",
                title="Итоговое состояние",
                table_ids=["state"],
            ),
            ReportSection(
                section_id="status_legend",
                title="Легенда статусов",
                table_ids=["status_legend"],
            ),
            ReportSection(
                section_id="status_events",
                title="Статусные события",
                table_ids=["status_events"],
            ),
            ReportSection(
                section_id="trend",
                title="Тренд по шагам",
                table_ids=["trend"],
            ),
        ]

    def _build_chart_specs(self) -> list[ReportChartSpec]:
        return [
            ReportChartSpec(
                chart_id="trend_temperature_power",
                title="Тренд температуры и мощности",
                source_table_id="trend",
                x_axis="Минута",
                y_axes=[
                    "Приток, °C",
                    "Помещение, °C",
                    "Нагрев, кВт",
                    "Суммарная мощность, кВт",
                ],
            )
        ]

    def _summary_rows(self, metadata: ScenarioReportMetadata) -> list[list[str]]:
        rows = [
            ["идентификатор_отчёта", metadata.report_id],
            ["время_формирования", metadata.generated_at.isoformat()],
            ["тип_источника", self._source_type_label(metadata.source_type)],
            ["источник", metadata.source_label],
            ["идентификатор_сценария", metadata.scenario_id or "-"],
            ["название_сценария", metadata.scenario_title or "-"],
            ["режим_управления", self._control_mode_label(metadata.control_mode)],
            ["статус", self._status_service.status_label(metadata.status)],
            ["количество_тревог", str(metadata.alarm_count)],
            ["точки_тренда", str(metadata.trend_points)],
            ["горизонт_минут", str(metadata.horizon_minutes)],
            ["шаг_минут", str(metadata.step_minutes)],
        ]
        if metadata.session_id is not None:
            rows.extend(
                [
                    ["идентификатор_сессии", metadata.session_id],
                    ["статус_сессии", self._session_status_label(metadata.session_status)],
                    ["прошло_минут", str(metadata.elapsed_minutes or 0)],
                ]
            )
        return rows

    def _field_rows(self, payload: dict[str, object]) -> list[list[str]]:
        rows: list[list[str]] = []
        for field_name, field_value in payload.items():
            if field_name == "status":
                rows.append([self._field_label(field_name), self._status_value_label(field_value)])
                continue
            rows.append([self._field_label(field_name), self._format_scalar(field_value)])
        return rows

    def _write_csv(self, report: ScenarioReport, target_path: Path) -> None:
        tables_by_id = {table.table_id: table for table in report.tables}
        with target_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["section", "key", "value"])
            writer.writerow(["metadata", "schema_version", report.schema_version])
            for key, value in self._summary_rows(report.metadata):
                writer.writerow(["metadata", key, value])

            writer.writerow([])
            writer.writerow(["section", "finding_id", "title", "severity", "conclusion"])
            for finding in report.findings:
                writer.writerow(
                    [
                        "findings",
                        finding.finding_id,
                        finding.title,
                        self._status_service.status_label(finding.severity),
                        finding.conclusion,
                    ]
                )

            for section in report.sections:
                if section.section_id in {"metadata", "findings"}:
                    continue
                for table_id in section.table_ids:
                    table = tables_by_id.get(table_id)
                    if table is None:
                        continue
                    writer.writerow([])
                    writer.writerow(["section", section.section_id, table.title])
                    writer.writerow([section.section_id, *table.columns])
                    for row in table.rows:
                        writer.writerow([section.section_id, *row])

    def _write_pdf(self, report: ScenarioReport, target_path: Path) -> None:
        if self._write_reportlab_pdf(report, target_path):
            return
        lines = self._build_pdf_lines(report)
        if write_text_pdf(target_path, lines, title="Сценарный отчёт"):
            return
        fallback_lines = [to_ascii_text(line) for line in lines]
        target_path.write_bytes(self._build_pdf_document(fallback_lines))

    def _write_reportlab_pdf(self, report: ScenarioReport, target_path: Path) -> bool:
        try:
            from reportlab.graphics.charts.linecharts import HorizontalLineChart
            from reportlab.graphics.shapes import Drawing, String
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.platypus import (
                PageBreak,
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )
        except Exception:
            return False

        try:
            font_name, supports_unicode = self._resolve_reportlab_font(pdfmetrics, TTFont)
            styles = getSampleStyleSheet()
            normal_style = ParagraphStyle(
                "AhuNormal",
                parent=styles["BodyText"],
                fontName=font_name,
                fontSize=9,
                leading=12,
            )
            heading_style = ParagraphStyle(
                "AhuHeading",
                parent=styles["Heading2"],
                fontName=font_name,
                fontSize=13,
                leading=16,
                spaceAfter=6,
            )
            title_style = ParagraphStyle(
                "AhuTitle",
                parent=styles["Title"],
                fontName=font_name,
                fontSize=20,
                leading=24,
                spaceAfter=12,
            )

            def text(value: object) -> str:
                raw = str(value)
                return raw if supports_unicode else to_ascii_text(raw)

            document = SimpleDocTemplate(
                str(target_path),
                pagesize=A4,
                rightMargin=14 * mm,
                leftMargin=14 * mm,
                topMargin=14 * mm,
                bottomMargin=14 * mm,
                title=text("Сценарный отчёт ПВУ"),
                author="Ahu Simulator",
            )
            story: list = [
                Paragraph(text("Сценарный отчёт ПВУ"), title_style),
                Paragraph(
                    text(
                        f"{report.metadata.source_label} · "
                        f"{self._status_service.status_label(report.metadata.status)} · "
                        f"{report.metadata.generated_at.isoformat()}"
                    ),
                    normal_style,
                ),
                Spacer(1, 8),
                self._pdf_table(
                    [["Показатель", "Значение"], *self._summary_rows(report.metadata)],
                    font_name,
                    normal_style,
                    text,
                ),
                Spacer(1, 8),
                Paragraph(text("KPI и статусная сводка"), heading_style),
                self._pdf_table(
                    self._limited_table_rows(
                        self._table_by_id(report, "status"),
                        text,
                        max_rows=12,
                    ),
                    font_name,
                    normal_style,
                    text,
                ),
                PageBreak(),
                Paragraph(text("Ключевые выводы"), heading_style),
            ]
            for finding in report.findings:
                story.append(
                    Paragraph(
                        text(
                            f"[{self._status_service.status_label(finding.severity)}] "
                            f"{finding.title}: {finding.conclusion}"
                        ),
                        normal_style,
                    )
                )
                story.append(Spacer(1, 4))

            for table_id in ("parameters", "state", "status_legend", "status_events"):
                table = self._table_by_id(report, table_id)
                story.extend(
                    [
                        Spacer(1, 8),
                        Paragraph(text(table.title), heading_style),
                        self._pdf_table(
                            self._limited_table_rows(table, text, max_rows=18),
                            font_name,
                            normal_style,
                            text,
                        ),
                    ]
                )

            trend_table = self._table_by_id(report, "trend")
            story.extend(
                [
                    PageBreak(),
                    Paragraph(text("Тренд по шагам"), heading_style),
                    self._build_trend_chart(
                        trend_table,
                        text,
                        HorizontalLineChart,
                        Drawing,
                        String,
                        colors,
                    ),
                    Spacer(1, 8),
                    self._pdf_table(
                        self._limited_table_rows(trend_table, text, max_rows=18),
                        font_name,
                        normal_style,
                        text,
                    ),
                ]
            )
            document.build(story)
            return True
        except Exception:
            return False

    def _pdf_table(
        self,
        rows: list[list[str]],
        font_name: str,
        normal_style,
        text,
    ):
        from reportlab.lib import colors
        from reportlab.platypus import Paragraph, Table, TableStyle

        formatted_rows = [
            [Paragraph(text(cell), normal_style) for cell in row]
            for row in rows
        ]
        table = Table(formatted_rows, repeatRows=1, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5eef6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f2933")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d8dee4")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        return table

    def _build_trend_chart(
        self,
        table: ScenarioReportTable,
        text,
        HorizontalLineChart,
        Drawing,
        String,
        colors,
    ):
        drawing = Drawing(500, 190)
        if not table.rows:
            drawing.add(String(42, 95, text("Трендовые точки отсутствуют."), fontSize=9))
            return drawing
        chart = HorizontalLineChart()
        chart.x = 40
        chart.y = 35
        chart.height = 120
        chart.width = 420
        chart.data = [
            [float(row[2]) for row in table.rows[:24]],
            [float(row[3]) for row in table.rows[:24]],
            [float(row[5]) for row in table.rows[:24]],
        ]
        chart.categoryAxis.categoryNames = [row[0] for row in table.rows[:24]]
        chart.categoryAxis.labels.angle = 45
        chart.categoryAxis.labels.boxAnchor = "ne"
        chart.valueAxis.valueMin = min(min(series) for series in chart.data) - 2
        chart.valueAxis.valueMax = max(max(series) for series in chart.data) + 2
        chart.lines[0].strokeColor = colors.HexColor("#f97316")
        chart.lines[1].strokeColor = colors.HexColor("#0891b2")
        chart.lines[2].strokeColor = colors.HexColor("#c2410c")
        drawing.add(chart)
        drawing.add(String(42, 170, text("Приток / помещение / мощность"), fontSize=9))
        return drawing

    def _limited_table_rows(
        self,
        table: ScenarioReportTable,
        text,
        *,
        max_rows: int,
    ) -> list[list[str]]:
        visible_rows = table.rows[:max_rows]
        rows = [table.columns, *visible_rows]
        if len(table.rows) > max_rows:
            rows.append(["…", text(f"Показано {max_rows} из {len(table.rows)} строк")])
        return rows

    def _table_by_id(self, report: ScenarioReport, table_id: str) -> ScenarioReportTable:
        for table in report.tables:
            if table.table_id == table_id:
                return table
        raise KeyError(table_id)

    def _artifact_validation(
        self,
        artifact_id: str,
        label: str,
        path: Path,
    ) -> ResultExportArtifact:
        exists = path.exists()
        return ResultExportArtifact(
            artifact_id=artifact_id,
            label=label,
            path=self._relative_path(path),
            exists=exists,
            size_bytes=path.stat().st_size if exists else None,
            sha256=self._sha256(path) if exists and artifact_id != "manifest" else None,
        )

    def _sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _resolve_reportlab_font(self, pdfmetrics, TTFont) -> tuple[str, bool]:
        font_path = self._find_unicode_font_path()
        if font_path is not None:
            font_name = "AhuUnicode"
            try:
                if font_name not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                return font_name, True
            except Exception:
                pass
        return "Helvetica", False

    def _find_unicode_font_path(self) -> Path | None:
        candidates = [
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/calibri.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
            Path("/Library/Fonts/Arial Unicode.ttf"),
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate
        return None

    def _build_pdf_lines(self, report: ScenarioReport) -> list[str]:
        lines = [
            "Сценарный отчёт ПВУ",
            "",
            "Метаданные",
        ]
        for key, value in self._summary_rows(report.metadata):
            lines.append(f"{key}: {value}")

        lines.extend(["", "Ключевые выводы"])
        for finding in report.findings:
            lines.append(
                f"- [{self._status_service.status_label(finding.severity)}] "
                f"{finding.title}: {finding.conclusion}"
            )

        for table in report.tables:
            lines.extend(["", table.title, " | ".join(table.columns)])
            lines.extend(" | ".join(row) for row in table.rows)
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

    def _format_scalar(self, value: object) -> str:
        if value is None:
            return "-"
        if isinstance(value, float):
            return self._format_float(value)
        return str(value)

    def _format_float(self, value: float) -> str:
        return f"{value:.2f}"

    def _source_metadata(self, result: SimulationResult) -> tuple[str, str]:
        if result.scenario_id and result.scenario_title:
            return "scenario", f"{result.scenario_title} ({result.scenario_id})"
        return "custom", "Пользовательский режим"

    def _source_type_label(self, source_type: str) -> str:
        source_type_labels = {
            "scenario": "Сценарий",
            "custom": "Пользовательский",
            "active": "Текущий прогон",
            "archive": "Архив",
        }
        return source_type_labels.get(source_type, source_type)

    def _control_mode_label(self, control_mode: str) -> str:
        control_mode_labels = {
            "auto": "Авто",
            "manual": "Ручной",
        }
        return control_mode_labels.get(control_mode, control_mode)

    def _session_status_label(self, session_status: str | None) -> str:
        if session_status is None:
            return "-"
        session_status_labels = {
            "idle": "Ожидание",
            "running": "Выполняется",
            "paused": "На паузе",
            "completed": "Завершено",
        }
        return session_status_labels.get(session_status, session_status)

    def _field_label(self, field_name: str) -> str:
        field_labels = {
            "outdoor_temp_c": "Наружная температура, °C",
            "airflow_m3_h": "Расход воздуха, м³/ч",
            "supply_temp_setpoint_c": "Уставка притока, °C",
            "heat_recovery_efficiency": "Эффективность рекуперации",
            "heater_power_kw": "Мощность нагревателя, кВт",
            "filter_contamination": "Загрязнение фильтра",
            "fan_speed_ratio": "Относительная скорость вентилятора",
            "room_temp_c": "Температура помещения, °C",
            "room_heat_gain_kw": "Теплопритоки помещения, кВт",
            "room_volume_m3": "Объём помещения, м³",
            "room_thermal_capacity_kwh_per_k": "Теплоёмкость помещения, кВт·ч/К",
            "room_loss_coeff_kw_per_k": "Коэффициент теплопотерь, кВт/К",
            "control_mode": "Режим управления",
            "horizon_minutes": "Горизонт моделирования, мин",
            "step_minutes": "Шаг моделирования, мин",
            "timestamp": "Метка времени",
            "actual_airflow_m3_h": "Фактический расход, м³/ч",
            "mixed_air_temp_c": "Температура смеси, °C",
            "recovered_air_temp_c": "Температура после рекуперации, °C",
            "supply_temp_c": "Температура притока, °C",
            "heating_power_kw": "Нагрев, кВт",
            "heater_load_ratio": "Доля нагрузки нагревателя",
            "fan_power_kw": "Мощность вентилятора, кВт",
            "total_power_kw": "Суммарная мощность, кВт",
            "energy_intensity_kw_per_1000_m3_h": "Удельная мощность, кВт/1000 м³/ч",
            "filter_pressure_drop_pa": "Перепад давления фильтра, Па",
            "heat_balance_kw": "Тепловой баланс, кВт",
            "status": "Статус",
        }
        return field_labels.get(field_name, field_name)

    def _alarm_level_label(self, alarm_level: str) -> str:
        alarm_level_labels = {
            "info": self._status_service.status_label(OperationStatus.NORMAL),
            "warning": self._status_service.status_label(OperationStatus.WARNING),
            "critical": self._status_service.status_label(OperationStatus.ALARM),
        }
        return alarm_level_labels.get(alarm_level, alarm_level)

    def _status_value_label(self, value: object) -> str:
        try:
            return self._status_service.status_label(OperationStatus(str(value)))
        except ValueError:
            return self._format_scalar(value)

    def _export_root(self) -> Path:
        return self._path_resolver.runtime_directories.exports

    def _export_directory(self, generated_at: datetime) -> Path:
        return self._export_root() / generated_at.astimezone().strftime("%Y-%m-%d")

    def _relative_path(self, absolute_path: Path) -> str:
        return self._path_resolver.to_display_path(absolute_path)
