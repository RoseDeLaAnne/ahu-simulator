from __future__ import annotations

from dataclasses import dataclass

from app.services.demo_readiness_service import (
    DemoPackageSnapshot,
    DemoReadinessEvaluation,
)
from app.simulation.state import OperationStatus
from app.ui.viewmodels.status_presenter import status_class_name


@dataclass(frozen=True)
class DemoReadinessCommandView:
    title: str
    command: str
    note: str


@dataclass(frozen=True)
class DemoReadinessEndpointView:
    label: str
    path: str
    purpose: str


@dataclass(frozen=True)
class DemoReadinessRuntimeView:
    component: str
    version: str


@dataclass(frozen=True)
class DemoReadinessCheckView:
    title: str
    detail: str
    status_text: str
    status_class_name: str
    evidence_path: str | None


@dataclass(frozen=True)
class DemoReadinessView:
    summary_text: str
    summary_class_name: str
    note: str
    generated_at_text: str
    launch_commands: list[DemoReadinessCommandView]
    endpoints: list[DemoReadinessEndpointView]
    runtime_versions: list[DemoReadinessRuntimeView]
    checks: list[DemoReadinessCheckView]


@dataclass(frozen=True)
class DemoPackageEntryView:
    title: str
    category: str
    note: str
    source_paths_text: str
    status_text: str
    status_class_name: str


@dataclass(frozen=True)
class DemoPackageView:
    status_text: str
    summary_text: str
    summary_class_name: str
    note: str
    generated_at_text: str
    target_directory_text: str
    bundle_name_pattern: str
    latest_bundle_text: str
    latest_manifest_text: str
    entries: list[DemoPackageEntryView]


def build_demo_readiness_view(
    evaluation: DemoReadinessEvaluation,
) -> DemoReadinessView:
    return DemoReadinessView(
        summary_text=evaluation.summary,
        summary_class_name=_status_class_name(evaluation.overall_status),
        note=evaluation.note,
        generated_at_text=evaluation.generated_at.isoformat(),
        launch_commands=[
            DemoReadinessCommandView(
                title=command.title,
                command=command.command,
                note=command.note,
            )
            for command in evaluation.launch_commands
        ],
        endpoints=[
            DemoReadinessEndpointView(
                label=endpoint.label,
                path=endpoint.path,
                purpose=endpoint.purpose,
            )
            for endpoint in evaluation.endpoints
        ],
        runtime_versions=[
            DemoReadinessRuntimeView(
                component=runtime.component,
                version=runtime.version,
            )
            for runtime in evaluation.runtime_versions
        ],
        checks=[
            DemoReadinessCheckView(
                title=check.title,
                detail=check.detail,
                status_text=_status_text(check.status),
                status_class_name=_status_class_name(check.status),
                evidence_path=check.evidence_path,
            )
            for check in evaluation.checks
        ],
    )


def build_demo_package_view(
    snapshot: DemoPackageSnapshot,
) -> DemoPackageView:
    return DemoPackageView(
        status_text=_package_status_text(snapshot.overall_status),
        summary_text=snapshot.summary,
        summary_class_name=_status_class_name(snapshot.overall_status),
        note=snapshot.note,
        generated_at_text=snapshot.generated_at.isoformat(),
        target_directory_text=snapshot.target_directory,
        bundle_name_pattern=snapshot.bundle_name_pattern,
        latest_bundle_text=snapshot.latest_bundle_path or "ещё не создан",
        latest_manifest_text=snapshot.latest_manifest_path or "ещё не создан",
        entries=[
            DemoPackageEntryView(
                title=entry.title,
                category=entry.category,
                note=entry.note,
                source_paths_text="; ".join(entry.source_paths),
                status_text="Готово" if entry.present else "Нет",
                status_class_name=_status_class_name(
                    OperationStatus.NORMAL if entry.present else OperationStatus.ALARM
                ),
            )
            for entry in snapshot.entries
        ],
    )


def _status_text(status: OperationStatus) -> str:
    mapping = {
        OperationStatus.NORMAL: "Готово",
        OperationStatus.WARNING: "Открыто",
        OperationStatus.ALARM: "Нет",
    }
    return mapping[status]


def _status_class_name(status: OperationStatus) -> str:
    return status_class_name(status)


def _package_status_text(status: OperationStatus) -> str:
    mapping = {
        OperationStatus.NORMAL: "Собран",
        OperationStatus.WARNING: "Готово к сборке",
        OperationStatus.ALARM: "Нет",
    }
    return mapping[status]
