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
                                _toggle_row(
                                    "Тема оформления",
                                    "palette",
                                    "Переключение между тёмной SCADA-темой и янтарной "
                                    "(применяется сразу, страница перезагружается).",
                                    options=(
                                        ("Concept03", "?theme=concept03&page=settings", "moon"),
                                        ("Legacy", "?theme=legacy&page=settings", "sun"),
                                    ),
                                ),
                                _toggle_row(
                                    "Режим защиты",
                                    "shield-check",
                                    "Defense-вариант для академической презентации "
                                    "(скрывает операторские элементы, добавляет defense-панели).",
                                    options=(
                                        ("Оператор", "?theme=concept03&page=settings", "settings"),
                                        (
                                            "Защита",
                                            "?theme=concept03&defense=1&page=settings",
                                            "shield-check",
                                        ),
                                    ),
                                ),
                            ],
                        ),
                        html.Section(
                            className="c03-page-section",
                            children=[
                                html.Div(
                                    className="c03-page-section__eyebrow",
                                    children="ДОКУМЕНТАЦИЯ И API",
                                ),
                                html.Div(
                                    className="c03-settings-links",
                                    children=[
                                        _settings_link(
                                            "Справочник проекта",
                                            "/handbook",
                                            "book-open",
                                        ),
                                        _settings_link(
                                            "Руководство по эксплуатации",
                                            "/handbook/44_app_operation_manual",
                                            "file-text",
                                        ),
                                        _settings_link(
                                            "Swagger API",
                                            "/docs",
                                            "book-marked",
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
                                html.Div(
                                    "Проверка среды выполнения (WebGL, размеры экрана, "
                                    "браузер). При ошибках 3D-сцены проверьте поддержку WebGL.",
                                    className="c03-page-section__text",
                                ),
                                html.Pre(
                                    "Сбор данных о среде…",
                                    id="concept03-settings-diagnostics",
                                    className="c03-settings-diagnostics",
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
                    ],
                ),
            ],
        ),
    ]


def _toggle_row(label: str, icon: str, desc: str, *, options) -> html.Div:
    return html.Div(
        className="c03-setting-row",
        children=[
            Icon(icon, size=22, class_name="c03-setting-row__icon"),
            html.Div(
                className="c03-setting-row__copy",
                children=[
                    html.Strong(label, className="c03-setting-row__label"),
                    html.Span(desc, className="c03-setting-row__desc"),
                    html.Div(
                        className="c03-setting-row__options",
                        children=[
                            html.A(
                                children=[
                                    Icon(opt_icon, size=15),
                                    html.Span(opt_label),
                                ],
                                href=opt_href,
                                className="c03-setting-option",
                            )
                            for opt_label, opt_href, opt_icon in options
                        ],
                    ),
                ],
            ),
        ],
    )


def _settings_link(label: str, href: str, icon: str) -> html.A:
    return html.A(
        href=href,
        target="_blank",
        rel="noreferrer",
        className="c03-settings-link",
        children=[Icon(icon, size=16), html.Span(label)],
    )


def _meta_pair(label: str, value: str) -> html.Div:
    return html.Div(
        className="c03-settings-meta__pair",
        children=[
            html.Dt(label, className="c03-settings-meta__key"),
            html.Dd(value, className="c03-settings-meta__value"),
        ],
    )
