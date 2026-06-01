"""Тесты структуры UI-панели режима сравнения side-by-side (Задача 3.2).

Проверяют, что панель `_scene3d_comparison_tools()` рендерится в составе
3D-рабочего пространства и предоставляет все контролы, на которые завязаны
clientside-callback `syncComparisonMode` и серверный `populate_comparison_sources`.
"""

from app.ui.render_modes.scene3d import build_scene3d_workspace
from app.ui.scene.model_catalog import SceneModelCatalog
from app.ui.scene.room_catalog import RoomCatalog


def _component_ids(component) -> set[str]:
    ids: set[str] = set()
    component_id = getattr(component, "id", None)
    if component_id:
        ids.add(str(component_id))

    children = getattr(component, "children", None)
    if children is None:
        return ids
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        ids.update(_component_ids(child))
    return ids


def _find_by_id(component, target_id: str):
    if getattr(component, "id", None) == target_id:
        return component
    children = getattr(component, "children", None)
    if children is None:
        return None
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        found = _find_by_id(child, target_id)
        if found is not None:
            return found
    return None


def _build_workspace(*, developer_tools_enabled: bool = True) -> object:
    return build_scene3d_workspace(
        SceneModelCatalog(),
        None,
        [{"label": "Base", "value": "base"}],
        "base",
        RoomCatalog(),
        None,
        developer_tools_enabled=developer_tools_enabled,
    )


# Идентификаторы, на которые завязаны Input/Output обоих callback в callbacks.py.
COMPARISON_CONTROL_IDS = {
    "scene3d-comparison-enabled",
    "scene3d-comparison-before-source",
    "scene3d-comparison-after-source",
    "scene3d-comparison-split",
    "scene3d-comparison-orientation",
    "scene3d-comparison-sync-cameras",
    "scene3d-comparison-diff-mode",
    "scene3d-comparison-compatibility",
    "scene3d-comparison-stats",
}


def test_comparison_controls_render_in_workspace() -> None:
    """Все контролы режима сравнения присутствуют в рабочем пространстве."""
    ids = _component_ids(_build_workspace())

    missing = COMPARISON_CONTROL_IDS - ids
    assert not missing, f"Отсутствуют контролы сравнения: {sorted(missing)}"


def test_comparison_controls_hidden_without_developer_tools() -> None:
    """Панель сравнения входит в группу developer-инструментов и скрыта по умолчанию."""
    ids = _component_ids(_build_workspace(developer_tools_enabled=False))

    assert "scene3d-comparison-enabled" not in ids
    assert "scene3d-comparison-diff-mode" not in ids


def test_comparison_diff_mode_offers_four_modes() -> None:
    """Dropdown режимов выделения предлагает status/temperature/power/alarms."""
    dropdown = _find_by_id(_build_workspace(), "scene3d-comparison-diff-mode")
    assert dropdown is not None

    values = {option["value"] for option in dropdown.options}
    assert values == {"status", "temperature", "power", "alarms"}
    assert dropdown.value == "status"
    assert dropdown.clearable is False


def test_comparison_orientation_offers_vertical_and_horizontal() -> None:
    """RadioItems ориентации предлагает вертикальное и горизонтальное разделение."""
    radio = _find_by_id(_build_workspace(), "scene3d-comparison-orientation")
    assert radio is not None

    values = {option["value"] for option in radio.options}
    assert values == {"vertical", "horizontal"}
    assert radio.value == "vertical"


def test_comparison_split_slider_bounds() -> None:
    """Слайдер соотношения разделения ограничен диапазоном 0.3–0.7 с шагом 0.1."""
    slider = _find_by_id(_build_workspace(), "scene3d-comparison-split")
    assert slider is not None

    assert slider.min == 0.3
    assert slider.max == 0.7
    assert slider.step == 0.1
    assert slider.value == 0.5


def test_comparison_sync_cameras_enabled_by_default() -> None:
    """Синхронизация камер включена по умолчанию."""
    checklist = _find_by_id(_build_workspace(), "scene3d-comparison-sync-cameras")
    assert checklist is not None
    assert checklist.value == ["sync"]


def test_comparison_disabled_by_default() -> None:
    """Режим сравнения выключен по умолчанию (пустой checklist)."""
    checklist = _find_by_id(_build_workspace(), "scene3d-comparison-enabled")
    assert checklist is not None
    assert checklist.value == []


def test_comparison_sources_start_empty() -> None:
    """Источники до/после пусты до заполнения серверным callback."""
    workspace = _build_workspace()
    before = _find_by_id(workspace, "scene3d-comparison-before-source")
    after = _find_by_id(workspace, "scene3d-comparison-after-source")

    assert before is not None and before.options == []
    assert after is not None and after.options == []
    assert before.value is None and after.value is None
