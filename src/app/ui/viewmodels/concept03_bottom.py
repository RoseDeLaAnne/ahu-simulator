from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from app.services.comparison_service import RunComparison, RunComparisonSnapshot
from app.services.demo_readiness_service import DemoReadinessEvaluation
from app.services.event_log_service import EventLogSnapshot
from app.services.export_service import ResultExportSnapshot
from app.simulation.state import AlarmLevel, OperationStatus, SimulationSession


@dataclass(frozen=True)
class Concept03ReadinessSectionView:
    section_id: str
    label: str
    percent: int
    state: str
    detail: str
    href: str


@dataclass(frozen=True)
class Concept03ReadinessPanelView:
    overall_percent: int
    status_text: str
    state: str
    generated_at_text: str
    sections: list[Concept03ReadinessSectionView]


@dataclass(frozen=True)
class Concept03ComparisonSeriesView:
    label: str
    points: list[float]
    dashed: bool = False


@dataclass(frozen=True)
class Concept03ComparisonMetricOptionView:
    metric_id: str
    label: str


@dataclass(frozen=True)
class Concept03MobileComparisonMetricView:
    metric_id: str
    label: str
    before_text: str
    after_text: str


@dataclass(frozen=True)
class Concept03ComparisonSourceOptionView:
    reference_id: str
    label: str


@dataclass(frozen=True)
class Concept03ComparisonPanelView:
    selected_metric_id: str
    selected_before_reference_id: str | None
    selected_after_reference_id: str | None
    metric_label: str
    metric_options: list[Concept03ComparisonMetricOptionView]
    source_options: list[Concept03ComparisonSourceOptionView]
    status_text: str
    state: str
    summary_text: str
    pair_text: str
    minutes: list[int]
    series: list[Concept03ComparisonSeriesView]
    mobile_metrics: list[Concept03MobileComparisonMetricView]
    cta_href: str


@dataclass(frozen=True)
class Concept03EventRowView:
    event_id: str
    timestamp_text: str
    level_text: str
    state: str
    message: str
    href: str


@dataclass(frozen=True)
class Concept03EventLogPanelView:
    status_text: str
    state: str
    summary_text: str
    rows: list[Concept03EventRowView]
    cta_href: str


@dataclass(frozen=True)
class Concept03ReportRowView:
    row_id: str
    title: str
    format_text: str
    state: str
    href: str | None


@dataclass(frozen=True)
class Concept03ReportsPanelView:
    status_text: str
    state: str
    summary_text: str
    latest_report_text: str
    rows: list[Concept03ReportRowView]


@dataclass(frozen=True)
class Concept03FooterNavItemView:
    page_id: str
    label: str
    icon: str
    href: str
    is_active: bool


@dataclass(frozen=True)
class Concept03SecuredLoopView:
    state: str
    label: str
    detail: str
    local_services_text: str
    external_dependencies_text: str


@dataclass(frozen=True)
class Concept03FooterNavView:
    items: list[Concept03FooterNavItemView]
    secured_loop: Concept03SecuredLoopView
    version_text: str


@dataclass(frozen=True)
class Concept03BottomView:
    readiness: Concept03ReadinessPanelView
    comparison: Concept03ComparisonPanelView
    event_log: Concept03EventLogPanelView
    reports: Concept03ReportsPanelView
    footer_nav: Concept03FooterNavView


FOOTER_NAV_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("dashboard", "Дашборд", "layout-grid"),
    ("equipment", "Оборудование", "boxes"),
    ("control", "Управление", "sliders-horizontal"),
    ("analytics", "Аналитика", "bar-chart-3"),
    ("library", "Библиотека", "book-marked"),
    ("settings", "Настройки", "settings"),
)

CONCEPT03_COMPARISON_METRICS: tuple[Concept03ComparisonMetricOptionView, ...] = (
    Concept03ComparisonMetricOptionView("supply_temp_c", "Приток"),
    Concept03ComparisonMetricOptionView("room_temp_c", "Помещение"),
    Concept03ComparisonMetricOptionView("actual_airflow_m3_h", "Расход"),
    Concept03ComparisonMetricOptionView("heating_power_kw", "Нагрев"),
    Concept03ComparisonMetricOptionView("total_power_kw", "Мощность"),
    Concept03ComparisonMetricOptionView("filter_pressure_drop_pa", "ΔP фильтра"),
)

