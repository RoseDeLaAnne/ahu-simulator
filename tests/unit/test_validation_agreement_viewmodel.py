from datetime import date, datetime, timezone

from app.services.validation_service import (
    ValidationAgreementCaseEvaluation,
    ValidationAgreementEvaluation,
    ValidationAgreementMetricEvaluation,
    ValidationAgreementStepEvaluation,
    ValidationBasisLevel,
    ValidationBasisSource,
)
from app.simulation.state import OperationStatus
from app.ui.viewmodels.validation_agreement import build_validation_agreement_view


def test_validation_agreement_view_formats_cases_and_steps() -> None:
    evaluation = ValidationAgreementEvaluation(
        generated_at=datetime(2026, 4, 4, 22, 0, tzinfo=timezone.utc),
        agreement_id="p1-quality-2026-04-04",
        title="P1 Quality Validation Agreement",
        status=OperationStatus.NORMAL,
        approved_on=date(2026, 4, 4),
        authority="DOE/NREL + FEMP + NIST",
        summary="1 контрольная точка и 2 шага согласованы.",
        note="Agreement note.",
        total_sources=2,
        total_cases=1,
        total_steps=2,
        sources=[
            ValidationBasisSource(
                source_id="nrel_vics_report",
                title="Research and Development of a Ventilation-Integrated Comfort System",
                organization="NREL / U.S. Department of Energy",
                published_label="DOE/NREL report, April 2021",
                url="https://www.nrel.gov/docs/fy21osti/78352.pdf",
                relevance="Sensible heat and effectiveness.",
            ),
            ValidationBasisSource(
                source_id="doe_fan_system_info_card",
                title="Fan System Info Card",
                organization="U.S. Department of Energy",
                published_label="Info card",
                url="https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/BP_Fan%20Systems_Info%20Card_Final_0.pdf",
                relevance="Fan laws.",
            ),
        ],
        control_points=[
            ValidationAgreementCaseEvaluation(
                case_id="winter_supply_heating",
                title="Зима, штатный нагрев",
                basis_level=ValidationBasisLevel.MIXED,
                source_ids=["nrel_vics_report"],
                expected_status=OperationStatus.NORMAL,
                expected_alarm_codes=[],
                note="Winter note.",
                metrics=[
                    ValidationAgreementMetricEvaluation(
                        metric_id="supply_temp_c",
                        label="Температура притока",
                        unit="°C",
                        target_value=21.0,
                        tolerance=0.1,
                        lower_bound=20.9,
                        upper_bound=21.1,
                        note="Supply note.",
                    )
                ],
            )
        ],
        manual_steps=[
            ValidationAgreementStepEvaluation(
                step_id="recovered_air_temp_c",
                label="Температура после рекуперации",
                unit="°C",
                basis_level=ValidationBasisLevel.EXTERNAL,
                tolerance=0.01,
                source_ids=["nrel_vics_report"],
                note="Recovery note.",
            ),
            ValidationAgreementStepEvaluation(
                step_id="fan_power_kw",
                label="Мощность вентилятора",
                unit="кВт",
                basis_level=ValidationBasisLevel.MIXED,
                tolerance=0.01,
                source_ids=["doe_fan_system_info_card"],
                note="Fan note.",
            ),
        ],
        limitations=["Scope is generalized AHU."],
    )

    view = build_validation_agreement_view(evaluation)

    assert view.summary_text == "1 контрольная точка и 2 шага согласованы."
    assert view.summary_class_name == "status-pill status-normal"
    assert view.authority_text == "DOE/NREL + FEMP + NIST"
    assert view.approved_on_text == "2026-04-04"
    assert view.control_points[0].level_text == "Смешанный"
    assert view.control_points[0].metrics[0].summary_text == (
        "Температура притока: цель 21.00 °C, окно 20.90 .. 21.10 °C"
    )
    assert view.manual_steps[0].tolerance_text == "±0.01 °C"
    assert view.manual_steps[1].sources[0].label == "Fan System Info Card"
    assert view.limitations == ["Scope is generalized AHU."]
