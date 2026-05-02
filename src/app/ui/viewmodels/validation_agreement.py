from __future__ import annotations

from dataclasses import dataclass

from app.services.validation_service import (
    ValidationAgreementCaseEvaluation,
    ValidationAgreementEvaluation,
    ValidationAgreementMetricEvaluation,
    ValidationAgreementStepEvaluation,
    ValidationBasisLevel,
    ValidationBasisSource,
)
from app.simulation.state import OperationStatus
from app.ui.viewmodels.status_presenter import status_class_name, status_text


@dataclass(frozen=True)
class ValidationAgreementLinkView:
    source_id: str
    label: str
    url: str


@dataclass(frozen=True)
class ValidationAgreementMetricView:
    summary_text: str
    note: str


@dataclass(frozen=True)
class ValidationAgreementCaseView:
    title: str
    level_text: str
    level_class_name: str
    status_text: str
    alarms_text: str
    note: str
    metrics: list[ValidationAgreementMetricView]
    sources: list[ValidationAgreementLinkView]


@dataclass(frozen=True)
class ValidationAgreementStepView:
    label: str
    level_text: str
    level_class_name: str
    tolerance_text: str
    note: str
    sources: list[ValidationAgreementLinkView]


@dataclass(frozen=True)
class ValidationAgreementView:
    summary_text: str
    summary_class_name: str
    authority_text: str
    approved_on_text: str
    generated_at_text: str
    note: str
    control_points: list[ValidationAgreementCaseView]
    manual_steps: list[ValidationAgreementStepView]
    limitations: list[str]


def build_validation_agreement_view(
    evaluation: ValidationAgreementEvaluation,
) -> ValidationAgreementView:
    source_map = {source.source_id: source for source in evaluation.sources}
    return ValidationAgreementView(
        summary_text=evaluation.summary,
        summary_class_name=_status_class(evaluation.status),
        authority_text=evaluation.authority,
        approved_on_text=evaluation.approved_on.isoformat(),
        generated_at_text=evaluation.generated_at.isoformat(),
        note=evaluation.note,
        control_points=[
            _build_case_view(case, source_map) for case in evaluation.control_points
        ],
        manual_steps=[
            _build_step_view(step, source_map) for step in evaluation.manual_steps
        ],
        limitations=evaluation.limitations,
    )


def _build_case_view(
    case: ValidationAgreementCaseEvaluation,
    source_map: dict[str, ValidationBasisSource],
) -> ValidationAgreementCaseView:
    expected_alarms = ", ".join(case.expected_alarm_codes) if case.expected_alarm_codes else "нет"
    return ValidationAgreementCaseView(
        title=case.title,
        level_text=_level_text(case.basis_level),
        level_class_name=_level_class(case.basis_level),
        status_text=f"Статус: {_status_text(case.expected_status)}.",
        alarms_text=f"Тревоги: {expected_alarms}.",
        note=case.note,
        metrics=[_build_metric_view(metric) for metric in case.metrics],
        sources=[
            ValidationAgreementLinkView(
                source_id=source_id,
                label=source_map[source_id].title,
                url=source_map[source_id].url,
            )
            for source_id in case.source_ids
            if source_id in source_map
        ],
    )


def _build_metric_view(
    metric: ValidationAgreementMetricEvaluation,
) -> ValidationAgreementMetricView:
    return ValidationAgreementMetricView(
        summary_text=(
            f"{metric.label}: цель {_format_number(metric.target_value)} {metric.unit}, "
            f"окно {_format_number(metric.lower_bound)} .. {_format_number(metric.upper_bound)} {metric.unit}"
        ),
        note=metric.note,
    )


def _build_step_view(
    step: ValidationAgreementStepEvaluation,
    source_map: dict[str, ValidationBasisSource],
) -> ValidationAgreementStepView:
    return ValidationAgreementStepView(
        label=step.label,
        level_text=_level_text(step.basis_level),
        level_class_name=_level_class(step.basis_level),
        tolerance_text=f"±{step.tolerance:.2f} {step.unit}",
        note=step.note,
        sources=[
            ValidationAgreementLinkView(
                source_id=source_id,
                label=source_map[source_id].title,
                url=source_map[source_id].url,
            )
            for source_id in step.source_ids
            if source_id in source_map
        ],
    )


def _level_text(level: ValidationBasisLevel) -> str:
    mapping = {
        ValidationBasisLevel.EXTERNAL: "Внешний",
        ValidationBasisLevel.MIXED: "Смешанный",
        ValidationBasisLevel.DERIVED: "Производный",
        ValidationBasisLevel.ASSUMPTION: "Допущение",
    }
    return mapping[level]


def _level_class(level: ValidationBasisLevel) -> str:
    mapping = {
        ValidationBasisLevel.EXTERNAL: "status-pill status-normal",
        ValidationBasisLevel.MIXED: "status-pill status-warning",
        ValidationBasisLevel.DERIVED: "status-pill status-info",
        ValidationBasisLevel.ASSUMPTION: "status-pill status-muted",
    }
    return mapping[level]


def _status_class(status: OperationStatus) -> str:
    return status_class_name(status)


def _status_text(status: OperationStatus) -> str:
    return status_text(status).lower()


def _format_number(value: float) -> str:
    return f"{value:.2f}"
