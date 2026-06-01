from __future__ import annotations

from collections import defaultdict

from dash import dcc, html

from app.ui.concept03.components.icon import Icon
from app.ui.concept03.defense_variant.central_canvas import (
    build_balances_panel_content,
    build_defense_tab_label,
)
from app.ui.concept03.scene3d_overlay import (
    build_camera_tools,
    build_callout_items,
    build_pagination_dots,
    build_scene3d_overlay,
)
from app.ui.viewmodels.concept03_central import (
    Concept03AlarmRowView,
    Concept03CentralView,
    Concept03ParameterRowView,
    Concept03TrendRowView,
)


DEFAULT_CENTRAL_TAB = "3d"


def build_central_canvas(
    view: Concept03CentralView,
    *,
    active_tab: str = DEFAULT_CENTRAL_TAB,
) -> html.Section:
    return html.Section(
        id="central-canvas",
        className="c03-region c03-central-canvas",
        tabIndex=0,
        children=[
            _build_substrip(view),
            _build_tabbar(view, active_tab),
            _build_viewport(view, active_tab),
            build_pagination_dots(),
            html.Div(id="concept03-overlay-sync", style={"display": "none"}),
        ],
    )


def central_tab_class_name(tab_id: str, active_tab: str | None) -> str:
    return "c03-canvas-tab" + (
        " c03-canvas-tab--active" if tab_id == (active_tab or DEFAULT_CENTRAL_TAB) else ""
    )


def central_panel_class_name(tab_id: str, active_tab: str | None) -> str:
    return "c03-central-panel" + (
        " c03-central-panel--active"
        if tab_id == (active_tab or DEFAULT_CENTRAL_TAB)
        else ""
    )


def build_callout_layer_content(view: Concept03CentralView) -> list:
    return build_scene3d_overlay(view.callouts)


def build_callout_items_content(view: Concept03CentralView) -> list:
    return build_callout_items(view.callouts)


def build_parameters_panel_content(view: Concept03CentralView) -> list:
    rows_by_group: dict[str, list[Concept03ParameterRowView]] = defaultdict(list)
    for row in view.parameter_rows:
        rows_by_group[row.group].append(row)
    return [
        html.Div(
            className="c03-parameter-group",
            children=[
                html.H3(group),
                html.Dl(
                    className="c03-parameter-list",
                    children=[
                        item
                        for row in rows
                        for item in (html.Dt(row.label), html.Dd(row.value))
                    ],
                ),
            ],
        )
        for group, rows in rows_by_group.items()
    ]


def build_trends_panel_content(view: Concept03CentralView) -> list:
    return [_build_trend_row(row) for row in view.trend_rows]


def build_alarms_panel_content(view: Concept03CentralView) -> list:
    if not view.alarm_rows:
        return [
            html.Div(
                className="c03-alarm-empty",
                children=[
                    Icon("shield-check", 22, class_name="c03-alarm-empty__icon"),
                    html.Strong(view.empty_alarm_text),
                ],
            )
        ]
    return [_build_alarm_row(row) for row in view.alarm_rows]


def _build_substrip(view: Concept03CentralView) -> html.Div:
    return html.Div(
        className="c03-canvas-substrip",
        children=[
            html.Span(
                [
                    html.Span("Объект: ", className="c03-canvas-substrip__label"),
                    view.object_label,
                ]
            ),
            html.Span(className="c03-canvas-substrip__divider"),
            html.Span(
                [
                    html.Span("Установка: ", className="c03-canvas-substrip__label"),
                    view.installation_label,
                ]
            ),
            html.Span(className="c03-canvas-substrip__spacer"),
            html.Span(view.status_text, className="c03-canvas-status"),
            build_camera_tools(),
            html.Span(
                "3D PNG: ожидает снимка",
                id="concept03-camera-capture-status",
                className="c03-camera-capture-status c03-defense-only",
            ),
        ],
    )


def _build_tabbar(view: Concept03CentralView, active_tab: str) -> html.Div:
    return html.Div(
        id="central-canvas-tabs",
        className="c03-canvas-tabbar",
        role="tablist",
        children=[
            html.Button(
                build_defense_tab_label(tab.tab_id, tab.label),
                id={"type": "concept03-central-tab", "tab_id": tab.tab_id},
                type="button",
                className=(
                    central_tab_class_name(tab.tab_id, active_tab)
                    + (" c03-operator-only" if tab.tab_id == "docs" else "")
                ),
                role="tab",
                **{
                    "data-tab-id": tab.tab_id,
                    "aria-selected": "true" if tab.tab_id == active_tab else "false",
                },
            )
            for tab in view.tabs
        ],
    )


def _build_viewport(view: Concept03CentralView, active_tab: str) -> html.Div:
    return html.Div(
        id="concept03-central-viewport",
        className="c03-central-viewport",
        children=[
            _build_3d_panel(view, active_tab),
            _build_2d_panel(active_tab),
            _build_parameters_panel(view, active_tab),
            _build_trends_panel(view, active_tab),
            _build_alarms_panel(view, active_tab),
            _build_docs_panel(view, active_tab),
        ],
    )


