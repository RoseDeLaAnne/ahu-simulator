"""Compatibility shim for tooling.scene.generate_glb."""

from __future__ import annotations

import sys
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tooling.scene.generate_glb import build_pvu_glb  # noqa: E402


__all__ = ["build_pvu_glb"]


if __name__ == "__main__":
    output = _PROJECT_ROOT / "data" / "visualization" / "assets" / "pvu_installation.glb"
    output.parent.mkdir(parents=True, exist_ok=True)
    build_pvu_glb(output)
