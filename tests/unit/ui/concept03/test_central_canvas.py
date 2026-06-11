from pathlib import Path

from app.services.simulation_service import SimulationService
from app.services.trend_service import TrendService
from app.simulation.scenarios import load_scenarios
from app.ui.concept03.central_canvas import (
    build_central_canvas,
    central_panel_class_name,
    central_tab_class_name,
)
from app.ui.viewmodels.concept03_central import build_concept03_central_view


def _build_service() -> SimulationService:
    scenario_path = (
        Path(__file__).resolve().parents[4] / "data" / "scenarios" / "presets.json"
    )
    return SimulationService(
        scenarios=load_scenarios(scenario_path),
        trend_service=TrendService(),
        default_scenario_id="midseason",
    )


def test_central_canvas_renders_phase5_regions_without_legacy_id_collision() -> None:
    service = _build_service()
    view = build_concept03_central_view(service.get_session())

    canvas = build_central_canvas(view)
    payload = str(canvas.to_plotly_json())
    ids = _collect_component_ids(canvas)

    assert canvas.id == "central-canvas"
    assert "central-canvas-tabs" in payload
    assert "concept03-scene-3d-canvas" in payload
    assert "concept03-scene-mode-select" in payload
    assert "concept03-scene-model-select" in payload
    assert "scene-3d-canvas" not in ids
    assert payload.count("c03-callout") >= 10
    assert "Пластинчатый рекуператор" in payload
    assert "concept03-mnemonic-svg-object" in payload


def test_central_canvas_contains_defense_tab_labels_and_balances() -> None:
    service = _build_service()
    view = build_concept03_central_view(service.get_session())

    canvas = build_central_canvas(view)
    payload = str(canvas.to_plotly_json())

    assert "Графики" in payload
    assert "Таблицы" in payload
    assert "Балансы" in payload
    assert "c03-balance-panel" in payload
    assert "view-layers" in payload
    assert "capture-png" in payload
    assert "concept03-camera-capture-status" in payload


def test_central_canvas_view_builds_operator_callouts_and_tabs() -> None:
    service = _build_service()
    session = service.get_session()

    view = build_concept03_central_view(session)

    assert [tab.tab_id for tab in view.tabs] == [
        "3d",
        "2d",
        "parameters",
        "trends",
        "alarms",
        "docs",
    ]
    assert [mode.mode_id for mode in view.scene_mode_options] == [
        "catalog",
        "digital_twin",
        "xray",
        "schematic",
    ]
    assert view.selected_scene_mode_id == "catalog"
    assert view.selected_scene_model_id is not None
    assert any(
        option.model_id == view.selected_scene_model_id
        for option in view.scene_model_options
    )
    operator_callouts = {
        callout.visual_id
        for callout in view.callouts
        if "c03-defense-only" not in callout.class_name
    }
    defense_callouts = {
        callout.visual_id
        for callout in view.callouts
        if "c03-defense-only" in callout.class_name
    }
    assert operator_callouts == {
        "outdoor_air",
        "filter_bank",
        "recuperator_core",
        "heater_coil",
        "supply_fan",
        "filter_fine",
        "cooler_coil",
        "silencer",
        "room_supply",
    }
    assert defense_callouts == {"room_zone"}
    assert len(view.callouts) == 10
    assert view.parameter_rows
    assert view.trend_rows
    assert view.doc_links


def test_central_canvas_renders_visible_installation_description() -> None:
    service = _build_service()
    view = build_concept03_central_view(service.get_session())

    # Viewmodel carries the installation description shown in the 3D scene.
    assert view.scene_about.title
    assert "рекупер" in view.scene_about.air_path.lower()
    assert view.scene_about.notes
    assert any("электрическ" in note.lower() for note in view.scene_about.notes)
    assert any("схематич" in note.lower() for note in view.scene_about.notes)

    canvas = build_central_canvas(view)
    payload = str(canvas.to_plotly_json())

    # Description is rendered (open by default) so it is visible on defense.
    assert "concept03-scene-about" in payload
    assert "c03-scene-about" in payload
    assert "электрический калорифер" in payload
    assert "рекуперац" in payload
    assert "схематич" in payload
    # Every labeled callout beside the card is accounted for in the air path.
    assert "водяной охладитель" in view.scene_about.air_path.lower()
    assert "тонкой очистки" in view.scene_about.air_path.lower()

    # The card MUST render open by default — a collapse regression would leave
    # all substring assertions green yet hide the description ("не увидел").
    about_3d = _find_component(canvas, "concept03-scene-about")
    assert about_3d is not None
    assert getattr(about_3d, "open", None) is True
    class_name = getattr(about_3d, "className", "") or ""
    assert "c03-operator-only" not in class_name
    assert "c03-defense-only" not in class_name
    # The same description also accompanies the 2D «Схема» tab.
    assert _find_component(canvas, "concept03-scene-about-2d") is not None


def test_central_tab_class_names_are_stable() -> None:
    assert central_tab_class_name("3d", "3d").endswith("--active")
    assert not central_tab_class_name("2d", "3d").endswith("--active")
    assert central_panel_class_name("alarms", "alarms").endswith("--active")
    assert not central_panel_class_name("docs", "alarms").endswith("--active")


def _find_component(component, target_id: str):
    if getattr(component, "id", None) == target_id:
        return component
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            found = _find_component(child, target_id)
            if found is not None:
                return found
    elif children is not None and not isinstance(children, (str, int, float)):
        return _find_component(children, target_id)
    return None


def _collect_component_ids(component) -> set[str]:
    ids: set[str] = set()
    component_id = getattr(component, "id", None)
    if isinstance(component_id, str):
        ids.add(component_id)
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            ids.update(_collect_component_ids(child))
    elif children is not None and not isinstance(children, (str, int, float)):
        ids.update(_collect_component_ids(children))
    return ids
