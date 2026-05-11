"""Compatibility shim for tooling.scene.generate_room_glbs."""

from __future__ import annotations

import sys
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tooling.scene.generate_room_glbs import build_room_glbs  # noqa: E402


__all__ = ["build_room_glbs"]


if __name__ == "__main__":
    target_dir = _PROJECT_ROOT / "models" / "rooms"
    paths = build_room_glbs(target_dir)
    for path in paths:
        print(f"Generated {path}")
