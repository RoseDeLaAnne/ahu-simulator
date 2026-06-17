"""Тесты встроенного просмотрщика документации /handbook."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.routers.handbook import (
    HANDBOOK_ENTRIES,
    handbook_document,
    handbook_index,
    render_markdown,
)


def test_render_markdown_handles_core_constructs() -> None:
    markdown = (
        "# Заголовок\n\n"
        "Абзац с `кодом`, **жирным** и [ссылкой](https://example.com).\n\n"
        "## Раздел\n"
        "- пункт 1\n"
        "- пункт 2\n\n"
        "1. раз\n"
        "2. два\n\n"
        "| A | B |\n|---|---|\n| 1 | 2 |\n\n"
        "```\nblock\n```\n"
    )
    html_out = render_markdown(markdown)
    assert "<h1>Заголовок</h1>" in html_out
    assert "<h2>Раздел</h2>" in html_out
    assert "<ul>" in html_out and "<ol>" in html_out
    assert "<table>" in html_out and "<th>A</th>" in html_out
    assert "<pre><code>" in html_out
    assert '<a href="https://example.com" target="_blank"' in html_out
    assert "<strong>жирным</strong>" in html_out
    assert "<code>кодом</code>" in html_out


def test_render_markdown_escapes_html() -> None:
    html_out = render_markdown("Текст <script>alert(1)</script> конец")
    assert "<script>" not in html_out
    assert "&lt;script&gt;" in html_out


def test_handbook_index_lists_allowlisted_documents() -> None:
    response = handbook_index()
    assert response.status_code == 200
    body = response.body.decode("utf-8")
    for entry in HANDBOOK_ENTRIES:
        assert f"/handbook/{entry.slug}" in body


def test_handbook_document_renders_allowlisted_slug() -> None:
    response = handbook_document("02_functionality")
    assert response.status_code == 200
    body = response.body.decode("utf-8")
    assert "<h1" in body or "<h2" in body


def test_handbook_document_rejects_unknown_slug() -> None:
    with pytest.raises(HTTPException) as excinfo:
        handbook_document("99_does_not_exist")
    assert excinfo.value.status_code == 404


def test_handbook_document_rejects_path_traversal() -> None:
    with pytest.raises(HTTPException) as excinfo:
        handbook_document("../config/defaults")
    assert excinfo.value.status_code == 404


def test_operation_manual_is_allowlisted_and_present() -> None:
    slugs = {entry.slug for entry in HANDBOOK_ENTRIES}
    assert "44_app_operation_manual" in slugs
    response = handbook_document("44_app_operation_manual")
    assert response.status_code == 200
