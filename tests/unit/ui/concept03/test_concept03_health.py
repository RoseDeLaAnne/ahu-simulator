from pathlib import Path

from app.services.simulation_service import SimulationService
from app.services.trend_service import TrendService
from app.simulation.scenarios import load_scenarios
from app.ui.viewmodels.concept03_health import build_concept03_health_view


PROJECT_ROOT = Path(__file__).resolve().parents[4]


def test_concept03_health_view_builds_status_banner_and_tiles() -> None:
    view = build_concept03_health_view(_preview("baseline_office_winter"))

    assert view.banner.title == "Состояние установки"
    assert view.banner.label == "Норма"
    assert view.banner.state == "normal"
    assert "c03-status-banner--normal" in view.banner.class_name
    assert [tile.health_id for tile in view.tiles] == [
        "equipment",
        "automation",
        "sensors",
        "safety",
    ]
    assert view.tiles[3].sub == "Без тревог"


def test_concept03_health_view_escalates_equipment_and_safety() -> None:
    view = build_concept03_health_view(_preview("dirty_filter"))
    tiles = {tile.health_id: tile for tile in view.tiles}

    assert view.banner.label == "Авария"
    assert view.banner.state == "alarm"
    assert "Активных тревог: 2" in view.banner.summary
    assert tiles["equipment"].state == "alarm"
    assert tiles["safety"].state == "alarm"
    assert tiles["safety"].sub == "Тревог: 2"


def test_concept03_health_view_marks_manual_automation_as_operator_control() -> None:
    view = build_concept03_health_view(_preview("manual_mode"))
    tiles = {tile.health_id: tile for tile in view.tiles}

    assert tiles["automation"].state == "warning"
    assert tiles["automation"].sub == "Оператор"


def _preview(scenario_id: str):
    service = SimulationService(
        scenarios=load_scenarios(PROJECT_ROOT / "data" / "scenarios" / "presets.json"),
        trend_service=TrendService(),
        default_scenario_id="baseline_office_winter",
    )
    return service.preview_scenario(scenario_id)
