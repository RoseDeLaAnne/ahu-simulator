from __future__ import annotations

from dataclasses import dataclass

from app.services.validation_service import ManualCheckEvaluation, ManualCheckStepEvaluation


@dataclass(frozen=True)
class ManualCheckStepView:
    label: str
    formula_text: str
    manual_text: str
    model_text: str
    tolerance_text: str
    delta_text: str
    result_text: str
    result_class_name: str


@dataclass(frozen=True)
class ManualCheckView:
    subject_name: str
    source_text: str
    matched_case_text: str
    summary_text: str
    summary_class_name: str
    agreement_text: str
    generated_at_text: str
    note: str
    steps: list[ManualCheckStepView]


def build_manual_check_view(evaluation: ManualCheckEvaluation) -> ManualCheckView:
    steps = [_build_step_view(step) for step in evaluation.steps]
    source_text = (
        f"Сценарий: {evaluation.scenario_id}"
        if evaluation.scenario_id
        else "Источник: пользовательские параметры"
    )
    matched_case_text = (
        f"Контрольная точка: {evaluation.matched_reference_case_title} ({evaluation.matched_reference_case_id})"
        if evaluation.matched_reference_case_id and evaluation.matched_reference_case_title
        else "Контрольная точка: текущий режим вне согласованной матрицы"
    )
    return ManualCheckView(
        subject_name=evaluation.subject_name,
        source_text=source_text,
        matched_case_text=matched_case_text,
        summary_text=(
            f"{evaluation.passed_steps} / {evaluation.total_steps} формульных шагов совпадают"
        ),
        summary_class_name=_result_class(evaluation.all_passed),
        agreement_text=f"Протокол согласия: {evaluation.agreement.summary}",
        generated_at_text=evaluation.generated_at.isoformat(),
        note=evaluation.note,
        steps=steps,
    )


def _build_step_view(step: ManualCheckStepEvaluation) -> ManualCheckStepView:
    return ManualCheckStepView(
        label=step.label,
        formula_text=step.formula,
        manual_text=f"{step.manual_value:.2f} {step.unit}",
        model_text=f"{step.model_value:.2f} {step.unit}",
        tolerance_text=f"±{step.tolerance:.2f} {step.unit}",
        delta_text=f"{step.delta_abs:.2f} {step.unit}",
        result_text="Норма" if step.passed else "Проверить",
        result_class_name=_result_class(step.passed),
    )


def _result_class(passed: bool) -> str:
    return "status-pill status-normal" if passed else "status-pill status-alarm"
