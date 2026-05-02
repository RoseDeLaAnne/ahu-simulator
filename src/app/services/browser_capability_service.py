from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field

from app.simulation.state import OperationStatus


class BrowserDiagnosticsSnapshot(BaseModel):
    model_config = ConfigDict(extra="ignore")

    browser_label: str = "Неизвестный браузер"
    platform: str = "Неизвестная платформа"
    online: bool | None = None
    secure_context: bool = False
    webgl_supported: bool = False
    webgl2_supported: bool = False
    hardware_concurrency: int | None = None
    device_memory_gb: float | None = None
    renderer: str | None = None
    vendor: str | None = None
    debug_renderer_info: bool = False
    max_texture_size: int | None = None
    max_viewport_width: int | None = None
    max_viewport_height: int | None = None
    viewport_width: int | None = None
    viewport_height: int | None = None
    screen_width: int | None = None
    screen_height: int | None = None
    device_pixel_ratio: float | None = None
    diagnostics_timestamp: str | None = None

    def readiness_status(self) -> OperationStatus:
        if not self.webgl_supported:
            return OperationStatus.ALARM
        if not self.webgl2_supported or not self.secure_context:
            return OperationStatus.WARNING
        if self.hardware_concurrency is not None and self.hardware_concurrency < 4:
            return OperationStatus.WARNING
        if self.device_memory_gb is not None and self.device_memory_gb < 4:
            return OperationStatus.WARNING
        return OperationStatus.NORMAL


class BrowserCapabilityRequirementConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    title: str
    field: str
    kind: Literal["boolean", "minimum_int", "minimum_float"]
    expected_bool: bool | None = None
    minimum_int: int | None = Field(default=None, ge=0)
    minimum_float: float | None = Field(default=None, ge=0)
    expected_text: str
    rationale: str


class BrowserRecommendedViewport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_width: int = Field(ge=1)
    min_height: int = Field(ge=1)
    note: str


class BrowserCapabilityProfileConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_id: str
    verified_at: datetime
    target_use: str
    verification_method: str
    summary: str
    note: str
    evidence_paths: list[str] = Field(default_factory=list)
    verified_environment: BrowserDiagnosticsSnapshot
    recommended_viewport: BrowserRecommendedViewport
    requirements: list[BrowserCapabilityRequirementConfig] = Field(default_factory=list)


class BrowserCapabilityRequirementEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    title: str
    expected_text: str
    actual_text: str
    passed: bool
    rationale: str


class BrowserCapabilityProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    profile_id: str
    verified_at: datetime
    overall_status: OperationStatus
    passed_requirements: int
    total_requirements: int
    target_use: str
    verification_method: str
    summary: str
    note: str
    evidence_paths: list[str] = Field(default_factory=list)
    verified_environment: BrowserDiagnosticsSnapshot
    recommended_viewport: BrowserRecommendedViewport
    requirements: list[BrowserCapabilityRequirementEvaluation] = Field(default_factory=list)


class BrowserCapabilityComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    profile_id: str
    overall_status: OperationStatus
    passed_requirements: int
    total_requirements: int
    summary: str
    note: str
    evaluations: list[BrowserCapabilityRequirementEvaluation] = Field(default_factory=list)


