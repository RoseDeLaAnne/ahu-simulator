from datetime import datetime, timezone

from app.services.project_baseline_service import (
    ProjectBaselineDecision,
    ProjectBaselineOutput,
    ProjectBaselineParameter,
    ProjectBaselineScenario,
    ProjectBaselineSnapshot,
    ProjectBaselineSubject,
    ProjectBaselineValidationLayer,
)
from app.simulation.state import OperationStatus
from app.ui.viewmodels.project_baseline import build_project_baseline_view


def test_project_baseline_view_formats_snapshot() -> None:
    snapshot = ProjectBaselineSnapshot(
        generated_at=datetime(2026, 4, 4, 21, 30, tzinfo=timezone.utc),
        baseline_version=1,
        overall_status=OperationStatus.NORMAL,
        summary="P0 baseline зафиксирован.",
        note="Рабочий baseline для MVP.",
        subject=ProjectBaselineSubject(
            subject_id="generalized_supply_ahu",
            title="Учебно-обобщенная ПВУ",
            scope_summary="Общая инженерная схема.",
            note="Рабочий baseline для MVP.",
        ),
        locked_decisions=[
            ProjectBaselineDecision(
                decision_id="subject_scope",
                title="Тип установки",
                summary="Учебная ПВУ.",
                rationale="Нет паспортных данных.",
                evidence_paths=["docs/19_p0_baseline.md"],
            )
        ],
        operator_inputs=[
            ProjectBaselineParameter(
                parameter_id="outdoor_temp_c",
                title="Наружная температура",
                unit="°C",
                why_required="Главный внешний фактор.",
            )
        ],
        fixed_model_inputs=[
            ProjectBaselineParameter(
                parameter_id="room_volume_m3",
                title="Объем помещения",
                unit="м³",
                why_fixed="Внутренний baseline.",
            )
        ],
        outputs=[
            ProjectBaselineOutput(
                output_id="supply_temp_c",
                title="Температура притока",
                unit="°C",
                location="state",
                why_required="Контрольная точка.",
            )
        ],
        defense_scenarios=[
            ProjectBaselineScenario(
                scenario_id="winter",
                title="Зима",
                description="Зимний режим.",
                category="heating",
                purpose="Показ нагрева.",
                key_demo_point="Рост мощности.",
            )
        ],
        validation_layers=[
            ProjectBaselineValidationLayer(
                layer_id="validation_pack",
                title="Validation Pack",
                artifact="GET /validation/matrix",
                purpose="Regression matrix.",
                evidence_paths=["data/validation/reference_points.json"],
            )
        ],
        follow_up_items=["Внешняя валидация остается phase 6."],
    )

    view = build_project_baseline_view(snapshot)

    assert view.summary_class_name == "status-pill status-normal"
    assert view.version_text == "Базовая версия 1"
    assert view.generated_at_text == "2026-04-04T21:30:00+00:00"
    assert view.operator_inputs[0].parameter_id == "outdoor_temp_c"
    assert view.fixed_model_inputs[0].why_text == "Внутренний baseline."
    assert view.validation_layers[0].artifact == "GET /validation/matrix"
