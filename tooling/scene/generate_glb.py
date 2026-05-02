"""Generate a procedural GLB model of the PVU installation.

Node names in the GLB match scene_node IDs from data/visualization/scene3d.json.
This script is run once to produce the asset; it is NOT part of the runtime.
"""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path

import numpy as np
import pygltflib


def _box_mesh(sx: float, sy: float, sz: float):
    """Return vertices, normals, indices for an axis-aligned box centered at origin."""
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    # 24 vertices (4 per face), 36 indices
    positions = []
    normals = []
    indices = []

    faces = [
        # (normal, corners)
        ([0, 0, 1], [(-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]),
        ([0, 0, -1], [(hx, -hy, -hz), (-hx, -hy, -hz), (-hx, hy, -hz), (hx, hy, -hz)]),
        ([0, 1, 0], [(-hx, hy, hz), (hx, hy, hz), (hx, hy, -hz), (-hx, hy, -hz)]),
        ([0, -1, 0], [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz)]),
        ([1, 0, 0], [(hx, -hy, hz), (hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz)]),
        ([-1, 0, 0], [(-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz)]),
    ]
    for n, corners in faces:
        base = len(positions)
        for c in corners:
            positions.append(c)
            normals.append(n)
        indices.extend([base, base + 1, base + 2, base, base + 2, base + 3])

    return (
        np.array(positions, dtype=np.float32),
        np.array(normals, dtype=np.float32),
        np.array(indices, dtype=np.uint16),
    )


def _cylinder_mesh(radius: float, height: float, segments: int = 16):
    """Return vertices, normals, indices for a Y-axis cylinder centered at origin."""
    positions = []
    normals_list = []
    indices = []
    hy = height / 2

    # Side
    for i in range(segments + 1):
        theta = 2 * math.pi * i / segments
        x = radius * math.cos(theta)
        z = radius * math.sin(theta)
        nx = math.cos(theta)
        nz = math.sin(theta)
        positions.append((x, -hy, z))
        normals_list.append((nx, 0, nz))
        positions.append((x, hy, z))
        normals_list.append((nx, 0, nz))

    for i in range(segments):
        b = i * 2
        indices.extend([b, b + 1, b + 3, b, b + 3, b + 2])

    # Top cap
    top_center = len(positions)
    positions.append((0, hy, 0))
    normals_list.append((0, 1, 0))
    for i in range(segments):
        theta = 2 * math.pi * i / segments
        positions.append((radius * math.cos(theta), hy, radius * math.sin(theta)))
        normals_list.append((0, 1, 0))
    for i in range(segments):
        indices.extend([top_center, top_center + 1 + i, top_center + 1 + (i + 1) % segments])

    # Bottom cap
    bot_center = len(positions)
    positions.append((0, -hy, 0))
    normals_list.append((0, -1, 0))
    for i in range(segments):
        theta = 2 * math.pi * i / segments
        positions.append((radius * math.cos(theta), -hy, radius * math.sin(theta)))
        normals_list.append((0, -1, 0))
    for i in range(segments):
        indices.extend([bot_center, bot_center + 1 + (i + 1) % segments, bot_center + 1 + i])

    return (
        np.array(positions, dtype=np.float32),
        np.array(normals_list, dtype=np.float32),
        np.array(indices, dtype=np.uint16),
    )


