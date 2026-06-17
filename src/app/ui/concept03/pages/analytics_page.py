from __future__ import annotations

from dash import dcc, html

from app.ui.concept03.components.icon import Icon

# (export_kind, заголовок, иконка, описание)
_EXPORTS = (
    (
        "pdf",
        "Сценарный отчёт (PDF)",
        "file-text",
        "Полный отчёт по активному прогону с таблицами и выводами.",
    ),
    (
        "csv",
        "Данные прогона (CSV)",
        "table",
        "Временные ряды параметров для внешнего анализа.",
    ),
    (
        "zip",
        "Пакет отчёта (ZIP)",
        "archive",
        "Архив: PDF-отчёт, CSV-данные и манифест прогона.",
    ),
)


def build_content() -> list:
    return [
        html.Div(
            className="c03-page c03-page--analytics",
            children=[
                dcc.Download(id="concept03-analytics-download"),
                html.Div(
                    className="c03-page__header",
                    children=[
                        html.H2("Аналитика", className="c03-page__title"),
                        html.Span(
                            "Тренды, сравнения и отчёты",
                            className="c03-page__subtitle",
                        ),
                    ],
                ),
                html.Div(
                    className="c03-page__body c03-analytics-body",
                    children=[
                        html.Section(
                            className="c03-page-section",
                            children=[
                                html.Div(
                                    className="c03-page-section__eyebrow",
                                    children="ТРЕНДЫ",
                                ),
                                html.Div(
                                    className="c03-analytics-placeholder",
                                    children=[
                                        Icon(
                                            "bar-chart-3",
                                            size=48,
                                            class_name="c03-analytics-placeholder__icon",
                                        ),
                                        html.P(
                                            "Графики трендов доступны на главном дашборде "
                                            "во вкладке «Тренды» центрального холста.",
                                            className="c03-analytics-placeholder__text",
                                        ),
                                        dcc.Link(
                                            "Перейти к дашборду →",
                                            href="?theme=concept03&page=dashboard",
                                            refresh=False,
                                            className="c03-analytics-placeholder__link",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Section(
                            className="c03-page-section",
                            children=[
                                html.Div(
                                    className="c03-page-section__eyebrow",
                                    children="ЭКСПОРТ",
                                ),
                                html.Div(
                                    "Экспорт собирается по активному прогону. Нажмите "
                                    "формат — файл сформируется и скачается.",
                                    className="c03-page-section__hint",
                                ),
                                html.Div(
                                    className="c03-analytics-export-grid",
                                    children=[
                                        _export_card(kind, title, icon, desc)
                                        for kind, title, icon, desc in _EXPORTS
                                    ],
                                ),
                                html.Div(
                                    "Экспорт ещё не запускался.",
                                    id="concept03-analytics-export-status",
                                    className="c03-analytics-export-status",
                                ),
                            ],
                        ),
                        html.Section(
                            className="c03-page-section",
                            children=[
                                html.Div(
                                    className="c03-page-section__eyebrow",
                                    children="СРАВНЕНИЕ ДО / ПОСЛЕ",
                                ),
                                html.P(
                                    "Сравнение прогонов доступно в нижней панели "
                                    "«Сравнение модель vs реальность» на главном дашборде.",
                                    className="c03-page-section__text",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]


def _export_card(kind: str, title: str, icon: str, desc: str) -> html.Button:
    return html.Button(
        id={"type": "concept03-analytics-export", "kind": kind},
        className="c03-export-card",
        type="button",
        n_clicks=0,
        title=title,
        **{"data-export-kind": kind},
        children=[
            Icon(icon, size=24, class_name="c03-export-card__icon"),
            html.Div(
                className="c03-export-card__copy",
                children=[
                    html.Strong(title, className="c03-export-card__title"),
                    html.Span(desc, className="c03-export-card__desc"),
                ],
            ),
            Icon("download", size=18, class_name="c03-export-card__action"),
        ],
    )