MOBILE_COMPARISON_METRICS: tuple[tuple[str, str, str, int], ...] = (
    ("supply_temp_c", "Приток", "°C", 1),
    ("actual_airflow_m3_h", "Расход", "м³/ч", 0),
    ("total_power_kw", "Мощн.", "кВт", 1),
    ("cop_estimate", "COP", "", 2),
)


def build_concept03_bottom_view(
    *,
    session: SimulationSession,
    demo_readiness: DemoReadinessEvaluation,
    comparison_snapshot: RunComparisonSnapshot,
    comparison: RunComparison | None = None,
    selected_before_reference_id: str | None = None,
    selected_after_reference_id: str | None = None,
    event_log_snapshot: EventLogSnapshot,
    export_snapshot: ResultExportSnapshot,
    active_page: str = "dashboard",
    app_version: str = "2.4.1",
) -> Concept03BottomView:
    return Concept03BottomView(
        readiness=_build_readiness_panel(demo_readiness),
        comparison=_build_comparison_panel(
            session,
            comparison_snapshot,
            comparison=comparison,
            selected_before_reference_id=selected_before_reference_id,
            selected_after_reference_id=selected_after_reference_id,
        ),
        event_log=_build_event_log_panel(event_log_snapshot),
        reports=_build_reports_panel(export_snapshot, comparison_snapshot),
        footer_nav=_build_footer_nav(
            demo_readiness,
            active_page=active_page,
            app_version=app_version,
        ),
    )


def footer_nav_class_name(page_id: str, active_page: str) -> str:
    class_name = "c03-footer-nav__link"
    if page_id == active_page:
        class_name += " c03-footer-nav__link--active"
    return class_name


def resolve_concept03_comparison_metric(metric_id: str | None) -> str:
    allowed_metric_ids = {
        option.metric_id for option in CONCEPT03_COMPARISON_METRICS
    }
    if metric_id in allowed_metric_ids:
        return str(metric_id)
    return CONCEPT03_COMPARISON_METRICS[0].metric_id


def _build_readiness_panel(
    evaluation: DemoReadinessEvaluation,
) -> Concept03ReadinessPanelView:
    total = max(evaluation.total_checks, 1)
    overall_percent = round(100 * evaluation.ready_checks / total)
    return Concept03ReadinessPanelView(
        overall_percent=overall_percent,
        status_text=_readiness_status_text(evaluation.overall_status, overall_percent),
        state=_state_name(evaluation.overall_status),
        generated_at_text=evaluation.generated_at.astimezone().strftime("%H:%M"),
        sections=_readiness_sections(evaluation),
    )


def _readiness_sections(
    evaluation: DemoReadinessEvaluation,
) -> list[Concept03ReadinessSectionView]:
    check_map = {check.item_id: check for check in evaluation.checks}

    section_specs = (
        (
            "structure",
            "Структура модели",
            ("runtime-stack", "launch-script"),
            "?theme=concept03&page=library&tab=architecture",
        ),
        (
            "parametrization",
            "Параметризация",
            ("source-inputs",),
            "?theme=concept03&page=library&tab=baseline",
        ),
        (
            "verification",
            "Верификация",
            ("tests-and-artifacts", "demo-pc-verification"),
            "?theme=concept03&page=analytics&tab=validation",
        ),
        (
            "validation",
            "Валидация",
            ("demo-pc-verification", "source-inputs"),
            "?theme=concept03&page=analytics&tab=manual-check",
        ),
        (
            "documentation",
            "Документирование",
            ("docs-and-defense",),
            "?theme=concept03&page=library&tab=defense",
        ),
    )

    sections: list[Concept03ReadinessSectionView] = []
    for section_id, label, check_ids, href in section_specs:
        checks = [check_map[check_id] for check_id in check_ids if check_id in check_map]
        percent = _status_percent([check.status for check in checks])
        sections.append(
            Concept03ReadinessSectionView(
                section_id=section_id,
                label=label,
                percent=percent,
                state=_percent_state(percent),
                detail=_section_detail(checks),
                href=href,
            )
        )
    return sections


