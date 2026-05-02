from __future__ import annotations

import json
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.infrastructure.runtime_paths import RuntimePathResolver
from app.services.browser_capability_service import BrowserCapabilityService
from app.simulation.state import OperationStatus


class DemoLaunchCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_id: str
    title: str
    command: str
    note: str


class DemoEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    path: str
    purpose: str


class DemoRuntimeVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component: str
    version: str


class DemoReadinessCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    title: str
    status: OperationStatus
    detail: str
    evidence_path: str | None = None


class DemoReadinessEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    overall_status: OperationStatus
    ready_checks: int
    total_checks: int
    summary: str
    note: str
    launch_commands: list[DemoLaunchCommand] = Field(default_factory=list)
    endpoints: list[DemoEndpoint] = Field(default_factory=list)
    runtime_versions: list[DemoRuntimeVersion] = Field(default_factory=list)
    checks: list[DemoReadinessCheck] = Field(default_factory=list)


class DemoPackageEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entry_id: str
    title: str
    category: str
    note: str
    source_paths: list[str] = Field(default_factory=list)
    required: bool = True
    present: bool


class DemoPackageSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    overall_status: OperationStatus
    summary: str
    note: str
    target_directory: str
    bundle_name_pattern: str
    latest_bundle_path: str | None = None
    latest_manifest_path: str | None = None
    entries: list[DemoPackageEntry] = Field(default_factory=list)


class DemoPackageBuildResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    bundle_path: str
    manifest_path: str
    file_count: int
    summary: str


