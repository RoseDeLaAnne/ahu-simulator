"""Generate lightweight GLB room contexts for the 3D studio.

The generated rooms are intentionally simple but real GLB assets:
- open-front office suite
- classroom wing
- laboratory cluster

Each file contains named anchor nodes used by the runtime 3D viewer:
- room.anchor.center
- room.anchor.inlet
- room.anchor.occupied_zone
- room.sensor.temperature
- room.sensor.co2
- room.sensor.humidity
- room.sensor.occupancy
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pygltflib


@dataclass(frozen=True)
class RoomPart:
    name: str
    size: tuple[float, float, float]
    translation: tuple[float, float, float]
    material: str


@dataclass(frozen=True)
class AnchorNode:
    name: str
    translation: tuple[float, float, float]


@dataclass(frozen=True)
class RoomBuildSpec:
    asset_name: str
    parts: tuple[RoomPart, ...]
    anchors: tuple[AnchorNode, ...]


def _box_mesh(sx: float, sy: float, sz: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    positions: list[tuple[float, float, float]] = []
    normals: list[tuple[float, float, float]] = []
    indices: list[int] = []
    faces = [
        ((0, 0, 1), [(-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]),
        ((0, 0, -1), [(hx, -hy, -hz), (-hx, -hy, -hz), (-hx, hy, -hz), (hx, hy, -hz)]),
        ((0, 1, 0), [(-hx, hy, hz), (hx, hy, hz), (hx, hy, -hz), (-hx, hy, -hz)]),
        ((0, -1, 0), [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz)]),
        ((1, 0, 0), [(hx, -hy, hz), (hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz)]),
        ((-1, 0, 0), [(-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz)]),
    ]
    for normal, corners in faces:
        base = len(positions)
        positions.extend(corners)
        normals.extend([normal] * 4)
        indices.extend([base, base + 1, base + 2, base, base + 2, base + 3])
    return (
        np.array(positions, dtype=np.float32),
        np.array(normals, dtype=np.float32),
        np.array(indices, dtype=np.uint16),
    )


def _add_material(
    gltf: pygltflib.GLTF2,
    *,
    name: str,
    color: tuple[float, float, float],
    metallic: float,
    roughness: float,
) -> int:
    index = len(gltf.materials)
    gltf.materials.append(
        pygltflib.Material(
            name=name,
            pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                baseColorFactor=[*color, 1.0],
                metallicFactor=metallic,
                roughnessFactor=roughness,
            ),
        )
    )
    return index


def _align_buffer(data: bytearray) -> None:
    while len(data) % 4 != 0:
        data.append(0)


def _add_mesh_to_gltf(
    gltf: pygltflib.GLTF2,
    buffers_data: bytearray,
    positions: np.ndarray,
    normals: np.ndarray,
    indices: np.ndarray,
    material_index: int,
) -> int:
    pos_bytes = positions.tobytes()
    norm_bytes = normals.tobytes()
    idx_bytes = indices.tobytes()

    _align_buffer(buffers_data)
    pos_offset = len(buffers_data)
    buffers_data.extend(pos_bytes)

    _align_buffer(buffers_data)
    norm_offset = len(buffers_data)
    buffers_data.extend(norm_bytes)

    _align_buffer(buffers_data)
    idx_offset = len(buffers_data)
    buffers_data.extend(idx_bytes)

    pos_bv = len(gltf.bufferViews)
    gltf.bufferViews.append(
        pygltflib.BufferView(
            buffer=0,
            byteOffset=pos_offset,
            byteLength=len(pos_bytes),
            target=34962,
        )
    )
    norm_bv = len(gltf.bufferViews)
    gltf.bufferViews.append(
        pygltflib.BufferView(
            buffer=0,
            byteOffset=norm_offset,
            byteLength=len(norm_bytes),
            target=34962,
        )
    )
    idx_bv = len(gltf.bufferViews)
    gltf.bufferViews.append(
        pygltflib.BufferView(
            buffer=0,
            byteOffset=idx_offset,
            byteLength=len(idx_bytes),
            target=34963,
        )
    )

    pos_acc = len(gltf.accessors)
    gltf.accessors.append(
        pygltflib.Accessor(
            bufferView=pos_bv,
            componentType=5126,
            count=len(positions),
            type="VEC3",
            min=positions.min(axis=0).tolist(),
            max=positions.max(axis=0).tolist(),
        )
    )
    norm_acc = len(gltf.accessors)
    gltf.accessors.append(
        pygltflib.Accessor(
            bufferView=norm_bv,
            componentType=5126,
            count=len(normals),
            type="VEC3",
        )
    )
    idx_acc = len(gltf.accessors)
    gltf.accessors.append(
        pygltflib.Accessor(
            bufferView=idx_bv,
            componentType=5123,
            count=len(indices),
            type="SCALAR",
        )
    )

    mesh_index = len(gltf.meshes)
    gltf.meshes.append(
        pygltflib.Mesh(
            primitives=[
                pygltflib.Primitive(
                    attributes=pygltflib.Attributes(POSITION=pos_acc, NORMAL=norm_acc),
                    indices=idx_acc,
                    material=material_index,
                )
            ]
        )
    )
    return mesh_index


def _room_specs() -> tuple[RoomBuildSpec, ...]:
    return (
        RoomBuildSpec(
            asset_name="office_suite.glb",
            parts=(
                RoomPart("room.floor", (2.6, 0.06, 1.8), (0.0, 0.03, 0.0), "floor"),
                RoomPart("room.wall.back", (2.6, 1.18, 0.06), (0.0, 0.59, -0.87), "wall"),
                RoomPart("room.wall.left", (0.06, 1.18, 1.8), (-1.27, 0.59, 0.0), "wall"),
                RoomPart("room.wall.right", (0.06, 1.18, 1.8), (1.27, 0.59, 0.0), "wall"),
                RoomPart("room.desk.a", (0.74, 0.08, 0.34), (-0.55, 0.42, 0.25), "desk"),
                RoomPart("room.desk.b", (0.74, 0.08, 0.34), (0.55, 0.42, 0.25), "desk"),
                RoomPart("room.meeting.table", (0.68, 0.08, 0.46), (0.0, 0.42, -0.22), "desk"),
                RoomPart("room.partition", (0.04, 0.86, 0.62), (0.0, 0.46, 0.52), "accent"),
                RoomPart("room.storage", (0.34, 0.78, 0.28), (1.0, 0.39, -0.48), "accent"),
            ),
            anchors=(
                AnchorNode("room.anchor.center", (0.0, 0.4, 0.0)),
                AnchorNode("room.anchor.inlet", (-1.0, 0.96, -0.46)),
                AnchorNode("room.anchor.occupied_zone", (0.0, 0.44, 0.18)),
                AnchorNode("room.sensor.temperature", (-0.12, 0.78, -0.16)),
                AnchorNode("room.sensor.co2", (0.54, 0.84, 0.22)),
                AnchorNode("room.sensor.humidity", (-0.64, 0.84, 0.18)),
                AnchorNode("room.sensor.occupancy", (0.0, 0.78, 0.48)),
            ),
        ),
        RoomBuildSpec(
            asset_name="classroom_wing.glb",
            parts=(
                RoomPart("room.floor", (3.0, 0.06, 2.0), (0.0, 0.03, 0.0), "floor"),
                RoomPart("room.wall.back", (3.0, 1.22, 0.06), (0.0, 0.61, -0.97), "wall"),
                RoomPart("room.wall.left", (0.06, 1.22, 2.0), (-1.47, 0.61, 0.0), "wall"),
                RoomPart("room.wall.right", (0.06, 1.22, 2.0), (1.47, 0.61, 0.0), "wall"),
                RoomPart("room.board", (0.96, 0.52, 0.03), (0.0, 0.84, -0.93), "accent"),
                RoomPart("room.teacher.table", (0.82, 0.08, 0.42), (0.0, 0.42, -0.42), "desk"),
                RoomPart("room.row.1.a", (0.48, 0.08, 0.28), (-0.8, 0.38, 0.0), "desk"),
                RoomPart("room.row.1.b", (0.48, 0.08, 0.28), (0.0, 0.38, 0.0), "desk"),
                RoomPart("room.row.1.c", (0.48, 0.08, 0.28), (0.8, 0.38, 0.0), "desk"),
                RoomPart("room.row.2.a", (0.48, 0.08, 0.28), (-0.8, 0.38, 0.46), "desk"),
                RoomPart("room.row.2.b", (0.48, 0.08, 0.28), (0.0, 0.38, 0.46), "desk"),
                RoomPart("room.row.2.c", (0.48, 0.08, 0.28), (0.8, 0.38, 0.46), "desk"),
                RoomPart("room.row.3.a", (0.48, 0.08, 0.28), (-0.8, 0.38, 0.92), "desk"),
                RoomPart("room.row.3.b", (0.48, 0.08, 0.28), (0.0, 0.38, 0.92), "desk"),
                RoomPart("room.row.3.c", (0.48, 0.08, 0.28), (0.8, 0.38, 0.92), "desk"),
            ),
            anchors=(
                AnchorNode("room.anchor.center", (0.0, 0.4, 0.22)),
                AnchorNode("room.anchor.inlet", (-1.12, 1.0, -0.5)),
                AnchorNode("room.anchor.occupied_zone", (0.0, 0.48, 0.56)),
                AnchorNode("room.sensor.temperature", (-0.2, 0.86, -0.16)),
                AnchorNode("room.sensor.co2", (0.7, 0.92, 0.46)),
                AnchorNode("room.sensor.humidity", (-0.86, 0.92, 0.62)),
                AnchorNode("room.sensor.occupancy", (0.0, 0.86, 1.08)),
            ),
        ),
        RoomBuildSpec(
            asset_name="lab_cluster.glb",
            parts=(
                RoomPart("room.floor", (2.8, 0.06, 1.9), (0.0, 0.03, 0.0), "floor"),
                RoomPart("room.wall.back", (2.8, 1.2, 0.06), (0.0, 0.6, -0.92), "wall"),
                RoomPart("room.wall.left", (0.06, 1.2, 1.9), (-1.37, 0.6, 0.0), "wall"),
                RoomPart("room.wall.right", (0.06, 1.2, 1.9), (1.37, 0.6, 0.0), "wall"),
                RoomPart("room.bench.left", (1.08, 0.08, 0.42), (-0.54, 0.44, -0.18), "desk"),
                RoomPart("room.bench.right", (1.08, 0.08, 0.42), (0.54, 0.44, -0.18), "desk"),
                RoomPart("room.island", (0.84, 0.08, 0.52), (0.0, 0.44, 0.46), "desk"),
                RoomPart("room.rack.a", (0.3, 0.94, 0.34), (1.04, 0.47, -0.38), "accent"),
                RoomPart("room.rack.b", (0.3, 0.94, 0.34), (-1.04, 0.47, -0.38), "accent"),
                RoomPart("room.exhaust.hood", (0.86, 0.16, 0.5), (0.0, 0.96, -0.18), "metal"),
            ),
            anchors=(
                AnchorNode("room.anchor.center", (0.0, 0.42, 0.16)),
                AnchorNode("room.anchor.inlet", (-1.02, 1.0, -0.24)),
                AnchorNode("room.anchor.occupied_zone", (0.0, 0.5, 0.36)),
                AnchorNode("room.sensor.temperature", (-0.16, 0.88, 0.06)),
                AnchorNode("room.sensor.co2", (0.7, 0.94, 0.3)),
                AnchorNode("room.sensor.humidity", (-0.74, 0.94, 0.3)),
                AnchorNode("room.sensor.occupancy", (0.0, 0.88, 0.76)),
            ),
        ),
    )


def _build_room_gltf(spec: RoomBuildSpec) -> pygltflib.GLTF2:
    gltf = pygltflib.GLTF2(
        asset=pygltflib.Asset(version="2.0", generator="ahu-simulator/generate_room_glbs"),
        scene=0,
    )
    gltf.scenes = [pygltflib.Scene(name=spec.asset_name, nodes=[])]
    gltf.nodes = []
    gltf.meshes = []
    gltf.materials = []
    gltf.bufferViews = []
    gltf.accessors = []
    gltf.buffers = [pygltflib.Buffer(byteLength=0)]
    buffer_data = bytearray()

    materials = {
        "wall": _add_material(gltf, name="wall", color=(0.86, 0.87, 0.89), metallic=0.02, roughness=0.92),
        "floor": _add_material(gltf, name="floor", color=(0.58, 0.62, 0.64), metallic=0.04, roughness=0.78),
        "desk": _add_material(gltf, name="desk", color=(0.72, 0.54, 0.34), metallic=0.02, roughness=0.68),
        "accent": _add_material(gltf, name="accent", color=(0.29, 0.53, 0.72), metallic=0.08, roughness=0.44),
        "metal": _add_material(gltf, name="metal", color=(0.64, 0.68, 0.72), metallic=0.38, roughness=0.32),
    }

    root_index = len(gltf.nodes)
    gltf.nodes.append(pygltflib.Node(name="Room_Root", children=[]))
    gltf.scenes[0].nodes.append(root_index)

    for part in spec.parts:
        positions, normals, indices = _box_mesh(*part.size)
        mesh_index = _add_mesh_to_gltf(
            gltf,
            buffer_data,
            positions,
            normals,
            indices,
            materials[part.material],
        )
        node_index = len(gltf.nodes)
        gltf.nodes.append(
            pygltflib.Node(
                name=part.name,
                mesh=mesh_index,
                translation=list(part.translation),
            )
        )
        gltf.nodes[root_index].children.append(node_index)

    for anchor in spec.anchors:
        node_index = len(gltf.nodes)
        gltf.nodes.append(
            pygltflib.Node(
                name=anchor.name,
                translation=list(anchor.translation),
            )
        )
        gltf.nodes[root_index].children.append(node_index)

    gltf.buffers[0].byteLength = len(buffer_data)
    gltf.set_binary_blob(bytes(buffer_data))
    return gltf


def build_room_glbs(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths: list[Path] = []
    for spec in _room_specs():
        output_path = output_dir / spec.asset_name
        gltf = _build_room_gltf(spec)
        gltf.save(str(output_path))
        output_paths.append(output_path)
    return output_paths


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    target_dir = project_root / "models" / "rooms"
    paths = build_room_glbs(target_dir)
    for path in paths:
        print(f"Generated {path}")
