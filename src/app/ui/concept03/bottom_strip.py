from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from app.ui.concept03.components.icon import Icon
from app.ui.concept03.regions import Region
from app.ui.concept03.defense_variant.bottom_strip import build_defense_bottom_panels
from app.ui.viewmodels.concept03_bottom import (
    Concept03BottomView,
    Concept03ComparisonPanelView,
    Concept03EventLogPanelView,
    Concept03ReadinessPanelView,
    Concept03ReportRowView,
    Concept03ReportsPanelView,
)
from app.ui.viewmodels.concept03_scenarios import (
    Concept03ScenarioCardView,
    Concept03ScenariosView,
)


def build_bottom_strip(
    view: Concept03BottomView,
    *,
    include_defense: bool = False,
    scenarios_view: Concept03ScenariosView | None = None,
) -> html.Section:
    return html.Section(
        id=Region.BOTTOM_STRIP.value,
        className="c03-bottom-strip",
        tabIndex=0,
        children=build_bottom_strip_content(
            view,
            include_defense=include_defense,
            scenarios_view=scenarios_view,
        ),
    )


def build_bottom_strip_content(
    view: Concept03BottomView,
    *,
    include_defense: bool = False,
    scenarios_view: Concept03ScenariosView | None = None,
) -> list:
    operator_children = [
        build_readiness_panel(view.readiness),
        build_comparison_panel(view.comparison),
        build_event_log_panel(view.event_log),
        build_reports_panel(view.reports),
    ]
    if scenarios_view is not None:
        operator_children.insert(
            0,
            build_mobile_field_row(scenarios_view, view.readiness),
        )
    children = [
        _build_strip_toggle_bar(),
        html.Div(
            className="c03-operator-bottom c03-operator-only",
            children=operator_children,
        ),
    ]
    if include_defense:
        children.append(
            html.Div(
                className="c03-defense-bottom c03-defense-only",
                children=build_defense_bottom_panels(view),
            )
        )
    return children


def _build_strip_toggle_bar() -> html.Div:
    """Узкая полоска-заголовок над панелями нижней полосы.

    Кнопка-шеврон сворачивает полосу (класс `c03-shell--strip-collapsed`
    на shell, обработчик в concept03_overlay.js), отдавая высоту
    центральному canvas. Состояние запоминается в localStorage.
    """
    return html.Div(
        className="c03-strip-toggle-bar",
        children=[
            html.Span(
                "Артефакты защиты: готовность · сравнение · журнал · отчёты",
                className="c03-strip-toggle-bar__label",
            ),
            html.Button(
                [
                    Icon(
                        "chevron-down",
                        14,
                        class_name="c03-strip-toggle-bar__chevron",
                    ),
                    html.Span(
                        "Свернуть",
                        className="c03-strip-toggle-bar__text",
                        **{"data-strip-label-expanded": "true"},
                    ),
                    html.Span(
                        "Развернуть",
                        className=(
                            "c03-strip-toggle-bar__text "
                            "c03-strip-toggle-bar__text--collapsed"
                        ),
                    ),
                ],
                id="concept03-bottom-strip-toggle",
                type="button",
                className="c03-strip-toggle-bar__button",
                title="Свернуть/развернуть нижнюю полосу",
                **{
                    "aria-label": "Свернуть или развернуть нижнюю полосу",
                    "data-strip-toggle": "bottom",
                },
            ),
        ],
    )


def build_mobile_field_row(
    scenarios: Concept03ScenariosView,
    readiness: Concept03ReadinessPanelView,
) -> html.Div:
    active_scenario = _active_scenario_card(scenarios)
    return html.Div(
        id="mobile-field-row",
        className="c03-mobile-field-row c03-mobile-only",
        children=[
            _build_mobile_scenario_card(scenarios, active_scenario),
            _build_mobile_readiness_card(readiness),
        ],
    )


