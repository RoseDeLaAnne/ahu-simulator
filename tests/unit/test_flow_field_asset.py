"""Копия flow_field.json в раздаваемых ассетах должна совпадать с канонической.

viewer3d.mjs загружает поле потока относительно своего модуля
(/dashboard/assets/data/visualization/flow_field.json); источник данных
живёт в data/visualization/. Если файлы разойдутся — 3D покажет устаревшее поле.
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL = PROJECT_ROOT / "data" / "visualization" / "flow_field.json"
SERVED = (
    PROJECT_ROOT
    / "src"
    / "app"
    / "ui"
    / "assets"
    / "data"
    / "visualization"
    / "flow_field.json"
)


def test_served_copy_exists() -> None:
    assert SERVED.is_file(), f"Нет копии ассета: {SERVED}"


def test_served_copy_matches_canonical() -> None:
    assert SERVED.read_bytes() == CANONICAL.read_bytes(), (
        "flow_field.json разошёлся с data/visualization/ — "
        "скопируйте канонический файл в src/app/ui/assets/data/visualization/"
    )


def test_flow_field_structure() -> None:
    payload = json.loads(CANONICAL.read_text(encoding="utf-8"))
    assert isinstance(payload.get("points"), list) and payload["points"], (
        "flow_field.json должен содержать непустой массив points"
    )