def _build_3d_panel(view: Concept03CentralView, active_tab: str) -> html.Div:
    return html.Div(
        id="concept03-panel-3d",
        className=central_panel_class_name("3d", active_tab),
        role="tabpanel",
        children=[
            html.Div(
                id="concept03-scene-3d-viewport",
                className="c03-scene-viewport",
                children=[
                    _build_scene_controls(view),
                    html.Div(
                        id="concept03-scene-3d-canvas",
                        className="c03-scene-viewport__canvas",
                    ),
                    *build_callout_layer_content(view),
                ],
            )
        ],
    )


def _build_scene_controls(view: Concept03CentralView) -> html.Div:
    return html.Div(
        className="c03-scene-control-bar c03-operator-only",
        children=[
            _build_scene_dropdown(
                "Режим",
                dcc.Dropdown(
                    id="concept03-scene-mode-select",
                    options=[
                        {"label": option.label, "value": option.mode_id}
                        for option in view.scene_mode_options
                    ],
                    value=view.selected_scene_mode_id,
                    clearable=False,
                    searchable=False,
                    optionHeight=38,
                    maxHeight=220,
                    className="c03-scene-select",
                ),
            ),
            _build_scene_dropdown(
                "Модель",
                dcc.Dropdown(
                    id="concept03-scene-model-select",
                    options=[
                        {"label": option.label, "value": option.model_id}
                        for option in view.scene_model_options
                    ],
                    value=view.selected_scene_model_id,
                    clearable=False,
                    searchable=False,
                    optionHeight=42,
                    maxHeight=260,
                    className="c03-scene-select c03-scene-model-select",
                ),
            ),
        ],
    )


def _build_scene_dropdown(label: str, control: dcc.Dropdown) -> html.Div:
    return html.Div(
        className="c03-scene-control-field",
        children=[
            html.Span(label, className="c03-scene-control-field__label"),
            control,
        ],
    )


def _build_2d_panel(active_tab: str) -> html.Div:
    return html.Div(
        id="concept03-panel-2d",
        className=central_panel_class_name("2d", active_tab),
        role="tabpanel",
        children=[
            html.ObjectEl(
                id="concept03-mnemonic-svg-object",
                data="assets/pvu_mnemonic.svg",
                type="image/svg+xml",
                className="c03-mnemonic-object",
            )
        ],
    )


def _build_parameters_panel(
    view: Concept03CentralView,
    active_tab: str,
) -> html.Div:
    return html.Div(
        id="concept03-panel-parameters",
        className=central_panel_class_name("parameters", active_tab),
        role="tabpanel",
        children=[
            html.Div(
                id="concept03-central-params",
                className="c03-parameters-panel",
                children=build_parameters_panel_content(view),
            )
        ],
    )


def _build_trends_panel(view: Concept03CentralView, active_tab: str) -> html.Div:
    return html.Div(
        id="concept03-panel-trends",
        className=central_panel_class_name("trends", active_tab),
        role="tabpanel",
        children=[
            html.Div(
                id="concept03-central-trends",
                className="c03-trends-panel",
                children=build_trends_panel_content(view),
            )
        ],
    )


def _build_alarms_panel(view: Concept03CentralView, active_tab: str) -> html.Div:
    return html.Div(
        id="concept03-panel-alarms",
        className=central_panel_class_name("alarms", active_tab),
        role="tabpanel",
        children=[
            html.Div(
                id="concept03-central-alarms",
                className="c03-alarms-panel",
                children=[
                    html.Div(
                        className="c03-operator-only",
                        children=build_alarms_panel_content(view),
                    ),
                    html.Div(
                        className="c03-defense-only",
                        children=build_balances_panel_content(view),
                    ),
                ],
            )
        ],
    )


def _build_docs_panel(view: Concept03CentralView, active_tab: str) -> html.Div:
    return html.Div(
        id="concept03-panel-docs",
        className=central_panel_class_name("docs", active_tab),
        role="tabpanel",
        children=[
            html.Div(
                className="c03-docs-panel",
                children=[
                    html.A(
                        className="c03-doc-card",
                        href=link.href,
                        target="_blank",
                        rel="noreferrer",
                        children=[
                            Icon("file-text", 22, class_name="c03-doc-card__icon"),
                            html.Strong(link.title),
                            html.Span(link.description),
                        ],
                    )
                    for link in view.doc_links
                ],
            )
        ],
    )


def _build_trend_row(row: Concept03TrendRowView) -> html.Div:
    return html.Div(
        id=f"concept03-trend-{row.metric_id}",
        className="c03-trend-row",
        children=[
            html.Span(row.label, className="c03-trend-row__label"),
            html.Strong(
                f"{row.value} {row.unit}",
                className="c03-trend-row__value",
            ),
            html.Span(
                className="c03-trend-row__spark",
                children=[
                    html.Span(
                        className="c03-trend-row__bar",
                        style={"height": f"{_bar_height(value, row.points)}%"},
                    )
                    for value in row.points
                ],
            ),
        ],
    )


def _build_alarm_row(row: Concept03AlarmRowView) -> html.Div:
    return html.Div(
        className=row.class_name,
        children=[
            html.Span(row.level_text, className="c03-alarm-row__level"),
            html.Code(row.code, className="c03-alarm-row__code"),
            html.Span(row.message, className="c03-alarm-row__message"),
        ],
    )


def _bar_height(value: float, points: tuple[float, ...]) -> float:
    if len(points) <= 1:
        return 64.0
    minimum = min(points)
    maximum = max(points)
    if abs(maximum - minimum) < 1e-9:
        return 64.0
    return 22.0 + ((value - minimum) / (maximum - minimum)) * 72.0
