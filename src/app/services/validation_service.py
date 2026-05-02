from __future__ import annotations

import json
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.services.simulation_service import SimulationService
from app.simulation.equations import (
    AIR_DENSITY_KG_PER_M3,
    AIR_HEAT_CAPACITY_J_PER_KG_K,
    MIN_MASS_FLOW_KG_S,
)
from app.simulation.parameters import SimulationParameters
from app.simulation.state import OperationStatus, SimulationResult


class ValidationRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lower: float
    upper: float


class ValidationAgreementSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agreement_id: str
    title: str
    status: OperationStatus
    approved_on: date
    authority: str
    summary: str
    note: str
    agreed_reference_cases: int
    agreed_manual_steps: int


class ValidationMetricEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: str
    label: str
    unit: str
    expected_range: ValidationRange
    actual_value: float
    passed: bool


class ValidationAlarmEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_codes: list[str] = Field(default_factory=list)
    actual_codes: list[str] = Field(default_factory=list)
    passed: bool


class ValidationCaseEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    title: str
    expected_status: OperationStatus
    actual_status: OperationStatus
    status_passed: bool
    metrics: list[ValidationMetricEvaluation] = Field(default_factory=list)
    alarms: ValidationAlarmEvaluation
    passed: bool


class ValidationMatrixEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    total_cases: int
    passed_cases: int
    all_passed: bool
    pending_note: str
    agreement: ValidationAgreementSnapshot
    cases: list[ValidationCaseEvaluation] = Field(default_factory=list)


class ManualCheckStepEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str
    label: str
    formula: str
    unit: str
    manual_value: float
    model_value: float
    tolerance: float
    delta_abs: float
    passed: bool


class ManualCheckEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    subject_name: str
    scenario_id: str | None = None
    matched_reference_case_id: str | None = None
    matched_reference_case_title: str | None = None
    total_steps: int
    passed_steps: int
    all_passed: bool
    note: str
    agreement: ValidationAgreementSnapshot
    steps: list[ManualCheckStepEvaluation] = Field(default_factory=list)


class ValidationBasisLevel(str, Enum):
    EXTERNAL = "external"
    MIXED = "mixed"
    DERIVED = "derived"
    ASSUMPTION = "assumption"


class ValidationBasisSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    title: str
    organization: str
    published_label: str
    url: str
    relevance: str


class ValidationBasisTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    title: str
    basis_level: ValidationBasisLevel
    source_ids: list[str] = Field(default_factory=list)
    note: str


class ValidationBasisEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    total_sources: int
    traced_manual_steps: int
    traced_reference_cases: int
    pending_note: str
    agreement: ValidationAgreementSnapshot
    sources: list[ValidationBasisSource] = Field(default_factory=list)
    manual_steps: list[ValidationBasisTrace] = Field(default_factory=list)
    reference_cases: list[ValidationBasisTrace] = Field(default_factory=list)


class ValidationAgreementMetricEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: str
    label: str
    unit: str
    target_value: float
    tolerance: float
    lower_bound: float
    upper_bound: float
    note: str


class ValidationAgreementCaseEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    title: str
    basis_level: ValidationBasisLevel
    source_ids: list[str] = Field(default_factory=list)
    expected_status: OperationStatus
    expected_alarm_codes: list[str] = Field(default_factory=list)
    note: str
    metrics: list[ValidationAgreementMetricEvaluation] = Field(default_factory=list)


class ValidationAgreementStepEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str
    label: str
    unit: str
    basis_level: ValidationBasisLevel
    tolerance: float
    source_ids: list[str] = Field(default_factory=list)
    note: str


class ValidationAgreementEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    agreement_id: str
    title: str
    status: OperationStatus
    approved_on: date
    authority: str
    summary: str
    note: str
    total_sources: int
    total_cases: int
    total_steps: int
    sources: list[ValidationBasisSource] = Field(default_factory=list)
    control_points: list[ValidationAgreementCaseEvaluation] = Field(default_factory=list)
    manual_steps: list[ValidationAgreementStepEvaluation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class _ReferenceExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: OperationStatus
    supply_temp_c: tuple[float, float]
    room_temp_c: tuple[float, float]
    actual_airflow_m3_h: tuple[float, float]
    total_power_kw: tuple[float, float]
    alarm_codes: list[str] = Field(default_factory=list)


class _ReferencePoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    parameters: SimulationParameters
    expected: _ReferenceExpectation


class _ValidationBasisPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pending_note: str
    sources: list[ValidationBasisSource] = Field(default_factory=list)
    manual_steps: list[ValidationBasisTrace] = Field(default_factory=list)
    reference_cases: list[ValidationBasisTrace] = Field(default_factory=list)


class _ValidationAgreementMetricPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: str
    target_value: float
    tolerance: float
    note: str


class _ValidationAgreementCasePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    basis_level: ValidationBasisLevel
    source_ids: list[str] = Field(default_factory=list)
    expected_status: OperationStatus
    expected_alarm_codes: list[str] = Field(default_factory=list)
    note: str
    metrics: list[_ValidationAgreementMetricPayload] = Field(default_factory=list)


class _ValidationAgreementStepPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str
    basis_level: ValidationBasisLevel
    tolerance: float
    source_ids: list[str] = Field(default_factory=list)
    note: str


class _ValidationAgreementPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agreement_id: str
    title: str
    status: OperationStatus
    approved_on: date
    authority: str
    summary: str
    note: str
    control_points: list[_ValidationAgreementCasePayload] = Field(default_factory=list)
    manual_steps: list[_ValidationAgreementStepPayload] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ValidationService:
    _METRIC_DEFINITIONS = (
        ("supply_temp_c", "Температура притока", "°C"),
        ("room_temp_c", "Температура помещения", "°C"),
        ("actual_airflow_m3_h", "Фактический расход", "м³/ч"),
        ("total_power_kw", "Суммарная мощность", "кВт"),
    )
    _MANUAL_CHECK_DEFINITIONS = (
        ("actual_airflow_m3_h", "Фактический расход", "м³/ч"),
        ("recovered_air_temp_c", "Температура после рекуперации", "°C"),
        ("filter_pressure_drop_pa", "Перепад на фильтре", "Па"),
        ("heating_power_kw", "Мощность нагрева", "кВт"),
        ("supply_temp_c", "Температура притока", "°C"),
        ("fan_power_kw", "Мощность вентилятора", "кВт"),
        ("total_power_kw", "Суммарная мощность", "кВт"),
        ("heat_balance_kw", "Тепловой баланс помещения", "кВт"),
        ("room_temp_c", "Температура помещения на шаге", "°C"),
    )
    _MANUAL_CHECK_DEFAULT_TOLERANCE = 0.01

    def __init__(
        self,
        simulation_service: SimulationService,
        reference_points_path: Path,
        reference_basis_path: Path,
        validation_agreement_path: Path,
    ) -> None:
        self._simulation_service = simulation_service
        self._reference_points = self._load_reference_points(reference_points_path)
        self._reference_points_by_id = {point.id: point for point in self._reference_points}
        self._reference_basis = self._load_reference_basis(reference_basis_path)
        self._validation_agreement = self._load_validation_agreement(
            validation_agreement_path
        )

    def build_matrix(self) -> ValidationMatrixEvaluation:
        cases = [self._evaluate_case(point) for point in self._reference_points]
        passed_cases = sum(1 for case in cases if case.passed)
        agreement = self._build_agreement_snapshot()
        return ValidationMatrixEvaluation(
            generated_at=datetime.now(timezone.utc),
            total_cases=len(cases),
            passed_cases=passed_cases,
            all_passed=passed_cases == len(cases),
            pending_note=(
                "Матрица удерживает регрессионный диапазон для всех согласованных контрольных "
                "режимов текущей учебно-обобщённой ПВУ. Источники, допуски и ручной вывод "
                "формул вынесены в Протокол согласия и Основания валидации."
            ),
            agreement=agreement,
            cases=cases,
        )

    def build_manual_check(
        self,
        parameters: SimulationParameters,
        result: SimulationResult | None = None,
    ) -> ManualCheckEvaluation:
        simulation_result = result or self._simulation_service.preview(parameters)
        manual_values = self._calculate_manual_values(parameters)
        agreement_steps = {
            step.step_id: step for step in self._validation_agreement.manual_steps
        }
        matched_point = self._match_reference_point(parameters)
        state = simulation_result.state

        steps = [
            self._build_manual_check_step(
                step_id="actual_airflow_m3_h",
                label="Фактический расход",
                formula=(
                    f"{parameters.airflow_m3_h:.1f} * {parameters.fan_speed_ratio:.2f} * "
                    f"max(0.45, 1 - 0.35 * {parameters.filter_contamination:.2f})"
                ),
                unit="м³/ч",
                manual_value=manual_values["actual_airflow_m3_h"],
                model_value=state.actual_airflow_m3_h,
                tolerance=self._manual_tolerance(
                    agreement_steps.get("actual_airflow_m3_h")
                ),
            ),
            self._build_manual_check_step(
                step_id="recovered_air_temp_c",
                label="Температура после рекуперации",
                formula=(
                    f"{parameters.outdoor_temp_c:.1f} + ({parameters.room_temp_c:.1f} - "
                    f"{parameters.outdoor_temp_c:.1f}) * {parameters.heat_recovery_efficiency:.2f}"
                ),
                unit="°C",
                manual_value=manual_values["recovered_air_temp_c"],
                model_value=state.recovered_air_temp_c,
                tolerance=self._manual_tolerance(
                    agreement_steps.get("recovered_air_temp_c")
                ),
            ),
            self._build_manual_check_step(
                step_id="filter_pressure_drop_pa",
                label="Перепад на фильтре",
                formula=f"120 + 300 * ({parameters.filter_contamination:.2f} ^ 1.35)",
                unit="Па",
                manual_value=manual_values["filter_pressure_drop_pa"],
                model_value=state.filter_pressure_drop_pa,
                tolerance=self._manual_tolerance(
                    agreement_steps.get("filter_pressure_drop_pa")
                ),
            ),
            self._build_manual_check_step(
                step_id="heating_power_kw",
                label="Мощность нагрева",
                formula=(
                    "min(m_dot * 1005 * (T_set - T_rec) / 1000, "
                    f"{parameters.heater_power_kw:.1f} * max(0.78, 1 - 0.12 * {parameters.filter_contamination:.2f}))"
                ),
                unit="кВт",
                manual_value=manual_values["heating_power_kw"],
                model_value=state.heating_power_kw,
                tolerance=self._manual_tolerance(agreement_steps.get("heating_power_kw")),
            ),
            self._build_manual_check_step(
                step_id="supply_temp_c",
                label="Температура притока",
                formula="T_rec + Q_heat * 1000 / (m_dot * 1005)",
                unit="°C",
                manual_value=manual_values["supply_temp_c"],
                model_value=state.supply_temp_c,
                tolerance=self._manual_tolerance(agreement_steps.get("supply_temp_c")),
            ),
            self._build_manual_check_step(
                step_id="fan_power_kw",
                label="Мощность вентилятора",
                formula=(
                    "0.25 + 1.7 * (L_fact / 3200)^3 * "
                    f"(1 + 0.28 * {parameters.filter_contamination:.2f})"
                ),
                unit="кВт",
                manual_value=manual_values["fan_power_kw"],
                model_value=state.fan_power_kw,
                tolerance=self._manual_tolerance(agreement_steps.get("fan_power_kw")),
            ),
            self._build_manual_check_step(
                step_id="total_power_kw",
                label="Суммарная мощность",
                formula="Q_heat + P_fan",
                unit="кВт",
                manual_value=manual_values["total_power_kw"],
                model_value=state.total_power_kw,
                tolerance=self._manual_tolerance(agreement_steps.get("total_power_kw")),
            ),
            self._build_manual_check_step(
                step_id="heat_balance_kw",
                label="Тепловой баланс помещения",
                formula=(
                    "m_dot * 1005 * (T_supply - T_room) / 1000 + "
                    f"{parameters.room_heat_gain_kw:.1f} - {parameters.room_loss_coeff_kw_per_k:.2f} * "
                    f"({parameters.room_temp_c:.1f} - {parameters.outdoor_temp_c:.1f})"
                ),
                unit="кВт",
                manual_value=manual_values["heat_balance_kw"],
                model_value=state.heat_balance_kw,
                tolerance=self._manual_tolerance(agreement_steps.get("heat_balance_kw")),
            ),
            self._build_manual_check_step(
                step_id="room_temp_c",
                label="Температура помещения на шаге",
                formula=(
                    f"{parameters.room_temp_c:.1f} + Q_balance * ({parameters.step_minutes} / 60) / "
                    f"{parameters.room_thermal_capacity_kwh_per_k:.1f}"
                ),
                unit="°C",
                manual_value=manual_values["room_temp_c"],
                model_value=state.room_temp_c,
                tolerance=self._manual_tolerance(agreement_steps.get("room_temp_c")),
            ),
        ]
        passed_steps = sum(1 for step in steps if step.passed)
        return ManualCheckEvaluation(
            generated_at=datetime.now(timezone.utc),
            subject_name=simulation_result.scenario_title or "Пользовательский режим",
            scenario_id=simulation_result.scenario_id,
            matched_reference_case_id=matched_point.id if matched_point else None,
            matched_reference_case_title=matched_point.title if matched_point else None,
            total_steps=len(steps),
            passed_steps=passed_steps,
            all_passed=passed_steps == len(steps),
            note=self._manual_check_note(matched_point),
            agreement=self._build_agreement_snapshot(),
            steps=steps,
        )

    def build_basis(self) -> ValidationBasisEvaluation:
        return ValidationBasisEvaluation(
            generated_at=datetime.now(timezone.utc),
            total_sources=len(self._reference_basis.sources),
            traced_manual_steps=len(self._reference_basis.manual_steps),
            traced_reference_cases=len(self._reference_basis.reference_cases),
            pending_note=self._reference_basis.pending_note,
            agreement=self._build_agreement_snapshot(),
            sources=self._reference_basis.sources,
            manual_steps=self._reference_basis.manual_steps,
            reference_cases=self._reference_basis.reference_cases,
        )

    def build_agreement(self) -> ValidationAgreementEvaluation:
        source_map = {
            source.source_id: source for source in self._reference_basis.sources
        }
        control_points = [
            self._build_agreement_case(case, source_map)
            for case in self._validation_agreement.control_points
        ]
        manual_steps = [
            self._build_agreement_step(step, source_map)
            for step in self._validation_agreement.manual_steps
        ]
        return ValidationAgreementEvaluation(
            generated_at=datetime.now(timezone.utc),
            agreement_id=self._validation_agreement.agreement_id,
            title=self._validation_agreement.title,
            status=self._validation_agreement.status,
            approved_on=self._validation_agreement.approved_on,
            authority=self._validation_agreement.authority,
            summary=self._validation_agreement.summary,
            note=self._validation_agreement.note,
            total_sources=len(self._reference_basis.sources),
            total_cases=len(control_points),
            total_steps=len(manual_steps),
            sources=self._reference_basis.sources,
            control_points=control_points,
            manual_steps=manual_steps,
            limitations=self._validation_agreement.limitations,
        )

    @staticmethod
    def _load_reference_points(reference_points_path: Path) -> list[_ReferencePoint]:
        payload = json.loads(reference_points_path.read_text(encoding="utf-8"))
        return [_ReferencePoint.model_validate(item) for item in payload]

    @staticmethod
    def _load_reference_basis(reference_basis_path: Path) -> _ValidationBasisPayload:
        payload = json.loads(reference_basis_path.read_text(encoding="utf-8"))
        return _ValidationBasisPayload.model_validate(payload)

    @staticmethod
    def _load_validation_agreement(
        validation_agreement_path: Path,
    ) -> _ValidationAgreementPayload:
        payload = json.loads(validation_agreement_path.read_text(encoding="utf-8"))
        return _ValidationAgreementPayload.model_validate(payload)

    def _build_agreement_snapshot(self) -> ValidationAgreementSnapshot:
        payload = self._validation_agreement
        return ValidationAgreementSnapshot(
            agreement_id=payload.agreement_id,
            title=payload.title,
            status=payload.status,
            approved_on=payload.approved_on,
            authority=payload.authority,
            summary=payload.summary,
            note=payload.note,
            agreed_reference_cases=len(payload.control_points),
            agreed_manual_steps=len(payload.manual_steps),
        )

    def _build_agreement_case(
        self,
        case: _ValidationAgreementCasePayload,
        source_map: dict[str, ValidationBasisSource],
    ) -> ValidationAgreementCaseEvaluation:
        reference_point = self._reference_points_by_id.get(case.case_id)
        if reference_point is None:
            raise ValueError(
                f"Validation agreement references unknown control point: {case.case_id}"
            )

        metrics = [
            self._build_agreement_metric(metric)
            for metric in case.metrics
        ]
        self._validate_agreement_sources(case.source_ids, source_map, case.case_id)
        return ValidationAgreementCaseEvaluation(
            case_id=case.case_id,
            title=reference_point.title,
            basis_level=case.basis_level,
            source_ids=case.source_ids,
            expected_status=case.expected_status,
            expected_alarm_codes=case.expected_alarm_codes,
            note=case.note,
            metrics=metrics,
        )

    def _build_agreement_metric(
        self,
        metric: _ValidationAgreementMetricPayload,
    ) -> ValidationAgreementMetricEvaluation:
        label, unit = self._metric_metadata(metric.metric_id)
        lower_bound = metric.target_value - metric.tolerance
        upper_bound = metric.target_value + metric.tolerance
        return ValidationAgreementMetricEvaluation(
            metric_id=metric.metric_id,
            label=label,
            unit=unit,
            target_value=self._round_value(metric.target_value),
            tolerance=self._round_value(metric.tolerance),
            lower_bound=self._round_value(lower_bound),
            upper_bound=self._round_value(upper_bound),
            note=metric.note,
        )

    def _build_agreement_step(
        self,
        step: _ValidationAgreementStepPayload,
        source_map: dict[str, ValidationBasisSource],
    ) -> ValidationAgreementStepEvaluation:
        label, unit = self._manual_step_metadata(step.step_id)
        self._validate_agreement_sources(step.source_ids, source_map, step.step_id)
        return ValidationAgreementStepEvaluation(
            step_id=step.step_id,
            label=label,
            unit=unit,
            basis_level=step.basis_level,
            tolerance=self._round_value(step.tolerance),
            source_ids=step.source_ids,
            note=step.note,
        )

    @staticmethod
    def _validate_agreement_sources(
        source_ids: list[str],
        source_map: dict[str, ValidationBasisSource],
        item_id: str,
    ) -> None:
        missing_sources = [source_id for source_id in source_ids if source_id not in source_map]
        if missing_sources:
            raise ValueError(
                f"Validation agreement item {item_id} references unknown sources: "
                + ", ".join(missing_sources)
            )

    def _evaluate_case(self, point: _ReferencePoint) -> ValidationCaseEvaluation:
        result = self._simulation_service.preview(point.parameters)
        metrics = [
            self._evaluate_metric(
                metric_id=metric_id,
                label=label,
                unit=unit,
                expected_range=getattr(point.expected, metric_id),
                actual_value=getattr(result.state, metric_id),
            )
            for metric_id, label, unit in self._METRIC_DEFINITIONS
        ]
        actual_alarm_codes = [alarm.code for alarm in result.alarms]
        alarms = ValidationAlarmEvaluation(
            expected_codes=point.expected.alarm_codes,
            actual_codes=actual_alarm_codes,
            passed=set(point.expected.alarm_codes).issubset(actual_alarm_codes),
        )
        status_passed = result.state.status == point.expected.status
        return ValidationCaseEvaluation(
            case_id=point.id,
            title=point.title,
            expected_status=point.expected.status,
            actual_status=result.state.status,
            status_passed=status_passed,
            metrics=metrics,
            alarms=alarms,
            passed=status_passed and alarms.passed and all(metric.passed for metric in metrics),
        )

    @staticmethod
    def _evaluate_metric(
        *,
        metric_id: str,
        label: str,
        unit: str,
        expected_range: tuple[float, float],
        actual_value: float,
    ) -> ValidationMetricEvaluation:
        lower, upper = expected_range
        return ValidationMetricEvaluation(
            metric_id=metric_id,
            label=label,
            unit=unit,
            expected_range=ValidationRange(lower=lower, upper=upper),
            actual_value=actual_value,
            passed=lower <= actual_value <= upper,
        )

    def _build_manual_check_step(
        self,
        *,
        step_id: str,
        label: str,
        formula: str,
        unit: str,
        manual_value: float,
        model_value: float,
        tolerance: float,
    ) -> ManualCheckStepEvaluation:
        delta_abs = abs(manual_value - model_value)
        return ManualCheckStepEvaluation(
            step_id=step_id,
            label=label,
            formula=formula,
            unit=unit,
            manual_value=manual_value,
            model_value=model_value,
            tolerance=self._round_value(tolerance),
            delta_abs=self._round_value(delta_abs),
            passed=delta_abs <= tolerance,
        )

    @classmethod
    def _calculate_manual_values(cls, parameters: SimulationParameters) -> dict[str, float]:
        fouling_factor = max(0.45, 1.0 - 0.35 * parameters.filter_contamination)
        actual_airflow_raw = (
            parameters.airflow_m3_h * parameters.fan_speed_ratio * fouling_factor
        )
        filter_pressure_drop_raw = 120.0 + 300.0 * (
            parameters.filter_contamination**1.35
        )
        recovered_air_temp_raw = parameters.outdoor_temp_c + (
            parameters.room_temp_c - parameters.outdoor_temp_c
        ) * parameters.heat_recovery_efficiency
        mass_flow_kg_s = actual_airflow_raw * AIR_DENSITY_KG_PER_M3 / 3600.0
        required_heating_raw = max(
            mass_flow_kg_s
            * AIR_HEAT_CAPACITY_J_PER_KG_K
            * (parameters.supply_temp_setpoint_c - recovered_air_temp_raw)
            / 1000.0,
            0.0,
        )
        heater_available_raw = parameters.heater_power_kw * max(
            0.78, 1.0 - 0.12 * parameters.filter_contamination
        )
        heating_power_raw = min(required_heating_raw, heater_available_raw)

        if mass_flow_kg_s > MIN_MASS_FLOW_KG_S:
            supply_temp_raw = recovered_air_temp_raw + (
                heating_power_raw * 1000.0
                / (mass_flow_kg_s * AIR_HEAT_CAPACITY_J_PER_KG_K)
            )
        else:
            supply_temp_raw = recovered_air_temp_raw

        flow_ratio = actual_airflow_raw / 3200.0
        fan_power_raw = 0.25 + 1.7 * (flow_ratio**3) * (
            1.0 + 0.28 * parameters.filter_contamination
        )
        total_power_raw = heating_power_raw + fan_power_raw
        heat_balance_raw = (
            mass_flow_kg_s
            * AIR_HEAT_CAPACITY_J_PER_KG_K
            * (supply_temp_raw - parameters.room_temp_c)
            / 1000.0
            + parameters.room_heat_gain_kw
            - parameters.room_loss_coeff_kw_per_k
            * (parameters.room_temp_c - parameters.outdoor_temp_c)
        )
        if parameters.step_minutes > 0:
            room_temp_raw = parameters.room_temp_c + (
                heat_balance_raw
                * (parameters.step_minutes / 60.0)
                / parameters.room_thermal_capacity_kwh_per_k
            )
        else:
            room_temp_raw = parameters.room_temp_c

        return {
            "actual_airflow_m3_h": cls._round_value(actual_airflow_raw),
            "recovered_air_temp_c": cls._round_value(recovered_air_temp_raw),
            "filter_pressure_drop_pa": cls._round_value(filter_pressure_drop_raw),
            "heating_power_kw": cls._round_value(heating_power_raw),
            "supply_temp_c": cls._round_value(supply_temp_raw),
            "fan_power_kw": cls._round_value(fan_power_raw),
            "total_power_kw": cls._round_value(total_power_raw),
            "heat_balance_kw": cls._round_value(heat_balance_raw),
            "room_temp_c": cls._round_value(room_temp_raw),
        }

    def _match_reference_point(
        self,
        parameters: SimulationParameters,
    ) -> _ReferencePoint | None:
        payload = parameters.model_dump(mode="python")
        for point in self._reference_points:
            if point.parameters.model_dump(mode="python") == payload:
                return point
        return None

    def _manual_check_note(self, matched_point: _ReferencePoint | None) -> str:
        if matched_point is None:
            return (
                "Ручная инженерная сверка использует согласованные формулы и допуски из "
                "Протокола согласия, но текущий пользовательский набор параметров не является одной "
                "из зафиксированных контрольных точек. Для полной трассировки можно "
                "сопоставить режим с Основаниями валидации и ближайшей согласованной контрольной точкой."
            )

        return (
            "Ручная инженерная сверка использует те же согласованные формулы и допуски, что и "
            f"контрольная точка `{matched_point.id}`. Это позволяет сверять живой "
            "режим дашборда с внешне зафиксированным инженерным диапазоном без выхода "
            "из приложения."
        )

    @classmethod
    def _manual_tolerance(
        cls,
        step: _ValidationAgreementStepPayload | None,
    ) -> float:
        if step is None:
            return cls._MANUAL_CHECK_DEFAULT_TOLERANCE
        return step.tolerance

    def _metric_metadata(self, metric_id: str) -> tuple[str, str]:
        for current_metric_id, label, unit in self._METRIC_DEFINITIONS:
            if current_metric_id == metric_id:
                return label, unit
        raise ValueError(f"Unknown validation metric in agreement: {metric_id}")

    def _manual_step_metadata(self, step_id: str) -> tuple[str, str]:
        for current_step_id, label, unit in self._MANUAL_CHECK_DEFINITIONS:
            if current_step_id == step_id:
                return label, unit
        raise ValueError(f"Unknown manual-check step in agreement: {step_id}")

    @staticmethod
    def _round_value(value: float) -> float:
        return round(float(value), 2)
