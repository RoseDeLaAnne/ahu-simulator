from __future__ import annotations

from dataclasses import dataclass

from app.services.project_baseline_service import ProjectBaselineSnapshot
from app.simulation.state import OperationStatus
from app.ui.viewmodels.status_presenter import status_class_name


@dataclass(frozen=True)
class ProjectBaselineDecisionView:
    title: str
    summary: str
    rationale: str
    evidence_paths_text: str


@dataclass(frozen=True)
class ProjectBaselineParameterView:
    title: str
    parameter_id: str
    unit: str
    why_text: str


@dataclass(frozen=True)
class ProjectBaselineOutputView:
    title: str
    output_id: str
    unit: str
    location_text: str
    why_required: str


@dataclass(frozen=True)
class ProjectBaselineScenarioView:
    title: str
    scenario_id: str
    category_text: str
    purpose: str
    key_demo_point: str


@dataclass(frozen=True)
class ProjectBaselineValidationLayerView:
    title: str
    artifact: str
    purpose: str
    evidence_paths_text: str


@dataclass(frozen=True)
class ProjectBaselineView:
    summary_text: str
    summary_class_name: str
    version_text: str
    subject_title: str
    subject_summary: str
    note: str
    generated_at_text: str
    locked_decisions: list[ProjectBaselineDecisionView]
    operator_inputs: list[ProjectBaselineParameterView]
    fixed_model_inputs: list[ProjectBaselineParameterView]
    outputs: list[ProjectBaselineOutputView]
    defense_scenarios: list[ProjectBaselineScenarioView]
    validation_layers: list[ProjectBaselineValidationLayerView]
    follow_up_items: list[str]


def build_project_baseline_view(snapshot: ProjectBaselineSnapshot) -> ProjectBaselineView:
    return ProjectBaselineView(
        summary_text=snapshot.summary,
        summary_class_name=_status_class_name(snapshot.overall_status),
        version_text=f"Базовая версия {snapshot.baseline_version}",
        subject_title=snapshot.subject.title,
        subject_summary=snapshot.subject.scope_summary,
        note=snapshot.note,
        generated_at_text=snapshot.generated_at.isoformat(),
        locked_decisions=[
            ProjectBaselineDecisionView(
                title=decision.title,
                summary=decision.summary,
                rationale=decision.rationale,
                evidence_paths_text="; ".join(decision.evidence_paths),
            )
            for decision in snapshot.locked_decisions
        ],
        operator_inputs=[
            ProjectBaselineParameterView(
                title=parameter.title,
                parameter_id=parameter.parameter_id,
                unit=parameter.unit,
                why_text=parameter.why_required or "",
            )
            for parameter in snapshot.operator_inputs
        ],
        fixed_model_inputs=[
            ProjectBaselineParameterView(
                title=parameter.title,
                parameter_id=parameter.parameter_id,
                unit=parameter.unit,
                why_text=parameter.why_fixed or "",
            )
            for parameter in snapshot.fixed_model_inputs
        ],
        outputs=[
            ProjectBaselineOutputView(
                title=output.title,
                output_id=output.output_id,
                unit=output.unit,
                location_text=output.location,
                why_required=output.why_required,
            )
            for output in snapshot.outputs
        ],
        defense_scenarios=[
            ProjectBaselineScenarioView(
                title=scenario.title,
                scenario_id=scenario.scenario_id,
                category_text=scenario.category,
                purpose=scenario.purpose,
                key_demo_point=scenario.key_demo_point,
            )
            for scenario in snapshot.defense_scenarios
        ],
        validation_layers=[
            ProjectBaselineValidationLayerView(
                title=layer.title,
                artifact=layer.artifact,
                purpose=layer.purpose,
                evidence_paths_text="; ".join(layer.evidence_paths),
            )
            for layer in snapshot.validation_layers
        ],
        follow_up_items=snapshot.follow_up_items,
    )


def _status_class_name(status: OperationStatus) -> str:
    return status_class_name(status)
