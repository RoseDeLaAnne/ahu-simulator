from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.infrastructure.settings import get_project_root

router = APIRouter(prefix="/handbook", tags=["handbook"])


@dataclass(frozen=True)
class HandbookEntry:
    slug: str
    title: str
    summary: str


# Allowlist: только эти документы из docs/ доступны через /handbook/<slug>.
# Slug совпадает с именем файла без расширения; произвольные пути запрещены,
# поэтому обхода каталога (path traversal) быть не может.
HANDBOOK_ENTRIES: tuple[HandbookEntry, ...] = (
    HandbookEntry(
        "44_app_operation_manual",
        "Руководство по эксплуатации",
        "Назначение, установка, запуск, функционал, настройка и эксплуатация комплекса.",
    ),
    HandbookEntry(
        "02_functionality",
        "Функциональность",
        "Контур работы ПВУ, режимы и сценарии демонстрации.",
    ),
    HandbookEntry(
        "03_architecture",
        "Архитектура и формулы",
        "Расчётная модель, допущения и связи модулей.",
    ),
    HandbookEntry(
        "43_project_overview",
        "Обзор проекта",
        "Краткое описание программного комплекса и его возможностей.",
    ),
    HandbookEntry(
        "40_product_capabilities",
        "Возможности продукта",
        "Перечень функций и сценариев использования.",
    ),
    HandbookEntry(
        "10_sources",
        "Источники",
        "Нормативная и инженерная база проекта.",
    ),
)

_ENTRY_BY_SLUG = {entry.slug: entry for entry in HANDBOOK_ENTRIES}
_SLUG_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def handbook_index() -> HTMLResponse:
    items = "\n".join(
        f'<li><a href="/handbook/{entry.slug}">{html.escape(entry.title)}</a>'
        f"<span>{html.escape(entry.summary)}</span></li>"
        for entry in HANDBOOK_ENTRIES
    )
    body = (
        '<h1>Справочник проекта</h1>'
        '<p class="handbook-lead">Документация программного комплекса '
        "имитационного моделирования приточной вентиляционной установки.</p>"
        f'<ul class="handbook-index">{items}</ul>'
    )
    return HTMLResponse(_render_page("Справочник проекта", body))


@router.get("/{slug}", response_class=HTMLResponse)
def handbook_document(slug: str) -> HTMLResponse:
    if not _SLUG_PATTERN.match(slug) or slug not in _ENTRY_BY_SLUG:
        raise HTTPException(status_code=404, detail="Документ не найден.")

    entry = _ENTRY_BY_SLUG[slug]
    document_path = get_project_root() / "docs" / f"{slug}.md"
    if not document_path.is_file():
        raise HTTPException(status_code=404, detail="Файл документа отсутствует.")

    markdown_text = document_path.read_text(encoding="utf-8")
    content_html = render_markdown(markdown_text)
    body = (
        '<p class="handbook-back"><a href="/handbook">← Все документы</a></p>'
        f"{content_html}"
    )
    return HTMLResponse(_render_page(entry.title, body))


def render_markdown(markdown_text: str) -> str:
    """Компактный отрисовщик Markdown в HTML без внешних зависимостей.

    Поддержаны: заголовки, абзацы, списки (маркированные/нумерованные),
    блоки кода ```...```, таблицы GFM, горизонтальная линия, а также
    инлайновое форматирование (код, жирный, курсив, ссылки). Любой текст
    экранируется до применения форматирования, поэтому HTML из документа
    не исполняется.
    """
    lines = markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    html_parts: list[str] = []
    paragraph: list[str] = []
    list_stack: list[str] = []  # "ul" | "ol"
    in_code = False
    code_buffer: list[str] = []
    table_buffer: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(segment.strip() for segment in paragraph)
            html_parts.append(f"<p>{_render_inline(text)}</p>")
            paragraph.clear()

    def close_lists() -> None:
        while list_stack:
            html_parts.append(f"</{list_stack.pop()}>")

    def flush_table() -> None:
        if not table_buffer:
            return
        rows = [row for row in table_buffer if row.strip()]
        table_buffer.clear()
        if len(rows) < 2:
            for row in rows:
                paragraph.append(row)
            flush_paragraph()
            return
        header_cells = _split_table_row(rows[0])
        body_rows = rows[2:]
        head_html = "".join(f"<th>{_render_inline(cell)}</th>" for cell in header_cells)
        body_html = ""
        for body_row in body_rows:
            cells = _split_table_row(body_row)
            body_html += "<tr>" + "".join(
                f"<td>{_render_inline(cell)}</td>" for cell in cells
            ) + "</tr>"
        html_parts.append(
            f"<table><thead><tr>{head_html}</tr></thead>"
            f"<tbody>{body_html}</tbody></table>"
        )

    def is_table_row(value: str) -> bool:
        stripped = value.strip()
        return stripped.startswith("|") and stripped.endswith("|") and "|" in stripped[1:]

    for raw_line in lines:
        line = raw_line.rstrip()

        fence_match = re.match(r"^\s*```(.*)$", line)
        if fence_match:
            if in_code:
                html_parts.append(
                    f"<pre><code>{html.escape(chr(10).join(code_buffer))}</code></pre>"
                )
                code_buffer.clear()
                in_code = False
            else:
                flush_paragraph()
                close_lists()
                flush_table()
                in_code = True
            continue

        if in_code:
            code_buffer.append(raw_line)
            continue

        if is_table_row(line):
            flush_paragraph()
            close_lists()
            table_buffer.append(line)
            continue
        if table_buffer:
            flush_table()

        if not line.strip():
            flush_paragraph()
            close_lists()
            continue

        if re.match(r"^\s*([-*_])\1{2,}\s*$", line):
            flush_paragraph()
            close_lists()
            html_parts.append("<hr>")
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            flush_paragraph()
            close_lists()
            level = len(heading_match.group(1))
            html_parts.append(
                f"<h{level}>{_render_inline(heading_match.group(2).strip())}</h{level}>"
            )
            continue

        ordered_match = re.match(r"^(\s*)\d+[.)]\s+(.*)$", raw_line)
        unordered_match = re.match(r"^(\s*)[-*+]\s+(.*)$", raw_line)
        if ordered_match or unordered_match:
            flush_paragraph()
            tag = "ol" if ordered_match else "ul"
            content = (ordered_match or unordered_match).group(2)
            if not list_stack or list_stack[-1] != tag:
                if list_stack:
                    html_parts.append(f"</{list_stack.pop()}>")
                html_parts.append(f"<{tag}>")
                list_stack.append(tag)
            html_parts.append(f"<li>{_render_inline(content.strip())}</li>")
            continue

        close_lists()
        paragraph.append(line)

    if in_code and code_buffer:
        html_parts.append(
            f"<pre><code>{html.escape(chr(10).join(code_buffer))}</code></pre>"
        )
    flush_paragraph()
    flush_table()
    close_lists()
    return "\n".join(html_parts)


