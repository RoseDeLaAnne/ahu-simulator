from __future__ import annotations

from dash import html

from app.ui.concept03.components.icon import Icon
from app.ui.viewmodels.concept03_central import Concept03CentralView


DEFENSE_TAB_LABELS = {
    "3d": "3D Модель",
    "2d": "2D Схема",
    "trends": "Графики",
    "parameters": "Таблицы",
    "alarms": "Балансы",
}


def build_defense_tab_label(tab_id: str, operator_label: str) -> list:
    defense_label = DEFENSE_TAB_LABELS.get(tab_id)
    if defense_label is None:
        return [
            html.Span(operator_label, className="c03-tab-label c03-operator-only"),
        ]
    return [
        html.Span(operator_label, className="c03-tab-label c03-operator-only"),
        html.Span(defense_label, className="c03-tab-label c03-defense-only"),
    ]


def build_balances_panel_content(view: Concept03CentralView) -> list:
    values = _parameter_value_map(view)
    rows = (
        (
            "Воздушный баланс",
            values.get("Фактический расход", "—"),
            values.get("Расход задания", "—"),
        ),
        (
            "Тепловой баланс помещения",
            values.get("Баланс помещения", "—"),
            values.get("Температура помещения", "—"),
        ),
        (
            "Температурный контур",
            values.get("Температура притока", "—"),
            values.get("Уставка притока", "—"),
        ),
        (
            "Аэродинамика фильтров",
            values.get("ΔP фильтра", "—"),
            "Порог контроля",
        ),
    )
    return [
        html.Div(
            className="c03-balance-panel",
            children=[
                html.Div(
                    className="c03-balance-panel__summary",
                    children=[
                        Icon("shield-check", 24, class_name="c03-balance-panel__icon"),
                        html.Strong("Балансы модели сведены"),
                        html.Span(
                            "Расход, температура и энергетика синхронизированы с текущим сценарием."
                        ),
                    ],
                ),
                html.Div(
                    className="c03-balance-table",
                    children=[
                        html.Div(
                            className="c03-balance-row",
                            children=[
                                html.Span(label),
                                html.Strong(value),
                                html.Span(reference),
                            ],
                        )
                        for label, value, reference in rows
                    ],
                ),
            ],
        )
    ]


def _parameter_value_map(view: Concept03CentralView) -> dict[str, str]:
    return {row.label: row.value for row in view.parameter_rows}
