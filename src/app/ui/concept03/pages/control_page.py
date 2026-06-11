from __future__ import annotations

from dash import html

from app.ui.concept03.components.icon import Icon

_CONTROL_CARDS = (
    ("Автоматический", "cpu", "Система управляет параметрами по заданному сценарию"),
    ("Ручной", "hand", "Оператор задаёт уставки вручную"),
    ("По расписанию", "calendar-clock", "Режимы переключаются по недельному графику"),
    ("Энергосберегающий", "leaf", "Оптимизация энергопотребления без ущерба комфорту"),
)


def build_content() -> list:
    return [
        html.Div(
            className="c03-page c03-page--control",
            children=[
                html.Div(
                    className="c03-page__header",
                    children=[
                        html.H2("Управление", className="c03-page__title"),
                        html.Span(
                            "Режимы работы и параметры установки",
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
                                    children="РЕЖИМЫ РАБОТЫ",
                                ),
                                html.Div(
                                    className="c03-control-grid",
                                    children=[
                                        _control_card(title, icon, desc)
                                        for title, icon, desc in _CONTROL_CARDS
                                    ],
                                ),
                            ],
                        ),
                        html.Section(
                            className="c03-page-section",
                            children=[
                                html.Div(
                                    className="c03-page-section__eyebrow",
                                    children="ПАРАМЕТРЫ СЦЕНАРИЯ",
                                ),
                                html.P(
                                    "Настройка параметров выполняется через левую панель «Сценарии» "
                                    "на главном дашборде. Выберите сценарий и режим управления, "
                                    "затем скорректируйте значения на панели параметров "
                                    "центрального холста.",
                                    className="c03-page-section__text",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]


def _control_card(title: str, icon: str, desc: str) -> html.Div:
    return html.Div(
        className="c03-control-card-page",
        children=[
            html.Div(
                className="c03-control-card-page__top",
                children=[
                    Icon(icon, size=28, class_name="c03-control-card-page__icon"),
                    html.Strong(title, className="c03-control-card-page__title"),
                ],
            ),
            html.P(desc, className="c03-control-card-page__desc"),
        ],
    )