def _build_comparison_panel(
    session: SimulationSession,
    comparison_snapshot: RunComparisonSnapshot,
    *,
    comparison: RunComparison | None,
    selected_before_reference_id: str | None,
    selected_after_reference_id: str | None,
) -> Concept03ComparisonPanelView:
    selected_metric_id = resolve_concept03_comparison_metric(
        comparison_snapshot.selected_metric_id
    )
    selected_before_reference_id = _resolve_selected_source_reference(
        comparison_snapshot,
        selected_before_reference_id,
        fallback_reference_id=comparison_snapshot.default_before_reference_id,
    )
    selected_after_reference_id = _resolve_selected_source_reference(
        comparison_snapshot,
        selected_after_reference_id,
        fallback_reference_id=comparison_snapshot.default_after_reference_id,
    )
    source_options = [
        Concept03ComparisonSourceOptionView(
            reference_id=source.reference_id,
            label=_compact_text(
                source.display_label,
                fallback=source.source_label,
                limit=46,
            ),
        )
        for source in comparison_snapshot.available_sources
    ]

    if comparison is not None:
        minutes, series = _build_comparison_delta_series(
            comparison,
            selected_metric_id,
        )
        return Concept03ComparisonPanelView(
            selected_metric_id=selected_metric_id,
            selected_before_reference_id=selected_before_reference_id,
            selected_after_reference_id=selected_after_reference_id,
            metric_label=(
                comparison_snapshot.selected_metric_title
                if getattr(comparison_snapshot, "selected_metric_title", None)
                else "Температура приточного воздуха, °C"
            ),
            metric_options=list(CONCEPT03_COMPARISON_METRICS),
            source_options=source_options,
            status_text=(
                _status_label(comparison.comparison_status)
                if comparison.compatibility.is_compatible
                else "Несовместимо"
            ),
            state=_state_name(comparison.comparison_status),
            summary_text=_compact_text(
                (
                    comparison.interpretation.summary
                    if comparison.compatibility.is_compatible
                    else comparison.compatibility.summary
                ),
                fallback=comparison.summary,
                limit=124,
            ),
            pair_text=_comparison_pair_text(
                comparison_snapshot,
                selected_before_reference_id,
                selected_after_reference_id,
            ),
            minutes=minutes,
            series=series,
            mobile_metrics=_build_mobile_comparison_metrics(
                session,
                comparison=comparison,
            ),
            cta_href="?theme=concept03&page=analytics&tab=comparison",
        )

    points = session.history.points
    if len(points) < 2:
        points = session.current_result.trend.points[:8]
    if not points:
        points = [session.current_result.state]
    minutes = [getattr(point, "minute", session.elapsed_minutes) for point in points]
    model_values = [
        _metric_value(point, selected_metric_id)
        for point in points
    ]
    reference_value = _reference_metric_value(session, selected_metric_id)
    reference_values = [reference_value for _ in points]
    if not minutes:
        minutes = [0]
        model_values = [
            _metric_value(session.current_result.state, selected_metric_id)
        ]
        reference_values = [reference_value]

    return Concept03ComparisonPanelView(
        selected_metric_id=selected_metric_id,
        selected_before_reference_id=selected_before_reference_id,
        selected_after_reference_id=selected_after_reference_id,
        metric_label=(
            comparison_snapshot.selected_metric_title
            if getattr(comparison_snapshot, "selected_metric_title", None)
            else "Температура приточного воздуха, °C"
        ),
        metric_options=list(CONCEPT03_COMPARISON_METRICS),
        source_options=source_options,
        status_text=_status_label(comparison_snapshot.overall_status),
        state=_state_name(comparison_snapshot.overall_status),
        summary_text=_compact_text(
            comparison_snapshot.summary,
            fallback="Активный прогон сравнивается с расчётной уставкой.",
            limit=124,
        ),
        pair_text=_comparison_pair_text(
            comparison_snapshot,
            selected_before_reference_id,
            selected_after_reference_id,
        ),
        minutes=minutes,
        series=[
            Concept03ComparisonSeriesView(
                label="Опора",
                points=reference_values,
                dashed=True,
            ),
            Concept03ComparisonSeriesView(
                label="Модель",
                points=model_values,
            ),
        ],
        mobile_metrics=_build_mobile_comparison_metrics(
            session,
            comparison=None,
        ),
        cta_href="?theme=concept03&page=analytics&tab=comparison",
    )


