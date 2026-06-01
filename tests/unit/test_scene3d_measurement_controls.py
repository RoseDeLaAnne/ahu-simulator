"""Тесты структуры UI-панели инструментов измерения (Задача 1.2).

Проверяют, что панель `_scene3d_measurement_tools()` рендерится в составе
3D-рабочего пространства и предоставляет все контролы, на которые завязан
clientside-callback `syncMeasurementMode`: режим, тип измерения (расстояние/угол),
очистка, сохранение/восстановление сессии и экспорт JSON/CSV.
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


# Идентификаторы, на которые завязаны Input/Output callback syncMeasurementMode.
MEASUREMENT_CONTROL_IDS = {
    "scene3d-measurement-mode",
    "scene3d-measurement-clear",
    "scene3d-measurement-type",
    "scene3d-measurement-save",
    "scene3d-measurement-restore",
    "scene3d-measurement-export-json",
    "scene3d-measurement-export-csv",
    "scene3d-measurement-status",
    "scene3d-measurement-list",
}


def test_measurement_controls_present_in_developer_mode() -> None:
    workspace = _build_workspace(developer_tools_enabled=True)
    ids = _component_ids(workspace)
    missing = MEASUREMENT_CONTROL_IDS - ids
    assert not missing, f"Отсутствуют контролы измерения: {sorted(missing)}"


def test_measurement_type_defaults_to_distance() -> None:
    workspace = _build_workspace(developer_tools_enabled=True)
    type_control = _find_by_id(workspace, "scene3d-measurement-type")
    assert type_control is not None
    assert type_control.value == "distance"
    option_values = {opt["value"] for opt in type_control.options}
    assert option_values == {"distance", "angle"}


def test_measurement_mode_defaults_to_disabled() -> None:
    workspace = _build_workspace(developer_tools_enabled=True)
    mode_control = _find_by_id(workspace, "scene3d-measurement-mode")
    assert mode_control is not None
    assert mode_control.value == []


def test_measurement_controls_absent_without_developer_tools() -> None:
    workspace = _build_workspace(developer_tools_enabled=False)
    ids = _component_ids(workspace)
    assert not (MEASUREMENT_CONTROL_IDS & ids)
