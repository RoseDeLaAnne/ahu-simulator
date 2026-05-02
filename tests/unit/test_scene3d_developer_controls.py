from app.ui.render_modes.scene3d import (
    SCENE3D_TRANSFORM_CONTROLS,
    build_scene3d_workspace,
    scene3d_transform_input_id,
    scene3d_transform_slider_id,
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


def test_scene3d_developer_controls_hidden_by_default() -> None:
    workspace = build_scene3d_workspace(
        SceneModelCatalog(),
        None,
        [{"label": "Base", "value": "base"}],
        "base",
        RoomCatalog(),
        None,
    )

    assert "scene3d-dev-model-scale" not in _component_ids(workspace)
    assert "scene3d-dev-transform-reset" not in _component_ids(workspace)


def test_scene3d_developer_controls_render_when_enabled() -> None:
    workspace = build_scene3d_workspace(
        SceneModelCatalog(),
        None,
        [{"label": "Base", "value": "base"}],
        "base",
        RoomCatalog(),
        None,
        developer_tools_enabled=True,
    )

    ids = _component_ids(workspace)

    for control in SCENE3D_TRANSFORM_CONTROLS:
        key = str(control["key"])
        assert scene3d_transform_input_id(key) in ids
        assert scene3d_transform_slider_id(key) in ids

    assert "scene3d-dev-model-long-scale" in ids
    assert "scene3d-dev-model-pitch-delta-slider" in ids
    assert "scene3d-dev-model-roll-delta-slider" in ids
    assert "scene3d-dev-transform-reset" in ids
