from app.ui.viewmodels.defense_pack import build_defense_pack_view


def test_defense_pack_includes_demo_flow_and_phase_8_materials() -> None:
    view = build_defense_pack_view()

    assert view.demo_duration == "5-7 минут"
    assert len(view.demo_flow) >= 6
    assert any(step.title == "Аварийный сценарий `dirty_filter`" for step in view.demo_flow)
    assert any("Основания валидации" in step.operator_action for step in view.demo_flow)
    assert any("2D SVG" in item for item in view.visual_scenario)
    assert any("Основаниями валидации" in item for item in view.visual_scenario)


def test_defense_pack_contains_tables_limitations_and_ai_notes() -> None:
    view = build_defense_pack_view()

    assert any(row.technology == "Dash" for row in view.technology_rows)
    assert any("src/app/ui/callbacks.py" in row.module_path for row in view.function_module_rows)
    assert any("validation_basis.py" in row.module_path for row in view.function_module_rows)
    assert any("WebGL" in item for item in view.model_limitations)
    assert any("вспомогательный инструмент" in item for item in view.ai_usage_notes)
