from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from app.simulation.parameters import SimulationParameters
from app.simulation.scenarios import load_scenarios
from app.simulation.state import OperationStatus, SimulationState


class ProjectBaselineDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_id: str
    title: str
    summary: str
    rationale: str
    evidence_paths: list[str] = Field(default_factory=list)


class ProjectBaselineParameter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parameter_id: str
    title: str
    unit: str
    why_required: str | None = None
    why_fixed: str | None = None


class ProjectBaselineOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_id: str
    title: str
    unit: str
    location: str
    why_required: str


class ProjectBaselineScenarioConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    category: str
    purpose: str
    key_demo_point: str


class ProjectBaselineScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    title: str
    description: str
    category: str
    purpose: str
    key_demo_point: str


class ProjectBaselineValidationLayer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    layer_id: str
    title: str
    artifact: str
    purpose: str
    evidence_paths: list[str] = Field(default_factory=list)


class ProjectBaselineSubject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str
    title: str
    scope_summary: str
    note: str


class ProjectBaselineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baseline_version: int
    subject: ProjectBaselineSubject
    locked_decisions: list[ProjectBaselineDecision] = Field(default_factory=list)
    operator_inputs: list[ProjectBaselineParameter] = Field(default_factory=list)
    fixed_model_inputs: list[ProjectBaselineParameter] = Field(default_factory=list)
    outputs: list[ProjectBaselineOutput] = Field(default_factory=list)
    defense_scenarios: list[ProjectBaselineScenarioConfig] = Field(default_factory=list)
    validation_layers: list[ProjectBaselineValidationLayer] = Field(default_factory=list)
    follow_up_items: list[str] = Field(default_factory=list)


class ProjectBaselineSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    baseline_version: int
    overall_status: OperationStatus
    summary: str
    note: str
    subject: ProjectBaselineSubject
    locked_decisions: list[ProjectBaselineDecision] = Field(default_factory=list)
    operator_inputs: list[ProjectBaselineParameter] = Field(default_factory=list)
    fixed_model_inputs: list[ProjectBaselineParameter] = Field(default_factory=list)
    outputs: list[ProjectBaselineOutput] = Field(default_factory=list)
    defense_scenarios: list[ProjectBaselineScenario] = Field(default_factory=list)
    validation_layers: list[ProjectBaselineValidationLayer] = Field(default_factory=list)
    follow_up_items: list[str] = Field(default_factory=list)


class ProjectBaselineService:
    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root
        self._baseline_path = project_root / "config" / "p0_baseline.yaml"
        self._scenario_path = project_root / "data" / "scenarios" / "presets.json"

    def build_snapshot(self) -> ProjectBaselineSnapshot:
        payload = yaml.safe_load(self._baseline_path.read_text(encoding="utf-8")) or {}
        config = ProjectBaselineConfig.model_validate(payload)
        self._validate_parameter_ids(config.operator_inputs + config.fixed_model_inputs)
        self._validate_output_ids(config.outputs)
        scenarios = self._build_scenarios(config.defense_scenarios)

        return ProjectBaselineSnapshot(
            generated_at=datetime.now(timezone.utc),
            baseline_version=config.baseline_version,
            overall_status=OperationStatus.NORMAL,
            summary=(
                f"Базовая конфигурация P0 зафиксирована: {len(config.operator_inputs)} обязательных входов, "
                f"{len(config.outputs)} обязательных выходов, {len(scenarios)} сценариев защиты "
                f"и {len(config.validation_layers)} слоя валидации."
            ),
            note=config.subject.note,
            subject=config.subject,
            locked_decisions=config.locked_decisions,
            operator_inputs=config.operator_inputs,
            fixed_model_inputs=config.fixed_model_inputs,
            outputs=config.outputs,
            defense_scenarios=scenarios,
            validation_layers=config.validation_layers,
            follow_up_items=config.follow_up_items,
        )

    def _build_scenarios(
        self,
        configured_scenarios: list[ProjectBaselineScenarioConfig],
    ) -> list[ProjectBaselineScenario]:
        scenario_map = {
            scenario.id: scenario for scenario in load_scenarios(self._scenario_path)
        }
        scenarios: list[ProjectBaselineScenario] = []
        missing_ids: list[str] = []

        for configured in configured_scenarios:
            scenario = scenario_map.get(configured.scenario_id)
            if scenario is None:
                missing_ids.append(configured.scenario_id)
                continue
            scenarios.append(
                ProjectBaselineScenario(
                    scenario_id=configured.scenario_id,
                    title=scenario.title,
                    description=scenario.description,
                    category=configured.category,
                    purpose=configured.purpose,
                    key_demo_point=configured.key_demo_point,
                )
            )

        if missing_ids:
            raise ValueError(
                "В baseline указаны отсутствующие сценарии: " + ", ".join(missing_ids)
            )
        return scenarios

    @staticmethod
    def _validate_parameter_ids(parameters: list[ProjectBaselineParameter]) -> None:
        available_ids = set(SimulationParameters.model_fields)
        invalid_ids = sorted(
            {
                parameter.parameter_id
                for parameter in parameters
                if parameter.parameter_id not in available_ids
            }
        )
        if invalid_ids:
            raise ValueError(
                "В baseline указаны неизвестные параметры модели: "
                + ", ".join(invalid_ids)
            )

    @staticmethod
    def _validate_output_ids(outputs: list[ProjectBaselineOutput]) -> None:
        available_state_ids = set(SimulationState.model_fields)
        available_result_ids = {
            "alarms",
            "trend",
            "parameters",
            "scenario_id",
            "scenario_title",
            "timestamp",
        }
        invalid_ids: list[str] = []

        for output in outputs:
            if output.location == "state" and output.output_id in available_state_ids:
                continue
            if output.location == "result" and output.output_id in available_result_ids:
                continue
            invalid_ids.append(f"{output.location}:{output.output_id}")

        if invalid_ids:
            raise ValueError(
                "В baseline указаны неизвестные выходы модели: " + ", ".join(invalid_ids)
            )
