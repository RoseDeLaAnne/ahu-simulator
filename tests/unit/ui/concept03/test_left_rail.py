from pathlib import Path

from app.services.project_baseline_service import ProjectBaselineService
from app.services.simulation_service import SimulationService
from app.services.trend_service import TrendService
from app.simulation.parameters import ControlMode
from app.simulation.scenarios import load_scenarios
from app.ui.concept03.left_rail import build_left_rail
from app.ui.viewmodels.concept03_config import build_concept03_config_view
from app.ui.viewmodels.concept03_modes import build_concept03_modes_view
from app.ui.viewmodels.concept03_scenarios import (
    CONCEPT03_SCENARIO_IDS,
    build_concept03_scenarios_view,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]


def test_left_rail_renders_five_operator_scenario_cards() -> None:
    rail = _build_left_rail(active_scenario_id="baseline_office_winter")
    scenario_cards = _find_pattern_components(rail, "concept03-scenario-card")

    assert [card.id["scenario_id"] for card in scenario_cards] == list(
        CONCEPT03_SCENARIO_IDS
    )
    assert "c03-scenario-card--active" in scenario_cards[0].className
    payload = str(rail.to_plotly_json())
    assert "Номинальный режим" in payload
    assert "Пожарная вентиляция" in payload
    assert "layout-grid" in payload
    assert "flame" in payload


def test_left_rail_renders_four_control_mode_cards() -> None:
    rail = _build_left_rail(
        active_scenario_id="baseline_office_winter",
        active_mode=ControlMode.SEMI_AUTO,
    )
    mode_cards = _find_pattern_components(rail, "concept03-mode-card")

    assert [card.id["mode_id"] for card in mode_cards] == [
        "auto",
        "semi_auto",
        "manual",
        "test",
    ]
    assert "c03-mode-card--active" in mode_cards[1].className
    assert "Полуавтоматический" in str(rail.to_plotly_json())


def test_left_rail_keeps_management_ctas_addressable() -> None:
    rail = _build_left_rail(active_scenario_id="baseline_office_winter")
    payload = str(rail.to_plotly_json())

    assert "concept03-manage-scenarios" in payload
    assert "?theme=concept03&page=control" in payload
    assert "concept03-installation-properties" in payload


def _build_left_rail(
    *,
    active_scenario_id: str,
    active_mode: ControlMode = ControlMode.AUTO,
):
    scenarios = load_scenarios(PROJECT_ROOT / "data" / "scenarios" / "presets.json")
    service = SimulationService(
        scenarios=scenarios,
        trend_service=TrendService(),
        default_scenario_id=active_scenario_id,
    )
    result = service.get_state()
    baseline = ProjectBaselineService(PROJECT_ROOT).build_snapshot()
    return build_left_rail(
        scenarios=build_concept03_scenarios_view(
            scenarios,
            active_scenario_id=active_scenario_id,
        ),
        modes=build_concept03_modes_view(active_mode),
        config=build_concept03_config_view(
            project_baseline=baseline,
            current_result=result,
        ),
    )


def _walk(component):
    yield component
    children = getattr(component, "children", None)
    if isinstance(children, list | tuple):
        for child in children:
            if child is not None:
                yield from _walk(child)
    elif children is not None and not isinstance(children, str):
        yield from _walk(children)


def _find_pattern_components(component, pattern_type: str) -> list:
    return [
        child
        for child in _walk(component)
        if isinstance(getattr(child, "id", None), dict)
        and child.id.get("type") == pattern_type
    ]
