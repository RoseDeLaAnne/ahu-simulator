from __future__ import annotations

from dash import html

from app.services.event_log_service import EventLogSnapshot
from app.simulation.state import SimulationSession
from app.ui.components.sparkline import build_sparkline_svg
from app.ui.concept03.components.icon import Icon
from app.ui.concept03.defense_variant.right_rail import (
    build_defense_right_rail_content,
)
from app.ui.viewmodels.concept03_health import Concept03HealthView
from app.ui.viewmodels.concept03_kpi import Concept03KpiView


def build_right_rail(
    *,
    kpis: Concept03KpiView,
    health: Concept03HealthView,
    session: SimulationSession | None = None,
    event_log_snapshot: EventLogSnapshot | None = None,
    include_defense: bool = True,
) -> html.Section:
    return html.Section(
        id="right-rail",
        className="c03-region c03-right-rail",
        tabIndex=0,
        children=build_right_rail_content(
            kpis=kpis,
            health=health,
            session=session,
            event_log_snapshot=event_log_snapshot,
            include_defense=include_defense,
        ),
    )


def build_right_rail_content(
    *,
    kpis: Concept03KpiView,
    health: Concept03HealthView,
    session: SimulationSession | None = None,
    event_log_snapshot: EventLogSnapshot | None = None,
    include_defense: bool = True,
) -> list:
    children = [
        html.Div(
            className="c03-operator-right c03-operator-only",
            children=[
                _build_status_banner(health),
                _build_kpi_section(kpis),
                _build_health_section(health),
            ],
        ),
    ]
    if include_defense:
        children.extend(
            build_defense_right_rail_content(
                kpis=kpis,
                health=health,
                session=session,
                event_log_snapshot=event_log_snapshot,
            )
        )
    return children


def _build_status_banner(view: Concept03HealthView) -> html.Div:
    banner = view.banner
    children = [
        Icon(banner.accent_icon, 26, class_name="c03-status-banner__icon"),
        html.Span(
            className="c03-status-banner__copy",
            children=[
                html.Span(banner.title.upper(), className="c03-section-eyebrow"),
                html.Strong(banner.label),
                html.Span(banner.summary),
            ],
        ),
    ]
    if banner.action_href:
        children.append(
            html.A(
                Icon("arrow-right", 16, class_name="c03-status-banner__action-icon"),
                href=banner.action_href,
                className="c03-status-banner__action",
                title="Открыть аналитику тревог",
                **{"aria-label": "Открыть аналитику тревог"},
            )
        )
    return html.Div(
        id="right-rail-status-banner",
        className=banner.class_name,
        **{"data-state": banner.state},
        children=children,
    )


def _build_kpi_section(view: Concept03KpiView) -> html.Section:
    return html.Section(
        id="right-rail-kpi",
        className="c03-right-section c03-right-section--kpi",
        children=[
            html.Div(
                className="c03-right-section__header",
                children=[
                    html.Span("КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ", className="c03-section-eyebrow"),
                ],
            ),
            html.Div(
                id="mobile-kpi-strip",
                className="c03-kpi-list",
                children=[_build_kpi_row(row) for row in view.rows],
            ),
        ],
    )


def _build_kpi_row(row) -> html.Div:
    value_children = [html.Strong(row.value_text)]
    if row.unit:
        value_children.append(html.Span(row.unit))

    # Add sparkline if data is available
    if row.sparkline_values and len(row.sparkline_values) >= 2:
        # Determine color based on state
        sparkline_color = {
            "normal": "#22c55e",
            "warning": "#facc15",
            "alarm": "#ef4444",
            "unavailable": "#94a3b8",
        }.get(row.state, "#64748b")

        sparkline_svg = build_sparkline_svg(
            values=row.sparkline_values,
            width=60,
            height=20,
            stroke_width=1.5,
            stroke_color=sparkline_color,
            fill_color=sparkline_color,
            class_name="c03-kpi-row__sparkline",
        )
        value_children.append(
            html.Div(
                className="c03-kpi-row__sparkline-container",
                dangerouslySetInnerHTML={"__html": sparkline_svg},
            )
        )

    return html.Div(
        id=row.kpi_id,
        className=row.class_name,
        role="group",
        **{
            "data-state": row.state,
            "aria-label": f"{row.label}: {row.value_text} {row.unit}".strip(),
        },
        children=[
            html.Div(
                className="c03-kpi-row__topline",
                children=[
                    Icon(row.icon, 18, class_name="c03-kpi-row__icon"),
                    html.Span(row.label),
                ],
            ),
            html.Div(className="c03-kpi-row__value", children=value_children),
            html.Div(
                className="c03-kpi-row__meta",
                children=[
                    html.Span(row.setpoint_text or ""),
                    html.Span(row.deviation_text),
                ],
            ),
            html.Div(
                className="c03-kpi-row__track",
                children=[
                    html.Span(
                        className="c03-kpi-row__progress",
                        style=row.progress_style,
                    )
                ],
            ),
        ],
    )


def _build_health_section(view: Concept03HealthView) -> html.Section:
    return html.Section(
        id="right-rail-health",
        className="c03-right-section c03-right-section--health",
        children=[
            html.Div(
                className="c03-right-section__header",
                children=[
                    html.Span("ОБЩЕЕ СОСТОЯНИЕ", className="c03-section-eyebrow"),
                ],
            ),
            html.Div(
                className="c03-health-grid",
                children=[_build_health_tile(tile) for tile in view.tiles],
            ),
        ],
    )


def _build_health_tile(tile) -> html.Div:
    return html.Div(
        id=f"health-tile-{tile.health_id}",
        className=tile.class_name,
        **{"data-state": tile.state},
        children=[
            Icon(tile.icon, 18, class_name="c03-health-tile__icon"),
            html.Span(tile.title, className="c03-health-tile__title"),
            html.Strong(tile.sub, className="c03-health-tile__sub"),
        ],
    )
