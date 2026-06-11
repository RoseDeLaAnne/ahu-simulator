"""Guard: геометрия SVG-мнемосхемы (замечания рецензента editing-1/editing-2).

editing-1: бейджи датчиков перекрывали заголовок и друг друга — теперь все
бейджи лежат в отдельном ряду и AABB-боксы попарно не пересекаются.
editing-2: на схеме отсутствовали рекуператор и вытяжная ветвь — теперь есть
узел recuperator_core и серые потоки «вытяжка из помещения» / «выброс».
Все легаси-ID сохранены: на них завязан clientside-синк visualization.js.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SVG_PATH = _REPO_ROOT / "src" / "app" / "ui" / "assets" / "pvu_mnemonic.svg"
_SVG_NS = "{http://www.w3.org/2000/svg}"

_LEGACY_VISUAL_IDS = (
    "outdoor_air",
    "filter_bank",
    "heater_coil",
    "supply_fan",
    "supply_duct",
    "room_zone",
    "sensor_outdoor_temp",
    "sensor_filter_pressure",
    "sensor_supply_temp",
    "sensor_airflow",
    "sensor_room_temp",
)

_LEGACY_FLOW_IDS = (
    "flow_outdoor_to_filter",
    "flow_filter_to_heater",
    "flow_heater_to_fan",
    "flow_fan_to_room",
)

_LEGACY_SCENE_IDS = ("scene-status", "scene-bindings-version", "scene-summary")

_NEW_IDS = (
    "recuperator_core",
    "recuperator_core__value",
    "recuperator_core__detail",
    "recuperator_core__alarm",
    "recuperator_core__alarm_text",
    "flow_room_to_recuperator",
    "flow_room_to_recuperator__line",
    "flow_recuperator_to_exhaust",
    "flow_recuperator_to_exhaust__line",
)

# Текстовые зоны шапки (приблизительные AABB по координатам/размеру шрифта).
_HEADER_BOXES = (
    (48.0, 40.0, 400.0, 58.0),  # subheading «Мнемосхема · структура и потоки»
    (48.0, 64.0, 760.0, 98.0),  # heading «Приточная вентиляционная установка (ПВУ)»
    (940.0, 42.0, 1150.0, 86.0),  # scene-status + scene-bindings-version
)


def _root() -> ET.Element:
    return ET.fromstring(_SVG_PATH.read_text(encoding="utf-8"))


def _collect_ids(root: ET.Element) -> set[str]:
    return {
        element.get("id")
        for element in root.iter()
        if element.get("id") is not None
    }


def _collect_boxes(root: ET.Element) -> dict[str, tuple[float, float, float, float]]:
    """AABB всех узлов и бейджей: translate(x y) группы + rect-оболочка."""
    boxes: dict[str, tuple[float, float, float, float]] = {}
    for group in root.iter(f"{_SVG_NS}g"):
        classes = (group.get("class") or "").split()
        if "visual-node" not in classes and "visual-sensor" not in classes:
            continue
        match = re.match(
            r"translate\(\s*(-?[\d.]+)[\s,]+(-?[\d.]+)\s*\)",
            group.get("transform") or "",
        )
        assert match is not None, f"группа {group.get('id')} без translate(x y)"
        shell = group.find(f"{_SVG_NS}rect")
        assert shell is not None, f"группа {group.get('id')} без rect-оболочки"
        x, y = float(match.group(1)), float(match.group(2))
        boxes[str(group.get("id"))] = (
            x,
            y,
            x + float(shell.get("width") or 0),
            y + float(shell.get("height") or 0),
        )
    return boxes


def _intersects(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def test_legacy_and_new_ids_present() -> None:
    ids = _collect_ids(_root())
    for visual_id in _LEGACY_VISUAL_IDS + ("recuperator_core",):
        assert visual_id in ids
        assert f"{visual_id}__value" in ids
        assert f"{visual_id}__detail" in ids
        assert f"{visual_id}__alarm" in ids
        assert f"{visual_id}__alarm_text" in ids
    for flow_id in _LEGACY_FLOW_IDS:
        assert flow_id in ids
        assert f"{flow_id}__line" in ids
        assert f"{flow_id}__value" in ids
        assert f"{flow_id}__detail" in ids
    for scene_id in _LEGACY_SCENE_IDS:
        assert scene_id in ids
    for new_id in _NEW_IDS:
        assert new_id in ids


def test_nodes_and_badges_do_not_overlap() -> None:
    boxes = _collect_boxes(_root())
    assert len(boxes) >= 12  # 7 узлов + 5 датчиков
    items = sorted(boxes.items())
    for index, (id_a, box_a) in enumerate(items):
        for id_b, box_b in items[index + 1 :]:
            assert not _intersects(box_a, box_b), f"{id_a} пересекает {id_b}"


def test_badges_clear_of_header_band() -> None:
    boxes = _collect_boxes(_root())
    for element_id, box in boxes.items():
        for header_box in _HEADER_BOXES:
            assert not _intersects(box, header_box), (
                f"{element_id} перекрывает зону заголовка {header_box}"
            )


def test_viewbox_extended_for_exhaust_band() -> None:
    root = _root()
    view_box = (root.get("viewBox") or "").split()
    assert len(view_box) == 4
    assert float(view_box[3]) >= 560.0


def test_exhaust_flows_are_slate_styled() -> None:
    root = _root()
    source = _SVG_PATH.read_text(encoding="utf-8")
    assert ".flow-line--exhaust" in source
    assert "#64748b" in source
    by_id = {element.get("id"): element for element in root.iter()}
    for line_id in (
        "flow_room_to_recuperator__line",
        "flow_recuperator_to_exhaust__line",
    ):
        classes = (by_id[line_id].get("class") or "").split()
        assert "flow-line--exhaust" in classes
