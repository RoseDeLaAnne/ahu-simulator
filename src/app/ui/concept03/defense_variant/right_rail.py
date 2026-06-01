from __future__ import annotations

from dash import html

from app.services.event_log_service import EventLogSnapshot
from app.simulation.state import AlarmLevel, SimulationSession
from app.ui.concept03.components.icon import Icon
from app.ui.viewmodels.concept03_health import Concept03HealthView
from app.ui.viewmodels.concept03_kpi import Concept03KpiRowView, Concept03KpiView


DEFENSE_KPI_IDS = (
    "kpi-row-airflow",
    "kpi-row-supply-temp",
    "kpi-row-humidity",
    "kpi-row-power",
)


def build_defense_right_rail_content(
    *,
    kpis: Concept03KpiView,
    health: Concept03HealthView,
    session: SimulationSession | None = None,
    event_log_snapshot: EventLogSnapshot | None = None,
) -> list:
    rows_by_id = {row.kpi_id: row for row in kpis.rows}
    result = session.current_result if session is not None else None
    return [
        html.Div(
            className="c03-defense-right c03-defense-only",
            children=[
                _build_current_state(health),
                html.Section(
                    className="c03-defense-kpi-section",
                    children=[
                        html.Span("КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ", className="c03-section-eyebrow"),
                        html.Div(
                            className="c03-kpi-card-grid",
                            children=[
                                _build_kpi_card(
                                    rows_by_id[kpi_id],
                                    _sparkline_points(kpi_id, session),
                                )
                                for kpi_id in DEFENSE_KPI_IDS
                                if kpi_id in rows_by_id
                            ],
                        ),
                    ],
                ),
                _build_component_status_list(kpis),
                _build_alarms_accordion(session),
                _build_event_log_accordion(event_log_snapshot),
            ],
            **{
                "data-status": result.state.status.value if result is not None else health.banner.state
            },
        )
    ]


def _build_current_state(health: Concept03HealthView) -> html.Section:
    state = health.banner.state
    return html.Section(
        className="c03-defense-state",
        children=[
            html.Span("ТЕКУЩЕЕ СОСТОЯНИЕ", className="c03-section-eyebrow"),
            html.Div(
                className=f"c03-defense-state__pill c03-defense-state__pill--{state}",
                children=[
                    Icon("shield-check", 18, class_name="c03-defense-state__icon"),
                    html.Strong(health.banner.label.upper()),
                ],
            ),
            html.Span(health.banner.summary, className="c03-defense-state__summary"),
        ],
    )


def _build_kpi_card(
    row: Concept03KpiRowView,
    points: tuple[float, ...],
) -> html.Div:
    return html.Div(
        id=f"defense-{row.kpi_id}",
        className=f"c03-kpi-card c03-kpi-card--{_state_suffix(row.state)}",
        **{"data-state": row.state},
        children=[
            html.Div(
                className="c03-kpi-card__topline",
                children=[
                    Icon(row.icon, 17, class_name="c03-kpi-card__icon"),
                    html.Span(row.label),
                ],
            ),
            html.Div(
                className="c03-kpi-card__value",
                children=[
                    html.Strong(row.value_text),
                    html.Span(row.unit),
                    html.Em(row.deviation_text, className="c03-kpi-card__delta"),
                ],
            ),
            _build_sparkline(points, row.state),
            html.Span(row.setpoint_text or "", className="c03-kpi-card__setpoint"),
        ],
    )


def _build_sparkline(points: tuple[float, ...], state: str) -> html.Span:
    bars = _normalize_points(points)
    return html.Span(
        className=f"c03-sparkline c03-sparkline--{_state_suffix(state)}",
        children=[
            html.Span(
                className="c03-sparkline__bar",
                style={"height": f"{height}%"},
            )
            for height in bars
        ],
    )


def _build_component_status_list(kpis: Concept03KpiView) -> html.Details:
    rows = (
        ("Фильтр F7", _row_value(kpis, "kpi-row-pressure"), _row_state(kpis, "kpi-row-pressure")),
        ("Рекуператор", _row_value(kpis, "kpi-row-recovery"), _row_state(kpis, "kpi-row-recovery")),
        ("Нагреватель", _row_value(kpis, "kpi-row-supply-temp"), _row_state(kpis, "kpi-row-supply-temp")),
        ("Вентилятор П1", _row_value(kpis, "kpi-row-airflow"), _row_state(kpis, "kpi-row-airflow")),
        ("Увлажнитель", _row_value(kpis, "kpi-row-humidity"), _row_state(kpis, "kpi-row-humidity")),
        ("Охладитель", "Контур готов", "normal"),
        ("Вентилятор П2", "Резерв", "normal"),
    )
    return _build_details(
        "СТАТУС КОМПОНЕНТОВ",
        badge=str(len(rows)),
        class_name="c03-component-status-list",
        children=[
            html.Div(
                className=f"c03-component-status-row c03-component-status-row--{_state_suffix(state)}",
                children=[
                    html.Span(label),
                    html.Strong(value),
                    html.Span(_status_mark(state), className="c03-component-status-row__mark"),
                ],
            )
            for label, value, state in rows
        ],
    )