def _build_event_log_panel(
    snapshot: EventLogSnapshot,
) -> Concept03EventLogPanelView:
    rows = [
        Concept03EventRowView(
            event_id=entry.event_id,
            timestamp_text=entry.captured_at.astimezone().strftime("%H:%M:%S"),
            level_text=_event_level_text(entry.level),
            state=_event_state(entry.level),
            message=_compact_text(entry.summary, fallback=entry.title, limit=74),
            href="?theme=concept03&page=analytics&tab=event-log",
        )
        for entry in snapshot.entries[:5]
    ]
    if not rows:
        rows = [
            Concept03EventRowView(
                event_id="event-log-empty",
                timestamp_text="--:--:--",
                level_text="Инфо",
                state="muted",
                message="Нет событий. Запустите сценарий или сформируйте отчёт.",
                href="?theme=concept03&page=analytics&tab=event-log",
            )
        ]

    return Concept03EventLogPanelView(
        status_text=_status_label(snapshot.overall_status),
        state=_state_name(snapshot.overall_status),
        summary_text=_compact_text(snapshot.summary, fallback="Журнал готов.", limit=96),
        rows=rows,
        cta_href="?theme=concept03&page=analytics&tab=event-log",
    )


def _build_reports_panel(
    export_snapshot: ResultExportSnapshot,
    comparison_snapshot: RunComparisonSnapshot,
) -> Concept03ReportsPanelView:
    latest_pdf_url = _export_download_url(export_snapshot.latest_pdf_path)
    latest_csv_url = _export_download_url(export_snapshot.latest_csv_path)
    latest_comparison_pdf_url = _comparison_download_url(
        comparison_snapshot.latest_pdf_path
    )
    rows = [
        Concept03ReportRowView(
            row_id="scenario-report",
            title="Отчёт по сценарию",
            format_text="PDF",
            state="ready" if latest_pdf_url else "pending",
            href=latest_pdf_url,
        ),
        Concept03ReportRowView(
            row_id="validation-protocol",
            title="Протокол валидации",
            format_text="PDF",
            state="ready",
            href="?theme=concept03&page=analytics&tab=validation",
        ),
        Concept03ReportRowView(
            row_id="comparison-report",
            title="Сравнительный отчёт",
            format_text="PDF",
            state="ready" if latest_comparison_pdf_url else "pending",
            href=latest_comparison_pdf_url,
        ),
        Concept03ReportRowView(
            row_id="simulation-data",
            title="Данные моделирования",
            format_text="CSV",
            state="ready" if latest_csv_url else "pending",
            href=latest_csv_url,
        ),
    ]
    return Concept03ReportsPanelView(
        status_text=_status_label(export_snapshot.overall_status),
        state=_state_name(export_snapshot.overall_status),
        summary_text=_compact_text(
            export_snapshot.summary,
            fallback="Единый отчёт ещё не формировался.",
            limit=96,
        ),
        latest_report_text=_latest_report_package_text(
            export_snapshot,
            comparison_snapshot,
        ),
        rows=rows,
    )


def _build_footer_nav(
    evaluation: DemoReadinessEvaluation,
    *,
    active_page: str,
    app_version: str,
) -> Concept03FooterNavView:
    secured_loop = evaluation.secured_loop
    items = [
        Concept03FooterNavItemView(
            page_id=page_id,
            label=label,
            icon=icon,
            href=f"?theme=concept03&page={page_id}",
            is_active=page_id == active_page,
        )
        for page_id, label, icon in FOOTER_NAV_ITEMS
    ]
    return Concept03FooterNavView(
        items=items,
        secured_loop=Concept03SecuredLoopView(
            state=secured_loop.state,
            label=secured_loop.label,
            detail=secured_loop.detail,
            local_services_text=(
                f"{secured_loop.local_services_ready} / "
                f"{secured_loop.local_services_total}"
            ),
            external_dependencies_text=str(secured_loop.external_dependencies),
        ),
        version_text=f"Версия: {app_version}",
    )


def _latest_report_package_text(
    export_snapshot: ResultExportSnapshot,
    comparison_snapshot: RunComparisonSnapshot,
) -> str:
    scenario_report = _compact_text(
        export_snapshot.latest_report_id,
        fallback="сценарий не создан",
        limit=30,
    )
    comparison_report = _compact_text(
        comparison_snapshot.latest_comparison_id,
        fallback="сравнение не создано",
        limit=32,
    )
    return f"Сценарий: {scenario_report} · Сравнение: {comparison_report}"


def _status_percent(statuses: list[OperationStatus]) -> int:
    if not statuses:
        return 0
    scores = {
        OperationStatus.NORMAL: 100,
        OperationStatus.WARNING: 72,
        OperationStatus.ALARM: 36,
    }
    return round(sum(scores[status] for status in statuses) / len(statuses))


