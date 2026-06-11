"""Guard: every concept03 icon name must have a CSS glyph definition.

The concept03 icon set is hand-drawn via ``[data-icon="X"]::before`` rules spread
across the ``concept03_*.css`` stylesheets.  The base ``[data-icon]::before`` rule
draws a rounded square, so an undefined name silently falls back to that blank
square on the defense interface.  This test fails loudly in that case.

Coverage: the five shell pages are rendered and their ``data-icon`` props walked;
every static icon name reachable by regex (``Icon("...")`` literals, ``data-icon``
dict literals, and ``icon=``/``accent_icon=`` keyword assignments in concept03
view-models) is also checked.  Residual gap: names supplied positionally inside
presentation tuples (e.g. ``("equipment", "Оборудование", "layout-grid")``) are not
statically resolvable here; those presentation tables were verified by hand and
all resolve to defined glyphs.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.ui.concept03.pages import (
    build_analytics_content,
    build_control_content,
    build_equipment_content,
    build_library_content,
    build_settings_content,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_ASSETS = _REPO_ROOT / "src" / "app" / "ui" / "assets"
_CONCEPT03_SRC = _REPO_ROOT / "src" / "app" / "ui" / "concept03"
_VIEWMODELS = _REPO_ROOT / "src" / "app" / "ui" / "viewmodels"

_DEFINED_RE = re.compile(r'\[data-icon="([a-z0-9-]+)"\]')
# Every way an icon name reaches the Icon() span, except positional tuples.
_USED_RES = (
    re.compile(r'Icon\(\s*"([a-z0-9-]+)"'),
    re.compile(r'"data-icon"\s*:\s*"([a-z0-9-]+)"'),
    re.compile(r'\bicon\s*=\s*"([a-z0-9-]+)"'),
    re.compile(r'\baccent_icon\s*=\s*"([a-z0-9-]+)"'),
)


def _defined_glyphs() -> set[str]:
    """Union of every glyph defined across the concept03 stylesheets.

    All ``concept03_*.css`` files ship together, so a glyph defined in any of them
    (e.g. ``menu``/``x``/``layers`` live in ``concept03_mobile.css``) counts.
    """
    defined: set[str] = set()
    for css in _ASSETS.glob("concept03_*.css"):
        defined.update(_DEFINED_RE.findall(css.read_text(encoding="utf-8")))
    return defined


def _collect_data_icons(node: object, acc: set[str]) -> None:
    data_icon = getattr(node, "__dict__", {}).get("data-icon")
    if isinstance(data_icon, str):
        acc.add(data_icon)
    children = getattr(node, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            _collect_data_icons(child, acc)
    elif children is not None and not isinstance(children, (str, int, float)):
        _collect_data_icons(children, acc)


def _rendered_page_icons() -> set[str]:
    used: set[str] = set()
    for builder in (
        build_equipment_content,
        build_control_content,
        build_analytics_content,
        build_library_content,
        build_settings_content,
    ):
        for top in builder():
            _collect_data_icons(top, used)
    return used


def _static_icon_names() -> set[str]:
    names: set[str] = set()
    sources = list(_CONCEPT03_SRC.rglob("*.py"))
    sources += list(_VIEWMODELS.glob("concept03_*.py"))
    for py in sources:
        text = py.read_text(encoding="utf-8")
        for pattern in _USED_RES:
            names.update(pattern.findall(text))
    return names


def test_all_rendered_page_icons_have_a_glyph() -> None:
    defined = _defined_glyphs()
    used = _rendered_page_icons()
    assert used, "expected the concept03 pages to render at least one icon"
    missing = sorted(used - defined)
    assert not missing, (
        f"concept03 page icons without a CSS glyph (render as blank squares): {missing}"
    )


def test_all_static_icon_names_have_a_glyph() -> None:
    defined = _defined_glyphs()
    used = _static_icon_names()
    missing = sorted(used - defined)
    assert not missing, (
        f"concept03 icon names without a CSS glyph (render as blank squares): {missing}"
    )


def test_known_recovered_glyphs_are_present() -> None:
    # Glyphs added 2026-06 to stop the shell pages rendering blank squares.
    defined = _defined_glyphs()
    for name in ("fan", "volume-2", "calendar-clock", "leaf", "table",
                 "archive", "book-open", "trending-down", "palette"):
        assert name in defined, f"missing recovered glyph: {name}"
