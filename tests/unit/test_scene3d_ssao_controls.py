"""Тесты структуры UI-панели SSAO post-processing (Задача 1.1).

Проверяют, что панель `_scene3d_ssao_controls()` рендерится в составе
3D-рабочего пространства в режиме разработчика и предоставляет все контролы,
на которые завязан clientside-callback `syncSSAOControls`: чекбокс включения и
input+slider для каждого параметра (радиус ядра, мин./макс. дистанция).
SSAO опционален, поэтому по умолчанию эффект выключен.
"""

from app.ui.render_modes.scene3d import (
    SCENE3D_SSAO_CONTROLS,
    build_scene3d_workspace,
    scene3d_ssao_input_id,
    scene3d_ssao_slider_id,
)
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


# Идентификаторы, на которые завязаны Input/Output callback syncSSAOControls.
# Выводим из источника истины (SCENE3D_SSAO_CONTROLS + хелперы), чтобы тест
# не расходился с реальными id при изменении набора параметров.
SSAO_ENABLED_ID = "scene3d-ssao-enabled"
SSAO_FIELD_IDS = {
    scene3d_ssao_input_id(str(c["key"])) for c in SCENE3D_SSAO_CONTROLS
} | {scene3d_ssao_slider_id(str(c["key"])) for c in SCENE3D_SSAO_CONTROLS}
SSAO_CONTROL_IDS = {SSAO_ENABLED_ID} | SSAO_FIELD_IDS


def test_ssao_controls_present_in_developer_mode() -> None:
    workspace = _build_workspace(developer_tools_enabled=True)
    ids = _component_ids(workspace)
    missing = SSAO_CONTROL_IDS - ids
    assert not missing, f"Отсутствуют контролы SSAO: {sorted(missing)}"


def test_ssao_enabled_defaults_to_off() -> None:
    workspace = _build_workspace(developer_tools_enabled=True)
    enabled = _find_by_id(workspace, SSAO_ENABLED_ID)
    assert enabled is not None
    # Эффект опционален — чекбокс по умолчанию пуст (выключен).
    assert enabled.value == []


def test_ssao_param_defaults_match_spec() -> None:
    workspace = _build_workspace(developer_tools_enabled=True)
    for control in SCENE3D_SSAO_CONTROLS:
        key = str(control["key"])
        input_component = _find_by_id(workspace, scene3d_ssao_input_id(key))
        slider_component = _find_by_id(workspace, scene3d_ssao_slider_id(key))
        assert input_component is not None, f"нет input для {key}"
        assert slider_component is not None, f"нет slider для {key}"
        assert input_component.value == control["value"]
        assert slider_component.value == control["value"]


def test_ssao_controls_absent_without_developer_tools() -> None:
    workspace = _build_workspace(developer_tools_enabled=False)
    ids = _component_ids(workspace)
    assert not (SSAO_CONTROL_IDS & ids)
