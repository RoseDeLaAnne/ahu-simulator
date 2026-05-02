from dash import dcc, html

from app.infrastructure.settings import get_project_root, get_settings
from app.services.browser_capability_service import BrowserCapabilityProfile
from app.services.comparison_service import RunComparisonSnapshot
from app.services.demo_readiness_service import (
    DemoPackageSnapshot,
    DemoReadinessEvaluation,
)
from app.services.event_log_service import EventLogSnapshot
from app.services.export_service import ResultExportSnapshot
from app.services.project_baseline_service import ProjectBaselineSnapshot
from app.services.scenario_archive_service import ScenarioArchiveSnapshot
from app.services.status_service import StatusLegendEntry
from app.services.validation_service import (
    ManualCheckEvaluation,
    ValidationAgreementEvaluation,
    ValidationBasisEvaluation,
    ValidationMatrixEvaluation,
)
from app.simulation.parameters import ControlMode
from app.simulation.scenarios import ScenarioDefinition
from app.simulation.state import SimulationResult, SimulationSession, SimulationSessionStatus
from app.ui.scene.bindings import load_scene_bindings
from app.ui.scene.model_catalog import build_scene_model_catalog
from app.ui.scene.room_catalog import (
    build_room_catalog,
    build_room_runtime_payload,
    resolve_room_descriptor,
)
from app.ui.render_modes import (
    build_scene2d_workspace,
    build_scene3d_workspace,
)
from app.ui.viewmodels.control_modes import ControlModeView, build_control_mode_view
from app.ui.viewmodels.demo_readiness import (
    DemoPackageEntryView,
    DemoPackageView,
    DemoReadinessCheckView,
    DemoReadinessCommandView,
    DemoReadinessEndpointView,
    DemoReadinessRuntimeView,
    DemoReadinessView,
    build_demo_package_view,
    build_demo_readiness_view,
)
from app.ui.viewmodels.export_pack import (
    ResultExportEntryView,
    ResultExportView,
    build_result_export_view,
)
from app.ui.viewmodels.browser_diagnostics import (
    DemoBrowserReadinessView,
    build_browser_profile_view,
    build_demo_browser_readiness_view,
)
from app.ui.viewmodels.run_comparison import (
    RunComparisonEntryView,
    RunComparisonView,
    build_run_comparison_view,
)
from app.ui.viewmodels.event_log import (
    EventLogEntryView,
    EventLogView,
    build_event_log_view,
)
from app.ui.viewmodels.defense_pack import (
    DefensePackView,
    DemoFlowStep,
    build_defense_pack_view,
)
from app.ui.viewmodels.manual_check import (
    ManualCheckStepView,
    ManualCheckView,
    build_manual_check_view,
)
from app.ui.viewmodels.project_baseline import (
    ProjectBaselineDecisionView,
    ProjectBaselineOutputView,
    ProjectBaselineParameterView,
    ProjectBaselineScenarioView,
    ProjectBaselineValidationLayerView,
    ProjectBaselineView,
    build_project_baseline_view,
)
from app.ui.viewmodels.scenario_archive import (
    ScenarioArchiveEntryView,
    ScenarioArchiveView,
    build_scenario_archive_view,
)
from app.ui.viewmodels.validation_basis import (
    ValidationBasisLinkView,
    ValidationBasisSourceView,
    ValidationBasisTraceView,
    ValidationBasisView,
    build_validation_basis_view,
)
from app.ui.viewmodels.validation_agreement import (
    ValidationAgreementCaseView,
    ValidationAgreementLinkView,
    ValidationAgreementMetricView,
    ValidationAgreementStepView,
    ValidationAgreementView,
    build_validation_agreement_view,
)
from app.ui.viewmodels.validation_matrix import (
    ValidationCaseView,
    ValidationMatrixView,
    ValidationMetricView,
    build_validation_matrix_view,
)