def _build_mobile_scenario_card(
    scenarios: Concept03ScenariosView,
    card: Concept03ScenarioCardView | None,
) -> html.A:
    icon = card.icon if card else "layers"
    title = card.title if card else "Сценарий работы"
    sub = card.sub if card else "Выберите режим"
    return html.A(
        id="mobile-scenario-card",
        href=scenarios.manage_href,
        className="c03-mobile-field-card c03-mobile-scenario-card",
        children=[
            html.Span("Сценарий работы", className="c03-mobile-field-card__eyebrow"),
            html.Span(
                className="c03-mobile-scenario-card__active",
                children=[
                    Icon(icon, 20, class_name="c03-mobile-scenario-card__icon"),
                    html.Span(
                        className="c03-mobile-scenario-card__copy",
                        children=[
                            html.Strong(title),
                            html.Span(sub),
                        ],
                    ),
                    Icon("arrow-right", 16, class_name="c03-mobile-scenario-card__arrow"),
                ],
            ),
            html.Span("Уставки активны", className="c03-mobile-scenario-card__pill"),
            html.Span("Управление сценариями", className="c03-mobile-field-card__link"),
        ],
    )


def _build_mobile_readiness_card(view: Concept03ReadinessPanelView) -> html.Div:
    return html.Div(
        id="mobile-readiness-card",
        className="c03-mobile-field-card c03-mobile-readiness-card",
        children=[
            html.Span("Готовность к защите", className="c03-mobile-field-card__eyebrow"),
            html.Div(
                className="c03-mobile-readiness-card__body",
                children=[
                    html.Div(
                        className=f"c03-donut c03-donut--{view.state}",
                        style={"--c03-donut-value": f"{view.overall_percent * 3.6}deg"},
                        children=[
                            html.Strong(f"{view.overall_percent}"),
                            html.Span("%"),
                        ],
                    ),
                    html.Div(
                        className="c03-mobile-readiness-card__checks",
                        children=[
                            html.A(
                                href=section.href,
                                title=section.detail,
                                className=(
                                    "c03-mobile-readiness-card__check "
                                    f"c03-mobile-readiness-card__check--{section.state}"
                                ),
                                children=[
                                    Icon("check", 13, class_name="c03-mobile-readiness-card__check-icon"),
                                    html.Span(section.label),
                                ],
                            )
                            for section in view.sections[:4]
                        ],
                    ),
                ],
            ),
            html.A(
                "Детализация проверки",
                href="?theme=concept03&page=analytics&tab=validation",
                className="c03-mobile-field-card__link",
            ),
        ],
    )


def _active_scenario_card(
    scenarios: Concept03ScenariosView,
) -> Concept03ScenarioCardView | None:
    return next(
        (card for card in scenarios.cards if card.is_active),
        scenarios.cards[0] if scenarios.cards else None,
    )


def build_readiness_panel(view: Concept03ReadinessPanelView) -> html.Div:
    return _build_bottom_panel(
        "bp-readiness",
        "ГОТОВНОСТЬ К ВАЛИДАЦИИ",
        right_slot=html.Span(view.status_text, className=_status_chip_class(view.state)),
        children=[
            html.Div(
                className="c03-readiness-ring",
                children=[
                    html.Div(
                        className=f"c03-donut c03-donut--{view.state}",
                        style={"--c03-donut-value": f"{view.overall_percent * 3.6}deg"},
                        children=[
                            html.Strong(f"{view.overall_percent}"),
                            html.Span("%"),
                        ],
                    ),
                    html.Div(
                        className="c03-readiness-ring__sections",
                        children=[
                            html.A(
                                href=section.href,
                                className=(
                                    "c03-readiness-section "
                                    f"c03-readiness-section--{section.state}"
                                ),
                                title=section.detail,
                                children=[
                                    html.Span(section.label),
                                    html.Strong(f"{section.percent}%"),
                                    html.Div(
                                        className="c03-readiness-section__bar",
                                        children=html.Span(
                                            style={"width": f"{section.percent}%"}
                                        ),
                                    ),
                                ],
                            )
                            for section in view.sections
                        ],
                    ),
                ],
            ),
            html.Div(
                className="c03-bottom-panel__footer",
                children=[
                    html.Span(f"Статус: {view.status_text}"),
                    html.Span(f"Срез {view.generated_at_text}"),
                ],
            ),
        ],
    )


