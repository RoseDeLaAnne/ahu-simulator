from __future__ import annotations

from dash import html

from app.simulation.parameters import ControlMode
from app.ui.concept03.components.icon import Icon

# Карточки режимов привязаны к реальным значениям ControlMode, поэтому выбор
# на этой странице меняет режим работающей модели (control-mode), как и левая
# панель дашборда. (mode_id, заголовок, иконка, описание)
_CONTROL_MODES = (
    (
        ControlMode.AUTO.value,
        "Автоматический",
        "cpu",
        "Система сама поддерживает уставки по выбранному сценарию.",
    ),
    (
        ControlMode.SEMI_AUTO.value,
        "Полуавтоматический",
        "sliders-horizontal",
        "Часть уставок задаёт оператор, остальное держит автоматика.",
    ),
    (
        ControlMode.MANUAL.value,
        "Ручной",
        "hand",
        "Оператор задаёт уставки вручную; автоматика не вмешивается.",
    ),
    (
        ControlMode.TEST.value,
        "Тестовый / наладка",
        "flask-conical",
        "Проверочный прогон оборудования и логики управления.",
    ),
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
                                    "Выберите режим — он сразу применяется к "
                                    "работающей модели и отражается на дашборде.",
                                    className="c03-page-section__hint",
                                ),
                                html.Div(
                                    className="c03-control-grid",
                                    children=[
                                        _control_card(mode_id, title, icon, desc)
                                        for mode_id, title, icon, desc in _CONTROL_MODES
                                    ],
                                ),
                                html.Div(
                                    "Текущий режим: —",
                                    id="concept03-control-page-status",
                                    className="c03-control-page-status",
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
                                    "Числовые уставки (наружная температура, расход, "
                                    "уставка притока, КПД рекуперации, мощность "
                                    "калорифера и др.) задаются на панели «Параметры» "
                                    "центрального холста дашборда. Готовые наборы "
                                    "параметров доступны на странице «Библиотека».",
                                    className="c03-page-section__text",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]


def _control_card(mode_id: str, title: str, icon: str, desc: str) -> html.Button:
    return html.Button(
        id={"type": "concept03-control-page-mode", "mode_id": mode_id},
        className="c03-control-card-page",
        type="button",
        n_clicks=0,
        title=f"{title}: {desc}",
        **{
            "data-mode-id": mode_id,
            "aria-pressed": "false",
        },
        children=[
            html.Div(
                className="c03-control-card-page__top",
                children=[
                    Icon(icon, size=28, class_name="c03-control-card-page__icon"),
                    html.Strong(title, className="c03-control-card-page__title"),
                    Icon(
                        "check",
                        size=16,
                        class_name="c03-control-card-page__check",
                    ),
                ],
            ),
            html.P(desc, className="c03-control-card-page__desc"),
        ],
    )


def control_page_mode_class_name(*, is_active: bool) -> str:
    return "c03-control-card-page" + (
        " c03-control-card-page--active" if is_active else ""
    )
