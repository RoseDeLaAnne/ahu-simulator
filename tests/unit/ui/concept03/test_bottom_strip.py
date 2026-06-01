from datetime import datetime, timezone
from pathlib import Path

from app.services.comparison_service import (
    ACTIVE_RUN_REFERENCE_ID,
    RunComparisonService,
    RunComparisonSnapshot,
)
from app.services.demo_readiness_service import (
    DemoReadinessCheck,
    DemoReadinessEvaluation,
    SecuredLoopStatus,
)
from app.services.event_log_service import EventCategory, EventLogEntry, EventLogSnapshot
from app.services.export_service import ResultExportSnapshot
from app.services.scenario_archive_service import ScenarioArchiveService
from app.services.simulation_service import SimulationService
from app.services.trend_service import TrendService
from app.simulation.parameters import ControlMode
from app.simulation.scenarios import load_scenarios
from app.simulation.state import AlarmLevel, OperationStatus
from app.ui.concept03.bottom_strip import build_bottom_strip
from app.ui.concept03.footer_nav import build_footer_nav
from app.ui.viewmodels.concept03_bottom import (
    CONCEPT03_COMPARISON_METRICS,
    build_concept03_bottom_view,
    resolve_concept03_comparison_metric,
)
from app.ui.viewmodels.concept03_scenarios import build_concept03_scenarios_view


PROJECT_ROOT = Path(__file__).resolve().parents[4]


def test_bottom_strip_renders_phase6_panels_and_report_action() -> None:
    view = _build_view(active_page="analytics")

    strip = build_bottom_strip(view)
    payload = str(strip.to_plotly_json())

    assert strip.id == "bottom-strip"
    assert "c03-bottom-strip" in strip.className
    assert len(_find_id_prefix(strip, "bp-")) == 4
    assert "ГОТОВНОСТЬ К ВАЛИДАЦИИ" in payload
    assert "concept03-comparison-metric" in payload
    assert "concept03-comparison-before" in payload
    assert "concept03-comparison-after" in payload
    assert "concept03-comparison-mini-graph" in payload
    assert "ЖУРНАЛ СОБЫТИЙ" in payload
    assert "concept03-report-build" in payload


def test_bottom_strip_renders_mobile_field_cards_and_comparison_table() -> None:
    view = _build_view(active_page="dashboard")

    strip = build_bottom_strip(
        view,
        scenarios_view=_scenario_view(active_scenario_id="summer_eco"),
    )
    payload = str(strip.to_plotly_json())

    assert "mobile-field-row" in payload
    assert "mobile-scenario-card" in payload
    assert "mobile-readiness-card" in payload
    assert "Зимний режим" in payload
    assert "Готовность к защите" in payload
    assert "mobile-comparison" in payload
    assert "mobile-event-log" in payload
    assert "mobile-exports" in payload
    assert "COP" in payload


def test_bottom_strip_can_render_defense_day_panels() -> None:
    view = _build_view(active_page="dashboard")

    strip = build_bottom_strip(view, include_defense=True)
    payload = str(strip.to_plotly_json())

    assert len(_find_id_prefix(strip, "bp-defense-")) == 5
    assert "ВАЛИДАЦИЯ МОДЕЛИ" in payload
    assert "ЭКСПОРТНЫЙ ПАКЕТ ДЛЯ ЗАЩИТЫ" in payload
    assert "СРАВНЕНИЕ СЦЕНАРИЕВ" in payload
    assert "ГОТОВНОСТЬ К ЗАЩИТЕ" in payload
    assert "concept03-defense-report-build" in payload


def test_footer_nav_renders_six_items_active_state_and_secured_loop() -> None:
    view = _build_view(active_page="analytics")

    footer = build_footer_nav(view.footer_nav)
    payload = str(footer.to_plotly_json())

    assert footer.id == "app-footer-nav"
    assert len(_find_id_prefix(footer, "footer-nav-")) == 6
    assert len(_find_id_prefix(footer, "mobile-nav-")) == 5
    assert "footer-nav-analytics" in payload
    assert "mobile-bottom-nav" in payload
    assert "mobile-offcanvas" in payload
    assert "Библиотека" in payload
    assert "c03-footer-nav__link--active" in payload
    assert "c03-mobile-bottom-nav__link--active" in payload
    assert "ЗАЩИЩЕННЫЙ КОНТУР" in payload
    assert "ВКР 2026" in payload
    assert "Сохранено" in payload


