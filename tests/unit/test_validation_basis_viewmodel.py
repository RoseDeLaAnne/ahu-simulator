from datetime import datetime, timezone

from app.services.validation_service import (
    ValidationAgreementSnapshot,
    ValidationBasisEvaluation,
    ValidationBasisLevel,
    ValidationBasisSource,
    ValidationBasisTrace,
)
from app.simulation.state import OperationStatus
from app.ui.viewmodels.validation_basis import build_validation_basis_view


def test_validation_basis_view_formats_traceability_and_sources() -> None:
    evaluation = ValidationBasisEvaluation(
        generated_at=datetime(2026, 4, 4, 20, 5, tzinfo=timezone.utc),
        total_sources=2,
        traced_manual_steps=3,
        traced_reference_cases=1,
        pending_note="Численные диапазоны пока остаются внутренними для MVP.",
        agreement=ValidationAgreementSnapshot(
            agreement_id="p1-quality-2026-04-04",
            title="P1 Quality Validation Agreement",
            status=OperationStatus.NORMAL,
            approved_on=datetime(2026, 4, 4, tzinfo=timezone.utc).date(),
            authority="DOE/NREL + FEMP + NIST",
            summary="1 контрольная точка и 3 шага согласованы.",
            note="Agreement snapshot.",
            agreed_reference_cases=1,
            agreed_manual_steps=3,
        ),
        sources=[
            ValidationBasisSource(
                source_id="nrel_vics_report",
                title="Research and Development of a Ventilation-Integrated Comfort System",
                organization="NREL / U.S. Department of Energy",
                published_label="DOE/NREL report, April 2021",
                url="https://www.nrel.gov/docs/fy21osti/78352.pdf",
                relevance="Формулы sensible heat и effectiveness.",
            ),
            ValidationBasisSource(
                source_id="doe_om_best_practices",
                title="Operations & Maintenance Best Practices Guide: Release 3.0",
                organization="FEMP / U.S. Department of Energy",
                published_label="FEMP guide",
                url="https://www1.eere.energy.gov/femp/pdfs/om_9.pdf",
                relevance="Pressure drop и обслуживание фильтров.",
            ),
        ],
        manual_steps=[
            ValidationBasisTrace(
                item_id="recovered_air_temp_c",
                title="Температура после рекуперации",
                basis_level=ValidationBasisLevel.EXTERNAL,
                source_ids=["nrel_vics_report"],
                note="Шаг опирается на effectiveness heat exchanger.",
            ),
            ValidationBasisTrace(
                item_id="filter_pressure_drop_pa",
                title="Перепад на фильтре",
                basis_level=ValidationBasisLevel.MIXED,
                source_ids=["doe_om_best_practices"],
                note="Pressure drop внешний, формула загрязнения внутренняя.",
            ),
            ValidationBasisTrace(
                item_id="room_temp_c",
                title="Температура помещения на шаге",
                basis_level=ValidationBasisLevel.ASSUMPTION,
                source_ids=[],
                note="Однозонное упрощение.",
            ),
        ],
        reference_cases=[
            ValidationBasisTrace(
                item_id="winter_supply_heating",
                title="Зима, штатный нагрев",
                basis_level=ValidationBasisLevel.MIXED,
                source_ids=["nrel_vics_report"],
                note="Зимняя точка опирается на DOE/NREL report.",
            )
        ],
    )

    view = build_validation_basis_view(evaluation)

    assert view.summary_text == "2 внешних источника, 3 шага и 1 контрольная точка привязаны"
    assert view.summary_class_name == "status-pill status-normal"
    assert view.coverage_text == "По шагам: 1 внешний, 1 смешанный, 0 производных, 1 допущение."
    assert view.agreement_text == "Протокол согласия: 1 контрольная точка и 3 шага согласованы."
    assert view.generated_at_text == "2026-04-04T20:05:00+00:00"
    assert view.sources[0].meta_text == "NREL / U.S. Department of Energy · DOE/NREL report, April 2021"
    assert view.manual_steps[0].level_text == "Внешний"
    assert view.manual_steps[0].sources[0].label == "Research and Development of a Ventilation-Integrated Comfort System"
    assert view.manual_steps[2].level_text == "Допущение"
    assert view.reference_cases[0].level_class_name == "status-pill status-warning"