class BrowserCapabilityService:
    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root
        self._profile_path = (
            project_root / "data" / "visualization" / "browser_capability_profile.json"
        )

    def build_profile(self) -> BrowserCapabilityProfile:
        config = self._load_profile_config()
        comparison = self._evaluate_snapshot(config.verified_environment, config)
        failing_titles = [
            evaluation.title
            for evaluation in comparison.evaluations
            if not evaluation.passed
        ]
        if failing_titles:
            raise ValueError(
                "Verified browser profile conflicts with its own requirements: "
                + ", ".join(failing_titles)
            )

        return BrowserCapabilityProfile(
            generated_at=datetime.now(timezone.utc),
            profile_id=config.profile_id,
            verified_at=config.verified_at,
            overall_status=comparison.overall_status,
            passed_requirements=comparison.passed_requirements,
            total_requirements=comparison.total_requirements,
            target_use=config.target_use,
            verification_method=config.verification_method,
            summary=config.summary,
            note=config.note,
            evidence_paths=config.evidence_paths,
            verified_environment=config.verified_environment,
            recommended_viewport=config.recommended_viewport,
            requirements=comparison.evaluations,
        )

    def build_comparison(
        self,
        payload: Mapping[str, Any] | None,
    ) -> BrowserCapabilityComparison | None:
        if not payload:
            return None

        config = self._load_profile_config()
        snapshot = BrowserDiagnosticsSnapshot.model_validate(payload)
        return self._evaluate_snapshot(snapshot, config)

    def _load_profile_config(self) -> BrowserCapabilityProfileConfig:
        config = BrowserCapabilityProfileConfig.model_validate_json(
            self._profile_path.read_text(encoding="utf-8")
        )
        self._validate_requirement_fields(config.requirements)
        return config

    @staticmethod
    def _validate_requirement_fields(
        requirements: list[BrowserCapabilityRequirementConfig],
    ) -> None:
        available_fields = set(BrowserDiagnosticsSnapshot.model_fields)
        invalid_fields = sorted(
            {requirement.field for requirement in requirements if requirement.field not in available_fields}
        )
        if invalid_fields:
            raise ValueError(
                "Unknown browser capability fields in profile: "
                + ", ".join(invalid_fields)
            )

    def _evaluate_snapshot(
        self,
        snapshot: BrowserDiagnosticsSnapshot,
        config: BrowserCapabilityProfileConfig,
    ) -> BrowserCapabilityComparison:
        evaluations = [
            self._evaluate_requirement(snapshot, requirement)
            for requirement in config.requirements
        ]
        passed_requirements = sum(
            1 for evaluation in evaluations if evaluation.passed
        )
        total_requirements = len(evaluations)

        if passed_requirements == total_requirements:
            overall_status = OperationStatus.NORMAL
        elif not snapshot.webgl_supported:
            overall_status = OperationStatus.ALARM
        else:
            overall_status = OperationStatus.WARNING

        return BrowserCapabilityComparison(
            generated_at=datetime.now(timezone.utc),
            profile_id=config.profile_id,
            overall_status=overall_status,
            passed_requirements=passed_requirements,
            total_requirements=total_requirements,
            summary=self._build_summary(overall_status, passed_requirements, total_requirements),
            note=self._build_note(overall_status, evaluations, config),
            evaluations=evaluations,
        )

    @staticmethod
    def _evaluate_requirement(
        snapshot: BrowserDiagnosticsSnapshot,
        requirement: BrowserCapabilityRequirementConfig,
    ) -> BrowserCapabilityRequirementEvaluation:
        actual_value = getattr(snapshot, requirement.field)

        if requirement.kind == "boolean":
            passed = actual_value is requirement.expected_bool
        elif requirement.kind == "minimum_int":
            passed = isinstance(actual_value, int) and actual_value >= (
                requirement.minimum_int or 0
            )
        else:
            passed = isinstance(actual_value, (int, float)) and float(actual_value) >= (
                requirement.minimum_float or 0.0
            )

        return BrowserCapabilityRequirementEvaluation(
            requirement_id=requirement.requirement_id,
            title=requirement.title,
            expected_text=requirement.expected_text,
            actual_text=BrowserCapabilityService._format_actual_value(actual_value),
            passed=passed,
            rationale=requirement.rationale,
        )

    @staticmethod
    def _build_summary(
        overall_status: OperationStatus,
        passed_requirements: int,
        total_requirements: int,
    ) -> str:
        if overall_status == OperationStatus.NORMAL:
            return (
                "Текущий браузер укладывается в подтверждённый диапазон WebGL: "
                f"{passed_requirements} из {total_requirements} требований проходят."
            )
        if overall_status == OperationStatus.ALARM:
            return (
                "Текущий браузер вне подтверждённого диапазона WebGL: "
                f"{passed_requirements} из {total_requirements} требований проходят, "
                "а WebGL недоступен."
            )
        return (
            "Текущий браузер частично совпадает с подтверждённым диапазоном WebGL: "
            f"{passed_requirements} из {total_requirements} требований проходят."
        )

    @staticmethod
    def _build_note(
        overall_status: OperationStatus,
        evaluations: list[BrowserCapabilityRequirementEvaluation],
        config: BrowserCapabilityProfileConfig,
    ) -> str:
        if overall_status == OperationStatus.NORMAL:
            return config.note

        mismatches = [
            f"{evaluation.title}: {evaluation.actual_text} (ожидается {evaluation.expected_text})"
            for evaluation in evaluations
            if not evaluation.passed
        ]
        mismatch_text = "; ".join(mismatches)
        return (
            "Отличия от подтверждённого профиля демо-браузера: "
            + mismatch_text
            + ". 2D SVG остаётся безопасным резервным режимом, а дополнительную 3D-проверку стоит "
            f"проводить только в окне не уже {config.recommended_viewport.min_width}x"
            f"{config.recommended_viewport.min_height}."
        )

    @staticmethod
    def _format_actual_value(value: Any) -> str:
        if value is None:
            return "н/д"
        if isinstance(value, bool):
            return "да" if value else "нет"
        if isinstance(value, float):
            return f"{value:.1f}"
        return str(value)
