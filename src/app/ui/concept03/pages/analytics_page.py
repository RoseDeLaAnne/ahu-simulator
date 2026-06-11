from __future__ import annotations

from dash import html

from app.ui.concept03.components.icon import Icon


def build_content() -> list:
    return [
        html.Div(
            className="c03-page c03-page--analytics",
            children=[
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
                                        html.A(
                                            "Перейти к дашборду →",
                                            href="?theme=concept03&page=dashboard",
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
                                    children="СРАВНЕНИЕ ДО / ПОСЛЕ",
                                ),
                                html.P(
                                    "Сравнение прогонов доступно в нижней панели "
                                    "«Сравнение модель vs реальность» на главном дашборде. "
                                    "Там же можно экспортировать результаты в CSV/PDF.",
                                    className="c03-page-section__text",
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
                                _export_card(
                                    "Сценарный отчёт (PDF)",
                                    "file-text",
                                    "Полный отчёт по активному сценарию с таблицами и графиками",
                                ),
                                _export_card(
                                    "Данные прогона (CSV)",
                                    "table",
                                    "Временные ряды всех параметров для внешнего анализа",
                                ),
                                _export_card(
                                    "Defense-пакет (ZIP)",
                                    "archive",
                                    "Пакет для защиты: отчёт, данные, скриншоты, манифест",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]


def _export_card(title: str, icon: str, desc: str) -> html.Div:
    return html.Div(
        className="c03-export-card",
        children=[
            Icon(icon, size=24, class_name="c03-export-card__icon"),
            html.Div(
                className="c03-export-card__copy",
                children=[
                    html.Strong(title, className="c03-export-card__title"),
                    html.Span(desc, className="c03-export-card__desc"),
                ],
            ),
        ],
    )