def _split_table_row(row: str) -> list[str]:
    trimmed = row.strip().strip("|")
    return [cell.strip() for cell in trimmed.split("|")]


def _render_inline(text: str) -> str:
    escaped = html.escape(text)
    # Инлайновый код сохраняем первым, чтобы внутри не сработали другие правила.
    code_tokens: list[str] = []

    def _stash_code(match: re.Match[str]) -> str:
        code_tokens.append(match.group(1))
        return f"\x00CODE{len(code_tokens) - 1}\x00"

    escaped = re.sub(r"`([^`]+)`", _stash_code, escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda match: _render_link(match.group(1), match.group(2)),
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    for index, code in enumerate(code_tokens):
        escaped = escaped.replace(f"\x00CODE{index}\x00", f"<code>{code}</code>")
    return escaped


def _render_link(label: str, target: str) -> str:
    # target уже HTML-экранирован вызывающим кодом; разрешаем только http(s),
    # относительные и handbook-ссылки, чтобы не протащить javascript: и пр.
    safe_target = target
    lowered = target.lower()
    if not (
        lowered.startswith("http://")
        or lowered.startswith("https://")
        or target.startswith("/")
        or target.startswith("#")
        or target.startswith("./")
        or target.startswith("../")
    ):
        safe_target = "#"
    external = lowered.startswith("http://") or lowered.startswith("https://")
    rel = ' target="_blank" rel="noreferrer"' if external else ""
    return f'<a href="{safe_target}"{rel}>{label}</a>'


def _render_page(title: str, body_html: str) -> str:
    return _PAGE_TEMPLATE.replace("__TITLE__", html.escape(title)).replace(
        "__BODY__", body_html
    )


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ · Справочник ПВУ</title>
<style>
:root {
  color-scheme: dark;
  --bg: #05121a;
  --panel: #0a1e29;
  --border: rgba(79, 195, 247, 0.22);
  --text: #e6f1f5;
  --muted: #9fb6c2;
  --accent: #4fc3f7;
  --code-bg: #07151d;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 32px 18px 72px;
  background: var(--bg);
  color: var(--text);
  font-family: "Segoe UI", system-ui, -apple-system, Arial, sans-serif;
  line-height: 1.62;
  font-size: 16px;
}
.handbook-shell { max-width: 880px; margin: 0 auto; }
h1, h2, h3, h4, h5, h6 { color: #fff; line-height: 1.25; margin: 1.6em 0 0.6em; }
h1 { font-size: 1.9rem; margin-top: 0; border-bottom: 1px solid var(--border); padding-bottom: 0.4em; }
h2 { font-size: 1.45rem; border-bottom: 1px solid var(--border); padding-bottom: 0.3em; }
h3 { font-size: 1.2rem; color: var(--accent); }
p { margin: 0.7em 0; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
ul, ol { padding-left: 1.5em; margin: 0.7em 0; }
li { margin: 0.32em 0; }
code {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 0.1em 0.4em;
  font-family: "Cascadia Code", "Fira Code", Consolas, monospace;
  font-size: 0.88em;
}
pre {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  overflow-x: auto;
}
pre code { border: 0; padding: 0; background: transparent; }
hr { border: 0; border-top: 1px solid var(--border); margin: 1.8em 0; }
table { border-collapse: collapse; width: 100%; margin: 1.1em 0; font-size: 0.94em; }
th, td { border: 1px solid var(--border); padding: 8px 11px; text-align: left; vertical-align: top; }
th { background: var(--panel); color: #fff; }
tr:nth-child(even) td { background: rgba(10, 30, 41, 0.5); }
blockquote { border-left: 3px solid var(--accent); margin: 1em 0; padding: 0.2em 1em; color: var(--muted); }
.handbook-lead { color: var(--muted); font-size: 1.05rem; }
.handbook-back { margin-bottom: 1.4em; }
.handbook-index { list-style: none; padding: 0; }
.handbook-index li {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  margin: 10px 0;
  background: var(--panel);
}
.handbook-index li a { font-size: 1.1rem; font-weight: 600; }
.handbook-index li span { display: block; color: var(--muted); margin-top: 4px; font-size: 0.92rem; }
</style>
</head>
<body>
<main class="handbook-shell">
__BODY__
</main>
</body>
</html>
"""
