from __future__ import annotations

from dash import html

from app.ui.concept03.components.icon import Icon

# (Заголовок, иконка, описание, slug документа в /handbook)
_DOCUMENTS = (
    (
        "Руководство по эксплуатации",
        "book-open",
        "Установка, запуск, функционал, настройка и эксплуатация.",
        "44_app_operation_manual",
    ),
    (
        "Техническая карта ПВУ",
        "file-text",
        "Контур работы установки и сценарии демонстрации.",
        "02_functionality",
    ),
    (
        "Методические основания",
        "book-marked",
        "Формулы, допущения, расчётная модель и связи модулей.",
        "03_architecture",
    ),
    (
        "Источники",
        "file-text",
        "Нормативная и инженерная база проекта.",
        "10_sources",
    ),
)

# (Заголовок, иконка, описание, scenario_id) — пресеты применяются к модели.
_PRESETS = (
    (
        "Зима (baseline)",
        "snowflake",
        "Базовый зимний режим офиса.",
        "baseline_office_winter",
    ),
    (
        "Межсезонье",
        "sun",
        "Переходный период, умеренный нагрев.",
        "midseason",
    ),
    (
        "Пониженный расход",
        "trending-down",
        "Энергосбережение; даёт предупреждения по расходу/фильтру.",
        "reduced_flow",
    ),
    (
        "Загрязнённый фильтр",
        "filter",
        "Имитация загрязнения; выводит установку в аварию по фильтру.",
        "dirty_filter",
    ),
    (
        "Ручной режим",
        "hand",
        "Ручное управление с предупреждениями.",
        "manual_mode",
    ),
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
                                    "Документы открываются во встроенном просмотрщике "
                                    "в новой вкладке.",
                                    className="c03-page-section__hint",
                                ),
                                html.Div(
                                    className="c03-library-grid",
                                    children=[
                                        _doc_card(title, icon, desc, slug)
                                        for title, icon, desc, slug in _DOCUMENTS
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
                                    "Нажмите пресет — он применится к работающей "
                                    "модели; результат смотрите на дашборде.",
                                    className="c03-page-section__hint",
                                ),
                                html.Div(
                                    className="c03-library-grid",
                                    children=[
                                        _preset_card(title, icon, desc, scenario_id)
                                        for title, icon, desc, scenario_id in _PRESETS
                                    ],
                                ),
                                html.Div(
                                    "Пресет не выбран.",
                                    id="concept03-library-preset-status",
                                    className="c03-library-preset-status",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]


def _doc_card(title: str, icon: str, desc: str, slug: str) -> html.A:
    return html.A(
        className="c03-library-card c03-library-card--link",
        href=f"/handbook/{slug}",
        target="_blank",
        rel="noreferrer",
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


def _preset_card(title: str, icon: str, desc: str, scenario_id: str) -> html.Button:
    return html.Button(
        id={"type": "concept03-library-preset", "scenario_id": scenario_id},
        className="c03-library-card c03-library-card--preset",
        type="button",
        n_clicks=0,
        title=f"{title}: {desc}",
        **{"data-scenario-id": scenario_id, "aria-pressed": "false"},
        children=[
            Icon(icon, size=28, class_name="c03-library-card__icon"),
            html.Div(
                className="c03-library-card__copy",
                children=[
                    html.Strong(title, className="c03-library-card__title"),
                    html.Span(desc, className="c03-library-card__desc"),
                ],
            ),
            Icon("check", size=16, class_name="c03-library-card__check"),
        ],
    )


def library_preset_class_name(*, is_active: bool) -> str:
    return "c03-library-card c03-library-card--preset" + (
        " c03-library-card--active" if is_active else ""
    )