def _section_detail(checks) -> str:
    if not checks:
        return "Нет данных для секции."
    if all(check.status == OperationStatus.NORMAL for check in checks):
        return "Все связанные проверки зелёные."
    return "; ".join(check.detail for check in checks)


def _percent_state(percent: int) -> str:
    if percent >= 85:
        return "normal"
    if percent >= 65:
        return "warning"
    return "alarm"


def _state_name(status: OperationStatus) -> str:
    if status == OperationStatus.ALARM:
        return "alarm"
    if status == OperationStatus.WARNING:
        return "warning"
    return "normal"


def _status_label(status: OperationStatus) -> str:
    if status == OperationStatus.ALARM:
        return "Тревога"
    if status == OperationStatus.WARNING:
        return "Внимание"
    return "Готово"


def _readiness_status_text(status: OperationStatus, percent: int) -> str:
    if status == OperationStatus.ALARM:
        return "Требует действий"
    if status == OperationStatus.WARNING:
        return "В процессе"
    if percent >= 100:
        return "Готово"
    return "В процессе"


def _event_level_text(level: AlarmLevel) -> str:
    if level == AlarmLevel.CRITICAL:
        return "Тревога"
    if level == AlarmLevel.WARNING:
        return "Предупр"
    return "Инфо"


def _event_state(level: AlarmLevel) -> str:
    if level == AlarmLevel.CRITICAL:
        return "alarm"
    if level == AlarmLevel.WARNING:
        return "warning"
    return "normal"


def _metric_value(point, metric_id: str) -> float:
    if metric_id == "actual_airflow_m3_h":
        return float(
            getattr(
                point,
                "airflow_m3_h",
                getattr(point, "actual_airflow_m3_h", 0.0),
            )
        )
    if metric_id == "cop_estimate":
        return _cop_estimate(point)
    return float(getattr(point, metric_id, 0.0))


def _reference_metric_value(session: SimulationSession, metric_id: str) -> float:
    parameters = session.current_result.parameters
    state = session.current_result.state
    if metric_id == "supply_temp_c":
        return float(parameters.supply_temp_setpoint_c)
    if metric_id == "room_temp_c":
        return float(parameters.room_temp_c)
    if metric_id == "actual_airflow_m3_h":
        return float(parameters.airflow_m3_h)
    if metric_id == "filter_pressure_drop_pa":
        return float(state.filter_pressure_drop_pa)
    if metric_id == "heating_power_kw":
        return float(state.heating_power_kw)
    if metric_id == "total_power_kw":
        return float(state.total_power_kw)
    if metric_id == "cop_estimate":
        return _cop_estimate(state)
    return _metric_value(state, metric_id)


def _build_mobile_comparison_metrics(
    session: SimulationSession,
    *,
    comparison: RunComparison | None,
) -> list[Concept03MobileComparisonMetricView]:
    deltas_by_metric = {
        delta.metric_id: delta for delta in comparison.metric_deltas
    } if comparison is not None else {}
    rows: list[Concept03MobileComparisonMetricView] = []
    for metric_id, label, unit, digits in MOBILE_COMPARISON_METRICS:
        before_value = _mobile_before_metric_value(
            session,
            metric_id,
            deltas_by_metric,
        )
        after_value = _mobile_after_metric_value(
            session,
            metric_id,
            deltas_by_metric,
        )
        rows.append(
            Concept03MobileComparisonMetricView(
                metric_id=metric_id,
                label=label,
                before_text=_format_metric_value(before_value, unit=unit, digits=digits),
                after_text=_format_metric_value(after_value, unit=unit, digits=digits),
            )
        )
    return rows


def _mobile_before_metric_value(
    session: SimulationSession,
    metric_id: str,
    deltas_by_metric,
) -> float:
    if metric_id == "cop_estimate":
        return _comparison_cop_value(deltas_by_metric, value_side="before") or _cop_estimate(
            session.current_result.state
        )
    if metric_id in deltas_by_metric:
        return float(deltas_by_metric[metric_id].before_value)
    return _reference_metric_value(session, metric_id)


def _mobile_after_metric_value(
    session: SimulationSession,
    metric_id: str,
    deltas_by_metric,
) -> float:
    if metric_id == "cop_estimate":
        return _comparison_cop_value(deltas_by_metric, value_side="after") or _cop_estimate(
            session.current_result.state
        )
    if metric_id in deltas_by_metric:
        return float(deltas_by_metric[metric_id].after_value)
    return _metric_value(session.current_result.state, metric_id)


