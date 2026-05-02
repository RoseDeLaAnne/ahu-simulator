from app.ui.scene.room_catalog import (
    build_room_catalog,
    build_room_runtime_payload,
    resolve_room_descriptor,
    resolve_room_preset,
)


def test_room_catalog_exposes_default_room_with_real_glb_and_presets() -> None:
    catalog = build_room_catalog()

    assert catalog.default_room_id is not None
    assert len(catalog.rooms) >= 3

    room = resolve_room_descriptor(catalog, catalog.default_room_id)
    assert room is not None
    assert room.model_path.startswith("models/")
    assert room.model_url.startswith("/models/")
    assert room.presets
    assert room.design_occupancy_people > 0


def test_room_catalog_prefers_new_detailed_room_models_from_folders() -> None:
    catalog = build_room_catalog()

    office = resolve_room_descriptor(catalog, "office_suite")
    classroom = resolve_room_descriptor(catalog, "classroom_wing")
    lab = resolve_room_descriptor(catalog, "lab_cluster")

    assert office is not None
    assert office.model_path == "models/rooms/office_suite.glb"
    assert classroom is not None
    assert classroom.model_path == "models/rooms/classroom_wing.glb"
    assert lab is not None
    assert lab.model_path == "models/rooms/lab_cluster.glb"


def test_room_runtime_payload_merges_active_preset_and_local_inputs() -> None:
    catalog = build_room_catalog()
    room = resolve_room_descriptor(catalog, "classroom_wing")
    assert room is not None
    preset = resolve_room_preset(room, "classroom_full_lesson")
    assert preset is not None

    payload = build_room_runtime_payload(
        room,
        preset_id=preset.id,
        occupancy_people=28,
        local_humidity_percent=53,
    )

    assert payload["id"] == "classroom_wing"
    assert payload["active_preset_id"] == "classroom_full_lesson"
    assert payload["occupancy_people"] == 28
    assert payload["local_humidity_percent"] == 53.0
    assert payload["active_preset"]["label"] == preset.label