def test_bottom_view_maps_readiness_percent_and_event_rows() -> None:
    view = _build_view(active_page="dashboard")

    assert view.readiness.overall_percent == 80
    assert len(view.readiness.sections) == 5
    assert view.event_log.rows[0].level_text == "Предупр"
    assert view.comparison.selected_metric_id == "supply_temp_c"
    assert view.comparison.selected_before_reference_id is None
    assert view.comparison.selected_after_reference_id is None
    assert len(view.comparison.metric_options) == len(CONCEPT03_COMPARISON_METRICS)
    assert [metric.metric_id for metric in view.comparison.mobile_metrics] == [
        "supply_temp_c",
        "actual_airflow_m3_h",
        "total_power_kw",
        "cop_estimate",
    ]
    assert len(view.comparison.series) == 2
    assert view.reports.rows[-1].format_text == "CSV"


def test_bottom_view_maps_selected_comparison_metric_to_series_points() -> None:
    service = SimulationService(
        scenarios=load_scenarios(PROJECT_ROOT / "data" / "scenarios" / "presets.json"),
        trend_service=TrendService(),
        default_scenario_id="baseline_office_winter",
    )
    session = service.get_session()
    view = _build_view(
        active_page="analytics",
        metric_id="total_power_kw",
        metric_title="Суммарная мощность, кВт",
        session=session,
    )

    expected_points = [
        point.total_power_kw
        for point in session.current_result.trend.points[:8]
    ]

    assert resolve_concept03_comparison_metric("unknown") == "supply_temp_c"
    assert view.comparison.selected_metric_id == "total_power_kw"
    assert view.comparison.metric_label == "Суммарная мощность, кВт"
    assert view.comparison.series[1].points == expected_points


def test_bottom_view_maps_selected_pair_to_delta_series(tmp_path: Path) -> None:
    simulation_service = SimulationService(
        scenarios=load_scenarios(PROJECT_ROOT / "data" / "scenarios" / "presets.json"),
        trend_service=TrendService(),
        default_scenario_id="baseline_office_winter",
    )
    session = simulation_service.get_session()
    archive_service = ScenarioArchiveService(project_root=tmp_path)
    archived_result = simulation_service.preview_scenario("winter")
    archive_entry = archive_service.save_result(archived_result).entry
    comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=archive_service,
    )
    before_reference_id = f"archive:{archive_entry.archive_id}"
    comparison = comparison_service.build_comparison_from_references(
        before_reference_id,
        ACTIVE_RUN_REFERENCE_ID,
        session.current_result,
        session,
    )
    snapshot = comparison_service.build_snapshot(
        session.current_result,
        session,
        metric_id="total_power_kw",
    )
    view = build_concept03_bottom_view(
        session=session,
        demo_readiness=_readiness(),
        comparison_snapshot=snapshot,
        comparison=comparison,
        selected_before_reference_id=before_reference_id,
        selected_after_reference_id=ACTIVE_RUN_REFERENCE_ID,
        event_log_snapshot=_event_log_snapshot(),
        export_snapshot=_export_snapshot(),
        active_page="analytics",
    )

    expected_points = [
        point.total_power_delta_kw
        for point in comparison.trend_deltas
    ]

    assert view.comparison.selected_before_reference_id == before_reference_id
    assert view.comparison.selected_after_reference_id == ACTIVE_RUN_REFERENCE_ID
    assert len(view.comparison.source_options) >= 2
    assert view.comparison.series[0].dashed is True
    assert view.comparison.series[1].label == "Δ после-до"
    assert view.comparison.series[1].points == expected_points
    assert len(view.comparison.mobile_metrics) == 4
    assert "Архив сценариев" in view.comparison.pair_text


def test_reports_panel_summarizes_scenario_and_comparison_package() -> None:
    view = _build_view(
        active_page="dashboard",
        latest_report_id="pvu-report-20260418-120000",
        latest_comparison_id="pvu-comparison-20260418-120000",
        latest_comparison_pdf_path=(
            "artifacts/exports/2026-04-18/pvu-comparison-20260418-120000.pdf"
        ),
    )

    assert "Сценарий: pvu-report-20260418-120000" in view.reports.latest_report_text
    assert "Сравнение: pvu-comparison-20260418-120000" in view.reports.latest_report_text
    assert view.reports.rows[2].row_id == "comparison-report"
    assert view.reports.rows[2].state == "ready"


