from __future__ import annotations

import unicodedata
from pathlib import Path

_CYRILLIC_TO_ASCII = str.maketrans(
    {
        "А": "A",
        "Б": "B",
        "В": "V",
        "Г": "G",
        "Д": "D",
        "Е": "E",
        "Ё": "E",
        "Ж": "Zh",
        "З": "Z",
        "И": "I",
        "Й": "Y",
        "К": "K",
        "Л": "L",
        "М": "M",
        "Н": "N",
        "О": "O",
        "П": "P",
        "Р": "R",
        "С": "S",
        "Т": "T",
        "У": "U",
        "Ф": "F",
        "Х": "Kh",
        "Ц": "Ts",
        "Ч": "Ch",
        "Ш": "Sh",
        "Щ": "Shch",
        "Ъ": "",
        "Ы": "Y",
        "Ь": "",
        "Э": "E",
        "Ю": "Yu",
        "Я": "Ya",
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
)

_REGISTERED_FONT: tuple[str, bool] | None = None


def write_text_pdf(target_path: Path, lines: list[str], *, title: str) -> bool:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas
    except Exception:
        return False

    font_name, supports_unicode = _resolve_font(pdfmetrics, TTFont)
    page_width, page_height = A4
    top_margin = 36
    bottom_margin = 36
    line_height = 14

    pdf = canvas.Canvas(str(target_path), pagesize=A4)
    pdf.setTitle(title)
    pdf.setAuthor("Ahu Simulator")
    pdf.setSubject(title)

    y = page_height - top_margin
    pdf.setFont(font_name, 10)

    for line in lines:
        line_text = line if supports_unicode else to_ascii_text(line)
        if y < bottom_margin:
            pdf.showPage()
            pdf.setFont(font_name, 10)
            y = page_height - top_margin
        pdf.drawString(36, y, line_text[:240])
        y -= line_height

    pdf.save()
    return True


def to_ascii_text(text: str) -> str:
    transliterated = text.translate(_CYRILLIC_TO_ASCII)
    normalized = unicodedata.normalize("NFKD", transliterated)
    normalized = normalized.replace("°", "").replace("³", "3")
    return normalized.encode("ascii", "ignore").decode("ascii")


def _resolve_font(pdfmetrics, TTFont) -> tuple[str, bool]:
    global _REGISTERED_FONT
    if _REGISTERED_FONT is not None:
        return _REGISTERED_FONT

    font_path = _find_unicode_font_path()
    if font_path is not None:
        font_name = "AhuUnicode"
        try:
            if font_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
            _REGISTERED_FONT = (font_name, True)
            return _REGISTERED_FONT
        except Exception:
            pass

    _REGISTERED_FONT = ("Helvetica", False)
    return _REGISTERED_FONT


def _find_unicode_font_path() -> Path | None:
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None
