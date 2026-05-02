from __future__ import annotations

from dataclasses import dataclass

from app.services.validation_service import (
    ValidationCaseEvaluation,
    ValidationMatrixEvaluation,
    ValidationMetricEvaluation,
)
from app.simulation.state import OperationStatus
from app.ui.viewmodels.status_presenter import status_text


@dataclass(frozen=True)
class ValidationMetricView:
    label: str
    expected_text: str
    actual_text: str
    result_text: str
    result_class_name: str


@dataclass(frozen=True)
class ValidationCaseView:
    case_id: str
    title: str
    badge_text: str
    badge_class_name: str
    status_text: str
    alarms_text: str
    metrics: list[ValidationMetricView]


@dataclass(frozen=True)
class ValidationMatrixView:
    summary_text: str
    summary_class_name: str
    intro: str
    agreement_text: str
    note: str
    generated_at_text: str
    cases: list[ValidationCaseView]


def build_validation_matrix_view(
    matrix: ValidationMatrixEvaluation,
) -> ValidationMatrixView:
    cases = [_build_case_view(case) for case in matrix.cases]
    return ValidationMatrixView(
        summary_text=f"{matrix.passed_cases} / {matrix.total_cases} эталонных режимов проходят",
        summary_class_name=_result_class(matrix.all_passed),
        intro=(
            "Пакет валидации показывает, как текущая MVP-модель воспроизводит согласованную "
            "матрицу из `data/validation/reference_points.json`."
        ),
        agreement_text=f"Протокол согласия: {matrix.agreement.summary}",
        note=matrix.pending_note,
        generated_at_text=matrix.generated_at.isoformat(),
        cases=cases,
    )


def _build_case_view(case: ValidationCaseEvaluation) -> ValidationCaseView:
    metrics = [_build_metric_view(metric) for metric in case.metrics]
    expected_status = _status_label(case.expected_status)
    actual_status = _status_label(case.actual_status)
    expected_alarms = ", ".join(case.alarms.expected_codes) if case.alarms.expected_codes else "нет"
    actual_alarms = ", ".join(case.alarms.actual_codes) if case.alarms.actual_codes else "нет"
    return ValidationCaseView(
        case_id=case.case_id,
        title=case.title,
        badge_text="Норма" if case.passed else "Проверить",
        badge_class_name=_result_class(case.passed),
        status_text=f"Статус: ожидается {expected_status}, факт {actual_status}.",
        alarms_text=(
            "Тревоги: ожидаются "
            f"{expected_alarms}; фактически {actual_alarms}."
        ),
        metrics=metrics,
    )


def _build_metric_view(metric: ValidationMetricEvaluation) -> ValidationMetricView:
    return ValidationMetricView(
        label=metric.label,
        expected_text=(
            f"{_format_number(metric.expected_range.lower)} .. "
            f"{_format_number(metric.expected_range.upper)} {metric.unit}"
        ),
        actual_text=f"{_format_number(metric.actual_value)} {metric.unit}",
        result_text="Норма" if metric.passed else "Вне диапазона",
        result_class_name=_result_class(metric.passed),
    )


def _result_class(passed: bool) -> str:
    return "status-pill status-normal" if passed else "status-pill status-alarm"


def _format_number(value: float) -> str:
    return f"{value:.1f}"


def _status_label(status: OperationStatus) -> str:
    return status_text(status).lower()
