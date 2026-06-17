"""Guard: every mnemonic <object> id in the layouts must be wired into
``visualization.js``.

The clientside ``pvuVisualization.renderMnemonic`` callback pushes live
simulation signals into the embedded ``pvu_mnemonic.svg`` documents. It can
only reach objects whose DOM id is listed in ``MNEMONIC_OBJECT_IDS`` inside
``visualization.js``. A layout adding a new mnemonic object id without
registering it there silently shows the static SVG with «Ожидание данных
моделирования» forever (this exact bug shipped with the concept03 «Схема»
tab). This test fails loudly instead.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VISUALIZATION_JS = _REPO_ROOT / "src" / "app" / "ui" / "assets" / "visualization.js"
_UI_SRC = _REPO_ROOT / "src" / "app" / "ui"

# Every html.ObjectEl(...) embedding pvu_mnemonic.svg carries an id ending in
# "mnemonic-svg-object" or "mnemonic-object" by convention.
_LAYOUT_ID_RE = re.compile(r'id="([a-z0-9-]*mnemonic[a-z0-9-]*-object)"')
_JS_ID_RE = re.compile(r'"([a-z0-9-]*mnemonic[a-z0-9-]*-object)"')


def _layout_mnemonic_ids() -> set[str]:
    ids: set[str] = set()
    for py in _UI_SRC.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        if "pvu_mnemonic.svg" not in text:
            continue
        ids.update(_LAYOUT_ID_RE.findall(text))
    return ids


def _registered_js_ids() -> set[str]:
    return set(_JS_ID_RE.findall(_VISUALIZATION_JS.read_text(encoding="utf-8")))


def test_layouts_define_mnemonic_objects() -> None:
    assert _layout_mnemonic_ids(), "expected at least one mnemonic <object> in layouts"


def test_all_layout_mnemonic_ids_are_registered_in_visualization_js() -> None:
    missing = sorted(_layout_mnemonic_ids() - _registered_js_ids())
    assert not missing, (
        "mnemonic <object> ids not handled by visualization.js "
        f"(scheme will show no live data): {missing}"
    )


def test_known_mnemonic_ids_present() -> None:
    registered = _registered_js_ids()
    for object_id in (
        "mnemonic-svg-object",
        "concept03-mnemonic-svg-object",
        "concept03-fallback-mnemonic-object",
    ):
        assert object_id in registered, f"visualization.js lost id: {object_id}"
