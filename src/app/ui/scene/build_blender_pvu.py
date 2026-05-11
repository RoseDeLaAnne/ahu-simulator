"""Compatibility shim for tooling.scene.build_blender_pvu.

The generator script was moved to tooling/scene during migration phase 2.
This module preserves the old import/script path used by local workflows.
"""

from __future__ import annotations

import sys
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tooling.scene import build_blender_pvu as _impl  # noqa: E402


PLAN = _impl.PLAN
SCENE_NODES = _impl.SCENE_NODES
build_scene = _impl.build_scene

__all__ = ["PLAN", "SCENE_NODES", "build_scene"]


if __name__ == "__main__":
    out_glb, out_blend, out_preview = _impl._parse_args()
    build_scene(out_glb, out_blend, out_preview)
    print(f"Saved Blender scene to: {out_blend}")
    print(f"Saved preview image to: {out_preview}")
    print(f"Exported GLB to: {out_glb}")
