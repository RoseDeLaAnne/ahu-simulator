from datetime import datetime, timezone

from app.services.validation_service import (
    ManualCheckEvaluation,
    ManualCheckStepEvaluation,
    ValidationAgreementSnapshot,
)
from app.simulation.state import OperationStatus
from app.ui.viewmodels.manual_check import build_manual_check_view


def test_manual_check_view_formats_summary_and_steps() -> None:
    evaluation = ManualCheckEvaluation(
        generated_at=datetime(2026, 4, 4, 19, 15, tzinfo=timezone.utc),
        subject_name="Зима, штатный нагрев",
        scenario_id="winter",
        matched_reference_case_id="winter_supply_heating",
        matched_reference_case_title="Зима, штатный нагрев",
        total_steps=2,
        passed_steps=1,
        all_passed=False,
        note="Внешнее согласование контрольных точек остаётся отдельным шагом.",
        agreement=ValidationAgreementSnapshot(
            agreement_id="p1-quality-2026-04-04",
            title="P1 Quality Validation Agreement",
            status=OperationStatus.NORMAL,
            approved_on=datetime(2026, 4, 4, tzinfo=timezone.utc).date(),
            authority="DOE/NREL + FEMP + NIST",
            summary="5 контрольных точек и 9 шагов согласованы.",
            note="Agreement snapshot.",
            agreed_reference_cases=5,
            agreed_manual_steps=9,
        ),
        steps=[
            ManualCheckStepEvaluation(
                step_id="actual_airflow_m3_h",
                label="Фактический расход",
                formula="3600 * 1.00 * max(0.45, 1 - 0.35 * 0.22)",
                unit="м³/ч",
                manual_value=3322.8,
                model_value=3322.8,
                tolerance=0.01,
                delta_abs=0.0,
                passed=True,
            ),
            ManualCheckStepEvaluation(
                step_id="total_power_kw",
                label="Суммарная мощность",
                formula="Q_heat + P_fan",
                unit="кВт",
                manual_value=20.84,
                model_value=21.11,
                tolerance=0.01,
                delta_abs=0.27,
                passed=False,
            ),
        ],
    )

    view = build_manual_check_view(evaluation)

    assert view.subject_name == "Зима, штатный нагрев"
    assert view.source_text == "Сценарий: winter"
    assert view.matched_case_text == "Контрольная точка: Зима, штатный нагрев (winter_supply_heating)"
    assert view.summary_text == "1 / 2 формульных шагов совпадают"
    assert view.summary_class_name == "status-pill status-alarm"
    assert view.agreement_text == "Протокол согласия: 5 контрольных точек и 9 шагов согласованы."
    assert view.generated_at_text == "2026-04-04T19:15:00+00:00"
    assert view.steps[0].manual_text == "3322.80 м³/ч"
    assert view.steps[0].tolerance_text == "±0.01 м³/ч"
    assert view.steps[1].delta_text == "0.27 кВт"
    assert view.steps[1].result_text == "Проверить"