def _add_mesh_to_gltf(
    gltf: pygltflib.GLTF2,
    buffers_data: bytearray,
    positions: np.ndarray,
    normals: np.ndarray,
    indices: np.ndarray,
    material_index: int,
) -> int:
    """Add mesh data to gltf, return mesh index."""
    pos_bytes = positions.tobytes()
    norm_bytes = normals.tobytes()
    idx_bytes = indices.tobytes()

    pos_offset = len(buffers_data)
    buffers_data.extend(pos_bytes)
    norm_offset = len(buffers_data)
    buffers_data.extend(norm_bytes)
    idx_offset = len(buffers_data)
    buffers_data.extend(idx_bytes)

    pos_bv = len(gltf.bufferViews)
    gltf.bufferViews.append(pygltflib.BufferView(
        buffer=0, byteOffset=pos_offset, byteLength=len(pos_bytes), target=34962,
    ))
    norm_bv = len(gltf.bufferViews)
    gltf.bufferViews.append(pygltflib.BufferView(
        buffer=0, byteOffset=norm_offset, byteLength=len(norm_bytes), target=34962,
    ))
    idx_bv = len(gltf.bufferViews)
    gltf.bufferViews.append(pygltflib.BufferView(
        buffer=0, byteOffset=idx_offset, byteLength=len(idx_bytes), target=34963,
    ))

    pos_min = positions.min(axis=0).tolist()
    pos_max = positions.max(axis=0).tolist()

    pos_acc = len(gltf.accessors)
    gltf.accessors.append(pygltflib.Accessor(
        bufferView=pos_bv, componentType=5126, count=len(positions),
        type="VEC3", max=pos_max, min=pos_min,
    ))
    norm_acc = len(gltf.accessors)
    gltf.accessors.append(pygltflib.Accessor(
        bufferView=norm_bv, componentType=5126, count=len(normals), type="VEC3",
    ))
    idx_acc = len(gltf.accessors)
    gltf.accessors.append(pygltflib.Accessor(
        bufferView=idx_bv, componentType=5123, count=len(indices), type="SCALAR",
    ))

    mesh_idx = len(gltf.meshes)
    gltf.meshes.append(pygltflib.Mesh(
        primitives=[pygltflib.Primitive(
            attributes=pygltflib.Attributes(POSITION=pos_acc, NORMAL=norm_acc),
            indices=idx_acc,
            material=material_index,
        )],
    ))
    return mesh_idx


def _add_material(
    gltf: pygltflib.GLTF2,
    name: str,
    color: tuple[float, float, float],
    metallic: float = 0.1,
    roughness: float = 0.7,
) -> int:
    idx = len(gltf.materials)
    gltf.materials.append(pygltflib.Material(
        name=name,
        pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
            baseColorFactor=[*color, 1.0],
            metallicFactor=metallic,
            roughnessFactor=roughness,
        ),
    ))
    return idx