def build_dashboard_layout(
    scenarios: list[ScenarioDefinition],
    default_scenario_id: str,
    browser_profile: BrowserCapabilityProfile,
    validation_matrix: ValidationMatrixEvaluation,
    validation_agreement: ValidationAgreementEvaluation,
    validation_basis: ValidationBasisEvaluation,
    manual_check: ManualCheckEvaluation,
    project_baseline: ProjectBaselineSnapshot,
    demo_readiness: DemoReadinessEvaluation,
    demo_package: DemoPackageSnapshot,
    export_snapshot: ResultExportSnapshot,
    scenario_archive: ScenarioArchiveSnapshot,
    comparison_snapshot: RunComparisonSnapshot,
    event_log_snapshot: EventLogSnapshot,
    status_legend: list[StatusLegendEntry],
    current_result: SimulationResult,
    current_session: SimulationSession,
    dashboard_path: str,
) -> html.Div:
    normalized_dashboard_path = dashboard_path.rstrip("/")
    if not normalized_dashboard_path:
        normalized_dashboard_path = "/"

    def _page_href(page_id: str, anchor: str | None = None) -> str:
        if normalized_dashboard_path == "/":
            href = f"/?page={page_id}"
        else:
            href = f"{normalized_dashboard_path}/?page={page_id}"
        if anchor:
            href = f"{href}#{anchor}"
        return href

    scenario_options = [_build_scenario_option(scenario) for scenario in scenarios]
    scenario_map = {scenario.id: scenario for scenario in scenarios}
    default_scenario = scenario_map.get(default_scenario_id, scenarios[0])
    bindings = load_scene_bindings()
    defense_pack = build_defense_pack_view()
    validation_pack = build_validation_matrix_view(validation_matrix)
    validation_agreement_view = build_validation_agreement_view(validation_agreement)
    validation_basis_view = build_validation_basis_view(validation_basis)
    manual_check_view = build_manual_check_view(manual_check)
    project_baseline_view = build_project_baseline_view(project_baseline)
    demo_readiness_view = build_demo_readiness_view(demo_readiness)
    demo_package_view = build_demo_package_view(demo_package)
    result_export_view = build_result_export_view(export_snapshot)
    scenario_archive_view = build_scenario_archive_view(scenario_archive)
    run_comparison_view = build_run_comparison_view(comparison_snapshot)
    event_log_view = build_event_log_view(event_log_snapshot)
    browser_profile_view = build_browser_profile_view(browser_profile)
    demo_browser_view = build_demo_browser_readiness_view(None, browser_profile)
    control_mode_view = build_control_mode_view(current_result.control)
    scene_model_catalog = build_scene_model_catalog()
    room_catalog = build_room_catalog()
    developer_tools_enabled = get_settings().developer_tools_enabled
    selected_scene_model = next(
        (
            model
            for model in scene_model_catalog.models
            if model.id == scene_model_catalog.default_model_id
        ),
        scene_model_catalog.models[0] if scene_model_catalog.models else None,
    )
    selected_room = resolve_room_descriptor(room_catalog, room_catalog.default_room_id)

    scene3d_meta = {
        "camera_presets": {},
        "orbit_controls": {},
        "performance_budget": {},
        "interactive_targets": [],
        "animation_rules": None,
        "status_colors": {},
        "emissive_highlight": {},
    }
    if bindings.asset:
        import json as _json
        _scene_path = get_project_root() / "data" / "visualization" / "scene3d.json"
        scene3d_meta = _json.loads(_scene_path.read_text(encoding="utf-8"))
    scene3d_meta["model_catalog"] = scene_model_catalog.model_dump(mode="json")
    scene3d_meta["room_catalog"] = room_catalog.model_dump(mode="json")
    session_status_text, session_status_class_name = _build_session_status_badge(
        current_session.status
    )
    current_scenario_title = current_result.scenario_title or default_scenario.title
    parameter_source_text = (
        "Пресет"
        if current_result.parameter_source.value == "preset"
        else "Ручная настройка"
    )

    return html.Div(
        id="app-shell",
        className="app-shell",
        children=[
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="scenario-preset-version", data=0),
            dcc.Interval(
                id="simulation-interval",
                interval=_session_interval_ms(current_session.playback_speed),
                n_intervals=0,
                disabled=True,
            ),
            dcc.Store(
                id="simulation-session-state",
                data=current_session.model_dump(mode="json"),
            ),
            dcc.Store(id="visualization-signals"),
            dcc.Store(id="browser-capabilities"),
            dcc.Store(id="scene3d-meta", data=scene3d_meta),
            dcc.Store(
                id="scene3d-room-config",
                data=(
                    build_room_runtime_payload(selected_room)
                    if selected_room
                    else None
                ),
            ),
            dcc.Store(
                id="scene3d-scale-config",
                data={
                    "model_scale": 1.0,
                    "model_long_scale": 1.0,
                    "model_side_scale": 1.0,
                    "model_vertical_scale": 1.0,
                    "model_long_delta": 0.0,
                    "model_side_delta": 0.0,
                    "model_vertical_delta": 0.0,
                    "model_rotation_delta_deg": 0.0,
                    "model_pitch_delta_deg": 0.0,
                    "model_roll_delta_deg": 0.0,
                    "room_scale": 1.0,
                    "room_long_delta": 0.0,
                    "room_side_delta": 0.0,
                    "room_vertical_delta": 0.0,
                    "room_rotation_delta_deg": 0.0,
                },
            ),
            html.Div(id="mnemonic-sync", style={"display": "none"}),
            html.Div(id="viewer3d-sync", style={"display": "none"}),
            html.Nav(
                className="site-nav",
                children=[
                    html.Div(
                        className="site-nav__inner",
                        children=[
                            html.A(
                                "Симулятор ПВУ",
                                href=_page_href("main"),
                                className="site-nav__logo",
                            ),
                            html.Div(
                                className="site-nav__links",
                                children=[
                                    html.A(
                                        "Симулятор",
                                        href=_page_href("main", "section-monitoring"),
                                    ),
                                    html.A(
                                        "2D / 3D",
                                        href=_page_href("main", "section-visualization"),
                                    ),
                                    html.A(
                                        "Результаты",
                                        href=_page_href("main", "section-analytics"),
                                    ),
                                    html.A(
                                        "Техцентр",
                                        href=_page_href("service-index"),
                                    ),
                                    html.A(
                                        "API",
                                        href="/docs",
                                        target="_blank",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="mobile-quick-nav",
                children=[
                    html.A(
                        "Симулятор",
                        href=_page_href("main", "section-monitoring"),
                    ),
                    html.A(
                        "2D / 3D",
                        href=_page_href("main", "section-visualization"),
                    ),
                    html.A(
                        "Результаты",
                        href=_page_href("main", "section-analytics"),
                    ),
                    html.A("Техцентр", href=_page_href("service-index")),
                ],
            ),
            html.Div(
                id="hero-panel",
                className="hero-panel",
                children=[
                    html.Div(
                        className="hero-copy-block",
                        children=[
                            html.P("MVP ДИПЛОМНОГО ПРОЕКТА", className="eyebrow"),
                            html.H1(
                                "Моделирование работы приточной вентиляционной установки",
                                className="hero-title",
                            ),
                            html.P(
                                "Сценарий, запуск, KPI, 2D/3D и итоговые тренды. "
                                "Всё вторичное вынесено в техцентр.",
                                className="hero-copy",
                            ),
                            html.Div(
                                className="hero-actions",
                                children=[
                                    html.A(
                                        "Открыть симулятор",
                                        href=_page_href("main", "section-monitoring"),
                                        className="hero-action hero-action-primary",
                                    ),
                                    html.A(
                                        "Технический центр",
                                        href=_page_href("service-index"),
                                        className="hero-action",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="hero-facts",
                                children=[
                                    html.Div(
                                        className="hero-fact",
                                        children=[
                                            html.Span(
                                                "Текущий сценарий",
                                                className="hero-fact__label",
                                            ),
                                            html.Strong(
                                                current_scenario_title,
                                                className="hero-fact__value",
                                            ),
                                            html.P(
                                                default_scenario.description,
                                                className="hero-fact__note",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="hero-fact",
                                        children=[
                                            html.Span(
                                                "Статус сессии",
                                                className="hero-fact__label",
                                            ),
                                            html.Strong(
                                                session_status_text,
                                                className="hero-fact__value",
                                            ),
                                            html.P(
                                                f"{parameter_source_text} · шаг {current_session.step_minutes} мин",
                                                className="hero-fact__note",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="hero-fact",
                                        children=[
                                            html.Span(
                                                "История модели",
                                                className="hero-fact__label",
                                            ),
                                            html.Strong(
                                                f"{len(current_session.history.points)} точек",
                                                className="hero-fact__value",
                                            ),
                                            html.P(
                                                "KPI, 2D и 3D используют одно расчётное ядро.",
                                                className="hero-fact__note",
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="hero-brief-card",
                        children=[
                            html.Div(
                                className="panel-header",
                                children=[
                                    html.H2("Фокус демонстрации"),
                                    html.Div(
                                        className=session_status_class_name,
                                        children=session_status_text,
                                    ),
                                ],
                            ),
                            html.P(
                                "Маршрут: пресет → запуск → 2D/3D → тревоги и тренды.",
                                className="summary-text",
                            ),
                            html.Div(
                                className="hero-route-list",
                                children=[
                                    html.A(
                                        "Запуск",
                                        href=_page_href("main", "section-monitoring"),
                                        className="hero-route-link",
                                    ),
                                    html.A(
                                        "2D / 3D",
                                        href=_page_href("main", "section-visualization"),
                                        className="hero-route-link",
                                    ),
                                    html.A(
                                        "Результаты",
                                        href=_page_href("main", "section-analytics"),
                                        className="hero-route-link",
                                    ),
                                    html.A(
                                        "Техцентр",
                                        href=_page_href("service-index"),
                                        className="hero-route-link",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="hero-brief-list",
                                children=[
                                    html.Div(
                                        className="hero-brief-row",
                                        children=[
                                            html.Span("Сценарий"),
                                            html.Strong(current_scenario_title),
                                        ],
                                    ),
                                    html.Div(
                                        className="hero-brief-row",
                                        children=[
                                            html.Span("Источник параметров"),
                                            html.Strong(parameter_source_text),
                                        ],
                                    ),
                                    html.Div(
                                        className="hero-brief-row",
                                        children=[
                                            html.Span("Точка запуска"),
                                            html.Strong("Симулятор MVP"),
                                        ],
                                    ),
                                ],
                            ),
                            html.Div(
                                className="hero-highlight-list",
                                children=[
                                    html.Div(
                                        parameter,
                                        className="hero-highlight-chip",
                                    )
                                    for parameter in default_scenario.key_parameters[:3]
                                ],
                            ),
                            html.A(
                                "Открыть 3D-студию",
                                href=_page_href("main", "3d-studio"),
                                className="hero-action hero-action-primary hero-action-inline",
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="site-section",
                id="section-monitoring",
                children=[
                    html.Div("01 — Симулятор MVP", className="section-label"),
                    html.Div(
                        className="section-intro",
                        children=[
                            html.H2("Запуск и контроль на одном экране."),
                            html.P(
                                "Выберите пресет, подстройте ключевые параметры и запустите расчёт.",
                            ),
                        ],
                    ),
                    html.Div(
                        className="workspace-grid",
                        children=[
                            html.Div(
                                className="panel control-panel control-panel--mvp",
                                children=[
                                    html.Div(
                                        className="panel-header",
                                        children=[
                                            html.H2("Параметры"),
                                            html.Span("MVP", className="panel-tag"),
                                        ],
                                    ),
                                    html.Label("Сценарий", className="field-label"),
                                    dcc.Dropdown(
                                        id="scenario-select",
                                        options=scenario_options,
                                        value=default_scenario.id,
                                        clearable=False,
                                        searchable=False,
                                        optionHeight=48,
                                        maxHeight=320,
                                    ),
                                    html.Div(
                                        _format_scenario_metadata(default_scenario),
                                        id="scenario-preset-metadata",
                                        className="scenario-preset-metadata",
                                    ),
                                    html.Div(
                                        className="scenario-preset-shortcuts",
                                        children=[
                                            html.Button(
                                                "Зима",
                                                id="preset-shortcut-winter",
                                                className="ghost-button preset-shortcut-button",
                                                n_clicks=0,
                                                disabled="winter" not in scenario_map,
                                            ),
                                            html.Button(
                                                "Лето",
                                                id="preset-shortcut-summer",
                                                className="ghost-button preset-shortcut-button",
                                                n_clicks=0,
                                                disabled="summer" not in scenario_map,
                                            ),
                                            html.Button(
                                                "Пик нагрузки",
                                                id="preset-shortcut-peak-load",
                                                className="ghost-button preset-shortcut-button",
                                                n_clicks=0,
                                                disabled="peak_load" not in scenario_map,
                                            ),
                                        ],
                                    ),
                                    html.P(
                                        _format_scenario_description(default_scenario),
                                        id="scenario-description",
                                        className="scenario-description",
                                    ),
                                    html.Div(
                                        className="user-preset-controls",
                                        children=[
                                            dcc.Input(
                                                id="user-preset-title",
                                                className="user-preset-input",
                                                placeholder="Название пользовательского пресета",
                                                type="text",
                                            ),
                                            html.Div(
                                                className="user-preset-actions",
                                                children=[
                                                    html.Button(
                                                        "Сохранить",
                                                        id="user-preset-save",
                                                        className="ghost-button",
                                                        n_clicks=0,
                                                    ),
                                                    html.Button(
                                                        "Переименовать",
                                                        id="user-preset-rename",
                                                        className="ghost-button",
                                                        n_clicks=0,
                                                    ),
                                                    html.Button(
                                                        "Удалить",
                                                        id="user-preset-delete",
                                                        className="ghost-button",
                                                        n_clicks=0,
                                                    ),
                                                ],
                                            ),
                                            dcc.Textarea(
                                                id="user-preset-import-payload",
                                                className="user-preset-textarea",
                                                placeholder="JSON для импорта пользовательского пресета",
                                            ),
                                            html.Div(
                                                className="user-preset-actions",
                                                children=[
                                                    html.Button(
                                                        "Импорт",
                                                        id="user-preset-import",
                                                        className="ghost-button",
                                                        n_clicks=0,
                                                    ),
                                                    html.Button(
                                                        "Экспорт",
                                                        id="user-preset-export",
                                                        className="ghost-button",
                                                        n_clicks=0,
                                                    ),
                                                ],
                                            ),
                                            html.P(
                                                "",
                                                id="user-preset-status",
                                                className="scenario-description",
                                            ),
                                            html.Pre(
                                                "",
                                                id="user-preset-export-payload",
                                                className="user-preset-export",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="control-group-grid",
                                        children=[
                                            _number_field(
                                                "Наружная температура, °C",
                                                "outdoor-temp",
                                                -45,
                                                45,
                                                0.5,
                                                default_scenario.parameters.outdoor_temp_c,
                                            ),
                                            _number_field(
                                                "Расход воздуха, м³/ч",
                                                "airflow",
                                                200,
                                                8000,
                                                50,
                                                default_scenario.parameters.airflow_m3_h,
                                            ),
                                            _number_field(
                                                "Уставка притока, °C",
                                                "setpoint",
                                                10,
                                                35,
                                                0.5,
                                                default_scenario.parameters.supply_temp_setpoint_c,
                                            ),
                                            _number_field(
                                                "Мощность нагревателя, кВт",
                                                "heater-power",
                                                0,
                                                120,
                                                0.5,
                                                default_scenario.parameters.heater_power_kw,
                                            ),
                                        ],
                                    ),
                                    html.Label("Режим", className="field-label"),
                                    dcc.Dropdown(
                                        id="control-mode",
                                        options=[
                                            {"label": "Авто", "value": ControlMode.AUTO.value},
                                            {"label": "Ручной", "value": ControlMode.MANUAL.value},
                                        ],
                                        value=default_scenario.parameters.control_mode.value,
                                        clearable=False,
                                        searchable=False,
                                        optionHeight=48,
                                        maxHeight=320,
                                    ),
                                    html.Details(
                                        className="control-details",
                                        children=[
                                            html.Summary(
                                                className="control-details__summary",
                                                children=[
                                                    html.Span("Расширенные параметры"),
                                                    html.Span(
                                                        "по запросу",
                                                        className="detail-tag",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="control-details__body",
                                                children=[
                                                    html.Div(
                                                        className="control-group-grid",
                                                        children=[
                                                            _number_field(
                                                                "КПД рекуперации",
                                                                "recovery-efficiency",
                                                                0,
                                                                0.85,
                                                                0.01,
                                                                default_scenario.parameters.heat_recovery_efficiency,
                                                            ),
                                                            _number_field(
                                                                "Загрязнение фильтра",
                                                                "filter-contamination",
                                                                0,
                                                                1,
                                                                0.01,
                                                                default_scenario.parameters.filter_contamination,
                                                            ),
                                                            _number_field(
                                                                "Относительная скорость вентилятора",
                                                                "fan-speed",
                                                                0.2,
                                                                1.2,
                                                                0.01,
                                                                default_scenario.parameters.fan_speed_ratio,
                                                            ),
                                                            _number_field(
                                                                "Температура помещения, °C",
                                                                "room-temp",
                                                                5,
                                                                40,
                                                                0.1,
                                                                default_scenario.parameters.room_temp_c,
                                                            ),
                                                            _number_field(
                                                                "Теплопритоки помещения, кВт",
                                                                "room-heat-gain",
                                                                -10,
                                                                40,
                                                                0.1,
                                                                default_scenario.parameters.room_heat_gain_kw,
                                                            ),
                                                            _number_field(
                                                                "Шаг времени, мин",
                                                                "step-minutes",
                                                                1,
                                                                60,
                                                                1,
                                                                default_scenario.parameters.step_minutes,
                                                            ),
                                                        ],
                                                    ),
                                                    html.Div(
                                                        id="control-modes",
                                                        className="artifact-panel-meta mode-brief",
                                                        children=[
                                                            html.Div(
                                                                className="browser-panel-header",
                                                                children=[
                                                                    html.H3("Режимы управления"),
                                                                    html.Div(
                                                                        id="control-mode-status",
                                                                        className=control_mode_view.target_status_class_name,
                                                                        children=control_mode_view.target_status_text,
                                                                    ),
                                                                ],
                                                            ),
                                                            html.P(
                                                                id="control-mode-summary",
                                                                className="validation-intro",
                                                                children=control_mode_view.summary,
                                                            ),
                                                            html.Div(
                                                                className="artifact-panel-meta-item",
                                                                children=[
                                                                    html.Strong("Активный режим", className="detail-label"),
                                                                    html.Code(control_mode_view.mode_text, id="control-mode-name", className="defense-code"),
                                                                ],
                                                            ),
                                                            html.Div(
                                                                className="artifact-panel-meta-item",
                                                                children=[
                                                                    html.Strong("Отклонение от уставки", className="detail-label"),
                                                                    html.Code(control_mode_view.setpoint_gap_text, id="control-mode-gap", className="defense-code"),
                                                                ],
                                                            ),
                                                            html.Div(
                                                                className="artifact-panel-meta-item",
                                                                children=[
                                                                    html.Strong("Отклонение по расходу", className="detail-label"),
                                                                    html.Code(control_mode_view.airflow_gap_text, id="control-mode-airflow-gap", className="defense-code"),
                                                                ],
                                                            ),
                                                            html.Div(
                                                                className="artifact-panel-meta-item",
                                                                children=[
                                                                    html.Strong("Нагреватель", className="detail-label"),
                                                                    html.Code(control_mode_view.heater_band_text, id="control-mode-heater-band", className="defense-code"),
                                                                ],
                                                            ),
                                                            html.Div(
                                                                className="artifact-panel-meta-item",
                                                                children=[
                                                                    html.Strong("Команда вентилятора", className="detail-label"),
                                                                    html.Code(control_mode_view.fan_command_text, id="control-mode-fan-command", className="defense-code"),
                                                                ],
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            html.Div(
                                className="main-stack",
                                children=[
                                    html.Div(
                                        className="panel metrics-panel",
                                        children=[
                                            html.Div(
                                                className="panel-header",
                                                children=[
                                                    html.H2("Состояние установки"),
                                                    html.Div(
                                                        id="status-pill",
                                                        className="status-pill status-normal",
                                                    ),
                                                ],
                                            ),
                                            html.P(
                                                "6 KPI и статус модели без перехода по дополнительным разделам.",
                                                className="summary-text",
                                            ),
                                            html.Div(
                                                className="metric-grid",
                                                children=[
                                                    _metric_card("Температура притока", "metric-supply-temp"),
                                                    _metric_card("Температура помещения", "metric-room-temp"),
                                                    _metric_card("Нагрев", "metric-heating-power"),
                                                    _metric_card("Суммарная мощность", "metric-total-power"),
                                                    _metric_card("Фактический расход", "metric-airflow"),
                                                    _metric_card("Перепад на фильтре", "metric-filter-pressure"),
                                                ],
                                            ),
                                            _build_status_legend_panel(status_legend),
                                        ],
                                    ),
                                    html.Div(
                                        className="panel session-panel",
                                        children=[
                                            html.Div(
                                                className="panel-header",
                                                children=[
                                                    html.H2("Сессия симуляции"),
                                                    html.Div(
                                                        id="simulation-session-status",
                                                        className=session_status_class_name,
                                                        children=session_status_text,
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                id="simulation-session-summary",
                                                className="summary-text",
                                                children=_build_session_summary(current_session),
                                            ),
                                            html.Div(
                                                className="session-meta-grid",
                                                children=[
                                                    _session_meta_item(
                                                        "Идентификатор сессии",
                                                        "simulation-session-id",
                                                        current_session.session_id,
                                                    ),
                                                    _session_meta_item(
                                                        "Шаг",
                                                        "simulation-session-step",
                                                        f"{current_session.step_minutes} мин",
                                                    ),
                                                    _session_meta_item(
                                                        "Прошло",
                                                        "simulation-session-elapsed",
                                                        _format_session_elapsed(current_session),
                                                    ),
                                                    _session_meta_item(
                                                        "Тиков",
                                                        "simulation-session-ticks",
                                                        _format_session_ticks(current_session),
                                                    ),
                                                    _session_meta_item(
                                                        "Скорость",
                                                        "simulation-session-speed",
                                                        f"x{current_session.playback_speed:g}",
                                                    ),
                                                    _session_meta_item(
                                                        "История",
                                                        "simulation-session-history",
                                                        f"{len(current_session.history.points)} точек",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="session-actions",
                                                children=[
                                                    html.Button(
                                                        "Старт",
                                                        id="simulation-start",
                                                        n_clicks=0,
                                                        className="action-btn action-btn-primary",
                                                        disabled=not current_session.actions.can_start,
                                                    ),
                                                    html.Button(
                                                        "Пауза",
                                                        id="simulation-pause",
                                                        n_clicks=0,
                                                        className="action-btn",
                                                        disabled=not current_session.actions.can_pause,
                                                    ),
                                                    html.Button(
                                                        "Шаг",
                                                        id="simulation-step",
                                                        n_clicks=0,
                                                        className="action-btn",
                                                        disabled=not current_session.actions.can_tick,
                                                    ),
                                                    html.Button(
                                                        "Сброс",
                                                        id="simulation-reset",
                                                        n_clicks=0,
                                                        className="action-btn action-btn-danger",
                                                        disabled=not current_session.actions.can_reset,
                                                    ),
                                                ],
                                            ),
                                            dcc.RadioItems(
                                                id="simulation-speed",
                                                options=[
                                                    {"label": "x0.25", "value": 0.25},
                                                    {"label": "x0.5", "value": 0.5},
                                                    {"label": "x1", "value": 1.0},
                                                    {"label": "x2", "value": 2.0},
                                                    {"label": "x4", "value": 4.0},
                                                ],
                                                value=current_session.playback_speed,
                                                inline=True,
                                                className="session-speed-control",
                                                inputClassName="session-speed-control__input",
                                                labelClassName="session-speed-control__option",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="panel demo-flow-panel",
                                        children=[
                                            html.Div(
                                                className="panel-header",
                                                children=[
                                                    html.H2("Как показать MVP"),
                                                    html.Span("3 шага", className="panel-tag"),
                                                ],
                                            ),
                                            html.Div(
                                                className="demo-flow-grid",
                                                children=[
                                                    _build_demo_step_card(
                                                        "1. Выберите пресет",
                                                        "Зима, лето или пиковая нагрузка.",
                                                    ),
                                                    _build_demo_step_card(
                                                        "2. Запустите сессию",
                                                        "KPI и тревоги обновляются сразу.",
                                                    ),
                                                    _build_demo_step_card(
                                                        "3. Покажите цифровой двойник",
                                                        "Переключитесь в 2D/3D и откройте тренды.",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="site-section",
                id="section-visualization",
                children=[
                    html.Div("02 — 2D и 3D", className="section-label"),
                    html.Div(
                        className="section-intro",
                        children=[
                            html.H2("2D для контроля, 3D для показа."),
                            html.P(
                                "Оба режима синхронизированы с одним расчётом и одним набором сигналов.",
                            ),
                        ],
                    ),
                    html.Nav(
                        className="studio-nav",
                        children=[
                            html.Div(
                                className="studio-nav__inner",
                                children=[
                                    html.A(
                                        "Симулятор ПВУ",
                                        href=_page_href("main", "section-monitoring"),
                                        className="studio-nav__logo",
                                    ),
                                    html.Div(
                                        className="studio-nav__right",
                                        children=[
                                            html.Span(
                                                "3D Студия",
                                                className="studio-nav__label",
                                            ),
                                            html.A(
                                                "← К запуску сценария",
                                                href=_page_href("main", "section-monitoring"),
                                                className="studio-nav__back",
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="panel mnemonic-panel",
                        id="digital-twin-3d",
                        children=[
                            html.Div(
                                className="panel-header",
                                children=[
                                    html.H2(
                                        "Цифровой двойник",
                                        id="mnemonic-panel-title",
                                    ),
                                    html.Div(
                                        className="render-mode-toggle",
                                        children=[
                                            html.Button(
                                                "2D",
                                                id="render-mode-2d",
                                                n_clicks=0,
                                                className="render-mode-btn active",
                                            ),
                                            html.Button(
                                                "3D",
                                                id="render-mode-3d",
                                                n_clicks=0,
                                                className="render-mode-btn",
                                            ),
                                        ],
                                    ),
                                    html.A(
                                        "Развернуть студию →",
                                        href="#3d-studio",
                                        className="studio-launch-btn",
                                    ),
                                    html.Span(
                                        f"Привязки v{bindings.version}",
                                        className="panel-tag",
                                    ),
                                ],
                            ),
                            dcc.Store(id="render-mode", data="2d"),
                            build_scene2d_workspace(browser_profile_view),
                            build_scene3d_workspace(
                                scene_model_catalog,
                                selected_scene_model,
                                scenario_options,
                                default_scenario.id,
                                room_catalog,
                                selected_room,
                                developer_tools_enabled,
                            ),
                        ],
                    ),
                    html.Div(
                        className="studio-info-toggle",
                        children=[
                            html.Button(
                                "ⓘ",
                                id="studio-info-btn",
                                className="studio-info-btn",
                                n_clicks=0,
                            ),
                            html.Div(
                                id="studio-info-panel",
                                className="studio-info-panel",
                                children=[
                                    html.Span(
                                        "3D Цифровой двойник",
                                        className="studio-info__title",
                                    ),
                                    html.P(
                                        "Показывает реакцию узлов, потоков и помещения на текущий сценарий.",
                                        className="studio-info__desc",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="site-section",
                id="section-analytics",
                children=[
                    html.Div("03 — Результаты", className="section-label"),
                    html.Div(
                        className="section-intro",
                        children=[
                            html.H2("Итоговый статус, тревоги и история процесса."),
                            html.P(
                                "Финальный экран для защиты: что произошло, где риск и как вёл себя процесс.",
                            ),
                        ],
                    ),
                    html.Div(
                        className="two-column",
                        children=[
                            html.Div(
                                className="panel alarm-panel",
                                children=[
                                    html.Div(
                                        className="panel-header",
                                        children=[
                                            html.H2("Риски и аварии"),
                                            html.Span("live", className="panel-tag"),
                                        ],
                                    ),
                                    html.Div(id="alarm-list", className="alarm-list"),
                                ],
                            ),
                            html.Div(
                                className="panel summary-panel",
                                children=[
                                    html.Div(
                                        className="panel-header",
                                        children=[
                                            html.H2("Сводка"),
                                            html.Span(
                                                "для защиты",
                                                className="panel-tag",
                                            ),
                                        ],
                                    ),
                                    html.Div(id="summary-text", className="summary-text"),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="panel trend-panel",
                        style={"marginTop": "24px"},
                        children=[
                            html.Div(
                                className="panel-header",
                                children=[
                                    html.H2("Тренды процесса"),
                                    html.Span(
                                        id="trend-panel-tag",
                                        className="panel-tag",
                                        children=f"История {current_session.elapsed_minutes} мин",
                                    ),
                                ],
                            ),
                            dcc.Graph(
                                id="trend-graph",
                                config={"displayModeBar": False},
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="site-section",
                id="section-service-map",
                children=[
                    html.Div("Технический центр", className="section-label"),
                    html.Div(
                        className="technical-hub-intro",
                        children=[
                            html.H2("Техцентр вне основного маршрута."),
                            html.P(
                                "Validation, baseline, архив, export и runtime-артефакты собраны отдельно.",
                            ),
                            html.Div(
                                className="hero-links",
                                children=[
                                    html.A("← Вернуться к MVP", href=_page_href("main")),
                                    html.A("Документация API", href="/docs", target="_blank"),
                                    html.A("Здоровье системы", href="/health", target="_blank"),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="tech-center-grid",
                        children=[
                            _build_technical_center_card(
                                "Валидация модели",
                                "matrix / agreement / sources / manual",
                                _page_href("service-validation"),
                                "QA",
                            ),
                            _build_technical_center_card(
                                "Инфраструктурная база",
                                "baseline / inputs / outputs / assumptions",
                                _page_href("service-baseline"),
                                "BASELINE",
                            ),
                            _build_technical_center_card(
                                "Готовность к демо",
                                "runtime / browser / package readiness",
                                _page_href("service-readiness"),
                                "READINESS",
                            ),
                            _build_technical_center_card(
                                "Сценарий защиты",
                                "demo flow / narrative / visual track",
                                _page_href("service-defense"),
                                "DEFENSE",
                            ),
                            _build_technical_center_card(
                                "Экспорт результатов",
                                "csv / pdf / manifest history",
                                _page_href("service-export"),
                                "EXPORT",
                            ),
                            _build_technical_center_card(
                                "Сравнение прогонов",
                                "before / after / delta metrics",
                                _page_href("service-comparison"),
                                "COMPARE",
                            ),
                            _build_technical_center_card(
                                "Архив сценариев",
                                "snapshots / replay / saved runs",
                                _page_href("service-archive"),
                                "ARCHIVE",
                            ),
                            _build_technical_center_card(
                                "Журнал событий",
                                "events / source / level / artifacts",
                                _page_href("service-event-log"),
                                "LOG",
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="site-section",
                id="page-service-validation",
                style={"display": "none"},
                children=[
                    html.Div("Технический раздел", className="section-label"),
                    html.Div(
                        className="hero-links",
                        children=[
                            html.A("← На главную", href=_page_href("main")),
                            html.A("Технический центр", href=_page_href("service-index")),
                        ],
                    ),
                    html.Div(
                        className="main-stack",
                        children=[
                            _build_validation_pack_panel(validation_pack),
                            _build_validation_agreement_panel(validation_agreement_view),
                            _build_validation_basis_panel(validation_basis_view),
                            _build_manual_check_panel(manual_check_view),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="site-section",
                id="page-service-baseline",
                style={"display": "none"},
                children=[
                    html.Div("Технический раздел", className="section-label"),
                    html.Div(
                        className="hero-links",
                        children=[
                            html.A("← На главную", href=_page_href("main")),
                            html.A("Технический центр", href=_page_href("service-index")),
                        ],
                    ),
                    _build_project_baseline_panel(project_baseline_view),
                ],
            ),
            html.Div(
                className="site-section",
                id="page-service-defense",
                style={"display": "none"},
                children=[
                    html.Div("Технический раздел", className="section-label"),
                    html.Div(
                        className="hero-links",
                        children=[
                            html.A("← На главную", href=_page_href("main")),
                            html.A("Технический центр", href=_page_href("service-index")),
                        ],
                    ),
                    _build_defense_pack_panel(defense_pack),
                ],
            ),
            html.Div(
                className="site-section",
                id="page-service-readiness",
                style={"display": "none"},
                children=[
                    html.Div("Технический раздел", className="section-label"),
                    html.Div(
                        className="hero-links",
                        children=[
                            html.A("← На главную", href=_page_href("main")),
                            html.A("Технический центр", href=_page_href("service-index")),
                        ],
                    ),
                    _build_demo_readiness_panel(
                        demo_readiness_view,
                        demo_package_view,
                        demo_browser_view,
                    ),
                ],
            ),
            html.Div(
                className="site-section",
                id="page-service-export",
                style={"display": "none"},
                children=[
                    html.Div("Технический раздел", className="section-label"),
                    html.Div(
                        className="hero-links",
                        children=[
                            html.A("← На главную", href=_page_href("main")),
                            html.A("Технический центр", href=_page_href("service-index")),
                        ],
                    ),
                    _build_result_export_panel(result_export_view),
                ],
            ),
            html.Div(
                className="site-section",
                id="page-service-comparison",
                style={"display": "none"},
                children=[
                    html.Div("Технический раздел", className="section-label"),
                    html.Div(
                        className="hero-links",
                        children=[
                            html.A("← На главную", href=_page_href("main")),
                            html.A("Технический центр", href=_page_href("service-index")),
                        ],
                    ),
                    _build_run_comparison_panel(run_comparison_view),
                ],
            ),
            html.Div(
                className="site-section",
                id="page-service-archive",
                style={"display": "none"},
                children=[
                    html.Div("Технический раздел", className="section-label"),
                    html.Div(
                        className="hero-links",
                        children=[
                            html.A("← На главную", href=_page_href("main")),
                            html.A("Технический центр", href=_page_href("service-index")),
                        ],
                    ),
                    _build_scenario_archive_panel(scenario_archive_view),
                ],
            ),
            html.Div(
                className="site-section",
                id="page-service-event-log",
                style={"display": "none"},
                children=[
                    html.Div("Технический раздел", className="section-label"),
                    html.Div(
                        className="hero-links",
                        children=[
                            html.A("← На главную", href=_page_href("main")),
                            html.A("Технический центр", href=_page_href("service-index")),
                        ],
                    ),
                    _build_event_log_panel(event_log_view),
                ],
            ),
            html.Div(
                className="site-footer",
                children=[
                    html.Div(
                        className="site-footer__inner",
                        children=[
                            html.Span(
                                "Симулятор ПВУ",
                                className="site-footer__brand",
                            ),
                            html.Span(
                                "MVP-маршрут для показа модели приточной вентиляционной установки"
                            ),
                            html.Div(
                                className="site-footer__links",
                                children=[
                                    html.A(
                                        "Технический центр",
                                        href=_page_href("service-index"),
                                    ),
                                    html.A(
                                        "Документация API",
                                        href="/docs",
                                        target="_blank",
                                    ),
                                    html.A(
                                        "Здоровье системы",
                                        href="/health",
                                        target="_blank",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _number_field(
    label: str,
    component_id: str,
    min_value: float,
    max_value: float,
    step: float,
    value: float,
) -> html.Div:
    return html.Div(
        className="field-block",
        children=[
            html.Label(label, className="field-label", htmlFor=component_id),
            dcc.Input(
                id=component_id,
                type="number",
                min=min_value,
                max=max_value,
                step=step,
                value=value,
                debounce=True,
                className="number-input",
            ),
        ],
    )


def _format_scenario_description(scenario: ScenarioDefinition) -> str:
    return scenario.description


def _build_scenario_option(scenario: ScenarioDefinition) -> dict[str, str]:
    source_label = "системный" if scenario.source == "system" else "пользовательский"
    lock_label = "только чтение" if scenario.locked else "редактируемый"
    return {
        "label": f"{scenario.title} · {source_label} · {lock_label}",
        "value": scenario.id,
    }


def _format_scenario_metadata(scenario: ScenarioDefinition) -> str:
    source_label = "Системный" if scenario.source == "system" else "Пользовательский"
    lock_label = "только чтение" if scenario.locked else "можно редактировать"
    version = scenario.schema_version
    updated_at = (
        f", обновлён {scenario.updated_at:%Y-%m-%d %H:%M}"
        if scenario.updated_at
        else ""
    )
    return f"{source_label} пресет, {lock_label}, схема {version}{updated_at}."


def _build_session_status_badge(
    status: SimulationSessionStatus,
) -> tuple[str, str]:
    mapping = {
        SimulationSessionStatus.IDLE: ("Готово", "status-pill status-muted"),
        SimulationSessionStatus.RUNNING: ("Выполняется", "status-pill status-info"),
        SimulationSessionStatus.PAUSED: ("На паузе", "status-pill status-warning"),
        SimulationSessionStatus.COMPLETED: ("Завершено", "status-pill status-normal"),
    }
    return mapping[status]


def _build_session_summary(session: SimulationSession) -> str:
    if session.status == SimulationSessionStatus.RUNNING:
        return (
            f"Сессия активна · шаг {session.step_minutes} мин · "
            f"{len(session.history.points)} точек в истории."
        )
    if session.status == SimulationSessionStatus.PAUSED:
        return (
            f"Сессия на паузе · {session.elapsed_minutes} мин расчёта · "
            "доступны продолжение, шаг и сброс."
        )
    if session.status == SimulationSessionStatus.COMPLETED:
        return (
            f"Горизонт достигнут · {session.elapsed_minutes} мин расчёта · "
            "для нового прогона выполните сброс."
        )
    return f"Сессия готова к запуску · шаг интегрирования {session.step_minutes} мин."


def _format_session_elapsed(session: SimulationSession) -> str:
    return f"{session.elapsed_minutes} / {session.current_result.parameters.horizon_minutes} мин"


def _format_session_ticks(session: SimulationSession) -> str:
    return f"{session.tick_count} / {session.max_ticks}"


def _session_interval_ms(playback_speed: float) -> int:
    return int(1000 / max(playback_speed, 0.25))


def _session_meta_item(
    label: str,
    component_id: str,
    value: str,
) -> html.Div:
    return html.Div(
        className="artifact-panel-meta-item session-meta-item",
        children=[
            html.Strong(label, className="detail-label"),
            html.Code(value, id=component_id, className="defense-code"),
        ],
    )


def _metric_card(title: str, component_id: str) -> html.Div:
    return html.Div(
        className="metric-card",
        children=[
            html.Span(title, className="metric-label"),
            html.Div(id=component_id, className="metric-card-body"),
        ],
    )


def _build_status_legend_panel(entries: list[StatusLegendEntry]) -> html.Div:
    return html.Div(
        className="status-legend-panel",
        children=[
            html.Div(
                className="panel-header",
                children=[
                    html.H2("Легенда статусов"),
                    html.Span("Норма / Риск / Авария", className="panel-tag"),
                ],
            ),
            html.P(
                "Пороги статусов зафиксированы в конфигурации времени выполнения и одинаково применяются к KPI, мнемосхеме, трендам и экспорту.",
                className="summary-text",
            ),
            html.Div(
                className="status-legend-grid",
                children=[
                    html.Div(
                        className="status-legend-item",
                        children=[
                            html.Div(entry.label, className=entry.class_name),
                            html.P(entry.summary, className="status-legend-note"),
                        ],
                    )
                    for entry in entries
                ],
            ),
        ],
    )


def _build_demo_step_card(title: str, body: str) -> html.Div:
    return html.Div(
        className="demo-step-card",
        children=[
            html.Strong(title, className="demo-step-card__title"),
            html.P(body, className="demo-step-card__body"),
        ],
    )


def _build_technical_center_card(
    title: str,
    summary: str,
    href: str,
    tag: str,
) -> html.A:
    return html.A(
        href=href,
        className="tech-center-card",
        children=[
            html.Span(tag, className="tech-center-card__tag"),
            html.Strong(title, className="tech-center-card__title"),
            html.P(summary, className="tech-center-card__summary"),
            html.Span("Открыть", className="tech-center-card__link"),
        ],
    )


def _build_defense_pack_panel(view: DefensePackView) -> html.Div:
    return html.Div(
        id="defense-pack",
        className="panel defense-panel",
        children=[
            html.Div(
                className="panel-header",
                children=[
                    html.H2("Пакет защиты"),
                    html.Span(view.demo_duration, className="panel-tag"),
                ],
            ),
            html.P(view.intro, className="defense-intro"),
            html.Div(
                className="defense-accordion",
                children=[
                    html.Details(
                        open=True,
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Демо-процесс 5-7 минут"),
                                    html.Span(
                                        f"{len(view.demo_flow)} шагов",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body",
                                children=[
                                    html.Ol(
                                        className="defense-step-list",
                                        children=[
                                            _build_demo_flow_step(step)
                                            for step in view.demo_flow
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Визуальный сценарий показа 2D-модели"),
                                    html.Span("SVG фокус", className="detail-tag"),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body",
                                children=[
                                    html.Ul(
                                        className="defense-bullet-list",
                                        children=[
                                            html.Li(item)
                                            for item in view.visual_scenario
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Технологии и их назначение"),
                                    html.Span("Стек", className="detail-tag"),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body",
                                children=[
                                    _build_table(
                                        header_left="Технология",
                                        header_right="Зачем используется",
                                        rows=[
                                            (
                                                row.technology,
                                                row.purpose,
                                            )
                                            for row in view.technology_rows
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Функции и модули проекта"),
                                    html.Span("Архитектура", className="detail-tag"),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body",
                                children=[
                                    _build_table(
                                        header_left="Функция",
                                        header_right="Модуль проекта",
                                        rows=[
                                            (
                                                row.function_name,
                                                row.module_path,
                                            )
                                            for row in view.function_module_rows
                                        ],
                                        code_right_column=True,
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Ограничения модели"),
                                    html.Span("Границы MVP", className="detail-tag"),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body",
                                children=[
                                    html.Ul(
                                        className="defense-bullet-list",
                                        children=[
                                            html.Li(item)
                                            for item in view.model_limitations
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Использование ИИ"),
                                    html.Span("Только поддержка", className="detail-tag"),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body",
                                children=[
                                    html.Ul(
                                        className="defense-bullet-list",
                                        children=[
                                            html.Li(item)
                                            for item in view.ai_usage_notes
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _build_demo_readiness_panel(
    view: DemoReadinessView,
    package_view: DemoPackageView,
    browser_view: DemoBrowserReadinessView,
) -> html.Div:
    return html.Div(
        id="demo-readiness",
        className="panel readiness-panel",
        children=[
            html.Div(
                className="panel-header",
                children=[
                    html.H2("Готовность к демо"),
                    html.Span("Офлайн-предполётная проверка", className="panel-tag"),
                ],
            ),
            html.Div(
                className="readiness-overview",
                children=[
                    html.Div(view.summary_text, className=view.summary_class_name),
                    html.P(view.note, className="validation-intro"),
                    html.P(
                        f"Снимок готовности: {view.generated_at_text}",
                        className="validation-meta",
                    ),
                ],
            ),
            html.Div(
                className="readiness-browser-card",
                children=[
                    html.Div(
                        className="browser-panel-header",
                        children=[
                            html.H3("Текущий браузер"),
                            html.Div(
                                id="demo-browser-status",
                                className=browser_view.status_class_name,
                                children=browser_view.status_text,
                            ),
                        ],
                    ),
                    html.P(
                        id="demo-browser-summary",
                        className="validation-intro",
                        children=browser_view.summary_text,
                    ),
                    html.Div(
                        id="demo-browser-list",
                        className="capability-list",
                        children=[
                            html.Div(item, className="capability-item")
                            for item in browser_view.items
                        ],
                    ),
                    html.P(
                        id="demo-browser-note",
                        className="mnemonic-note",
                        children=browser_view.note,
                    ),
                ],
            ),
            html.Div(
                className="defense-accordion",
                children=[
                    html.Details(
                        open=True,
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Демо-комплект"),
                                    html.Span("Упаковка", className="detail-tag"),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body artifact-panel-body",
                                children=[
                                    html.Div(
                                        className="artifact-panel-actions",
                                        children=[
                                            html.Div(
                                                id="demo-package-status",
                                                className=package_view.summary_class_name,
                                                children=package_view.status_text,
                                            ),
                                            html.Button(
                                                "Собрать демо-архив",
                                                id="demo-package-build",
                                                n_clicks=0,
                                                type="button",
                                                className="ghost-button",
                                            ),
                                        ],
                                    ),
                                    html.P(
                                        id="demo-package-summary",
                                        className="validation-intro",
                                        children=package_view.summary_text,
                                    ),
                                    html.P(
                                        id="demo-package-note",
                                        className="validation-meta",
                                        children=package_view.note,
                                    ),
                                    html.Div(
                                        className="artifact-panel-meta",
                                        children=[
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Папка сборки",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        package_view.target_directory_text,
                                                        id="demo-package-target",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Шаблон имени",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        package_view.bundle_name_pattern,
                                                        id="demo-package-pattern",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Последний архив",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        package_view.latest_bundle_text,
                                                        id="demo-package-latest",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Последний манифест",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        package_view.latest_manifest_text,
                                                        id="demo-package-manifest",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Снимок",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        package_view.generated_at_text,
                                                        id="demo-package-generated",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                        ],
                                    ),
                                    html.Table(
                                        className="defense-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Блок"),
                                                        html.Th("Категория"),
                                                        html.Th("Статус"),
                                                        html.Th("Состав"),
                                                        html.Th("Комментарий"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                id="demo-package-entries",
                                                children=[
                                                    _build_demo_package_entry_row(entry)
                                                    for entry in package_view.entries
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        open=True,
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Чек-лист"),
                                    html.Span(
                                        f"{len(view.checks)} пунктов",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body",
                                children=[
                                    html.Table(
                                        className="defense-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Проверка"),
                                                        html.Th("Статус"),
                                                        html.Th("Детали"),
                                                        html.Th("Основание"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_demo_readiness_check_row(check)
                                                    for check in view.checks
                                                ]
                                            ),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Как запускать"),
                                    html.Span("Сначала Windows", className="detail-tag"),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body",
                                children=[
                                    html.Table(
                                        className="defense-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Шаг"),
                                                        html.Th("Команда"),
                                                        html.Th("Комментарий"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_demo_readiness_command_row(command)
                                                    for command in view.launch_commands
                                                ]
                                            ),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Среда выполнения и маршруты"),
                                    html.Span("Снимок", className="detail-tag"),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body readiness-two-column",
                                children=[
                                    html.Table(
                                        className="defense-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Компонент"),
                                                        html.Th("Версия"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_demo_readiness_runtime_row(runtime)
                                                    for runtime in view.runtime_versions
                                                ]
                                            ),
                                        ],
                                    ),
                                    html.Table(
                                        className="defense-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Маршрут"),
                                                        html.Th("Назначение"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_demo_readiness_endpoint_row(endpoint)
                                                    for endpoint in view.endpoints
                                                ]
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _build_result_export_panel(view: ResultExportView) -> html.Div:
    return html.Div(
        id="export-pack",
        className="panel defense-panel",
        children=[
            html.Div(
                className="panel-header",
                children=[
                    html.H2("Отчёт по сценарию"),
                    html.Span("CSV / PDF", className="panel-tag"),
                ],
            ),
            html.Div(
                className="defense-accordion",
                children=[
                    html.Details(
                        open=True,
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Собранные отчёты"),
                                    html.Span(
                                        f"{view.total_entries_text} отчётов",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body artifact-panel-body",
                                children=[
                                    html.Div(
                                        className="artifact-panel-actions",
                                        children=[
                                            html.Div(
                                                id="export-pack-status",
                                                className=view.summary_class_name,
                                                children=view.status_text,
                                            ),
                                            html.Button(
                                                "Предпросмотр",
                                                id="export-pack-preview",
                                                n_clicks=0,
                                                type="button",
                                                className="ghost-button",
                                            ),
                                            html.Button(
                                                "Собрать отчёт PDF/CSV",
                                                id="export-pack-build",
                                                n_clicks=0,
                                                type="button",
                                                className="ghost-button",
                                            ),
                                        ],
                                    ),
                                    html.P(
                                        id="export-pack-summary",
                                        className="validation-intro",
                                        children=view.summary_text,
                                    ),
                                    html.P(
                                        id="export-pack-note",
                                        className="validation-meta",
                                        children=view.note,
                                    ),
                                    html.P(
                                        id="export-pack-preview-text",
                                        className="validation-meta",
                                        children=view.preview_text,
                                    ),
                                    html.Div(
                                        className="basis-link-list",
                                        children=[
                                            html.A(
                                                "Скачать последний CSV",
                                                id="export-pack-download-csv",
                                                href=view.latest_csv_download_url,
                                                target="_blank",
                                                rel="noreferrer",
                                                className="basis-link",
                                            ),
                                            html.Span(" · ", className="validation-meta"),
                                            html.A(
                                                "Скачать последний PDF",
                                                id="export-pack-download-pdf",
                                                href=view.latest_pdf_download_url,
                                                target="_blank",
                                                rel="noreferrer",
                                                className="basis-link",
                                            ),
                                            html.Span(" · ", className="validation-meta"),
                                            html.A(
                                                "Скачать последний манифест",
                                                id="export-pack-download-manifest",
                                                href=view.latest_manifest_download_url,
                                                target="_blank",
                                                rel="noreferrer",
                                                className="basis-link",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="artifact-panel-meta",
                                        children=[
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Папка отчётов",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.target_directory_text,
                                                        id="export-pack-target",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Последний идентификатор отчёта",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.latest_report_id_text,
                                                        id="export-pack-latest-report",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Последний CSV",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.latest_csv_text,
                                                        id="export-pack-latest-csv",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Последний PDF",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.latest_pdf_text,
                                                        id="export-pack-latest-pdf",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Последний манифест",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.latest_manifest_text,
                                                        id="export-pack-latest-manifest",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Снимок",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.generated_at_text,
                                                        id="export-pack-generated",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                        ],
                                    ),
                                    html.Table(
                                        className="defense-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Время"),
                                                        html.Th("Источник"),
                                                        html.Th("Статус"),
                                                        html.Th("Форматы"),
                                                        html.Th("Скачивание"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                id="export-pack-entries",
                                                children=[
                                                    _build_result_export_entry_row(entry)
                                                    for entry in view.entries
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _build_run_comparison_panel(view: RunComparisonView) -> html.Div:
    return html.Div(
        id="run-comparison",
        className="panel defense-panel",
        children=[
            html.Div(
                className="panel-header",
                children=[
                    html.H2("Сравнение прогонов"),
                    html.Span("До / После", className="panel-tag"),
                ],
            ),
            html.Div(
                className="defense-accordion",
                children=[
                    html.Details(
                        open=True,
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Пара прогонов и экспорт сравнения"),
                                    html.Span(
                                        f"{view.total_exports_text} экспортов",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body artifact-panel-body",
                                children=[
                                    html.Div(
                                        className="artifact-panel-actions",
                                        children=[
                                            html.Div(
                                                id="comparison-status",
                                                className=view.summary_class_name,
                                                children=view.status_text,
                                            ),
                                            html.Button(
                                                "Зафиксировать До",
                                                id="comparison-save-before",
                                                n_clicks=0,
                                                type="button",
                                                className="ghost-button",
                                            ),
                                            html.Button(
                                                "Зафиксировать После",
                                                id="comparison-save-after",
                                                n_clicks=0,
                                                type="button",
                                                className="ghost-button",
                                            ),
                                            html.Button(
                                                "Экспорт CSV/PDF",
                                                id="comparison-export-build",
                                                n_clicks=0,
                                                type="button",
                                                className="ghost-button",
                                                disabled=view.default_before_reference_id is None,
                                            ),
                                        ],
                                    ),
                                    html.P(
                                        id="comparison-summary",
                                        className="validation-intro",
                                        children=view.summary_text,
                                    ),
                                    html.P(
                                        id="comparison-note",
                                        className="validation-meta",
                                        children=view.note,
                                    ),
                                    html.Div(
                                        className="artifact-panel-meta",
                                        children=[
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "До",
                                                        className="detail-label",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="comparison-before-run",
                                                        options=view.source_options,
                                                        value=view.default_before_reference_id,
                                                        placeholder="Выберите базовый прогон",
                                                        clearable=True,
                                                        searchable=False,
                                                        optionHeight=48,
                                                        maxHeight=320,
                                                    ),
                                                    html.P(
                                                        view.named_before_text,
                                                        id="comparison-selected-before-label",
                                                        className="validation-meta",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "После",
                                                        className="detail-label",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="comparison-after-run",
                                                        options=view.source_options,
                                                        value=view.default_after_reference_id,
                                                        placeholder="Выберите целевой прогон",
                                                        clearable=True,
                                                        searchable=False,
                                                        optionHeight=48,
                                                        maxHeight=320,
                                                    ),
                                                    html.P(
                                                        view.named_after_text,
                                                        id="comparison-selected-after-label",
                                                        className="validation-meta",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Последний идентификатор сравнения",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.latest_comparison_id_text,
                                                        id="comparison-latest-id",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Последний CSV",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.latest_csv_text,
                                                        id="comparison-latest-csv",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Последний PDF",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.latest_pdf_text,
                                                        id="comparison-latest-pdf",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Последний манифест",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.latest_manifest_text,
                                                        id="comparison-latest-manifest",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Снимок",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.generated_at_text,
                                                        id="comparison-generated",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="artifact-panel-actions",
                                        children=[
                                            html.P(
                                                id="comparison-pair-summary",
                                                className="validation-intro",
                                                children=(
                                                    "Выберите пару из текущего прогона "
                                                    "и архива сценариев."
                                                ),
                                            ),
                                            html.Div(
                                                id="comparison-compatibility",
                                                className="status-pill status-muted",
                                                children="Пара не выбрана",
                                            ),
                                        ],
                                    ),
                                    html.P(
                                        id="comparison-compatibility-summary",
                                        className="validation-meta",
                                        children=(
                                            "После выбора пары будет выполнена проверка "
                                            "совместимости по шагу, горизонту и сетке тренда."
                                        ),
                                    ),
                                    html.Div(
                                        id="comparison-interpretation",
                                        className="validation-intro",
                                        children="Интерпретация появится после совместимого сравнения.",
                                    ),
                                    html.Div(
                                        id="comparison-top-deltas",
                                        className="capability-list",
                                        children=[
                                            html.Div(
                                                "Top deltas появятся после расчёта пары.",
                                                className="capability-item",
                                            )
                                        ],
                                    ),
                                    html.Table(
                                        className="defense-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Метрика"),
                                                        html.Th("До"),
                                                        html.Th("После"),
                                                        html.Th("Δ"),
                                                        html.Th("Ед."),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                id="comparison-metric-rows",
                                                children=[
                                                    html.Tr(
                                                        children=[
                                                            html.Td(
                                                                "Выберите совместимую пару прогонов.",
                                                                colSpan=5,
                                                            )
                                                        ]
                                                    )
                                                ],
                                            ),
                                        ],
                                    ),
                                    dcc.Graph(
                                        id="comparison-delta-graph",
                                        config={"displayModeBar": False},
                                    ),
                                    html.Table(
                                        className="defense-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Время"),
                                                        html.Th("Пара"),
                                                        html.Th("Совместимость"),
                                                        html.Th("Форматы"),
                                                        html.Th("Скачивание"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                id="comparison-export-entries",
                                                children=[
                                                    _build_run_comparison_entry_row(entry)
                                                    for entry in view.entries
                                                ]
                                                or [
                                                    html.Tr(
                                                        children=[
                                                            html.Td(
                                                                "История экспорта сравнения пока пуста.",
                                                                colSpan=5,
                                                            )
                                                        ]
                                                    )
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _build_scenario_archive_panel(view: ScenarioArchiveView) -> html.Div:
    return html.Div(
        id="scenario-archive",
        className="panel defense-panel",
        children=[
            html.Div(
                className="panel-header",
                children=[
                    html.H2("Архив сценариев"),
                    html.Span("Локальные снимки", className="panel-tag"),
                ],
            ),
            html.Div(
                className="defense-accordion",
                children=[
                    html.Details(
                        open=True,
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Сохранённые прогоны"),
                                    html.Span(
                                        f"{view.total_entries_text} записей",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body artifact-panel-body",
                                children=[
                                    html.Div(
                                        className="artifact-panel-actions",
                                        children=[
                                            html.Div(
                                                id="scenario-archive-status",
                                                className=view.summary_class_name,
                                                children=view.status_text,
                                            ),
                                            html.Button(
                                                "Сохранить текущий прогон",
                                                id="scenario-archive-save",
                                                n_clicks=0,
                                                type="button",
                                                className="ghost-button",
                                            ),
                                        ],
                                    ),
                                    html.P(
                                        id="scenario-archive-summary",
                                        className="validation-intro",
                                        children=view.summary_text,
                                    ),
                                    html.P(
                                        id="scenario-archive-note",
                                        className="validation-meta",
                                        children=view.note,
                                    ),
                                    html.Div(
                                        className="artifact-panel-meta",
                                        children=[
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Папка архива",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.target_directory_text,
                                                        id="scenario-archive-target",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Последний снимок",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.latest_entry_text,
                                                        id="scenario-archive-latest",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Количество записей",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.total_entries_text,
                                                        id="scenario-archive-total",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Снимок",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.generated_at_text,
                                                        id="scenario-archive-generated",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                        ],
                                    ),
                                    html.Table(
                                        className="defense-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Время"),
                                                        html.Th("Источник"),
                                                        html.Th("Статус"),
                                                        html.Th("Ключевые показатели"),
                                                        html.Th("Тревоги"),
                                                        html.Th("Скачивание"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                id="scenario-archive-entries",
                                                children=[
                                                    _build_scenario_archive_entry_row(entry)
                                                    for entry in view.entries
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _build_event_log_panel(view: EventLogView) -> html.Div:
    return html.Div(
        id="event-log",
        className="panel defense-panel",
        children=[
            html.Div(
                className="panel-header",
                children=[
                    html.H2("Журнал событий"),
                    html.Span("Переходы состояний", className="panel-tag"),
                ],
            ),
            html.Div(
                className="defense-accordion",
                children=[
                    html.Details(
                        open=True,
                        className="defense-section",
                        children=[
                            html.Summary(
                                className="defense-summary",
                                children=[
                                    html.Span("Журнал событий"),
                                    html.Span(
                                        f"{view.total_entries_text} записей",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="defense-section-body artifact-panel-body",
                                children=[
                                    html.Div(
                                        className="artifact-panel-actions",
                                        children=[
                                            html.Div(
                                                id="event-log-status",
                                                className=view.summary_class_name,
                                                children=view.status_text,
                                            ),
                                        ],
                                    ),
                                    html.P(
                                        id="event-log-summary",
                                        className="validation-intro",
                                        children=view.summary_text,
                                    ),
                                    html.P(
                                        id="event-log-note",
                                        className="validation-meta",
                                        children=view.note,
                                    ),
                                    html.Div(
                                        className="artifact-panel-meta",
                                        children=[
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Папка журнала",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.target_directory_text,
                                                        id="event-log-target",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Последняя запись",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.latest_entry_text,
                                                        id="event-log-latest",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Количество записей",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.total_entries_text,
                                                        id="event-log-total",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong(
                                                        "Снимок",
                                                        className="detail-label",
                                                    ),
                                                    html.Code(
                                                        view.generated_at_text,
                                                        id="event-log-generated",
                                                        className="defense-code",
                                                    ),
                                                ],
                                                className="artifact-panel-meta-item",
                                            ),
                                        ],
                                    ),
                                    html.Table(
                                        className="defense-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Время"),
                                                        html.Th("Категория"),
                                                        html.Th("Серьёзность"),
                                                        html.Th("Источник"),
                                                        html.Th("Сводка"),
                                                        html.Th("Детали"),
                                                        html.Th("Артефакт"),
                                                        html.Th("JSON"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                id="event-log-entries",
                                                children=[
                                                    _build_event_log_entry_row(entry)
                                                    for entry in view.entries
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _build_validation_pack_panel(view: ValidationMatrixView) -> html.Div:
    return html.Div(
        id="validation-pack",
        className="panel validation-panel",
        children=[
            html.Div(
                className="panel-header",
                children=[
                    html.H2("Пакет валидации"),
                    html.Span("Справочная матрица", className="panel-tag"),
                ],
            ),
            html.Div(
                className="validation-overview",
                children=[
                    html.Div(view.summary_text, className=view.summary_class_name),
                    html.P(view.intro, className="validation-intro"),
                    html.P(view.agreement_text, className="validation-meta"),
                    html.P(view.note, className="mnemonic-note"),
                    html.P(
                        f"Снимок матрицы: {view.generated_at_text}",
                        className="validation-meta",
                    ),
                ],
            ),
            html.Div(
                className="validation-accordion",
                children=[
                    _build_validation_case_panel(case, open_by_default=index == 0)
                    for index, case in enumerate(view.cases)
                ],
            ),
        ],
    )


def _build_manual_check_panel(view: ManualCheckView) -> html.Div:
    return html.Div(
        id="manual-check",
        className="panel manual-check-panel",
        children=[
            html.Div(
                className="panel-header",
                children=[
                    html.H2("Ручная проверка"),
                    html.Span("Живые формулы", className="panel-tag"),
                ],
            ),
            html.Div(id="manual-check-content", children=build_manual_check_panel_content(view)),
        ],
    )


def _build_project_baseline_panel(view: ProjectBaselineView) -> html.Div:
    return html.Div(
        id="p0-baseline",
        className="panel basis-panel",
        children=[
            html.Div(
                className="panel-header",
                children=[
                    html.H2("Базовые показатели P0"),
                    html.Span(view.version_text, className="panel-tag"),
                ],
            ),
            html.Div(
                className="basis-overview",
                children=[
                    html.Div(view.summary_text, className=view.summary_class_name),
                    html.P(view.subject_title, className="manual-check-subject"),
                    html.P(view.subject_summary, className="validation-intro"),
                    html.P(view.note, className="mnemonic-note"),
                    html.P(
                        f"Снимок базового профиля: {view.generated_at_text}",
                        className="validation-meta",
                    ),
                ],
            ),
            html.Div(
                className="basis-accordion",
                children=[
                    html.Details(
                        open=True,
                        className="validation-section",
                        children=[
                            html.Summary(
                                className="validation-summary",
                                children=[
                                    html.Span("Зафиксированные решения"),
                                    html.Span(
                                        f"{len(view.locked_decisions)} решения",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="validation-section-body",
                                children=[
                                    html.Table(
                                        className="basis-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Решение"),
                                                        html.Th("Что зафиксировано"),
                                                        html.Th("Почему"),
                                                        html.Th("Доказательство"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_project_baseline_decision_row(decision)
                                                    for decision in view.locked_decisions
                                                ]
                                            ),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="validation-section",
                        children=[
                            html.Summary(
                                className="validation-summary",
                                children=[
                                    html.Span("Входные параметры"),
                                    html.Span(
                                        f"{len(view.operator_inputs)} операторских + {len(view.fixed_model_inputs)} фиксированных",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="validation-section-body readiness-two-column",
                                children=[
                                    html.Table(
                                        className="basis-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Ввод оператора"),
                                                        html.Th("ID"),
                                                        html.Th("Ед."),
                                                        html.Th("Зачем обязателен"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_project_baseline_input_row(parameter)
                                                    for parameter in view.operator_inputs
                                                ]
                                            ),
                                        ],
                                    ),
                                    html.Table(
                                        className="basis-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Фикс. ввод модели"),
                                                        html.Th("ID"),
                                                        html.Th("Ед."),
                                                        html.Th("Почему зафиксирован"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_project_baseline_input_row(parameter)
                                                    for parameter in view.fixed_model_inputs
                                                ]
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="validation-section",
                        children=[
                            html.Summary(
                                className="validation-summary",
                                children=[
                                    html.Span("Обязательные выходы"),
                                    html.Span(
                                        f"{len(view.outputs)} выходов",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="validation-section-body",
                                children=[
                                    html.Table(
                                        className="basis-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Выход"),
                                                        html.Th("ID"),
                                                        html.Th("Где формируется"),
                                                        html.Th("Зачем обязателен"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_project_baseline_output_row(output)
                                                    for output in view.outputs
                                                ]
                                            ),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="validation-section",
                        children=[
                            html.Summary(
                                className="validation-summary",
                                children=[
                                    html.Span("Сценарии защиты"),
                                    html.Span(
                                        f"{len(view.defense_scenarios)} сценариев",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="validation-section-body",
                                children=[
                                    html.Table(
                                        className="basis-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Сценарий"),
                                                        html.Th("Категория"),
                                                        html.Th("Зачем нужен"),
                                                        html.Th("Что показать"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_project_baseline_scenario_row(scenario)
                                                    for scenario in view.defense_scenarios
                                                ]
                                            ),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="validation-section",
                        children=[
                            html.Summary(
                                className="validation-summary",
                                children=[
                                    html.Span("Формат валидации и дальнейшие шаги"),
                                    html.Span(
                                        f"{len(view.validation_layers)} слоя",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="validation-section-body",
                                children=[
                                    html.Table(
                                        className="basis-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Слой"),
                                                        html.Th("Артефакт"),
                                                        html.Th("Назначение"),
                                                        html.Th("Доказательство"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_project_baseline_validation_row(layer)
                                                    for layer in view.validation_layers
                                                ]
                                            ),
                                        ],
                                    ),
                                    html.Ul(
                                        className="defense-bullet-list",
                                        children=[
                                            html.Li(item) for item in view.follow_up_items
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _build_validation_basis_panel(view: ValidationBasisView) -> html.Div:
    return html.Div(
        id="validation-basis",
        className="panel basis-panel",
        children=[
            html.Div(
                className="panel-header",
                children=[
                    html.H2("Основания валидации"),
                    html.Span("Внешнее обоснование", className="panel-tag"),
                ],
            ),
            html.Div(
                className="basis-overview",
                children=[
                    html.Div(view.summary_text, className=view.summary_class_name),
                    html.P(view.coverage_text, className="validation-intro"),
                    html.P(view.agreement_text, className="validation-meta"),
                    html.P(view.note, className="mnemonic-note"),
                    html.P(
                        f"Снимок методической базы: {view.generated_at_text}",
                        className="validation-meta",
                    ),
                ],
            ),
            html.Div(
                className="basis-accordion",
                children=[
                    html.Details(
                        open=True,
                        className="validation-section",
                        children=[
                            html.Summary(
                                className="validation-summary",
                                children=[
                                    html.Span("Внешние источники"),
                                    html.Span(
                                        f"{len(view.sources)} источника",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="validation-section-body",
                                children=[
                                    html.Table(
                                        className="basis-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("ID"),
                                                        html.Th("Источник"),
                                                        html.Th("Зачем нужен"),
                                                        html.Th("Ссылка"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_validation_basis_source_row(source)
                                                    for source in view.sources
                                                ]
                                            ),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="validation-section",
                        children=[
                            html.Summary(
                                className="validation-summary",
                                children=[
                                    html.Span("Трассировка формул ручной проверки"),
                                    html.Span(
                                        f"{len(view.manual_steps)} шагов",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="validation-section-body",
                                children=[
                                    html.Table(
                                        className="basis-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Шаг"),
                                                        html.Th("Основание"),
                                                        html.Th("Источники"),
                                                        html.Th("Комментарий"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_validation_basis_trace_row(trace)
                                                    for trace in view.manual_steps
                                                ]
                                            ),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="validation-section",
                        children=[
                            html.Summary(
                                className="validation-summary",
                                children=[
                                    html.Span("Трассировка контрольных точек"),
                                    html.Span(
                                        f"{len(view.reference_cases)} режимов",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="validation-section-body",
                                children=[
                                    html.Table(
                                        className="basis-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Контрольная точка"),
                                                        html.Th("Основание"),
                                                        html.Th("Источники"),
                                                        html.Th("Комментарий"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_validation_basis_trace_row(trace)
                                                    for trace in view.reference_cases
                                                ]
                                            ),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _build_validation_agreement_panel(view: ValidationAgreementView) -> html.Div:
    return html.Div(
        id="validation-agreement",
        className="panel basis-panel",
        children=[
            html.Div(
                className="panel-header",
                children=[
                    html.H2("Протокол согласия"),
                    html.Span("Этап 6 — закрытие", className="panel-tag"),
                ],
            ),
            html.Div(
                className="basis-overview",
                children=[
                    html.Div(view.summary_text, className=view.summary_class_name),
                    html.P(view.authority_text, className="validation-intro"),
                    html.P(view.note, className="mnemonic-note"),
                    html.P(
                        f"Согласовано: {view.approved_on_text}",
                        className="validation-meta",
                    ),
                    html.P(
                        f"Снимок протокола: {view.generated_at_text}",
                        className="validation-meta",
                    ),
                ],
            ),
            html.Div(
                className="basis-accordion",
                children=[
                    html.Details(
                        open=True,
                        className="validation-section",
                        children=[
                            html.Summary(
                                className="validation-summary",
                                children=[
                                    html.Span("Согласованные контрольные точки"),
                                    html.Span(
                                        f"{len(view.control_points)} режимов",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="validation-section-body",
                                children=[
                                    html.Table(
                                        className="basis-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Контрольная точка"),
                                                        html.Th("Основание"),
                                                        html.Th("Статус и тревоги"),
                                                        html.Th("Метрики"),
                                                        html.Th("Источники"),
                                                        html.Th("Комментарий"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_validation_agreement_case_row(case)
                                                    for case in view.control_points
                                                ]
                                            ),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="validation-section",
                        children=[
                            html.Summary(
                                className="validation-summary",
                                children=[
                                    html.Span("Согласованные шаги ручной проверки"),
                                    html.Span(
                                        f"{len(view.manual_steps)} шагов",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="validation-section-body",
                                children=[
                                    html.Table(
                                        className="basis-table",
                                        children=[
                                            html.Thead(
                                                html.Tr(
                                                    children=[
                                                        html.Th("Шаг"),
                                                        html.Th("Основание"),
                                                        html.Th("Допуск"),
                                                        html.Th("Источники"),
                                                        html.Th("Комментарий"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(
                                                [
                                                    _build_validation_agreement_step_row(step)
                                                    for step in view.manual_steps
                                                ]
                                            ),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Details(
                        className="validation-section",
                        children=[
                            html.Summary(
                                className="validation-summary",
                                children=[
                                    html.Span("Границы применимости"),
                                    html.Span(
                                        f"{len(view.limitations)} пункта",
                                        className="detail-tag",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="validation-section-body",
                                children=[
                                    html.Ul(
                                        className="defense-bullet-list",
                                        children=[
                                            html.Li(item) for item in view.limitations
                                        ],
                                    )
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def build_manual_check_panel_content(view: ManualCheckView) -> list:
    return [
        html.Div(
            className="manual-check-overview",
            children=[
                html.Div(view.summary_text, className=view.summary_class_name),
                html.P(view.subject_name, className="manual-check-subject"),
                html.P(view.source_text, className="validation-meta"),
                html.P(view.matched_case_text, className="validation-meta"),
                html.P(view.agreement_text, className="validation-meta"),
                html.P(view.note, className="mnemonic-note"),
                html.P(
                    f"Снимок ручной проверки: {view.generated_at_text}",
                    className="validation-meta",
                ),
            ],
        ),
        html.Table(
            className="manual-check-table",
            children=[
                html.Thead(
                    html.Tr(
                        children=[
                            html.Th("Шаг"),
                            html.Th("Подстановка"),
                            html.Th("Ручной расчёт"),
                            html.Th("Модель"),
                            html.Th("Допуск"),
                            html.Th("Δ"),
                            html.Th("Результат"),
                        ]
                    )
                ),
                html.Tbody(
                    [_build_manual_check_row(step) for step in view.steps]
                ),
            ],
        ),
    ]


def _build_manual_check_row(step: ManualCheckStepView) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(step.label),
            html.Td(html.Code(step.formula_text, className="defense-code")),
            html.Td(step.manual_text),
            html.Td(step.model_text),
            html.Td(step.tolerance_text),
            html.Td(step.delta_text),
            html.Td(html.Span(step.result_text, className=step.result_class_name)),
        ]
    )


def _build_demo_readiness_check_row(check: DemoReadinessCheckView) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(check.title),
            html.Td(html.Span(check.status_text, className=check.status_class_name)),
            html.Td(check.detail),
            html.Td(
                html.Code(check.evidence_path, className="defense-code")
                if check.evidence_path
                else "—"
            ),
        ]
    )


def _build_demo_readiness_command_row(command: DemoReadinessCommandView) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(command.title),
            html.Td(html.Code(command.command, className="defense-code")),
            html.Td(command.note),
        ]
    )


def _build_demo_readiness_runtime_row(runtime: DemoReadinessRuntimeView) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(runtime.component),
            html.Td(html.Code(runtime.version, className="defense-code")),
        ]
    )


def _build_demo_readiness_endpoint_row(endpoint: DemoReadinessEndpointView) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(
                [
                    html.Code(endpoint.path, className="defense-code"),
                    html.P(endpoint.label, className="validation-meta"),
                ]
            ),
            html.Td(endpoint.purpose),
        ]
    )


def _build_demo_package_entry_row(entry: DemoPackageEntryView) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(entry.title),
            html.Td(entry.category),
            html.Td(html.Span(entry.status_text, className=entry.status_class_name)),
            html.Td(html.Code(entry.source_paths_text, className="defense-code")),
            html.Td(entry.note),
        ]
    )


def _build_project_baseline_decision_row(
    decision: ProjectBaselineDecisionView,
) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(decision.title),
            html.Td(decision.summary),
            html.Td(decision.rationale),
            html.Td(html.Code(decision.evidence_paths_text, className="defense-code")),
        ]
    )


def _build_project_baseline_input_row(
    parameter: ProjectBaselineParameterView,
) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(parameter.title),
            html.Td(html.Code(parameter.parameter_id, className="defense-code")),
            html.Td(parameter.unit),
            html.Td(parameter.why_text),
        ]
    )


def _build_project_baseline_output_row(
    output: ProjectBaselineOutputView,
) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(output.title),
            html.Td(html.Code(output.output_id, className="defense-code")),
            html.Td(html.Code(output.location_text, className="defense-code")),
            html.Td(output.why_required),
        ]
    )


def _build_project_baseline_scenario_row(
    scenario: ProjectBaselineScenarioView,
) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(
                [
                    html.Strong(scenario.title),
                    html.P(
                        html.Code(scenario.scenario_id, className="defense-code"),
                        className="validation-meta",
                    ),
                ]
            ),
            html.Td(scenario.category_text),
            html.Td(scenario.purpose),
            html.Td(scenario.key_demo_point),
        ]
    )


def _build_project_baseline_validation_row(
    layer: ProjectBaselineValidationLayerView,
) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(layer.title),
            html.Td(layer.artifact),
            html.Td(layer.purpose),
            html.Td(html.Code(layer.evidence_paths_text, className="defense-code")),
        ]
    )


def _build_result_export_entry_row(entry: ResultExportEntryView) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(html.Code(entry.captured_at_text, className="defense-code")),
            html.Td(entry.source_text),
            html.Td(html.Span(entry.status_text, className=entry.status_class_name)),
            html.Td(entry.formats_text),
            html.Td(
                html.Div(
                    className="basis-link-list",
                    children=[
                        html.A("CSV", href=entry.csv_download_url, target="_blank", rel="noreferrer", className="basis-link"),
                        html.Span(" · ", className="validation-meta"),
                        html.A("PDF", href=entry.pdf_download_url, target="_blank", rel="noreferrer", className="basis-link"),
                        html.Span(" · ", className="validation-meta"),
                        html.A("Манифест", href=entry.manifest_download_url, target="_blank", rel="noreferrer", className="basis-link"),
                    ],
                )
            ),
        ]
    )


def _build_run_comparison_entry_row(entry: RunComparisonEntryView) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(html.Code(entry.captured_at_text, className="defense-code")),
            html.Td(entry.pair_text),
            html.Td(html.Span(entry.status_text, className=entry.status_class_name)),
            html.Td(entry.formats_text),
            html.Td(
                html.Div(
                    className="basis-link-list",
                    children=[
                        html.A("CSV", href=entry.csv_download_url, target="_blank", rel="noreferrer", className="basis-link"),
                        html.Span(" · ", className="validation-meta"),
                        html.A("PDF", href=entry.pdf_download_url, target="_blank", rel="noreferrer", className="basis-link"),
                        html.Span(" · ", className="validation-meta"),
                        html.A("Манифест", href=entry.manifest_download_url, target="_blank", rel="noreferrer", className="basis-link"),
                    ],
                )
            ),
        ]
    )


def _build_scenario_archive_entry_row(entry: ScenarioArchiveEntryView) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(html.Code(entry.captured_at_text, className="defense-code")),
            html.Td(entry.source_text),
            html.Td(html.Span(entry.status_text, className=entry.status_class_name)),
            html.Td(entry.metrics_text),
            html.Td(entry.alarms_text),
            html.Td(
                html.A(
                    "Скачать JSON",
                    href=entry.file_download_url,
                    target="_blank",
                    rel="noreferrer",
                    className="basis-link",
                )
            ),
        ]
    )


def _build_event_log_entry_row(entry: EventLogEntryView) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(html.Code(entry.captured_at_text, className="defense-code")),
            html.Td(entry.category_text),
            html.Td(html.Span(entry.level_text, className=entry.level_class_name)),
            html.Td(entry.source_text),
            html.Td(entry.summary_text),
            html.Td(entry.details_text),
            html.Td(
                (
                    html.A(
                        "Скачать артефакт",
                        href=entry.artifact_download_url,
                        target="_blank",
                        rel="noreferrer",
                        className="basis-link",
                    )
                    if entry.artifact_download_url
                    else "—"
                )
            ),
            html.Td(
                html.A(
                    "Скачать JSON",
                    href=entry.file_download_url,
                    target="_blank",
                    rel="noreferrer",
                    className="basis-link",
                )
            ),
        ]
    )


def _build_validation_basis_source_row(source: ValidationBasisSourceView) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(html.Code(source.source_id, className="defense-code")),
            html.Td(
                [
                    html.Strong(source.title),
                    html.P(source.meta_text, className="validation-meta"),
                ]
            ),
            html.Td(source.relevance),
            html.Td(
                html.A(
                    "Открыть",
                    href=source.url,
                    target="_blank",
                    rel="noreferrer",
                    className="basis-link",
                )
            ),
        ]
    )


def _build_validation_basis_trace_row(trace: ValidationBasisTraceView) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(trace.title),
            html.Td(html.Span(trace.level_text, className=trace.level_class_name)),
            html.Td(_build_validation_basis_links(trace.sources)),
            html.Td(trace.note),
        ]
    )


def _build_validation_basis_links(
    sources: list[ValidationBasisLinkView],
) -> html.Div | str:
    if not sources:
        return "Внутреннее допущение MVP"

    children: list = []
    for index, source in enumerate(sources):
        if index > 0:
            children.append(html.Span(", ", className="validation-meta"))
        children.append(
            html.A(
                source.label,
                href=source.url,
                target="_blank",
                rel="noreferrer",
                className="basis-link",
            )
        )
    return html.Div(children, className="basis-link-list")


def _build_validation_agreement_case_row(
    case: ValidationAgreementCaseView,
) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(case.title),
            html.Td(html.Span(case.level_text, className=case.level_class_name)),
            html.Td(
                [
                    html.P(case.status_text, className="validation-meta"),
                    html.P(case.alarms_text, className="validation-meta"),
                ]
            ),
            html.Td(
                html.Ul(
                    className="defense-bullet-list",
                    children=[
                        html.Li(
                            [
                                html.Span(metric.summary_text),
                                html.P(metric.note, className="validation-meta"),
                            ]
                        )
                        for metric in case.metrics
                    ],
                )
            ),
            html.Td(_build_validation_agreement_links(case.sources)),
            html.Td(case.note),
        ]
    )


def _build_validation_agreement_step_row(
    step: ValidationAgreementStepView,
) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(step.label),
            html.Td(html.Span(step.level_text, className=step.level_class_name)),
            html.Td(step.tolerance_text),
            html.Td(_build_validation_agreement_links(step.sources)),
            html.Td(step.note),
        ]
    )


def _build_validation_agreement_links(
    sources: list[ValidationAgreementLinkView],
) -> html.Div | str:
    if not sources:
        return "Проектное допущение"

    children: list = []
    for index, source in enumerate(sources):
        if index > 0:
            children.append(html.Span(", ", className="validation-meta"))
        children.append(
            html.A(
                source.label,
                href=source.url,
                target="_blank",
                rel="noreferrer",
                className="basis-link",
            )
        )
    return html.Div(children, className="basis-link-list")


def _build_validation_case_panel(
    case: ValidationCaseView,
    *,
    open_by_default: bool,
) -> html.Details:
    return html.Details(
        open=open_by_default,
        className="validation-section",
        children=[
            html.Summary(
                className="validation-summary",
                children=[
                    html.Span(case.title),
                    html.Span(case.badge_text, className=case.badge_class_name),
                ],
            ),
            html.Div(
                className="validation-section-body",
                children=[
                    html.P(case.status_text, className="validation-meta"),
                    html.P(case.alarms_text, className="validation-meta"),
                    html.Table(
                        className="validation-table",
                        children=[
                            html.Thead(
                                html.Tr(
                                    children=[
                                        html.Th("Метрика"),
                                        html.Th("Эталон"),
                                        html.Th("Факт"),
                                        html.Th("Результат"),
                                    ]
                                )
                            ),
                            html.Tbody(
                                [
                                    _build_validation_metric_row(metric)
                                    for metric in case.metrics
                                ]
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _build_validation_metric_row(metric: ValidationMetricView) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(metric.label),
            html.Td(metric.expected_text),
            html.Td(metric.actual_text),
            html.Td(
                html.Span(metric.result_text, className=metric.result_class_name),
            ),
        ]
    )


def _build_demo_flow_step(step: DemoFlowStep) -> html.Li:
    return html.Li(
        className="defense-step",
        children=[
            html.Div(step.minute_range, className="defense-step-time"),
            html.Div(
                className="defense-step-copy",
                children=[
                    html.Strong(step.title, className="defense-step-title"),
                    html.P(step.operator_action, className="defense-step-text"),
                    html.P(step.expected_outcome, className="defense-step-text defense-step-outcome"),
                ],
            ),
        ],
    )


def _build_table(
    header_left: str,
    header_right: str,
    rows: list[tuple[str, str]],
    *,
    code_right_column: bool = False,
) -> html.Table:
    body_rows = []
    for left_cell, right_cell in rows:
        right_content = (
            html.Code(right_cell, className="defense-code")
            if code_right_column
            else right_cell
        )
        body_rows.append(
            html.Tr(
                children=[
                    html.Td(left_cell),
                    html.Td(right_content),
                ]
            )
        )

    return html.Table(
        className="defense-table",
        children=[
            html.Thead(
                html.Tr(
                    children=[
                        html.Th(header_left),
                        html.Th(header_right),
                    ]
                )
            ),
            html.Tbody(body_rows),
        ],
    )