def _comparison_cop_value(deltas_by_metric, *, value_side: str) -> float | None:
    heating = deltas_by_metric.get("heating_power_kw")
    total = deltas_by_metric.get("total_power_kw")
    if heating is None or total is None:
        return None
    heating_value = getattr(heating, f"{value_side}_value")
    total_value = getattr(total, f"{value_side}_value")
    return float(heating_value) / max(float(total_value), 0.1)


def _cop_estimate(point) -> float:
    heating_power_kw = float(getattr(point, "heating_power_kw", 0.0))
    total_power_kw = float(getattr(point, "total_power_kw", 0.0))
    return heating_power_kw / max(total_power_kw, 0.1)


def _format_metric_value(value: float, *, unit: str, digits: int) -> str:
    number = f"{value:,.{digits}f}".replace(",", " ")
    if digits == 0:
        number = number.split(".")[0]
    return f"{number} {unit}".strip()


def _resolve_selected_source_reference(
    snapshot: RunComparisonSnapshot,
    current_reference_id: str | None,
    *,
    fallback_reference_id: str | None,
) -> str | None:
    available_reference_ids = {
        source.reference_id for source in snapshot.available_sources
    }
    if current_reference_id in available_reference_ids:
        return current_reference_id
    if fallback_reference_id in available_reference_ids:
        return fallback_reference_id
    return None


def _comparison_pair_text(
    snapshot: RunComparisonSnapshot,
    before_reference_id: str | None,
    after_reference_id: str | None,
) -> str:
    before_label = _source_label(snapshot, before_reference_id, fallback="До не выбрано")
    after_label = _source_label(snapshot, after_reference_id, fallback="После не выбрано")
    return _compact_text(
        f"{before_label} → {after_label}",
        fallback="Пара сравнения не выбрана.",
        limit=112,
    )


def _source_label(
    snapshot: RunComparisonSnapshot,
    reference_id: str | None,
    *,
    fallback: str,
) -> str:
    for source in snapshot.available_sources:
        if source.reference_id == reference_id:
            return source.display_label
    return fallback


def _build_comparison_delta_series(
    comparison: RunComparison,
    metric_id: str,
) -> tuple[list[int], list[Concept03ComparisonSeriesView]]:
    trend_field = _trend_delta_field(metric_id)
    if comparison.compatibility.is_compatible and trend_field and comparison.trend_deltas:
        minutes = [point.minute for point in comparison.trend_deltas]
        delta_values = [
            float(getattr(point, trend_field))
            for point in comparison.trend_deltas
        ]
        return minutes, [
            Concept03ComparisonSeriesView("0", [0.0 for _ in minutes], dashed=True),
            Concept03ComparisonSeriesView("Δ после-до", delta_values),
        ]

    metric_delta = next(
        (
            metric
            for metric in comparison.metric_deltas
            if metric.metric_id == metric_id
        ),
        None,
    )
    if metric_delta is not None:
        return [0, 1], [
            Concept03ComparisonSeriesView("0", [0.0, 0.0], dashed=True),
            Concept03ComparisonSeriesView(
                "Δ после-до",
                [0.0, float(metric_delta.delta_value)],
            ),
        ]

    return [0, 1], [
        Concept03ComparisonSeriesView("0", [0.0, 0.0], dashed=True),
        Concept03ComparisonSeriesView("Δ после-до", [0.0, 0.0]),
    ]


def _trend_delta_field(metric_id: str) -> str | None:
    fields = {
        "supply_temp_c": "supply_temp_delta_c",
        "room_temp_c": "room_temp_delta_c",
        "actual_airflow_m3_h": "airflow_delta_m3_h",
        "total_power_kw": "total_power_delta_kw",
        "filter_pressure_drop_pa": "filter_pressure_drop_delta_pa",
    }
    return fields.get(metric_id)


def _compact_text(text: str | None, *, fallback: str, limit: int) -> str:
    value = (text or fallback).strip()
    if len(value) <= limit:
        return value
    return value[: max(limit - 1, 1)].rstrip() + "…"


def _export_download_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"/exports/result/download?path={quote(path, safe='')}"


def _comparison_download_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"/comparison/runs/download?path={quote(path, safe='')}"
