"""Guard: видимый нейминг установки — расшифровка «ПВУ» (замечание рецензента).

Рецензент: «ПВУ обычно — приточно-вытяжная установка; либо расшифруй правильно
(приточная вентиляционная установка), либо замени на ПУ». Принятое решение —
расшифровать: видимый текст логотипа/футера использует «Симулятор приточной
установки», а аббревиатура остаётся только рядом с полной формой (tooltips,
заголовок мнемосхемы, About-карточка).
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LAYOUT_PATH = _REPO_ROOT / "src" / "app" / "ui" / "layout.py"


def test_visible_brand_text_expands_pvu() -> None:
    source = _LAYOUT_PATH.read_text(encoding="utf-8")
    assert "Симулятор приточной установки" in source
    assert "Симулятор ПВУ" not in source


def test_brand_tooltip_keeps_full_expansion() -> None:
    source = _LAYOUT_PATH.read_text(encoding="utf-8")
    assert source.count("Приточная вентиляционная установка (ПВУ)") >= 3
