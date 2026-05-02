"""Build a complex apartment PVU scene in Blender and export it as GLB.

This script is intended to run inside Blender:

    blender.exe --background --python tooling/scene/build_blender_pvu.py

The scene is rebuilt around the main use case of modelling a supply ventilation
installation serving multiple rooms in an apartment-like plan, with additional
contextual exhaust routing to better match the image references. The exported
GLB keeps stable scene node names expected by the dashboard.
"""

from __future__ import annotations

import math
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Vector


SCENE_NODES = {
    "intake": "pvu.intake.outdoor_air",
    "flow_outdoor_to_filter": "pvu.flow.outdoor_to_filter",
    "filter": "pvu.filter.bank",
    "flow_filter_to_heater": "pvu.flow.filter_to_heater",
    "heater": "pvu.heater.coil",
    "flow_heater_to_fan": "pvu.flow.heater_to_fan",
    "fan": "pvu.fan.supply",
    "fan_rotor": "pvu.fan.rotor",
    "duct": "pvu.duct.supply",
    "flow_fan_to_room": "pvu.flow.fan_to_room",
    "room_plumes": "pvu.flow.room_plumes",
    "extract_context": "building.flow.extract_context",
    "damper_intake": "pvu.damper.intake",
    "damper_living": "pvu.damper.living",
    "damper_bedroom_north": "pvu.damper.bedroom_north",
    "damper_bedroom_south": "pvu.damper.bedroom_south",
    "damper_study": "pvu.damper.study",
    "damper_kitchen": "pvu.damper.kitchen",
    "room": "building.room.zone_a",
    "sensor_outdoor": "pvu.sensors.outdoor_temp",
    "sensor_filter": "pvu.sensors.filter_pressure",
    "sensor_supply": "pvu.sensors.supply_temp",
    "sensor_airflow": "pvu.sensors.airflow",
    "sensor_room": "building.sensors.room_temp",
}

PLAN = {
    "floor_x": 13.2,
    "floor_z": 9.8,
    "wall_height": 2.78,
    "duct_y": 2.38,
    "ceiling_neck_y": 2.59,
    "ceiling_y": 2.74,
    "wall_thickness": 0.12,
}


def _to_blender_location(value: tuple[float, float, float]) -> tuple[float, float, float]:
    """Map semantic coordinates (x, height, depth) into Blender's native (x, y, z)."""
    return (value[0], value[2], value[1])


def _to_blender_dimensions(value: tuple[float, float, float]) -> tuple[float, float, float]:
    return (value[0], value[2], value[1])


def _to_blender_rotation(value: tuple[float, float, float]) -> tuple[float, float, float]:
    """Map semantic Euler rotations (X, Y-up, Z-depth) into Blender's Z-up axes."""
    return (value[0], value[2], value[1])


def _project_root() -> Path:
    if "__file__" in globals():
        return Path(__file__).resolve().parents[2]
    return Path.cwd()


def _parse_args() -> tuple[Path, Path, Path]:
    root = _project_root()
    output_glb = root / "data" / "visualization" / "assets" / "pvu_installation.glb"
    output_blend = root / "3d-references" / "pvu_parametric_generated.blend"
    output_preview = root / "3d-references" / "pvu_parametric_preview.png"

    argv = sys.argv
    if "--" not in argv:
        return output_glb, output_blend, output_preview

    extra = argv[argv.index("--") + 1:]
    for idx, arg in enumerate(extra):
        if arg == "--output-glb" and idx + 1 < len(extra):
            output_glb = Path(extra[idx + 1]).resolve()
        if arg == "--output-blend" and idx + 1 < len(extra):
            output_blend = Path(extra[idx + 1]).resolve()
        if arg == "--output-preview" and idx + 1 < len(extra):
            output_preview = Path(extra[idx + 1]).resolve()
    return output_glb, output_blend, output_preview


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.curves,
        bpy.data.images,
        bpy.data.worlds,
    ):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def _set_scene_units() -> None:
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = 160
    if scene.world is None:
        scene.world = bpy.data.worlds.new("PVUWorld")
    world = scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg is not None:
        bg.inputs[0].default_value = (0.87, 0.89, 0.93, 1.0)
        bg.inputs[1].default_value = 0.55


def _look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(_to_blender_location(target)) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Z").to_euler()