def build_comparison_panel(view: Concept03ComparisonPanelView) -> html.Div:
    return _build_bottom_panel(
        "bp-comparison",
        "СРАВНЕНИЕ: МОДЕЛЬ vs ЭТАЛОН",
        right_slot=html.Div(
            className="c03-bottom-panel__actions",
            children=[
                dcc.Dropdown(
                    id="concept03-comparison-metric",
                    className=(
                        "c03-comparison-select "
                        "c03-comparison-metric-select"
                    ),
                    options=[
                        {"label": option.label, "value": option.metric_id}
                        for option in view.metric_options
                    ],
                    value=view.selected_metric_id,
                    clearable=False,
                    searchable=False,
                    placeholder="Метрика",
                ),
                html.Span(view.status_text, className=_status_chip_class(view.state)),
            ],
        ),
        children=[
            html.Div(
                className="c03-comparison-pair-row",
                children=[
                    _build_comparison_source_select(
                        "concept03-comparison-before",
                        "До",
                        view.selected_before_reference_id,
                        view.source_options,
                    ),
                    _build_comparison_source_select(
                        "concept03-comparison-after",
                        "После",
                        view.selected_after_reference_id,
                        view.source_options,
                    ),
                ],
            ),
            _build_mobile_comparison_table(view),
            dcc.Graph(
                id="concept03-comparison-mini-graph",
                className="c03-comparison-panel__graph",
                figure=_build_comparison_figure(view),
                config={"displayModeBar": False, "responsive": True},
            ),
            html.Div(
                className="c03-bottom-panel__footer",
                children=[
                    html.Span(
                        f"Пара: {view.pair_text} · Показатель: {view.metric_label}"
                    ),
                    html.A("Детальный анализ", href=view.cta_href),
                ],
            ),
        ],
    )


def build_event_log_panel(view: Concept03EventLogPanelView) -> html.Div:
    return _build_bottom_panel(
        "bp-event-log",
        "ЖУРНАЛ СОБЫТИЙ",
        right_slot=html.Span(view.status_text, className=_status_chip_class(view.state)),
        children=[
            html.Div(
                id="mobile-event-log",
                className="c03-event-log-table",
                children=[
                    html.A(
                        href=row.href,
                        className=f"c03-event-log-row c03-event-log-row--{row.state}",
                        children=[
                            html.Span(row.timestamp_text, className="c03-event-log-row__time"),
                            html.Span(row.level_text, className=_event_pill_class(row.state)),
                            html.Span(row.message, className="c03-event-log-row__message"),
                        ],
                    )
                    for row in view.rows
                ],
            ),
            html.Div(
                className="c03-bottom-panel__footer",
                children=[
                    html.Span(view.summary_text),
                    html.A("Открыть журнал", href=view.cta_href),
                ],
            ),
        ],
    )


def build_reports_panel(view: Concept03ReportsPanelView) -> html.Div:
    return _build_bottom_panel(
        "bp-reports",
        "ОТЧЁТЫ И ЭКСПОРТ",
        right_slot=html.Span(view.status_text, className=_status_chip_class(view.state)),
        children=[
            html.Div(
                id="mobile-exports",
                className="c03-reports-panel",
                children=[_build_report_row(row) for row in view.rows],
            ),
            html.Div(
                className="c03-bottom-panel__footer c03-bottom-panel__footer--reports",
                children=[
                    html.Span(view.latest_report_text),
                    html.Button(
                        id="concept03-report-build",
                        type="button",
                        className="c03-report-build-button",
                        children=[
                            html.Span(
                                className="c03-report-build-button__icon",
                                **{"data-icon": "file-text"},
                            ),
                            html.Span("Собрать пакет"),
                        ],
                    ),
                ],
            ),
        ],
    )