def _build_alarms_accordion(session: SimulationSession | None) -> html.Details:
    alarms = tuple(session.current_result.alarms) if session is not None else ()
    return _build_details(
        "АКТИВНЫЕ АЛАРМЫ",
        badge=str(len(alarms)),
        class_name="c03-alarms-accordion",
        children=[
            html.Div(
                className=f"c03-defense-alarm-row c03-defense-alarm-row--{alarm.level.value}",
                children=[
                    html.Span(_alarm_level_text(alarm.level)),
                    html.Code(alarm.code),
                    html.Strong(alarm.message),
                ],
            )
            for alarm in alarms
        ]
        or [html.Div("Нет активных тревог", className="c03-defense-empty-row")],
    )


def _build_event_log_accordion(snapshot: EventLogSnapshot | None) -> html.Details:
    entries = tuple((snapshot.entries if snapshot is not None else [])[:7])
    return _build_details(
        "ЖУРНАЛ СОБЫТИЙ",
        badge=str(len(entries)),
        class_name="c03-event-log-accordion",
        children=[
            html.Div(
                className=f"c03-defense-event-row c03-defense-event-row--{entry.level.value}",
                children=[
                    html.Span(entry.captured_at.astimezone().strftime("%H:%M:%S")),
                    html.Strong(entry.title),
                    html.Span(entry.summary),
                ],
            )
            for entry in entries
        ]
        or [html.Div("Событий пока нет", className="c03-defense-empty-row")],
    )


def _build_details(
    title: str,
    *,
    badge: str,
    class_name: str,
    children: list,
) -> html.Details:
    return html.Details(
        open=True,
        className=f"c03-defense-accordion {class_name}",
        children=[
            html.Summary(
                children=[
                    html.Span(title),
                    html.Strong(badge, className="c03-defense-accordion__badge"),
                ]
            ),
            html.Div(className="c03-defense-accordion__body", children=children),
        ],
    )


def _sparkline_points(
    kpi_id: str,
    session: SimulationSession | None,
) -> tuple[float, ...]:
    if session is None or not session.history.points:
        fallback = {
            "kpi-row-airflow": (72, 74, 78, 82, 86, 90, 94, 98),
            "kpi-row-supply-temp": (19, 20, 21, 21.5, 22, 22.1, 22.0),
            "kpi-row-humidity": (38, 39, 39, 40, 39, 38, 38),
            "kpi-row-power": (4.8, 4.6, 4.9, 5.1, 5.0, 4.7, 4.5),
        }
        return fallback.get(kpi_id, (1, 1, 1))
    points = session.history.points[-12:]
    if kpi_id == "kpi-row-airflow":
        return tuple(point.airflow_m3_h for point in points)
    if kpi_id == "kpi-row-supply-temp":
        return tuple(point.supply_temp_c for point in points)
    if kpi_id == "kpi-row-power":
        return tuple(point.total_power_kw for point in points)
    if kpi_id == "kpi-row-humidity":
        return tuple(38.0 for _ in points)
    return tuple(1.0 for _ in points)


def _normalize_points(points: tuple[float, ...]) -> tuple[int, ...]:
    if not points:
        return (50,)
    min_value = min(points)
    max_value = max(points)
    span = max(max_value - min_value, 1e-6)
    return tuple(round(24 + (value - min_value) / span * 70) for value in points)


def _row_value(kpis: Concept03KpiView, kpi_id: str) -> str:
    row = next((item for item in kpis.rows if item.kpi_id == kpi_id), None)
    if row is None:
        return "Недоступно"
    return f"{row.value_text} {row.unit}".strip()


def _row_state(kpis: Concept03KpiView, kpi_id: str) -> str:
    row = next((item for item in kpis.rows if item.kpi_id == kpi_id), None)
    return row.state if row is not None else "unavailable"


def _state_suffix(state: str) -> str:
    return {
        "normal": "normal",
        "warning": "warn",
        "alarm": "alarm",
        "unavailable": "unavailable",
    }.get(state, "unavailable")


def _status_mark(state: str) -> str:
    return {
        "normal": "✓",
        "warning": "⚠",
        "alarm": "✕",
        "unavailable": "—",
    }.get(state, "—")


def _alarm_level_text(level: AlarmLevel) -> str:
    return {
        AlarmLevel.INFO: "Инфо",
        AlarmLevel.WARNING: "Предупр",
        AlarmLevel.CRITICAL: "Тревога",
    }[level]