def _new_material(
    name: str,
    base_color: tuple[float, float, float, float],
    *,
    metallic: float,
    roughness: float,
    transmission: float = 0.0,
    emission: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.6,
    alpha_blend: bool = False,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        raise RuntimeError(f"Material {name} is missing the Principled BSDF node")

    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = base_color[3]
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = transmission
    if emission is not None:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = emission
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    if alpha_blend:
        mat.blend_method = "BLEND"
        if hasattr(mat, "shadow_method"):
            mat.shadow_method = "HASHED"
    return mat


def _set_node_name(obj: bpy.types.Object, name: str) -> bpy.types.Object:
    obj.name = name
    obj["scene_node"] = name
    return obj


def _parent_keep_world(
    obj: bpy.types.Object,
    parent: bpy.types.Object | None,
) -> bpy.types.Object:
    if parent is None:
        return obj
    bpy.context.view_layer.update()
    world_matrix = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = world_matrix
    return obj


def _make_empty(
    name: str,
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
    *,
    parent: bpy.types.Object | None = None,
) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.18
    obj.location = _to_blender_location(location)
    bpy.context.scene.collection.objects.link(obj)
    _parent_keep_world(obj, parent)
    return _set_node_name(obj, name)


def _make_box(
    name: str,
    *,
    location: tuple[float, float, float],
    dimensions: tuple[float, float, float],
    material: bpy.types.Material | None = None,
    parent: bpy.types.Object | None = None,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=_to_blender_location(location))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = tuple(value / 2 for value in _to_blender_dimensions(dimensions))
    if material is not None:
        obj.data.materials.clear()
        obj.data.materials.append(material)
    _parent_keep_world(obj, parent)
    return obj


def _make_cylinder(
    name: str,
    *,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    vertices: int = 32,
    material: bpy.types.Material | None = None,
    parent: bpy.types.Object | None = None,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=_to_blender_location(location),
        rotation=_to_blender_rotation(rotation),
    )
    obj = bpy.context.active_object
    obj.name = name
    if material is not None:
        obj.data.materials.clear()
        obj.data.materials.append(material)
    _parent_keep_world(obj, parent)
    return obj


def _make_uv_sphere(
    name: str,
    *,
    location: tuple[float, float, float],
    radius: float,
    material: bpy.types.Material | None = None,
    parent: bpy.types.Object | None = None,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=_to_blender_location(location))
    obj = bpy.context.active_object
    obj.name = name
    if material is not None:
        obj.data.materials.clear()
        obj.data.materials.append(material)
    _parent_keep_world(obj, parent)
    return obj


def _make_axis_segment(
    name: str,
    *,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    width: float,
    height: float,
    material: bpy.types.Material,
    parent: bpy.types.Object | None = None,
) -> bpy.types.Object:
    start_vec = Vector(start)
    end_vec = Vector(end)
    delta = end_vec - start_vec
    axes = [abs(delta.x), abs(delta.y), abs(delta.z)]
    major_axis = max(range(3), key=axes.__getitem__)
    location = tuple((start_vec + end_vec) / 2)

    if axes[major_axis] <= 0.0001:
        raise ValueError(f"Segment {name} has zero length")
    if sum(value > 0.0001 for value in axes) != 1:
        raise ValueError(f"Segment {name} must be axis aligned")

    if major_axis == 0:
        dims = (axes[0], height, width)
    elif major_axis == 1:
        dims = (width, axes[1], width)
    else:
        dims = (width, height, axes[2])
    return _make_box(name, location=location, dimensions=dims, material=material, parent=parent)


def _make_round_segment(
    name: str,
    *,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
    material: bpy.types.Material,
    parent: bpy.types.Object | None = None,
) -> bpy.types.Object:
    start_vec = Vector(start)
    end_vec = Vector(end)
    delta = end_vec - start_vec
    axes = [abs(delta.x), abs(delta.y), abs(delta.z)]
    major_axis = max(range(3), key=axes.__getitem__)
    location = tuple((start_vec + end_vec) / 2)

    if axes[major_axis] <= 0.0001:
        raise ValueError(f"Round segment {name} has zero length")
    if sum(value > 0.0001 for value in axes) != 1:
        raise ValueError(f"Round segment {name} must be axis aligned")

    if major_axis == 0:
        rotation = (0.0, 0.0, math.radians(90))
        depth = axes[0]
    elif major_axis == 1:
        rotation = (0.0, 0.0, 0.0)
        depth = axes[1]
    else:
        rotation = (math.radians(90), 0.0, 0.0)
        depth = axes[2]
    return _make_cylinder(
        name,
        location=location,
        radius=radius,
        depth=depth,
        rotation=rotation,
        material=material,
        parent=parent,
    )


def _make_wall_segment(
    name: str,
    *,
    start: tuple[float, float],
    end: tuple[float, float],
    height: float,
    thickness: float,
    material: bpy.types.Material,
    parent: bpy.types.Object | None = None,
) -> bpy.types.Object:
    start_vec = Vector((start[0], 0.0, start[1]))
    end_vec = Vector((end[0], 0.0, end[1]))
    delta = end_vec - start_vec
    axes = [abs(delta.x), abs(delta.z)]
    if sum(value > 0.0001 for value in axes) != 1:
        raise ValueError(f"Wall {name} must be axis aligned")

    if axes[0] > 0:
        dims = (axes[0], height, thickness)
    else:
        dims = (thickness, height, axes[1])
    location = ((start_vec + end_vec) / 2).to_tuple()
    location = (location[0], height / 2, location[2])
    return _make_box(name, location=location, dimensions=dims, material=material, parent=parent)


def _make_disc_diffuser(
    name: str,
    *,
    location: tuple[float, float, float],
    material: bpy.types.Material,
    parent: bpy.types.Object | None = None,
) -> None:
    body = _make_cylinder(
        name,
        location=location,
        radius=0.16,
        depth=0.05,
        rotation=(0.0, 0.0, 0.0),
        material=material,
        parent=parent,
    )
    _make_cylinder(
        f"{name}.neck",
        location=(location[0], location[1] - 0.1, location[2]),
        radius=0.055,
        depth=0.18,
        rotation=(0.0, 0.0, 0.0),
        material=material,
        parent=body,
    )


def _make_linear_diffuser(
    name: str,
    *,
    location: tuple[float, float, float],
    length: float,
    material: bpy.types.Material,
    parent: bpy.types.Object | None = None,
) -> None:
    frame = _make_box(
        name,
        location=location,
        dimensions=(length, 0.03, 0.16),
        material=material,
        parent=parent,
    )
    for idx in range(4):
        _make_box(
            f"{name}.slot_{idx + 1}",
            location=(location[0] - length / 2 + 0.12 + idx * (length - 0.24) / 3, location[1] + 0.005, location[2]),
            dimensions=(0.06, 0.014, 0.13),
            material=material,
            parent=frame,
        )


def _make_hanger(
    name: str,
    *,
    location: tuple[float, float, float],
    span: float,
    material: bpy.types.Material,
    parent: bpy.types.Object | None = None,
) -> None:
    x_pos, y_pos, z_pos = location
    rod_top = PLAN["ceiling_y"] - 0.03
    for idx, offset in enumerate((-span / 2, span / 2), start=1):
        _make_round_segment(
            f"{name}.rod_{idx}",
            start=(x_pos + offset, rod_top, z_pos),
            end=(x_pos + offset, y_pos, z_pos),
            radius=0.012,
            material=material,
            parent=parent,
        )
    _make_box(
        f"{name}.strap",
        location=(x_pos, y_pos, z_pos),
        dimensions=(span + 0.12, 0.03, 0.04),
        material=material,
        parent=parent,
    )


def _make_damper_assembly(
    scene_node: str,
    *,
    location: tuple[float, float, float],
    orientation: str,
    materials: dict[str, bpy.types.Material],
    parent: bpy.types.Object | None = None,
) -> bpy.types.Object:
    root = _make_empty(scene_node, location=location, parent=parent)
    if orientation == "z":
        root.rotation_euler = _to_blender_rotation((0.0, math.radians(90), 0.0))

    _make_box(
        f"{scene_node}.frame",
        location=location,
        dimensions=(0.28, 0.18, 0.22),
        material=materials["damper_frame"],
        parent=root,
    )
    for idx, offset in enumerate((-0.065, 0.0, 0.065), start=1):
        blade = _make_box(
            f"{scene_node}.blade_{idx}",
            location=(location[0], location[1], location[2] + offset),
            dimensions=(0.18, 0.018, 0.045),
            material=materials["damper_blade"],
            parent=root,
        )
        blade.rotation_euler = _to_blender_rotation((0.0, 0.0, math.radians(-20)))
    lever = _make_box(
        f"{scene_node}.lever",
        location=(location[0] + 0.11, location[1] + 0.1, location[2] + 0.1),
        dimensions=(0.09, 0.02, 0.03),
        material=materials["accent"],
        parent=root,
    )
    lever.rotation_euler = _to_blender_rotation((0.0, math.radians(22), 0.0))
    return root


def _build_floor_and_walls(
    root: bpy.types.Object,
    *,
    floor_mat: bpy.types.Material,
    wall_mat: bpy.types.Material,
    glass_mat: bpy.types.Material,
    ceiling_mat: bpy.types.Material,
    outline_mat: bpy.types.Material,
) -> None:
    shell_root = _make_empty("building.shell", parent=root)
    _make_box(
        "building.floor",
        location=(0.0, -0.04, 0.0),
        dimensions=(PLAN["floor_x"], 0.08, PLAN["floor_z"]),
        material=floor_mat,
        parent=shell_root,
    )
    perimeter_specs = [
        ("building.outline.north", (-6.55, 0.01, 4.85), (6.45, 0.01, 4.85)),
        ("building.outline.south", (-6.55, 0.01, -4.85), (6.45, 0.01, -4.85)),
        ("building.outline.west", (-6.55, 0.01, -4.85), (-6.55, 0.01, 4.85)),
        ("building.outline.east", (6.45, 0.01, -4.85), (6.45, 0.01, 4.85)),
    ]
    for name, start, end in perimeter_specs:
        _make_axis_segment(
            name,
            start=start,
            end=end,
            width=0.09,
            height=0.03,
            material=outline_mat,
            parent=shell_root,
        )
    full_height = 1.75
    mid_height = 1.0
    low_height = 0.34
    wall_specs = [
        ("building.wall.outer_north", (-6.55, 4.85), (6.45, 4.85), full_height),
        ("building.wall.outer_west", (-6.55, -4.85), (-6.55, 4.85), low_height),
        ("building.wall.outer_east_upper", (6.45, 1.35), (6.45, 4.85), full_height),
        ("building.wall.outer_east_mid", (6.45, -0.55), (6.45, 1.35), mid_height),
        ("building.wall.bedroom_north_east", (-2.25, 0.75), (-2.25, 4.45), mid_height),
        ("building.wall.bedroom_south_east", (-2.25, -4.45), (-2.25, -0.85), mid_height),
        ("building.wall.central_split", (-2.25, -0.85), (0.85, -0.85), mid_height),
        ("building.wall.living_kitchen_split", (3.2, 1.15), (3.2, 4.45), mid_height),
        ("building.wall.utility_west", (1.65, 1.15), (1.65, 4.45), mid_height),
        ("building.wall.utility_south", (1.65, 1.15), (6.45, 1.15), mid_height),
        ("building.wall.corridor_top", (-2.25, 0.75), (1.65, 0.75), mid_height),
        ("building.wall.corridor_stub", (0.25, 0.75), (0.25, 2.4), mid_height),
        ("building.wall.study_west", (0.85, -4.45), (0.85, -1.0), mid_height),
        ("building.wall.study_top", (0.85, -1.0), (3.15, -1.0), mid_height),
        ("building.wall.bath_core", (1.65, 2.15), (3.2, 2.15), mid_height),
        ("building.wall.bath_vertical", (3.2, 1.15), (3.2, 2.15), mid_height),
    ]
    for name, start, end, height in wall_specs:
        _make_wall_segment(
            name,
            start=start,
            end=end,
            height=height,
            thickness=PLAN["wall_thickness"],
            material=wall_mat,
            parent=shell_root,
        )
        _make_axis_segment(
            f"{name}.trace",
            start=(start[0], 0.012, start[1]),
            end=(end[0], 0.012, end[1]),
            width=PLAN["wall_thickness"] + 0.012,
            height=0.02,
            material=outline_mat,
            parent=shell_root,
        )
        _make_axis_segment(
            f"{name}.cap",
            start=(start[0], height, start[1]),
            end=(end[0], height, end[1]),
            width=PLAN["wall_thickness"] + 0.02,
            height=0.03,
            material=outline_mat,
            parent=shell_root,
        )

    cutaway_specs = [
        ("building.wall.cutaway_east_lower", (6.45, -4.85), (6.45, -0.55)),
    ]
    for name, start, end in cutaway_specs:
        _make_wall_segment(
            name,
            start=start,
            end=end,
            height=0.14,
            thickness=PLAN["wall_thickness"],
            material=wall_mat,
            parent=shell_root,
        )
        _make_axis_segment(
            f"{name}.trace",
            start=(start[0], 0.012, start[1]),
            end=(end[0], 0.012, end[1]),
            width=PLAN["wall_thickness"] + 0.012,
            height=0.02,
            material=outline_mat,
            parent=shell_root,
        )
        _make_axis_segment(
            f"{name}.cap",
            start=(start[0], 0.14, start[1]),
            end=(end[0], 0.14, end[1]),
            width=PLAN["wall_thickness"] + 0.02,
            height=0.03,
            material=outline_mat,
            parent=shell_root,
        )

    window_specs = [
        ((-5.15, 1.45, 4.77), (1.25, 1.15, 0.03)),
        ((-4.7, 1.45, -4.77), (1.1, 1.1, 0.03)),
        ((4.55, 1.45, 4.77), (1.3, 1.15, 0.03)),
        ((5.92, 1.25, 0.05), (0.03, 1.0, 1.4)),
    ]
    for idx, (location, dims) in enumerate(window_specs, start=1):
        _make_box(
            f"building.window_{idx}",
            location=location,
            dimensions=dims,
            material=glass_mat,
            parent=shell_root,
        )


def _build_room_overlays(root: bpy.types.Object, room_mat: bpy.types.Material) -> None:
    room_root = _make_empty(SCENE_NODES["room"], location=(0.0, 0.03, 0.0), parent=root)
    room_specs = [
        ("zone.living", (-0.15, 0.025, 2.0), (5.8, 0.015, 3.6)),
        ("zone.bedroom_north", (-4.4, 0.025, 2.6), (3.8, 0.015, 3.3)),
        ("zone.bedroom_south", (-4.45, 0.025, -2.65), (3.7, 0.015, 3.0)),
        ("zone.study", (1.95, 0.025, -2.7), (2.1, 0.015, 2.8)),
        ("zone.kitchen", (4.7, 0.025, 2.95), (2.6, 0.015, 2.8)),
    ]
    for name, location, dims in room_specs:
        _make_box(name, location=location, dimensions=dims, material=room_mat, parent=room_root)


def _build_simple_furniture(
    root: bpy.types.Object,
    furniture_mat: bpy.types.Material,
    wood_mat: bpy.types.Material,
) -> None:
    furn_root = _make_empty("building.furniture", parent=root)
    _make_box(
        "living.sofa",
        location=(-2.35, 0.28, 1.6),
        dimensions=(1.8, 0.34, 0.9),
        material=furniture_mat,
        parent=furn_root,
    )
    _make_box(
        "living.table",
        location=(-0.85, 0.2, 2.25),
        dimensions=(0.9, 0.055, 0.55),
        material=wood_mat,
        parent=furn_root,
    )
    _make_box(
        "bedroom_north.bed",
        location=(-4.6, 0.21, 2.75),
        dimensions=(1.95, 0.24, 1.45),
        material=furniture_mat,
        parent=furn_root,
    )
    _make_box(
        "bedroom_south.bed",
        location=(-4.7, 0.2, -2.65),
        dimensions=(1.85, 0.22, 1.35),
        material=furniture_mat,
        parent=furn_root,
    )
    _make_box(
        "study.desk",
        location=(2.1, 0.24, -2.45),
        dimensions=(1.55, 0.06, 0.7),
        material=wood_mat,
        parent=furn_root,
    )
    _make_box(
        "kitchen.counter",
        location=(5.15, 0.42, 3.85),
        dimensions=(1.95, 0.8, 0.6),
        material=furniture_mat,
        parent=furn_root,
    )
    _make_box(
        "utility.cabinet",
        location=(5.4, 1.15, 1.0),
        dimensions=(0.7, 2.1, 0.45),
        material=furniture_mat,
        parent=furn_root,
    )


def _build_ahu(root: bpy.types.Object, materials: dict[str, bpy.types.Material]) -> dict[str, tuple[float, float, float]]:
    service_z = 0.95
    service_y = 0.98
    ahu_root = _make_empty("pvu.installation", parent=root)
    base_root = _make_empty("pvu.installation.base", parent=ahu_root)

    for idx, z_offset in enumerate((-0.75, 0.75), start=1):
        _make_box(
            f"pvu.base.rail_{idx}",
            location=(2.95, 0.16, service_z + z_offset),
            dimensions=(5.5, 0.07, 0.08),
            material=materials["frame"],
            parent=base_root,
        )
    for idx, x_pos in enumerate((0.45, 2.05, 3.65, 5.35), start=1):
        _make_box(
            f"pvu.base.leg_{idx}_a",
            location=(x_pos, 0.08, service_z - 0.75),
            dimensions=(0.08, 0.26, 0.08),
            material=materials["frame"],
            parent=base_root,
        )
        _make_box(
            f"pvu.base.leg_{idx}_b",
            location=(x_pos, 0.08, service_z + 0.75),
            dimensions=(0.08, 0.26, 0.08),
            material=materials["frame"],
            parent=base_root,
        )

    section_defs = [
        (SCENE_NODES["intake"], 5.1, 0.84),
        (SCENE_NODES["filter"], 4.15, 0.84),
        ("pvu.silencer.section", 3.2, 0.8),
        (SCENE_NODES["heater"], 2.25, 0.8),
        (SCENE_NODES["fan"], 1.2, 0.96),
        (SCENE_NODES["duct"], 0.2, 0.88),
    ]
    section_roots: dict[str, bpy.types.Object] = {}
    for node_name, x_pos, length in section_defs:
        root_obj = _make_empty(node_name, location=(x_pos, service_y, service_z), parent=ahu_root)
        section_roots[node_name] = root_obj
        shell_height = 1.5 if node_name == SCENE_NODES["fan"] else 1.38
        shell_width = 1.46 if node_name == SCENE_NODES["fan"] else 1.3
        _make_box(
            f"{node_name}.shell",
            location=(x_pos, service_y - 0.08, service_z),
            dimensions=(length, shell_height, shell_width),
            material=materials["casing"],
            parent=root_obj,
        )
        _make_box(
            f"{node_name}.door",
            location=(x_pos, service_y - 0.08, service_z + shell_width / 2 - 0.03),
            dimensions=(length * 0.82, shell_height * 0.78, 0.045),
            material=materials["panel"],
            parent=root_obj,
        )
        _make_cylinder(
            f"{node_name}.handle",
            location=(x_pos + 0.18, service_y - 0.08, service_z + shell_width / 2 - 0.01),
            radius=0.018,
            depth=0.08,
            rotation=(math.radians(90), 0.0, 0.0),
            material=materials["frame"],
            parent=root_obj,
        )

    intake_root = section_roots[SCENE_NODES["intake"]]
    filter_root = section_roots[SCENE_NODES["filter"]]
    silencer_root = section_roots["pvu.silencer.section"]
    heater_root = section_roots[SCENE_NODES["heater"]]
    fan_root = section_roots[SCENE_NODES["fan"]]
    plenum_root = section_roots[SCENE_NODES["duct"]]

    _make_box(
        "pvu.intake.weather_hood",
        location=(5.95, service_y - 0.02, service_z),
        dimensions=(0.46, 1.18, 1.12),
        material=materials["frame"],
        parent=intake_root,
    )
    for idx, offset in enumerate((-0.34, -0.17, 0.0, 0.17, 0.34), start=1):
        louver = _make_box(
            f"pvu.intake.louver_{idx}",
            location=(5.72, service_y + 0.02, service_z + offset),
            dimensions=(0.08, 0.08, 0.54),
            material=materials["frame"],
            parent=intake_root,
        )
        louver.rotation_euler = _to_blender_rotation((0.0, math.radians(12), 0.0))
    _make_axis_segment(
        "pvu.intake.transition",
        start=(5.7, service_y + 0.02, service_z),
        end=(5.42, service_y + 0.02, service_z),
        width=0.74,
        height=0.72,
        material=materials["frame"],
        parent=intake_root,
    )
    _make_damper_assembly(
        SCENE_NODES["damper_intake"],
        location=(5.42, service_y + 0.04, service_z),
        orientation="x",
        materials=materials,
        parent=intake_root,
    )

    _make_box(
        "pvu.filter.frame",
        location=(4.15, service_y - 0.04, service_z),
        dimensions=(0.66, 1.04, 0.09),
        material=materials["frame"],
        parent=filter_root,
    )
    for idx in range(6):
        fin = _make_box(
            f"pvu.filter.media_{idx + 1}",
            location=(4.15, 0.46 + idx * 0.16, service_z),
            dimensions=(0.58, 0.05, 0.98),
            material=materials["filter"],
            parent=filter_root,
        )
        fin.rotation_euler = _to_blender_rotation((0.0, 0.0, math.radians(8)))

    for idx in range(4):
        _make_box(
            f"pvu.silencer.baffle_{idx + 1}",
            location=(3.2, 0.46 + idx * 0.25, service_z),
            dimensions=(0.56, 0.08, 1.02),
            material=materials["silencer"],
            parent=silencer_root,
        )

    _make_box(
        "pvu.heater.frame",
        location=(2.25, service_y - 0.04, service_z),
        dimensions=(0.6, 1.0, 0.09),
        material=materials["frame"],
        parent=heater_root,
    )
    for idx in range(10):
        _make_box(
            f"pvu.heater.fin_{idx + 1}",
            location=(2.25, 0.36 + idx * 0.12, service_z),
            dimensions=(0.5, 0.028, 0.98),
            material=materials["heater"],
            parent=heater_root,
        )
    for label, z_pos in (("supply", service_z + 0.48), ("return", service_z - 0.48)):
        _make_cylinder(
            f"pvu.heater.pipe_{label}",
            location=(2.62, 1.12, z_pos),
            radius=0.03,
            depth=0.56,
            rotation=(math.radians(90), 0.0, 0.0),
            material=materials["heater"],
            parent=heater_root,
        )

    rotor_root = _make_empty(SCENE_NODES["fan_rotor"], location=(1.2, service_y, service_z), parent=fan_root)
    _make_cylinder(
        "pvu.fan.scroll_housing",
        location=(1.2, service_y, service_z),
        radius=0.48,
        depth=0.72,
        rotation=(math.radians(90), 0.0, 0.0),
        material=materials["frame"],
        parent=fan_root,
    )
    _make_cylinder(
        "pvu.fan.inlet",
        location=(1.42, service_y, service_z),
        radius=0.22,
        depth=0.16,
        rotation=(math.radians(90), 0.0, 0.0),
        material=materials["casing"],
        parent=fan_root,
    )
    _make_cylinder(
        "pvu.fan.hub",
        location=(1.2, service_y, service_z),
        radius=0.1,
        depth=0.22,
        rotation=(math.radians(90), 0.0, 0.0),
        material=materials["fan"],
        parent=rotor_root,
    )
    for idx in range(8):
        blade = _make_box(
            f"pvu.fan.blade_{idx + 1}",
            location=(1.2, service_y, service_z + 0.23),
            dimensions=(0.46, 0.045, 0.11),
            material=materials["fan"],
            parent=rotor_root,
        )
        blade.rotation_euler = _to_blender_rotation((math.radians(10), 0.0, math.radians(idx * 45)))
    rotor_root.rotation_euler = _to_blender_rotation((math.radians(90), 0.0, 0.0))

    _make_axis_segment(
        "pvu.plenum.transition",
        start=(0.58, service_y + 0.02, service_z),
        end=(0.0, service_y + 0.02, service_z),
        width=0.7,
        height=0.68,
        material=materials["frame"],
        parent=plenum_root,
    )
    _make_box(
        "pvu.duct.supply.status_shell",
        location=(0.2, service_y - 0.08, service_z),
        dimensions=(0.88, 1.1, 1.1),
        material=materials["status_shell"],
        parent=plenum_root,
    )

    flow_outdoor_root = _make_empty(SCENE_NODES["flow_outdoor_to_filter"], location=(4.75, service_y, service_z), parent=ahu_root)
    _make_axis_segment(
        "flow.outdoor.segment_1",
        start=(5.96, service_y + 0.02, service_z),
        end=(5.38, service_y + 0.02, service_z),
        width=0.42,
        height=0.42,
        material=materials["flow_cool"],
        parent=flow_outdoor_root,
    )
    _make_axis_segment(
        "flow.outdoor.segment_2",
        start=(5.38, service_y + 0.02, service_z),
        end=(4.48, service_y + 0.02, service_z),
        width=0.36,
        height=0.36,
        material=materials["flow_cool"],
        parent=flow_outdoor_root,
    )

    flow_filter_root = _make_empty(SCENE_NODES["flow_filter_to_heater"], location=(3.25, service_y, service_z), parent=ahu_root)
    _make_axis_segment(
        "flow.filter.segment_1",
        start=(3.84, service_y, service_z),
        end=(2.78, service_y, service_z),
        width=0.32,
        height=0.32,
        material=materials["flow_neutral"],
        parent=flow_filter_root,
    )

    flow_heater_root = _make_empty(SCENE_NODES["flow_heater_to_fan"], location=(1.72, service_y, service_z), parent=ahu_root)
    _make_axis_segment(
        "flow.heater.segment",
        start=(2.05, service_y, service_z),
        end=(1.52, service_y, service_z),
        width=0.32,
        height=0.32,
        material=materials["flow_warm"],
        parent=flow_heater_root,
    )

    _make_round_segment(
        "building.outdoor.intake_stack",
        start=(6.22, 0.28, service_z),
        end=(6.22, 2.45, service_z),
        radius=0.14,
        material=materials["frame"],
        parent=ahu_root,
    )
    _make_round_segment(
        "building.outdoor.exhaust_stack",
        start=(5.8, 0.28, service_z + 0.72),
        end=(5.8, 2.45, service_z + 0.72),
        radius=0.13,
        material=materials["frame"],
        parent=ahu_root,
    )

    return {
        "supply_outlet": (-0.18, PLAN["duct_y"], service_z),
        "main_trunk_z": service_z,
    }


def _build_internal_flows(root: bpy.types.Object, flow_mats: dict[str, bpy.types.Material]) -> None:
    # Internal AHU flow sections are now built together with the AHU itself.
    del root
    del flow_mats


def _build_supply_network(
    root: bpy.types.Object,
    materials: dict[str, bpy.types.Material],
    *,
    start: tuple[float, float, float],
    trunk_z: float,
) -> None:
    physical_root = _make_empty("building.systems.supply_network", parent=root)
    flow_root = _make_empty(SCENE_NODES["flow_fan_to_room"], location=start, parent=root)
    plume_root = _make_empty(SCENE_NODES["room_plumes"], location=start, parent=flow_root)

    duct_segments = [
        ("duct.main_01", start, (-1.2, PLAN["duct_y"], trunk_z), 0.34, 0.24),
        ("duct.main_02", (-1.2, PLAN["duct_y"], trunk_z), (-4.95, PLAN["duct_y"], trunk_z), 0.34, 0.24),
        ("duct.branch_kitchen_rise", (0.35, PLAN["duct_y"], trunk_z), (0.35, PLAN["duct_y"], 3.2), 0.28, 0.22),
        ("duct.branch_kitchen_run", (0.35, PLAN["duct_y"], 3.2), (4.45, PLAN["duct_y"], 3.2), 0.28, 0.22),
        ("duct.branch_living_rise", (-1.55, PLAN["duct_y"], trunk_z), (-1.55, PLAN["duct_y"], 2.55), 0.28, 0.22),
        ("duct.branch_living_run", (-1.55, PLAN["duct_y"], 2.55), (-3.45, PLAN["duct_y"], 2.55), 0.28, 0.22),
        ("duct.branch_bed_north", (-4.35, PLAN["duct_y"], trunk_z), (-4.35, PLAN["duct_y"], 3.55), 0.26, 0.2),
        ("duct.branch_bed_south_rise", (-3.15, PLAN["duct_y"], trunk_z), (-3.15, PLAN["duct_y"], -2.95), 0.26, 0.2),
        ("duct.branch_bed_south_run", (-3.15, PLAN["duct_y"], -2.95), (-4.5, PLAN["duct_y"], -2.95), 0.26, 0.2),
        ("duct.branch_study_rise", (-0.35, PLAN["duct_y"], trunk_z), (-0.35, PLAN["duct_y"], -2.15), 0.24, 0.18),
        ("duct.branch_study_run", (-0.35, PLAN["duct_y"], -2.15), (1.65, PLAN["duct_y"], -2.15), 0.24, 0.18),
    ]
    for name, seg_start, seg_end, width, height in duct_segments:
        _make_axis_segment(
            name,
            start=seg_start,
            end=seg_end,
            width=width,
            height=height,
            material=materials["duct_supply"],
            parent=physical_root,
        )

    flow_segments = [
        ("flow.supply.main_01", start, (-1.2, PLAN["duct_y"], trunk_z), 0.12, 0.12),
        ("flow.supply.main_02", (-1.2, PLAN["duct_y"], trunk_z), (-4.95, PLAN["duct_y"], trunk_z), 0.12, 0.12),
        ("flow.supply.kitchen_rise", (0.35, PLAN["duct_y"], trunk_z), (0.35, PLAN["duct_y"], 3.2), 0.1, 0.1),
        ("flow.supply.kitchen_run", (0.35, PLAN["duct_y"], 3.2), (4.45, PLAN["duct_y"], 3.2), 0.1, 0.1),
        ("flow.supply.living_rise", (-1.55, PLAN["duct_y"], trunk_z), (-1.55, PLAN["duct_y"], 2.55), 0.1, 0.1),
        ("flow.supply.living_run", (-1.55, PLAN["duct_y"], 2.55), (-3.45, PLAN["duct_y"], 2.55), 0.1, 0.1),
        ("flow.supply.bed_north", (-4.35, PLAN["duct_y"], trunk_z), (-4.35, PLAN["duct_y"], 3.55), 0.1, 0.1),
        ("flow.supply.bed_south_rise", (-3.15, PLAN["duct_y"], trunk_z), (-3.15, PLAN["duct_y"], -2.95), 0.1, 0.1),
        ("flow.supply.bed_south_run", (-3.15, PLAN["duct_y"], -2.95), (-4.5, PLAN["duct_y"], -2.95), 0.1, 0.1),
        ("flow.supply.study_rise", (-0.35, PLAN["duct_y"], trunk_z), (-0.35, PLAN["duct_y"], -2.15), 0.09, 0.09),
        ("flow.supply.study_run", (-0.35, PLAN["duct_y"], -2.15), (1.65, PLAN["duct_y"], -2.15), 0.09, 0.09),
    ]
    for name, seg_start, seg_end, width, height in flow_segments:
        _make_axis_segment(
            name,
            start=seg_start,
            end=seg_end,
            width=width,
            height=height,
            material=materials["flow_supply"],
            parent=flow_root,
        )

    diffuser_specs = [
        ("living_a", (-3.45, PLAN["ceiling_neck_y"], 2.55), "linear"),
        ("living_b", (-1.85, PLAN["ceiling_neck_y"], 2.1), "disc"),
        ("bed_north", (-4.35, PLAN["ceiling_neck_y"], 3.45), "disc"),
        ("bed_south", (-4.5, PLAN["ceiling_neck_y"], -2.95), "disc"),
        ("study", (1.65, PLAN["ceiling_neck_y"], -2.15), "disc"),
        ("kitchen", (4.45, PLAN["ceiling_neck_y"], 3.2), "linear"),
    ]
    for name, location, diffuser_type in diffuser_specs:
        _make_axis_segment(
            f"duct.neck_{name}",
            start=(location[0], PLAN["duct_y"], location[2]),
            end=(location[0], location[1], location[2]),
            width=0.15,
            height=0.22,
            material=materials["duct_supply"],
            parent=physical_root,
        )
        if diffuser_type == "linear":
            _make_linear_diffuser(
                f"duct.diffuser_{name}",
                location=(location[0], location[1] + 0.015, location[2]),
                length=0.38,
                material=materials["diffuser"],
                parent=physical_root,
            )
        else:
            _make_disc_diffuser(
                f"duct.diffuser_{name}",
                location=(location[0], location[1] + 0.04, location[2]),
                material=materials["diffuser"],
                parent=physical_root,
            )

    plume_specs = [
        ("living_a", (-3.45, 1.42, 2.55), 0.14, 0.64),
        ("living_b", (-1.85, 1.34, 2.1), 0.13, 0.58),
        ("bed_north", (-4.35, 1.4, 3.45), 0.13, 0.6),
        ("bed_south", (-4.5, 1.34, -2.95), 0.13, 0.58),
        ("study", (1.65, 1.28, -2.15), 0.12, 0.54),
        ("kitchen", (4.45, 1.44, 3.2), 0.14, 0.6),
    ]
    for name, location, radius, depth in plume_specs:
        plume = _make_cylinder(
            f"flow.plume_{name}",
            location=location,
            radius=radius,
            depth=depth,
            material=materials["flow_plume"],
            parent=plume_root,
        )
        plume.scale = (0.72, 1.0, 1.18)
        _make_cylinder(
            f"flow.plume_{name}.cap",
            location=(location[0], location[1] + depth / 2, location[2]),
            radius=radius * 0.56,
            depth=0.1,
            material=materials["flow_plume"],
            parent=plume_root,
        )

    damper_specs = [
        (SCENE_NODES["damper_kitchen"], (0.35, PLAN["duct_y"], 1.55), "z"),
        (SCENE_NODES["damper_living"], (-1.55, PLAN["duct_y"], 1.45), "z"),
        (SCENE_NODES["damper_bedroom_north"], (-4.35, PLAN["duct_y"], 2.0), "z"),
        (SCENE_NODES["damper_bedroom_south"], (-3.15, PLAN["duct_y"], -1.15), "z"),
        (SCENE_NODES["damper_study"], (-0.35, PLAN["duct_y"], -0.9), "z"),
    ]
    for scene_node, location, orientation in damper_specs:
        _make_damper_assembly(
            scene_node,
            location=location,
            orientation=orientation,
            materials=materials,
            parent=physical_root,
        )

    # Dedicated hangers are omitted in the default cutaway presentation.


def _build_extract_context(root: bpy.types.Object, materials: dict[str, bpy.types.Material]) -> None:
    physical_root = _make_empty("building.systems.extract_network", parent=root)
    flow_root = _make_empty(SCENE_NODES["extract_context"], location=(0.0, PLAN["duct_y"], 0.0), parent=root)

    extract_segments = [
        ("extract.main_vertical", (5.4, 0.28, 1.9), (5.4, PLAN["duct_y"], 1.9), 0.1),
        ("extract.kitchen_run", (4.75, PLAN["duct_y"], 3.55), (5.4, PLAN["duct_y"], 3.55), 0.095),
        ("extract.kitchen_drop", (5.4, PLAN["duct_y"], 3.55), (5.4, PLAN["duct_y"], 1.9), 0.095),
        ("extract.bath_run", (2.55, PLAN["duct_y"], 2.35), (5.4, PLAN["duct_y"], 2.35), 0.085),
        ("extract.wc_drop", (3.8, PLAN["duct_y"], 1.45), (5.4, PLAN["duct_y"], 1.45), 0.08),
    ]
    for name, seg_start, seg_end, radius in extract_segments:
        _make_round_segment(
            name,
            start=seg_start,
            end=seg_end,
            radius=radius,
            material=materials["duct_extract"],
            parent=physical_root,
        )
        _make_round_segment(
            f"{name}.flow",
            start=seg_start,
            end=seg_end,
            radius=max(radius - 0.03, 0.03),
            material=materials["flow_extract"],
            parent=flow_root,
        )

    grille_specs = [
        ("kitchen", (4.75, PLAN["ceiling_neck_y"], 3.55)),
        ("bath", (2.55, PLAN["ceiling_neck_y"], 2.35)),
        ("wc", (3.8, PLAN["ceiling_neck_y"], 1.45)),
    ]
    for name, location in grille_specs:
        _make_axis_segment(
            f"extract.neck_{name}",
            start=(location[0], PLAN["duct_y"], location[2]),
            end=(location[0], location[1], location[2]),
            width=0.12,
            height=0.18,
            material=materials["duct_extract"],
            parent=physical_root,
        )
        _make_linear_diffuser(
            f"extract.grille_{name}",
            location=(location[0], location[1] + 0.015, location[2]),
            length=0.26,
            material=materials["diffuser_dark"],
            parent=physical_root,
        )
        _make_cylinder(
            f"extract.plume_{name}",
            location=(location[0], 1.38, location[2]),
            radius=0.12,
            depth=0.7,
            material=materials["flow_extract_plume"],
            parent=flow_root,
        )


def _build_sensors(root: bpy.types.Object, sensor_mat: bpy.types.Material, label_mat: bpy.types.Material) -> None:
    sensor_specs = [
        (SCENE_NODES["sensor_outdoor"], (6.15, 1.95, 0.95), (6.15, 1.58, 0.95)),
        (SCENE_NODES["sensor_filter"], (4.2, 1.82, 1.5), (4.2, 1.38, 1.5)),
        (SCENE_NODES["sensor_supply"], (-0.3, PLAN["duct_y"] + 0.32, 1.2), (-0.3, PLAN["duct_y"], 1.2)),
        (SCENE_NODES["sensor_airflow"], (-2.4, PLAN["duct_y"] + 0.32, 1.2), (-2.4, PLAN["duct_y"], 1.2)),
        (SCENE_NODES["sensor_room"], (-0.6, 1.7, 1.6), (-0.6, 1.2, 1.6)),
    ]
    for name, location, anchor in sensor_specs:
        sensor_root = _make_empty(name, location=location, parent=root)
        _make_round_segment(
            f"{name}.stem",
            start=anchor,
            end=location,
            radius=0.014,
            material=label_mat,
            parent=sensor_root,
        )
        _make_uv_sphere(
            f"{name}.probe",
            location=location,
            radius=0.085,
            material=sensor_mat,
            parent=sensor_root,
        )
        _make_cylinder(
            f"{name}.ring",
            location=location,
            radius=0.13,
            depth=0.012,
            rotation=(math.radians(90), 0.0, 0.0),
            material=label_mat,
            parent=sensor_root,
        )
        _make_box(
            f"{name}.tag",
            location=(location[0], location[1] + 0.12, location[2]),
            dimensions=(0.06, 0.018, 0.18),
            material=label_mat,
            parent=sensor_root,
        )


def _add_camera_and_lights(root: bpy.types.Object, accent_mat: bpy.types.Material) -> None:
    bpy.ops.object.light_add(type="SUN", location=_to_blender_location((2.0, 10.0, 3.0)))
    sun = bpy.context.active_object
    sun.name = "SceneSun"
    sun.data.energy = 1.6
    sun.rotation_euler = _to_blender_rotation((math.radians(48), 0.0, math.radians(24)))
    sun.parent = root

    bpy.ops.object.light_add(type="AREA", location=_to_blender_location((1.5, 6.5, -5.2)))
    area = bpy.context.active_object
    area.name = "SceneFill"
    area.data.energy = 2400
    area.data.shape = "RECTANGLE"
    area.data.size = 9.0
    area.data.size_y = 5.5
    area.rotation_euler = _to_blender_rotation((math.radians(68), 0.0, math.radians(28)))
    area.parent = root

    bpy.ops.object.light_add(type="POINT", location=_to_blender_location((5.6, 2.9, 2.6)))
    point = bpy.context.active_object
    point.name = "SceneAccent"
    point.data.energy = 280
    point.data.color = accent_mat.diffuse_color[:3]
    point.parent = root

    bpy.ops.object.camera_add(location=_to_blender_location((7.9, 8.7, -7.4)))
    camera = bpy.context.active_object
    camera.name = "OverviewCamera"
    camera.data.lens = 24
    _look_at(camera, (-0.9, 1.65, 0.9))
    bpy.context.scene.camera = camera
    camera.parent = root


def _render_preview(output_preview: Path) -> None:
    output_preview.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    available = {item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items}
    if "BLENDER_EEVEE_NEXT" in available:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    elif "BLENDER_EEVEE" in available:
        scene.render.engine = "BLENDER_EEVEE"
    else:
        scene.render.engine = "BLENDER_WORKBENCH"
    if hasattr(scene, "eevee"):
        eevee = scene.eevee
        if hasattr(eevee, "taa_render_samples"):
            eevee.taa_render_samples = 48
        if hasattr(eevee, "use_gtao"):
            eevee.use_gtao = True
        if hasattr(eevee, "use_bloom"):
            eevee.use_bloom = True
    scene.render.resolution_x = 1680
    scene.render.resolution_y = 1020
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output_preview)
    bpy.ops.render.render(write_still=True)


