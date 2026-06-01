from pathlib import Path

from app.services.simulation_service import SimulationService
from app.services.trend_service import TrendService
from app.simulation.scenarios import load_scenarios
from app.ui.concept03.right_rail import build_right_rail
from app.ui.viewmodels.concept03_health import build_concept03_health_view
from app.ui.viewmodels.concept03_kpi import build_concept03_kpi_view


PROJECT_ROOT = Path(__file__).resolve().parents[4]


def test_right_rail_renders_status_kpis_and_health_grid() -> None:
    result = _preview("dirty_filter")
    rail = build_right_rail(
        kpis=build_concept03_kpi_view(result),
        health=build_concept03_health_view(result),
    )
    payload = str(rail.to_plotly_json())

    assert rail.id == "right-rail"
    assert "c03-right-rail" in rail.className
    assert "right-rail-status-banner" in payload
    assert "КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ" in payload
    assert "ОБЩЕЕ СОСТОЯНИЕ" in payload
    assert "mobile-kpi-strip" in payload
    assert len(_find_id_prefix(rail, "kpi-row-")) == 6
    assert len(_find_id_prefix(rail, "health-tile-")) == 4


def test_right_rail_contains_defense_kpi_cards_and_accordions() -> None:
    result = _preview("baseline_office_winter")
    rail = build_right_rail(
        kpis=build_concept03_kpi_view(result),
        health=build_concept03_health_view(result),
    )
    payload = str(rail.to_plotly_json())

    assert "ТЕКУЩЕЕ СОСТОЯНИЕ" in payload
    assert "СТАТУС КОМПОНЕНТОВ" in payload
    assert "АКТИВНЫЕ АЛАРМЫ" in payload
    assert "ЖУРНАЛ СОБЫТИЙ" in payload
    assert len(_find_id_prefix(rail, "defense-kpi-row-")) == 4
    assert "c03-sparkline" in payload


def _preview(scenario_id: str):
    service = SimulationService(
        scenarios=load_scenarios(PROJECT_ROOT / "data" / "scenarios" / "presets.json"),
        trend_service=TrendService(),
        default_scenario_id="baseline_office_winter",
    )
    return service.preview_scenario(scenario_id)


def _walk(component):
    yield component
    children = getattr(component, "children", None)
    if isinstance(children, list | tuple):
        for child in children:
            if child is not None:
                yield from _walk(child)
    elif children is not None and not isinstance(children, str):
        yield from _walk(children)


def _find_id_prefix(component, prefix: str) -> list:
    return [
        child
        for child in _walk(component)
        if isinstance(getattr(child, "id", None), str)
        and child.id.startswith(prefix)
    ]