def _build_mobile_comparison_table(view: Concept03ComparisonPanelView) -> html.Div:
    before_label = view.series[0].label if view.series else "Опора"
    after_label = view.series[1].label if len(view.series) > 1 else "Модель"
    return html.Div(
        id="mobile-comparison",
        className="c03-mobile-comparison-table c03-mobile-only",
        role="table",
        **{"aria-label": "Сравнение сценариев по ключевым показателям"},
        children=[
            html.Div(
                className="c03-mobile-comparison-table__legend",
                children=[
                    html.Span(before_label, className="c03-mobile-comparison-table__legend-item c03-mobile-comparison-table__legend-item--before"),
                    html.Span(after_label, className="c03-mobile-comparison-table__legend-item c03-mobile-comparison-table__legend-item--after"),
                ],
            ),
            html.Div(
                className="c03-mobile-comparison-table__grid",
                children=[
                    html.Span(metric.label, role="columnheader")
                    for metric in view.mobile_metrics
                ]
                + [
                    html.Strong(metric.before_text, role="cell")
                    for metric in view.mobile_metrics
                ]
                + [
                    html.Strong(metric.after_text, role="cell")
                    for metric in view.mobile_metrics
                ],
            ),
            html.A("Все сценарии", href=view.cta_href, className="c03-mobile-comparison-table__link"),
        ],
    )


def _build_bottom_panel(
    panel_id: str,
    title: str,
    *,
    right_slot,
    children: list,
) -> html.Div:
    return html.Div(
        id=panel_id,
        className=f"c03-bottom-panel c03-bottom-panel--{panel_id.removeprefix('bp-')}",
        children=[
            html.Div(
                className="c03-bottom-panel__title",
                children=[
                    html.Strong(title),
                    right_slot,
                ],
            ),
            html.Div(className="c03-bottom-panel__body", children=children),
        ],
    )


def _build_comparison_source_select(
    select_id: str,
    label: str,
    value: str | None,
    options,
) -> html.Div:
    return html.Div(
        className="c03-comparison-pair-field",
        children=[
            html.Span(label),
            dcc.Dropdown(
                id=select_id,
                className=(
                    "c03-comparison-select "
                    "c03-comparison-source-select"
                ),
                options=[
                    {"label": option.label, "value": option.reference_id}
                    for option in options
                ],
                value=value,
                clearable=False,
                searchable=False,
                placeholder=label,
                optionHeight=38,
                maxHeight=180,
            ),
        ],
    )


def _build_report_row(row: Concept03ReportRowView):
    class_name = f"c03-report-row c03-report-row--{row.state}"
    children = [
        html.Span(row.title),
        html.Strong(row.format_text),
    ]
    if row.href:
        return html.A(
            id=f"concept03-report-row-{row.row_id}",
            href=row.href,
            className=class_name,
            children=children,
        )
    return html.Div(
        id=f"concept03-report-row-{row.row_id}",
        className=class_name,
        children=children,
    )


def _build_comparison_figure(view: Concept03ComparisonPanelView) -> go.Figure:
    figure = go.Figure()
    colors = ("rgba(79, 195, 247, 0.72)", "rgba(63, 203, 120, 0.94)")
    for index, series in enumerate(view.series):
        figure.add_trace(
            go.Scatter(
                x=view.minutes,
                y=series.points,
                name=series.label,
                mode="lines+markers",
                line={
                    "color": colors[index % len(colors)],
                    "width": 2.4,
                    "dash": "dash" if series.dashed else "solid",
                },
                marker={"size": 4, "color": colors[index % len(colors)]},
            )
        )
    figure.update_layout(
        autosize=True,
        height=94,
        margin={"l": 4, "r": 4, "t": 4, "b": 4},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        uirevision="concept03-bottom-comparison",
    )
    figure.update_xaxes(visible=False, fixedrange=True)
    figure.update_yaxes(visible=False, fixedrange=True)
    return figure


def _status_chip_class(state: str) -> str:
    return f"c03-bottom-status c03-bottom-status--{state}"


def _event_pill_class(state: str) -> str:
    return f"c03-event-pill c03-event-pill--{state}"