def _export_assets(output_glb: Path, output_blend: Path, output_preview: Path) -> None:
    output_glb.parent.mkdir(parents=True, exist_ok=True)
    output_blend.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(output_blend))
    _render_preview(output_preview)
    bpy.ops.export_scene.gltf(
        filepath=str(output_glb),
        export_format="GLB",
        use_selection=False,
        export_yup=True,
        export_apply=False,
        export_texcoords=True,
        export_normals=True,
        export_materials="EXPORT",
        export_animations=False,
    )

    root = _project_root()
    ui_asset = root / "src" / "app" / "ui" / "assets" / "pvu_installation.glb"
    if output_glb.resolve() != ui_asset.resolve():
        ui_asset.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output_glb, ui_asset)


def build_scene(output_glb: Path, output_blend: Path, output_preview: Path) -> None:
    _clear_scene()
    _set_scene_units()

    materials = {
        "floor": _new_material("Floor", (0.9, 0.92, 0.94, 1.0), metallic=0.0, roughness=0.97),
        "wall": _new_material("Wall", (0.94, 0.95, 0.97, 0.08), metallic=0.0, roughness=0.88, alpha_blend=True),
        "glass": _new_material("Glass", (0.72, 0.84, 0.92, 0.16), metallic=0.0, roughness=0.06, transmission=0.18, alpha_blend=True),
        "ceiling": _new_material("CeilingCutaway", (0.93, 0.95, 0.98, 0.08), metallic=0.0, roughness=0.94, alpha_blend=True),
        "outline": _new_material("Outline", (0.62, 0.69, 0.76, 0.96), metallic=0.0, roughness=0.72),
        "room": _new_material("RoomOverlay", (0.58, 0.72, 0.84, 0.06), metallic=0.0, roughness=0.62, alpha_blend=True),
        "furniture": _new_material("Furniture", (0.8, 0.82, 0.84, 0.46), metallic=0.02, roughness=0.9, alpha_blend=True),
        "wood": _new_material("Wood", (0.76, 0.67, 0.55, 0.42), metallic=0.0, roughness=0.78, alpha_blend=True),
        "casing": _new_material("AHUCasing", (0.84, 0.86, 0.9, 0.18), metallic=0.16, roughness=0.34, alpha_blend=True),
        "panel": _new_material("AHUPanel", (0.95, 0.96, 0.98, 0.22), metallic=0.1, roughness=0.26, alpha_blend=True),
        "status_shell": _new_material("StatusShell", (0.78, 0.84, 0.9, 0.1), metallic=0.06, roughness=0.32, alpha_blend=True),
        "frame": _new_material("FrameMetal", (0.24, 0.28, 0.33, 1.0), metallic=0.66, roughness=0.34),
        "filter": _new_material("FilterMedia", (0.58, 0.72, 0.64, 1.0), metallic=0.02, roughness=0.86),
        "heater": _new_material("HeaterCoil", (0.88, 0.43, 0.22, 1.0), metallic=0.18, roughness=0.54),
        "silencer": _new_material("SilencerBaffle", (0.62, 0.66, 0.72, 1.0), metallic=0.16, roughness=0.62),
        "fan": _new_material("FanMetal", (0.34, 0.52, 0.64, 1.0), metallic=0.42, roughness=0.3),
        "duct_supply": _new_material("SupplyDuct", (0.79, 0.24, 0.18, 1.0), metallic=0.22, roughness=0.46),
        "duct_extract": _new_material("ExtractDuct", (0.22, 0.48, 0.86, 1.0), metallic=0.22, roughness=0.48),
        "diffuser": _new_material("Diffuser", (0.96, 0.97, 0.98, 1.0), metallic=0.04, roughness=0.24),
        "diffuser_dark": _new_material("DiffuserDark", (0.74, 0.78, 0.84, 1.0), metallic=0.06, roughness=0.3),
        "damper_frame": _new_material("DamperFrame", (0.3, 0.34, 0.38, 1.0), metallic=0.45, roughness=0.38),
        "damper_blade": _new_material("DamperBlade", (0.63, 0.68, 0.74, 1.0), metallic=0.22, roughness=0.5),
        "accent": _new_material(
            "AccentOrange",
            (0.94, 0.54, 0.22, 1.0),
            metallic=0.04,
            roughness=0.4,
            emission=(0.58, 0.22, 0.06, 1.0),
            emission_strength=0.4,
        ),
        "flow_cool": _new_material("FlowCool", (0.2, 0.72, 0.98, 0.4), metallic=0.0, roughness=0.08, transmission=0.04, alpha_blend=True),
        "flow_neutral": _new_material("FlowNeutral", (0.5, 0.86, 0.64, 0.34), metallic=0.0, roughness=0.08, transmission=0.04, alpha_blend=True),
        "flow_warm": _new_material("FlowWarm", (0.99, 0.64, 0.26, 0.42), metallic=0.0, roughness=0.08, transmission=0.05, alpha_blend=True),
        "flow_supply": _new_material("FlowSupply", (0.98, 0.38, 0.18, 0.46), metallic=0.0, roughness=0.1, transmission=0.05, alpha_blend=True),
        "flow_plume": _new_material("FlowPlume", (0.98, 0.52, 0.46, 0.18), metallic=0.0, roughness=0.12, transmission=0.06, alpha_blend=True),
        "flow_extract": _new_material("FlowExtract", (0.22, 0.62, 0.98, 0.36), metallic=0.0, roughness=0.1, transmission=0.04, alpha_blend=True),
        "flow_extract_plume": _new_material("FlowExtractPlume", (0.48, 0.78, 0.98, 0.16), metallic=0.0, roughness=0.12, transmission=0.05, alpha_blend=True),
        "sensor": _new_material(
            "SensorGlow",
            (0.18, 0.73, 0.95, 1.0),
            metallic=0.14,
            roughness=0.24,
            emission=(0.14, 0.53, 0.88, 1.0),
            emission_strength=2.0,
        ),
        "sensor_tag": _new_material(
            "SensorTag",
            (0.14, 0.42, 0.66, 1.0),
            metallic=0.05,
            roughness=0.44,
            emission=(0.08, 0.25, 0.46, 1.0),
            emission_strength=0.7,
        ),
    }

    root = bpy.data.objects.new("SceneRoot", None)
    bpy.context.scene.collection.objects.link(root)

    _build_floor_and_walls(
        root,
        floor_mat=materials["floor"],
        wall_mat=materials["wall"],
        glass_mat=materials["glass"],
        ceiling_mat=materials["ceiling"],
        outline_mat=materials["outline"],
    )
    _build_room_overlays(root, materials["room"])
    ahu_info = _build_ahu(root, materials)
    _build_supply_network(
        root,
        materials,
        start=ahu_info["supply_outlet"],
        trunk_z=ahu_info["main_trunk_z"],
    )
    _build_extract_context(root, materials)
    _build_sensors(root, materials["sensor"], materials["sensor_tag"])
    _add_camera_and_lights(root, materials["sensor"])
    _export_assets(output_glb, output_blend, output_preview)


if __name__ == "__main__":
    out_glb, out_blend, out_preview = _parse_args()
    build_scene(out_glb, out_blend, out_preview)
    print(f"Saved Blender scene to: {out_blend}")
    print(f"Saved preview image to: {out_preview}")
    print(f"Exported GLB to: {out_glb}")
