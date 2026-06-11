from __future__ import annotations

from dash import html

from app.ui.concept03.components.icon import Icon

_DOCUMENTS = (
    (
        "Техническая карта ПВУ (приточной вентиляционной установки)",
        "file-text",
        "Расчётные параметры, схема, паспортные данные установки П1",
    ),
    (
        "Методические основания",
        "book-marked",
        "Формулы, допущения, нормативная база расчётов",
    ),
    (
        "Валидационная матрица",
        "check",
        "Контрольные точки и результаты проверки модели",
    ),
    (
        "Руководство оператора",
        "book-open",
        "Инструкция по работе с пультом цифрового двойника",
    ),
)

_PRESETS = (
    ("Зима (baseline)", "snowflake", "Базовый зимний сценарий: -25°C наружный воздух"),
    ("Межсезонье", "sun", "Переходный период: +5°C, умеренный нагрев"),
    ("Пониженный расход", "trending-down", "Режим энергосбережения: 70% расхода"),
    ("Загрязнённый фильтр", "filter", "Имитация загрязнения: перепад +150 Па"),
    ("Ручной режим", "sliders-horizontal", "Полностью ручное управление параметрами"),
)


def build_content() -> list:
    return [
        html.Div(
            className="c03-page c03-page--library",
            children=[
                html.Div(
                    className="c03-page__header",
                    children=[
                        html.H2("Библиотека", className="c03-page__title"),
                        html.Span(
                            "Документация и пресеты сценариев",
                            className="c03-page__subtitle",
                        ),
                    ],
                ),
                html.Div(
                    className="c03-page__body",
                    children=[
                        html.Section(
                            className="c03-page-section",
                            children=[
                                html.Div(
                                    className="c03-page-section__eyebrow",
                                    children="ДОКУМЕНТАЦИЯ",
                                ),
                                html.Div(
                                    className="c03-library-grid",
                                    children=[
                                        _doc_card(title, icon, desc)
                                        for title, icon, desc in _DOCUMENTS
                                    ],
                                ),
                            ],
                        ),
                        html.Section(
                            className="c03-page-section",
                            children=[
                                html.Div(
                                    className="c03-page-section__eyebrow",
                                    children="ПРЕСЕТЫ СЦЕНАРИЕВ",
                                ),
                                html.Div(
                                    className="c03-library-grid",
                                    children=[
                                        _doc_card(title, icon, desc)
                                        for title, icon, desc in _PRESETS
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]


def _doc_card(title: str, icon: str, desc: str) -> html.Div:
    return html.Div(
        className="c03-library-card",
        children=[
            Icon(icon, size=28, class_name="c03-library-card__icon"),
            html.Div(
                className="c03-library-card__copy",
                children=[
                    html.Strong(title, className="c03-library-card__title"),
                    html.Span(desc, className="c03-library-card__desc"),
                ],
            ),
        ],
    )
