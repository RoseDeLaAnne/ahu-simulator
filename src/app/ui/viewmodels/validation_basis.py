from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from app.services.validation_service import (
    ValidationBasisEvaluation,
    ValidationBasisLevel,
    ValidationBasisSource,
    ValidationBasisTrace,
)
from app.simulation.state import OperationStatus
from app.ui.viewmodels.status_presenter import status_class_name


@dataclass(frozen=True)
class ValidationBasisLinkView:
    source_id: str
    label: str
    url: str


@dataclass(frozen=True)
class ValidationBasisSourceView:
    source_id: str
    title: str
    meta_text: str
    relevance: str
    url: str


@dataclass(frozen=True)
class ValidationBasisTraceView:
    title: str
    level_text: str
    level_class_name: str
    note: str
    sources: list[ValidationBasisLinkView]


@dataclass(frozen=True)
class ValidationBasisView:
    summary_text: str
    summary_class_name: str
    coverage_text: str
    agreement_text: str
    generated_at_text: str
    note: str
    sources: list[ValidationBasisSourceView]
    manual_steps: list[ValidationBasisTraceView]
    reference_cases: list[ValidationBasisTraceView]


def build_validation_basis_view(evaluation: ValidationBasisEvaluation) -> ValidationBasisView:
    source_map = {source.source_id: source for source in evaluation.sources}
    manual_counts = Counter(step.basis_level for step in evaluation.manual_steps)
    return ValidationBasisView(
        summary_text=(
            f"{_format_count(evaluation.total_sources, 'внешний источник', 'внешних источника', 'внешних источников')}, "
            f"{_format_count(evaluation.traced_manual_steps, 'шаг', 'шага', 'шагов')} и "
            f"{_format_count(evaluation.traced_reference_cases, 'контрольная точка', 'контрольные точки', 'контрольных точек')} привязаны"
        ),
        summary_class_name=_status_class(evaluation.agreement.status),
        coverage_text=(
            "По шагам: "
            f"{_format_count(manual_counts[ValidationBasisLevel.EXTERNAL], 'внешний', 'внешних', 'внешних')}, "
            f"{_format_count(manual_counts[ValidationBasisLevel.MIXED], 'смешанный', 'смешанных', 'смешанных')}, "
            f"{_format_count(manual_counts[ValidationBasisLevel.DERIVED], 'производный', 'производных', 'производных')}, "
            f"{_format_count(manual_counts[ValidationBasisLevel.ASSUMPTION], 'допущение', 'допущения', 'допущений')}."
        ),
        agreement_text=f"Протокол согласия: {evaluation.agreement.summary}",
        generated_at_text=evaluation.generated_at.isoformat(),
        note=evaluation.pending_note,
        sources=[_build_source_view(source) for source in evaluation.sources],
        manual_steps=[
            _build_trace_view(step, source_map) for step in evaluation.manual_steps
        ],
        reference_cases=[
            _build_trace_view(case, source_map) for case in evaluation.reference_cases
        ],
    )


def _build_source_view(source: ValidationBasisSource) -> ValidationBasisSourceView:
    return ValidationBasisSourceView(
        source_id=source.source_id,
        title=source.title,
        meta_text=f"{source.organization} · {source.published_label}",
        relevance=source.relevance,
        url=source.url,
    )


def _build_trace_view(
    trace: ValidationBasisTrace,
    source_map: dict[str, ValidationBasisSource],
) -> ValidationBasisTraceView:
    return ValidationBasisTraceView(
        title=trace.title,
        level_text=_level_text(trace.basis_level),
        level_class_name=_level_class(trace.basis_level),
        note=trace.note,
        sources=[
            ValidationBasisLinkView(
                source_id=source_id,
                label=source_map[source_id].title,
                url=source_map[source_id].url,
            )
            for source_id in trace.source_ids
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


def _format_count(value: int, singular: str, paucal: str, plural: str) -> str:
    remainder_hundred = value % 100
    remainder_ten = value % 10

    if 11 <= remainder_hundred <= 14:
        label = plural
    elif remainder_ten == 1:
        label = singular
    elif 2 <= remainder_ten <= 4:
        label = paucal
    else:
        label = plural
    return f"{value} {label}"


def _status_class(status: OperationStatus) -> str:
    return status_class_name(status)
