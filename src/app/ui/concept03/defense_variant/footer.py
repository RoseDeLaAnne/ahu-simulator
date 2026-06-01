from __future__ import annotations

from dash import html

from app.infrastructure.settings import AcademicSettings, get_settings
from app.ui.concept03.components.icon import Icon


def build_academic_footer(
    settings: AcademicSettings | None = None,
) -> html.Div:
    academic = settings or get_settings().academic
    return html.Div(
        className="c03-academic-footer c03-defense-only",
        children=[
            html.Strong(academic.program, className="c03-academic-footer__program"),
            html.Span(academic.speciality),
            html.Span(f"Профиль: {academic.profile}"),
            html.Span(f"Кафедра: {academic.department}"),
            html.Span(f"Версия модели: {academic.model_version}"),
            html.Span(
                className="c03-academic-footer__saved",
                children=[
                    Icon("check", 14, class_name="c03-academic-footer__saved-icon"),
                    html.Span("Сохранено"),
                ],
            ),
        ],
    )