def build_pvu_glb(output_path: Path) -> None:
    gltf = pygltflib.GLTF2(
        asset=pygltflib.Asset(version="2.0", generator="pvu_diploma_project"),
        scene=0,
    )
    gltf.scenes = [pygltflib.Scene(name="PVU", nodes=[])]
    gltf.buffers = [pygltflib.Buffer(byteLength=0)]
    buf = bytearray()

    # Materials
    mat_duct = _add_material(gltf, "duct_metal", (0.6, 0.65, 0.7), metallic=0.4, roughness=0.5)
    mat_filter = _add_material(gltf, "filter", (0.45, 0.55, 0.45), metallic=0.05, roughness=0.85)
    mat_heater = _add_material(gltf, "heater", (0.85, 0.35, 0.2), metallic=0.3, roughness=0.6)
    mat_fan = _add_material(gltf, "fan", (0.4, 0.5, 0.6), metallic=0.5, roughness=0.4)
    mat_room = _add_material(gltf, "room", (0.75, 0.72, 0.65), metallic=0.0, roughness=0.9)
    mat_sensor = _add_material(gltf, "sensor", (0.2, 0.7, 0.9), metallic=0.2, roughness=0.5)
    mat_flow = _add_material(gltf, "flow", (0.3, 0.8, 0.5), metallic=0.0, roughness=0.8)
    mat_outdoor = _add_material(gltf, "outdoor", (0.5, 0.7, 0.85), metallic=0.0, roughness=0.9)

    # Scene layout (X = left-to-right flow direction):
    # outdoor_air -> filter -> heater -> fan -> supply_duct -> room
    components: list[tuple[str, tuple, np.ndarray, np.ndarray, np.ndarray]] = []

    # Outdoor air intake (box)
    p, n, i = _box_mesh(0.8, 0.8, 0.8)
    components.append(("pvu.intake.outdoor_air", (-5.0, 0.5, 0.0), p, n, i))
    mats = [mat_outdoor]

    # Duct: outdoor -> filter
    p, n, i = _box_mesh(1.2, 0.5, 0.5)
    components.append(("pvu.flow.outdoor_to_filter", (-3.6, 0.5, 0.0), p, n, i))
    mats.append(mat_flow)

    # Filter bank (box)
    p, n, i = _box_mesh(0.6, 1.0, 0.9)
    components.append(("pvu.filter.bank", (-2.5, 0.6, 0.0), p, n, i))
    mats.append(mat_filter)

    # Duct: filter -> heater
    p, n, i = _box_mesh(0.8, 0.5, 0.5)
    components.append(("pvu.flow.filter_to_heater", (-1.7, 0.5, 0.0), p, n, i))
    mats.append(mat_flow)

    # Heater coil (box)
    p, n, i = _box_mesh(0.6, 1.0, 0.9)
    components.append(("pvu.heater.coil", (-0.8, 0.6, 0.0), p, n, i))
    mats.append(mat_heater)

    # Duct: heater -> fan
    p, n, i = _box_mesh(0.6, 0.5, 0.5)
    components.append(("pvu.flow.heater_to_fan", (-0.1, 0.5, 0.0), p, n, i))
    mats.append(mat_flow)

    # Supply fan (cylinder)
    p, n, i = _cylinder_mesh(0.45, 0.5, 20)
    components.append(("pvu.fan.supply", (0.6, 0.5, 0.0), p, n, i))
    mats.append(mat_fan)

    # Duct: fan -> room (supply duct)
    p, n, i = _box_mesh(1.8, 0.5, 0.5)
    components.append(("pvu.duct.supply", (2.0, 0.5, 0.0), p, n, i))
    mats.append(mat_duct)

    # Duct flow visual: fan -> room
    p, n, i = _box_mesh(1.6, 0.3, 0.3)
    components.append(("pvu.flow.fan_to_room", (2.0, 0.5, 0.0), p, n, i))
    mats.append(mat_flow)

    # Room zone (large box)
    p, n, i = _box_mesh(2.5, 1.8, 2.0)
    components.append(("building.room.zone_a", (4.6, 0.9, 0.0), p, n, i))
    mats.append(mat_room)

    # Sensors (small boxes placed near their associated equipment)
    sensor_defs = [
        ("pvu.sensors.outdoor_temp", (-5.0, 1.2, 0.5)),
        ("pvu.sensors.filter_pressure", (-2.5, 1.4, 0.55)),
        ("pvu.sensors.supply_temp", (1.5, 1.0, 0.35)),
        ("pvu.sensors.airflow", (2.5, 1.0, 0.35)),
        ("building.sensors.room_temp", (4.6, 2.1, 0.0)),
    ]
    for sensor_name, sensor_pos in sensor_defs:
        p, n, i = _box_mesh(0.2, 0.2, 0.2)
        components.append((sensor_name, sensor_pos, p, n, i))
        mats.append(mat_sensor)

    # Build all meshes and nodes
    material_list = [
        mat_outdoor, mat_flow, mat_filter, mat_flow, mat_heater, mat_flow,
        mat_fan, mat_duct, mat_flow, mat_room,
        mat_sensor, mat_sensor, mat_sensor, mat_sensor, mat_sensor,
    ]

    root_node_idx = len(gltf.nodes)
    gltf.nodes.append(pygltflib.Node(name="PVU_Root", children=[]))
    gltf.scenes[0].nodes.append(root_node_idx)

    for idx, (name, translation, pos, norm, indices) in enumerate(components):
        mesh_idx = _add_mesh_to_gltf(gltf, buf, pos, norm, indices, material_list[idx])
        node_idx = len(gltf.nodes)
        gltf.nodes.append(pygltflib.Node(
            name=name,
            mesh=mesh_idx,
            translation=list(translation),
        ))
        gltf.nodes[root_node_idx].children.append(node_idx)

    # Finalize buffer
    gltf.buffers[0].byteLength = len(buf)
    gltf.set_binary_blob(bytes(buf))

    gltf.save(str(output_path))
    print(f"GLB saved: {output_path} ({output_path.stat().st_size} bytes)")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    output = project_root / "data" / "visualization" / "assets" / "pvu_installation.glb"
    output.parent.mkdir(parents=True, exist_ok=True)
    build_pvu_glb(output)
