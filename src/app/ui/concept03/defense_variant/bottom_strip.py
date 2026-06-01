from __future__ import annotations

from dash import html

from app.ui.viewmodels.concept03_bottom import Concept03BottomView


def build_defense_bottom_panels(view: Concept03BottomView) -> list:
    return [
        _build_validation_summary_panel(view),
        _build_export_package_panel(view),
        _build_scenario_comparison_panel(view),
        _build_event_log_table_panel(view),
        _build_readiness_checks_panel(view),
    ]


def _build_validation_summary_panel(view: Concept03BottomView) -> html.Div:
    sections = view.readiness.sections[:4]
    return _build_panel(
        "bp-defense-validation",
        "ВАЛИДАЦИЯ МОДЕЛИ",
        right_slot=html.Span("МОДЕЛЬ ВАЛИДИРОВАНА", className="c03-defense-chip c03-defense-chip--ok"),
        children=[
            html.Div(
                className="c03-validation-summary",
                children=[
                    html.Div(
                        className=f"c03-validation-summary__row c03-validation-summary__row--{section.state}",
                        children=[
                            html.Span("✓" if section.state == "normal" else "⚠"),
                            html.Strong(section.label),
                            html.Em(f"{section.percent}%"),
                        ],
                    )
                    for section in sections
                ],
            ),
            html.Div(
                className="c03-defense-panel__footer",
                children=[
                    html.Span(f"Срез {view.readiness.generated_at_text}"),
                    html.Span(view.readiness.status_text),
                ],
            ),
        ],
    )


def _build_export_package_panel(view: Concept03BottomView) -> html.Div:
    rows = (
        ("Паспорт установки", "PDF"),
        ("Описание модели", "PDF"),
        ("Результаты сценария", "CSV"),
        ("Графики сравнения", "PDF"),
        ("2D схема", "SVG"),
        ("3D вид", "PNG"),
    )
    return _build_panel(
        "bp-defense-export",
        "ЭКСПОРТНЫЙ ПАКЕТ ДЛЯ ЗАЩИТЫ",
        right_slot=html.Span(view.reports.status_text, className=_chip_class(view.reports.state)),
        children=[
            html.Div(
                className="c03-export-package",
                children=[
                    html.Div(
                        className="c03-export-package__row",
                        children=[
                            html.Span(title),
                            html.Strong(format_text),
                        ],
                    )
                    for title, format_text in rows
                ],
            ),
            html.Div(
                className="c03-defense-panel__footer",
                children=[
                    html.Span(view.reports.latest_report_text),
                    html.Button(
                        id="concept03-defense-report-build",
                        type="button",
                        className="c03-report-build-button",
                        children="Сформировать пакет",
                    ),
                ],
            ),
        ],
    )


def _build_scenario_comparison_panel(view: Concept03BottomView) -> html.Div:
    rows = (
        ("Показатель", view.comparison.metric_label),
        ("Пара сценариев", view.comparison.pair_text),
        ("Состояние", view.comparison.status_text),
        ("Итог", view.comparison.summary_text),
    )
    return _build_panel(
        "bp-defense-comparison",
        "СРАВНЕНИЕ СЦЕНАРИЕВ",
        right_slot=html.Span(view.comparison.status_text, className=_chip_class(view.comparison.state)),
        children=[
            html.Div(
                className="c03-defense-comparison",
                children=[
                    html.Div(
                        className="c03-defense-comparison__row",
                        children=[
                            html.Span(label),
                            html.Strong(value),
                        ],
                    )
                    for label, value in rows
                ],
            ),
            html.Div(
                className="c03-defense-panel__footer",
                children=[
                    html.Span("Готово для демонстрационного вопроса о сценариях"),
                    html.A("Открыть детальное сравнение", href=view.comparison.cta_href),
                ],
            ),
        ],
    )


def _build_event_log_table_panel(view: Concept03BottomView) -> html.Div:
    return _build_panel(
        "bp-defense-event-log",
        "ЖУРНАЛ СОБЫТИЙ",
        right_slot=html.Span(view.event_log.status_text, className=_chip_class(view.event_log.state)),
        children=[
            html.Div(
                className="c03-defense-event-table",
                children=[
                    html.A(
                        href=row.href,
                        className=f"c03-defense-event-table__row c03-defense-event-table__row--{row.state}",
                        children=[
                            html.Span(row.timestamp_text),
                            html.Strong(row.level_text),
                            html.Span(row.message),
                        ],
                    )
                    for row in view.event_log.rows[:7]
                ],
            ),
            html.Div(
                className="c03-defense-panel__footer",
                children=[
                    html.Span(view.event_log.summary_text),
                    html.A("Открыть журнал", href=view.event_log.cta_href),
                ],
            ),
        ],
    )


def _build_readiness_checks_panel(view: Concept03BottomView) -> html.Div:
    checks = (
        ("Модель валидирована", view.readiness.status_text),
        ("Сценарии готовы", f"{len(view.comparison.source_options)} источн."),
        ("Отчёты сформированы", view.reports.status_text),
        ("2D схема актуальна", "Да"),
    )
    return _build_panel(
        "bp-defense-readiness",
        "ГОТОВНОСТЬ К ЗАЩИТЕ",
        right_slot=html.Span("Проверено", className="c03-defense-chip c03-defense-chip--ok"),
        children=[
            html.Div(
                className="c03-readiness-checks",
                children=[
                    html.Div(
                        className=f"c03-donut c03-donut--{view.readiness.state}",
                        style={"--c03-donut-value": f"{view.readiness.overall_percent * 3.6}deg"},
                        children=[
                            html.Strong(f"{view.readiness.overall_percent}"),
                            html.Span("%"),
                        ],
                    ),
                    html.Div(
                        className="c03-readiness-checks__list",
                        children=[
                            html.Div(
                                className="c03-readiness-checks__row",
                                children=[
                                    html.Span("✓"),
                                    html.Strong(label),
                                    html.Em(value),
                                ],
                            )
                            for label, value in checks
                        ],
                    ),
                ],
            ),
            html.Div(
                className="c03-defense-panel__footer",
                children=[
                    html.Span("Контур защиты готов к офлайн-показу"),
                    html.A("Открыть чек-лист защиты", href="?theme=concept03&defense=true&page=analytics#defense-checklist"),
                ],
            ),
        ],
    )


def _build_panel(
    panel_id: str,
    title: str,
    *,
    right_slot,
    children: list,
) -> html.Div:
    return html.Div(
        id=panel_id,
        className="c03-bottom-panel c03-defense-bottom-panel",
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


def _chip_class(state: str) -> str:
    return f"c03-bottom-status c03-bottom-status--{state}"
