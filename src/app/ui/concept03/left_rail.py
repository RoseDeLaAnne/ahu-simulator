from __future__ import annotations

from dash import html

from app.ui.concept03.components.icon import Icon
from app.ui.viewmodels.concept03_config import Concept03ConfigView
from app.ui.viewmodels.concept03_modes import Concept03ModesView
from app.ui.viewmodels.concept03_scenarios import Concept03ScenariosView


def build_left_rail(
    *,
    scenarios: Concept03ScenariosView,
    modes: Concept03ModesView,
    config: Concept03ConfigView,
) -> html.Section:
    return html.Section(
        id="left-rail",
        className="c03-region c03-left-rail",
        tabIndex=0,
        children=[
            _build_scenario_section(scenarios),
            _build_cta(
                "Управление сценариями",
                scenarios.manage_href,
                cta_id="concept03-manage-scenarios",
            ),
            _build_modes_section(modes),
            _build_config_section(config),
            _build_cta(
                "Свойства установки",
                config.properties_href,
                cta_id="concept03-installation-properties",
            ),
        ],
    )


def _build_scenario_section(view: Concept03ScenariosView) -> html.Div:
    return html.Div(
        id="sidebar-scenarios",
        className="c03-left-section c03-left-section--scenarios",
        children=[
            html.Div(
                className="c03-left-section__header",
                children=[
                    html.Span("СЦЕНАРИИ", className="c03-section-eyebrow"),
                    html.A(
                        Icon("plus", 16, title="Добавить сценарий"),
                        id="concept03-add-scenario",
                        href=view.add_href,
                        className="c03-icon-button",
                        title="Добавить сценарий",
                        **{"aria-label": "Добавить сценарий"},
                    ),
                ],
            ),
            html.Div(
                className="c03-scenario-list",
                children=[_build_scenario_card(card) for card in view.cards],
            ),
        ],
    )


def _build_scenario_card(card) -> html.Button:
    return html.Button(
        id={"type": "concept03-scenario-card", "scenario_id": card.scenario_id},
        className=card.class_name,
        type="button",
        n_clicks=0,
        title=f"{card.title}: {card.sub}",
        **{
            "data-scenario-id": card.scenario_id,
            "aria-pressed": "true" if card.is_active else "false",
        },
        children=[
            Icon(card.icon, 22, class_name="c03-card-icon"),
            html.Span(
                className="c03-card-copy",
                children=[
                    html.Strong(card.title),
                    html.Span(card.sub),
                ],
            ),
            (
                html.Span("Custom", className="c03-card-chip")
                if card.is_user_preset
                else None
            ),
            Icon("check", 16, class_name="c03-active-check"),
        ],
    )


def _build_modes_section(view: Concept03ModesView) -> html.Div:
    return html.Div(
        id="sidebar-control-modes",
        className="c03-left-section c03-left-section--modes",
        children=[
            html.Div(
                className="c03-left-section__header",
                children=[
                    html.Span("РЕЖИМЫ РАБОТЫ", className="c03-section-eyebrow"),
                ],
            ),
            html.Div(
                className="c03-mode-list",
                children=[_build_mode_card(card) for card in view.cards],
            ),
        ],
    )


def _build_mode_card(card) -> html.Button:
    return html.Button(
        id={"type": "concept03-mode-card", "mode_id": card.mode_id},
        className=card.class_name,
        type="button",
        n_clicks=0,
        title=f"{card.title}: {card.sub}",
        **{
            "data-mode-id": card.mode_id,
            "aria-pressed": "true" if card.is_active else "false",
        },
        children=[
            Icon(card.icon, 22, class_name="c03-card-icon"),
            html.Span(
                className="c03-card-copy",
                children=[
                    html.Strong(card.title),
                    html.Span(card.sub),
                ],
            ),
            html.Span(className="c03-mode-dot", **{"aria-hidden": "true"}),
        ],
    )


def _build_config_section(view: Concept03ConfigView) -> html.Details:
    return html.Details(
        id="sidebar-config",
        className="c03-left-section c03-config-brief",
        open=True,
        children=[
            html.Summary(
                className="c03-left-section__header c03-config-brief__summary",
                children=[
                    html.Span(view.title.upper(), className="c03-section-eyebrow"),
                    html.Span("▾", className="c03-config-brief__chevron"),
                ],
            ),
            html.Dl(
                className="c03-config-brief__list",
                children=[
                    item
                    for row in view.items
                    for item in (
                        html.Dt(row.label),
                        html.Dd(row.value),
                    )
                ],
            ),
        ],
    )


def _build_cta(label: str, href: str, *, cta_id: str) -> html.A:
    return html.A(
        id=cta_id,
        href=href,
        className="c03-left-cta",
        children=[
            html.Span(label),
            Icon("arrow-right", 16, class_name="c03-left-cta__icon"),
        ],
    )
