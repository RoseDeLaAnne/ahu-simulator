from datetime import datetime, timezone

from app.services.validation_service import (
    ValidationAgreementSnapshot,
    ValidationAlarmEvaluation,
    ValidationCaseEvaluation,
    ValidationMatrixEvaluation,
    ValidationMetricEvaluation,
    ValidationRange,
)
from app.simulation.state import OperationStatus
from app.ui.viewmodels.validation_matrix import build_validation_matrix_view


def test_validation_matrix_view_formats_summary_and_cases() -> None:
    matrix = ValidationMatrixEvaluation(
        generated_at=datetime(2026, 4, 4, 18, 0, tzinfo=timezone.utc),
        total_cases=2,
        passed_cases=1,
        all_passed=False,
        pending_note="Внешняя ручная валидация остаётся открытой.",
        agreement=ValidationAgreementSnapshot(
            agreement_id="p1-quality-2026-04-04",
            title="P1 Quality Validation Agreement",
            status=OperationStatus.NORMAL,
            approved_on=datetime(2026, 4, 4, tzinfo=timezone.utc).date(),
            authority="DOE/NREL + FEMP + NIST",
            summary="2 точки и 2 шага согласованы.",
            note="Agreement snapshot.",
            agreed_reference_cases=2,
            agreed_manual_steps=2,
        ),
        cases=[
            ValidationCaseEvaluation(
                case_id="winter_supply_heating",
                title="Зима, штатный нагрев",
                expected_status=OperationStatus.NORMAL,
                actual_status=OperationStatus.NORMAL,
                status_passed=True,
                metrics=[
                    ValidationMetricEvaluation(
                        metric_id="supply_temp_c",
                        label="Температура притока",
                        unit="°C",
                        expected_range=ValidationRange(lower=20.9, upper=21.1),
                        actual_value=21.0,
                        passed=True,
                    )
                ],
                alarms=ValidationAlarmEvaluation(
                    expected_codes=[],
                    actual_codes=[],
                    passed=True,
                ),
                passed=True,
            ),
            ValidationCaseEvaluation(
                case_id="dirty_filter_alarm",
                title="Загрязнение фильтра, сервисная тревога",
                expected_status=OperationStatus.ALARM,
                actual_status=OperationStatus.WARNING,
                status_passed=False,
                metrics=[
                    ValidationMetricEvaluation(
                        metric_id="total_power_kw",
                        label="Суммарная мощность",
                        unit="кВт",
                        expected_range=ValidationRange(lower=10.9, upper=11.2),
                        actual_value=12.4,
                        passed=False,
                    )
                ],
                alarms=ValidationAlarmEvaluation(
                    expected_codes=["FILTER_SERVICE_NOW"],
                    actual_codes=["AIRFLOW_WARNING"],
                    passed=False,
                ),
                passed=False,
            ),
        ],
    )

    view = build_validation_matrix_view(matrix)

    assert view.summary_text == "1 / 2 эталонных режимов проходят"
    assert view.summary_class_name == "status-pill status-alarm"
    assert "reference_points.json" in view.intro
    assert view.agreement_text == "Протокол согласия: 2 точки и 2 шага согласованы."
    assert view.generated_at_text == "2026-04-04T18:00:00+00:00"
    assert view.cases[0].badge_text == "Норма"
    assert view.cases[1].badge_text == "Проверить"
    assert view.cases[1].status_text == "Статус: ожидается авария, факт риск."
    assert "FILTER_SERVICE_NOW" in view.cases[1].alarms_text
    assert view.cases[1].metrics[0].result_text == "Вне диапазона"
    assert view.cases[1].metrics[0].actual_text == "12.4 кВт"
