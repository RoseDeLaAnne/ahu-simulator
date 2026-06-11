from __future__ import annotations

from dash import html

from app.ui.concept03.components.icon import Icon


def build_content() -> list:
    return [
        html.Div(
            className="c03-page c03-page--settings",
            children=[
                html.Div(
                    className="c03-page__header",
                    children=[
                        html.H2("Настройки", className="c03-page__title"),
                        html.Span(
                            "Конфигурация пульта цифрового двойника",
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
                                    children="ИНТЕРФЕЙС",
                                ),
                                _setting_row(
                                    "Тема оформления",
                                    "palette",
                                    "Concept03 (тёмная SCADA-тема) / Legacy (янтарная)",
                                ),
                                _setting_row(
                                    "Режим защиты",
                                    "shield-check",
                                    "Включить defense-вариант для академической презентации",
                                ),
                            ],
                        ),
                        html.Section(
                            className="c03-page-section",
                            children=[
                                html.Div(
                                    className="c03-page-section__eyebrow",
                                    children="О СИСТЕМЕ",
                                ),
                                html.Dl(
                                    className="c03-settings-meta",
                                    children=[
                                        _meta_pair("Версия", "0.1.0"),
                                        _meta_pair(
                                            "Проект",
                                            "ВКР «Моделирование приточной "
                                            "вентиляционной установки (ПВУ)» · 09.04.01",
                                        ),
                                        _meta_pair(
                                            "Организация",
                                            'ООО "НПО Каскад-ГРУП"',
                                        ),
                                        _meta_pair(
                                            "Стек",
                                            "Python 3.14 · FastAPI · Dash · Three.js · Capacitor",
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
                                    children="ДИАГНОСТИКА",
                                ),
                                html.P(
                                    "Проверьте работоспособность сервера, 3D-рендерера "
                                    "и доступность API. При возникновении ошибок "
                                    "WebGL, проверьте поддержку браузером.",
                                    className="c03-page-section__text",
                                ),
                                html.A(
                                    "Swagger API →",
                                    href="/docs",
                                    target="_blank",
                                    className="c03-settings-link",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]


def _setting_row(label: str, icon: str, desc: str) -> html.Div:
    return html.Div(
        className="c03-setting-row",
        children=[
            Icon(icon, size=22, class_name="c03-setting-row__icon"),
            html.Div(
                className="c03-setting-row__copy",
                children=[
                    html.Strong(label, className="c03-setting-row__label"),
                    html.Span(desc, className="c03-setting-row__desc"),
                ],
            ),
        ],
    )


def _meta_pair(label: str, value: str) -> html.Div:
    return html.Div(
        className="c03-settings-meta__pair",
        children=[
            html.Dt(label, className="c03-settings-meta__key"),
            html.Dd(value, className="c03-settings-meta__value"),
        ],
    )