class DemoReadinessService:
    def __init__(
        self,
        project_root: Path,
        dashboard_path: str,
        path_resolver: RuntimePathResolver | None = None,
    ) -> None:
        self._project_root = project_root
        self._dashboard_path = dashboard_path
        self._path_resolver = path_resolver or RuntimePathResolver(project_root)

    def build_readiness(self) -> DemoReadinessEvaluation:
        runtime_versions = self._build_runtime_versions()
        checks = [
            self._build_runtime_stack_check(runtime_versions),
            self._build_presence_check(
                item_id="launch-script",
                title="Локальный стартовый скрипт",
                detail="PowerShell-точка входа для локального показа присутствует.",
                evidence_path="deploy/run-local.ps1; deploy/build-demo-package.ps1",
                required_paths=[
                    "deploy/run-local.ps1",
                    "deploy/build-demo-package.ps1",
                ],
            ),
            self._build_presence_check(
                item_id="source-inputs",
                title="Исходные конфиги и сценарии",
                detail=(
                    "Конфиг, пресеты сценариев, валидационные данные и профиль "
                    "браузера/WebGL присутствуют."
                ),
                evidence_path=(
                    "config/defaults.yaml; config/p0_baseline.yaml; data/scenarios/presets.json; "
                    "data/validation/reference_points.json; data/validation/reference_basis.json; "
                    "data/validation/validation_agreement.json; "
                    "data/visualization/browser_capability_profile.json"
                ),
                required_paths=[
                    "config/defaults.yaml",
                    "config/p0_baseline.yaml",
                    "data/scenarios/presets.json",
                    "data/validation/reference_points.json",
                    "data/validation/reference_basis.json",
                    "data/validation/validation_agreement.json",
                    "data/visualization/browser_capability_profile.json",
                ],
            ),
            self._build_presence_check(
                item_id="docs-and-defense",
                title="Материалы к защите и фазы",
                detail="Документы по фазам, списку задач и защите находятся в проекте.",
                evidence_path=(
                    "docs/05_execution_phases.md; docs/06_todo.md; "
                    "docs/19_p0_baseline.md; "
                    "docs/14_defense_pack.md; docs/15_demo_readiness.md; "
                    "docs/16_demo_package.md; docs/17_scenario_archive.md; "
                    "docs/18_export_pack.md"
                ),
                required_paths=[
                    "docs/05_execution_phases.md",
                    "docs/06_todo.md",
                    "docs/19_p0_baseline.md",
                    "docs/14_defense_pack.md",
                    "docs/15_demo_readiness.md",
                    "docs/16_demo_package.md",
                    "docs/17_scenario_archive.md",
                    "docs/18_export_pack.md",
                ],
            ),
            self._build_presence_check(
                item_id="tests-and-artifacts",
                title="Тесты и артефакты",
                detail=(
                    "Модульные, интеграционные и сценарные тесты, а также "
                    "структурированные директории артефактов доступны."
                ),
                evidence_path=(
                    "tests/unit; tests/integration; tests/scenario; "
                    "artifacts/playwright/README.md; artifacts/demo-packages/README.md; "
                    "artifacts/scenario-archive/README.md; artifacts/exports/README.md"
                ),
                required_paths=[
                    "tests/unit",
                    "tests/integration",
                    "tests/scenario",
                    "artifacts/playwright/README.md",
                    "artifacts/demo-packages/README.md",
                    "artifacts/scenario-archive/README.md",
                    "artifacts/exports/README.md",
                ],
            ),
            self._build_demo_pc_verification_check(),
        ]

        ready_checks = sum(1 for check in checks if check.status == OperationStatus.NORMAL)
        overall_status = self._derive_overall_status(checks)
        return DemoReadinessEvaluation(
            generated_at=datetime.now(timezone.utc),
            overall_status=overall_status,
            ready_checks=ready_checks,
            total_checks=len(checks),
            summary=self._build_readiness_summary(ready_checks, len(checks)),
            note=(
                "Этот блок фиксирует проектную готовность к офлайн-показу: как запускать приложение, "
                "какие артефакты уже собраны, какой профиль браузера/WebGL подтверждён и какие "
                "локальные проверки остаются привязанными к текущему окну браузера."
            ),
            launch_commands=self._build_launch_commands(),
            endpoints=self._build_endpoints(),
            runtime_versions=runtime_versions,
            checks=checks,
        )

    def build_package_snapshot(self) -> DemoPackageSnapshot:
        generated_at = datetime.now(timezone.utc)
        entries = self._build_package_entries()
        latest_bundle_path, latest_manifest_path = self._find_latest_bundle_artifacts()
        has_missing_required_entries = any(
            not entry.present and entry.required for entry in entries
        )

        if has_missing_required_entries:
            overall_status = OperationStatus.ALARM
            summary = "Не все входы для демо-пакета присутствуют; упаковка пока не готова."
        elif latest_bundle_path is None or latest_manifest_path is None:
            overall_status = OperationStatus.WARNING
            summary = (
                "Все входы для демо-пакета готовы, но архив в этой рабочей копии ещё не собран."
            )
        else:
            overall_status = OperationStatus.NORMAL
            summary = (
                "Демо-пакет уже собран; zip и манифест доступны в artifacts/demo-packages."
            )

        return DemoPackageSnapshot(
            generated_at=generated_at,
            overall_status=overall_status,
            summary=summary,
            note=(
                "Пакет включает исходный код, конфиги, валидационные данные, профиль "
                "браузера/WebGL, deploy-скрипты, материалы защиты, последнюю папку ручных "
                "проверок панели Playwright и структуры локального архива сценариев и экспортов."
            ),
            target_directory=self._relative_path(self._bundle_directory(generated_at)),
            bundle_name_pattern="pvu-demo-package-ГГГГММДД-ЧЧММСС.zip",
            latest_bundle_path=(
                self._relative_path(latest_bundle_path) if latest_bundle_path else None
            ),
            latest_manifest_path=(
                self._relative_path(latest_manifest_path)
                if latest_manifest_path
                else None
            ),
            entries=entries,
        )

    def build_demo_package(self) -> DemoPackageBuildResult:
        snapshot = self.build_package_snapshot()
        missing_entries = [
            entry.title
            for entry in snapshot.entries
            if entry.required and not entry.present
        ]
        if missing_entries:
            raise ValueError(
                "Демо-пакет не может быть собран. Отсутствуют обязательные блоки: "
                + ", ".join(missing_entries)
            )

        generated_at = datetime.now(timezone.utc)
        bundle_directory = self._bundle_directory(generated_at)
        bundle_directory.mkdir(parents=True, exist_ok=True)
        bundle_stem = f"pvu-demo-package-{generated_at.astimezone():%Y%m%d-%H%M%S}"
        bundle_path = bundle_directory / f"{bundle_stem}.zip"
        manifest_path = bundle_directory / f"{bundle_stem}.manifest.json"
        files_to_package = self._collect_package_files(snapshot.entries)
        manifest_payload = {
            "generated_at": generated_at.isoformat(),
            "bundle_name": bundle_path.name,
            "bundle_root": bundle_stem,
            "file_count": len(files_to_package),
            "entries": [
                {
                    "entry_id": entry.entry_id,
                    "title": entry.title,
                    "category": entry.category,
                    "note": entry.note,
                    "source_paths": entry.source_paths,
                }
                for entry in snapshot.entries
            ],
        }
        manifest_path.write_text(
            json.dumps(manifest_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        with ZipFile(bundle_path, mode="w", compression=ZIP_DEFLATED) as zip_file:
            for relative_path, source_path in files_to_package.items():
                zip_file.write(
                    source_path,
                    arcname=str(Path(bundle_stem) / relative_path),
                )
            zip_file.write(
                manifest_path,
                arcname=str(Path(bundle_stem) / manifest_path.name),
            )

        return DemoPackageBuildResult(
            generated_at=generated_at,
            bundle_path=self._relative_path(bundle_path),
            manifest_path=self._relative_path(manifest_path),
            file_count=len(files_to_package),
            summary=(
                f"Собран демо-пакет: {bundle_path.name}. "
                f"Внутри {len(files_to_package)} файлов и отдельный манифест."
            ),
        )

    def _build_launch_commands(self) -> list[DemoLaunchCommand]:
        return [
            DemoLaunchCommand(
                command_id="run-local-ps1",
                title="Основной локальный запуск",
                command=r".\deploy\run-local.ps1",
                note="Рекомендуемый способ перед демонстрацией на Windows.",
            ),
            DemoLaunchCommand(
                command_id="uvicorn-direct",
                title="Ручной запуск через uvicorn",
                command="python -m uvicorn app.main:app --app-dir src --reload",
                note="Резервный вариант, если нужно запустить приложение без PowerShell-обёртки.",
            ),
            DemoLaunchCommand(
                command_id="pytest-full",
                title="Полный тест-пакет",
                command="pytest",
                note="Использовать перед упаковкой и после заметных изменений интерфейса/API.",
            ),
            DemoLaunchCommand(
                command_id="build-demo-package",
                title="Собрать демо-пакет",
                command=r".\deploy\build-demo-package.ps1",
                note="Создаёт zip и манифест в artifacts/demo-packages/<дата>/...",
            ),
        ]

    def _build_endpoints(self) -> list[DemoEndpoint]:
        return [
            DemoEndpoint(
                label="Панель управления",
                path=self._dashboard_path,
                purpose="Основной экран демонстрации и защиты.",
            ),
            DemoEndpoint(
                label="Документация API",
                path="/docs",
                purpose="Ручная проверка API-контрактов перед показом.",
            ),
            DemoEndpoint(
                label="Состояние",
                path="/health",
                purpose="Быстрая проверка, что приложение поднялось.",
            ),
            DemoEndpoint(
                label="Матрица валидации",
                path="/validation/matrix",
                purpose="Повторяемая сверка внутренних эталонных режимов.",
            ),
            DemoEndpoint(
                label="Протокол валидации",
                path="/validation/agreement",
                purpose="Снимок внешне согласованных контрольных точек и допусков ручной проверки.",
            ),
            DemoEndpoint(
                label="Профиль браузера",
                path="/visualization/browser-profile",
                purpose="Зафиксированный контур браузера/WebGL для будущего 3D-режима.",
            ),
            DemoEndpoint(
                label="Базовый профиль P0",
                path="/project/baseline",
                purpose="Фиксация рабочего объёма, входов, выходов и сценариев первой версии.",
            ),
            DemoEndpoint(
                label="Готовность к демо",
                path="/readiness/demo",
                purpose="API-снимок преддемонстрационной готовности проекта.",
            ),
            DemoEndpoint(
                label="Демо-пакет",
                path="/readiness/package",
                purpose="Снимок готовности к упаковке и последних артефактов пакета.",
            ),
            DemoEndpoint(
                label="Архив сценариев",
                path="/archive/scenarios",
                purpose="Локальный архив JSON-снимков для сохранённых прогонов и защиты.",
            ),
            DemoEndpoint(
                label="Экспорты результатов",
                path="/exports/result",
                purpose="Снимок локальных CSV/PDF сценарных отчётов для текущих прогонов.",
            ),
        ]

    def _build_runtime_versions(self) -> list[DemoRuntimeVersion]:
        return [
            DemoRuntimeVersion(component="Python", version=self._python_version_label()),
            DemoRuntimeVersion(component="FastAPI", version=self._package_version("fastapi")),
            DemoRuntimeVersion(component="Dash", version=self._package_version("dash")),
            DemoRuntimeVersion(component="Plotly", version=self._package_version("plotly")),
            DemoRuntimeVersion(component="Pydantic", version=self._package_version("pydantic")),
            DemoRuntimeVersion(component="Uvicorn", version=self._package_version("uvicorn")),
            DemoRuntimeVersion(component="pytest", version=self._package_version("pytest")),
        ]

    def _build_runtime_stack_check(
        self,
        runtime_versions: list[DemoRuntimeVersion],
    ) -> DemoReadinessCheck:
        missing_components = [
            runtime.component
            for runtime in runtime_versions
            if runtime.version == "не установлен"
        ]
        if missing_components:
            return DemoReadinessCheck(
                item_id="runtime-stack",
                title="Стек выполнения",
                status=OperationStatus.ALARM,
                detail=(
                    "Не все требуемые библиотеки доступны в текущей среде: "
                    + ", ".join(missing_components)
                ),
                evidence_path="requirements.txt",
            )

        return DemoReadinessCheck(
            item_id="runtime-stack",
            title="Стек выполнения",
            status=OperationStatus.NORMAL,
            detail="Базовые зависимости времени выполнения определяются и готовы к локальному запуску.",
            evidence_path="requirements.txt",
        )

    def _build_demo_pc_verification_check(self) -> DemoReadinessCheck:
        try:
            profile = BrowserCapabilityService(self._project_root).build_profile()
        except (FileNotFoundError, ValidationError, ValueError):
            return DemoReadinessCheck(
                item_id="demo-pc-verification",
                title="Профиль браузера/WebGL демо-ПК",
                status=OperationStatus.ALARM,
                detail=(
                    "Зафиксированный профиль браузера/WebGL отсутствует или не проходит "
                    "собственные требования."
                ),
                evidence_path="data/visualization/browser_capability_profile.json",
            )

        browser_evidence = self._latest_browser_diagnostics_path()
        if browser_evidence is None:
            return DemoReadinessCheck(
                item_id="demo-pc-verification",
                title="Профиль браузера/WebGL демо-ПК",
                status=OperationStatus.WARNING,
                detail=(
                    "Профиль демо-браузера зафиксирован, но в artifacts/playwright ещё нет "
                    "свежей папки dashboard/browser-diagnostics с визуальным подтверждением."
                ),
                evidence_path="data/visualization/browser_capability_profile.json",
            )

        return DemoReadinessCheck(
            item_id="demo-pc-verification",
            title="Профиль браузера/WebGL демо-ПК",
            status=OperationStatus.NORMAL,
            detail=(
                f"Зафиксирован подтверждённый профиль `{profile.profile_id}` и сохранены "
                "Playwright-артефакты по диагностике браузера/WebGL для локального "
                "контура WebGL."
            ),
            evidence_path=(
                "data/visualization/browser_capability_profile.json; "
                + browser_evidence
            ),
        )

    def _build_presence_check(
        self,
        *,
        item_id: str,
        title: str,
        detail: str,
        evidence_path: str,
        required_paths: list[str],
    ) -> DemoReadinessCheck:
        missing_paths = [
            relative_path
            for relative_path in required_paths
            if not (self._project_root / relative_path).exists()
        ]
        if missing_paths:
            return DemoReadinessCheck(
                item_id=item_id,
                title=title,
                status=OperationStatus.ALARM,
                detail="Отсутствуют обязательные файлы/каталоги: " + ", ".join(missing_paths),
                evidence_path=evidence_path,
            )

        return DemoReadinessCheck(
            item_id=item_id,
            title=title,
            status=OperationStatus.NORMAL,
            detail=detail,
            evidence_path=evidence_path,
        )

    @staticmethod
    def _build_readiness_summary(ready_checks: int, total_checks: int) -> str:
        if ready_checks == total_checks:
            return (
                f"{ready_checks} из {total_checks} пунктов готовы; "
                "проектный предварительный контроль закрыт, профиль браузера/WebGL подтверждён."
            )
        return (
            f"{ready_checks} из {total_checks} пунктов готовы; "
            "в проектном предварительном контроле ещё остаются незакрытые шаги."
        )

    def _build_package_entries(self) -> list[DemoPackageEntry]:
        latest_dashboard_evidence = self._latest_manual_dashboard_path()
        latest_browser_evidence = self._latest_browser_diagnostics_path()
        latest_archive_evidence = self._latest_scenario_archive_path()
        latest_export_evidence = self._latest_export_path()
        evidence_paths = [
            "artifacts/demo-packages/README.md",
            "artifacts/playwright/README.md",
        ]
        if latest_dashboard_evidence is not None:
            evidence_paths.append(latest_dashboard_evidence)
        if latest_browser_evidence is not None:
            evidence_paths.append(latest_browser_evidence)

        archive_paths = ["artifacts/scenario-archive/README.md"]
        if latest_archive_evidence is not None:
            archive_paths.append(latest_archive_evidence)

        export_paths = ["artifacts/exports/README.md"]
        if latest_export_evidence is not None:
            export_paths.append(latest_export_evidence)

        return [
            DemoPackageEntry(
                entry_id="application-source",
                title="Исходный код приложения",
                category="Код",
                note="Расчётный слой, API, Dash UI и визуальные адаптеры.",
                source_paths=["src/app"],
                present=self._paths_exist(["src/app"]),
            ),
            DemoPackageEntry(
                entry_id="runtime-inputs",
                title="Конфиг, сценарии, валидация и профиль браузера",
                category="Конфиг и данные",
                note=(
                    "Источник воспроизводимых параметров, эталонов, базового реестра и "
                    "подтверждённого контура браузера/WebGL."
                ),
                source_paths=[
                    "config/defaults.yaml",
                    "config/p0_baseline.yaml",
                    "data/scenarios/presets.json",
                    "data/validation/reference_points.json",
                    "data/validation/reference_basis.json",
                    "data/validation/validation_agreement.json",
                    "data/visualization/scene3d.json",
                    "data/visualization/browser_capability_profile.json",
                ],
                present=self._paths_exist(
                    [
                        "config/defaults.yaml",
                        "config/p0_baseline.yaml",
                        "data/scenarios/presets.json",
                        "data/validation/reference_points.json",
                        "data/validation/reference_basis.json",
                        "data/validation/validation_agreement.json",
                        "data/visualization/scene3d.json",
                        "data/visualization/browser_capability_profile.json",
                    ]
                ),
            ),
            DemoPackageEntry(
                entry_id="deploy-runtime",
                title="Скрипты запуска и зависимости",
                category="Запуск",
                note="Локальный старт, сборка пакета и список Python-зависимостей.",
                source_paths=[
                    "deploy/run-local.ps1",
                    "deploy/build-demo-package.ps1",
                    "deploy/README.md",
                    "requirements.txt",
                ],
                present=self._paths_exist(
                    [
                        "deploy/run-local.ps1",
                        "deploy/build-demo-package.ps1",
                        "deploy/README.md",
                        "requirements.txt",
                    ]
                ),
            ),
            DemoPackageEntry(
                entry_id="defense-docs",
                title="Фазы, задачи и материалы защиты",
                category="Документы",
                note="Основной документационный пакет для показа и передачи проекта дальше.",
                source_paths=[
                    "README.md",
                    "docs/05_execution_phases.md",
                    "docs/06_todo.md",
                    "docs/19_p0_baseline.md",
                    "docs/14_defense_pack.md",
                    "docs/15_demo_readiness.md",
                    "docs/16_demo_package.md",
                    "docs/17_scenario_archive.md",
                    "docs/18_export_pack.md",
                ],
                present=self._paths_exist(
                    [
                        "README.md",
                        "docs/05_execution_phases.md",
                        "docs/06_todo.md",
                        "docs/19_p0_baseline.md",
                        "docs/14_defense_pack.md",
                        "docs/15_demo_readiness.md",
                        "docs/16_demo_package.md",
                        "docs/17_scenario_archive.md",
                        "docs/18_export_pack.md",
                    ]
                ),
            ),
            DemoPackageEntry(
                entry_id="ui-evidence",
                title="Структура артефактов и последние проверки панели",
                category="Артефакты",
                note=(
                    "README по артефактам и последняя папка ручных Playwright-скриншотов "
                    "для панели управления."
                ),
                source_paths=evidence_paths,
                present=self._paths_exist(evidence_paths),
            ),
            DemoPackageEntry(
                entry_id="scenario-archive",
                title="Локальный архив сценариев",
                category="Артефакты",
                note=(
                    "README архива и последняя дата сохранённых JSON-снимков прогонов, "
                    "если записи уже существуют."
                ),
                source_paths=archive_paths,
                required=False,
                present=self._paths_exist(["artifacts/scenario-archive/README.md"]),
            ),
            DemoPackageEntry(
                entry_id="exports",
                title="Локальные сценарные отчёты",
                category="Артефакты",
                note=(
                    "README структуры экспортов и последняя дата CSV/PDF выгрузок, "
                    "если такие артефакты уже собирались."
                ),
                source_paths=export_paths,
                required=False,
                present=self._paths_exist(["artifacts/exports/README.md"]),
            ),
        ]

    def _collect_package_files(
        self,
        entries: list[DemoPackageEntry],
    ) -> dict[Path, Path]:
        files: dict[Path, Path] = {}
        for entry in entries:
            for relative_source_path in entry.source_paths:
                source_path = self._project_root / relative_source_path
                if source_path.is_file():
                    files[Path(relative_source_path)] = source_path
                    continue

                if not source_path.is_dir():
                    continue

                for nested_path in sorted(
                    path for path in source_path.rglob("*") if path.is_file()
                ):
                    files[nested_path.relative_to(self._project_root)] = nested_path
        return files

    def _find_latest_bundle_artifacts(self) -> tuple[Path | None, Path | None]:
        bundle_root = self._path_resolver.runtime_directories.demo_packages
        if not bundle_root.exists():
            return None, None

        zip_candidates = sorted(
            bundle_root.rglob("*.zip"),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
        if not zip_candidates:
            return None, None

        latest_bundle = zip_candidates[0]
        matching_manifest = latest_bundle.with_suffix(".manifest.json")
        if matching_manifest.exists():
            return latest_bundle, matching_manifest
        return latest_bundle, None

    def _latest_manual_dashboard_path(self) -> str | None:
        manual_root = self._project_root / "artifacts" / "playwright" / "manual"
        if not manual_root.exists():
            return None

        dated_dashboard_directories = sorted(
            (
                candidate / "dashboard"
                for candidate in manual_root.iterdir()
                if candidate.is_dir() and (candidate / "dashboard").exists()
            ),
            key=lambda candidate: candidate.name,
        )
        if not dated_dashboard_directories:
            return None
        return self._relative_path(dated_dashboard_directories[-1])

    def _latest_browser_diagnostics_path(self) -> str | None:
        manual_root = self._project_root / "artifacts" / "playwright" / "manual"
        if not manual_root.exists():
            return None

        candidates = sorted(
            (
                candidate / "dashboard" / "browser-diagnostics"
                for candidate in manual_root.iterdir()
                if candidate.is_dir()
                and (candidate / "dashboard" / "browser-diagnostics").exists()
            ),
            key=lambda candidate: candidate.parents[1].name,
        )
        if not candidates:
            return None
        return self._relative_path(candidates[-1])

    def _latest_scenario_archive_path(self) -> str | None:
        archive_root = self._path_resolver.runtime_directories.scenario_archive
        if not archive_root.exists():
            return None

        dated_directories = sorted(
            (
                candidate
                for candidate in archive_root.iterdir()
                if candidate.is_dir()
            ),
            key=lambda candidate: candidate.name,
        )
        if not dated_directories:
            return None
        return self._relative_path(dated_directories[-1])

    def _latest_export_path(self) -> str | None:
        export_root = self._path_resolver.runtime_directories.exports
        if not export_root.exists():
            return None

        dated_directories = sorted(
            (
                candidate
                for candidate in export_root.iterdir()
                if candidate.is_dir()
            ),
            key=lambda candidate: candidate.name,
        )
        if not dated_directories:
            return None
        return self._relative_path(dated_directories[-1])

    def _bundle_directory(self, generated_at: datetime) -> Path:
        return self._path_resolver.runtime_directories.demo_packages / generated_at.astimezone().strftime(
            "%Y-%m-%d"
        )

    def _paths_exist(self, relative_paths: list[str]) -> bool:
        return all((self._project_root / relative_path).exists() for relative_path in relative_paths)

    def _relative_path(self, absolute_path: Path) -> str:
        return self._path_resolver.to_display_path(absolute_path)

    @staticmethod
    def _derive_overall_status(
        checks: list[DemoReadinessCheck],
    ) -> OperationStatus:
        if any(check.status == OperationStatus.ALARM for check in checks):
            return OperationStatus.ALARM
        if any(check.status == OperationStatus.WARNING for check in checks):
            return OperationStatus.WARNING
        return OperationStatus.NORMAL

    @staticmethod
    def _package_version(package_name: str) -> str:
        try:
            return version(package_name)
        except PackageNotFoundError:
            return "не установлен"

    @staticmethod
    def _python_version_label() -> str:
        from sys import version_info

        return ".".join(str(part) for part in version_info[:3])