def _build_view(
    active_page: str,
    *,
    metric_id: str = "supply_temp_c",
    metric_title: str = "Температура приточного воздуха, °C",
    latest_report_id: str | None = None,
    latest_comparison_id: str | None = None,
    latest_comparison_pdf_path: str | None = None,
    session=None,
):
    service = SimulationService(
        scenarios=load_scenarios(PROJECT_ROOT / "data" / "scenarios" / "presets.json"),
        trend_service=TrendService(),
        default_scenario_id="baseline_office_winter",
    )
    if session is None:
        session = service.get_session()
    return build_concept03_bottom_view(
        session=session,
        demo_readiness=_readiness(),
        comparison_snapshot=RunComparisonSnapshot(
            generated_at=datetime.now(timezone.utc),
            overall_status=OperationStatus.NORMAL,
            summary="Сравнение готово.",
            note="",
            selected_metric_id=metric_id,
            selected_metric_title=metric_title,
            latest_comparison_id=latest_comparison_id,
            latest_pdf_path=latest_comparison_pdf_path,
            total_exports=0,
        ),
        event_log_snapshot=_event_log_snapshot(),
        export_snapshot=_export_snapshot(latest_report_id=latest_report_id),
        active_page=active_page,
    )


def _scenario_view(*, active_scenario_id: str):
    scenarios = load_scenarios(PROJECT_ROOT / "data" / "scenarios" / "presets.json")
    return build_concept03_scenarios_view(
        scenarios,
        active_scenario_id=active_scenario_id,
    )


def _readiness() -> DemoReadinessEvaluation:
    checks = [
        DemoReadinessCheck(
            item_id="runtime-stack",
            title="Runtime",
            status=OperationStatus.NORMAL,
            detail="Runtime готов.",
        ),
        DemoReadinessCheck(
            item_id="launch-script",
            title="Launch",
            status=OperationStatus.NORMAL,
            detail="Скрипт готов.",
        ),
        DemoReadinessCheck(
            item_id="source-inputs",
            title="Inputs",
            status=OperationStatus.NORMAL,
            detail="Входы готовы.",
        ),
        DemoReadinessCheck(
            item_id="tests-and-artifacts",
            title="Tests",
            status=OperationStatus.NORMAL,
            detail="Тесты готовы.",
        ),
        DemoReadinessCheck(
            item_id="demo-pc-verification",
            title="Browser",
            status=OperationStatus.WARNING,
            detail="Требуется свежий браузерный прогон.",
        ),
    ]
    return DemoReadinessEvaluation(
        generated_at=datetime.now(timezone.utc),
        overall_status=OperationStatus.WARNING,
        ready_checks=4,
        total_checks=5,
        summary="4 из 5 пунктов готовы.",
        note="",
        checks=checks,
        secured_loop=SecuredLoopStatus(
            state="reduced",
            label="ЗАЩИЩЕННЫЙ КОНТУР",
            detail="Контур локальный.",
            local_services_ready=4,
            local_services_total=5,
            external_dependencies=0,
        ),
    )


def _event_log_snapshot() -> EventLogSnapshot:
    return EventLogSnapshot(
        generated_at=datetime.now(timezone.utc),
        overall_status=OperationStatus.WARNING,
        summary="В журнале есть предупреждение.",
        note="",
        target_directory="artifacts/event-log",
        latest_entry_path="artifacts/event-log/latest.json",
        total_entries=1,
        entries=[
            EventLogEntry(
                event_id="event-1",
                captured_at=datetime.now(timezone.utc),
                category=EventCategory.SIMULATION,
                level=AlarmLevel.WARNING,
                title="Фильтр",
                summary="ΔP фильтра выше нормы.",
                source_type="test",
                source_label="Unit",
                control_mode=ControlMode.AUTO,
                status=OperationStatus.WARNING,
                file_path="artifacts/event-log/event-1.json",
            )
        ],
    )


def _export_snapshot(
    *,
    latest_report_id: str | None = None,
) -> ResultExportSnapshot:
    return ResultExportSnapshot(
        generated_at=datetime.now(timezone.utc),
        overall_status=OperationStatus.WARNING,
        summary="Отчёты ещё не собирались.",
        note="",
        target_directory="artifacts/exports",
        latest_report_id=latest_report_id,
        total_entries=0,
    )


def _walk(component):
    yield component
    children = getattr(component, "children", None)
    if isinstance(children, list | tuple):
        for child in children:
            if child is not None:
                yield from _walk(child)
    elif children is not None and not isinstance(children, str):
        yield from _walk(children)


def _find_id_prefix(component, prefix: str) -> list:
    return [
        child
        for child in _walk(component)
        if isinstance(getattr(child, "id", None), str)
        and child.id.startswith(prefix)
    ]
