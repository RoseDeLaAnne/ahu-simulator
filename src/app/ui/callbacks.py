from dash import Dash, Input, Output, State, ctx, html, no_update
from dash.dependencies import ClientsideFunction
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from urllib.parse import parse_qs

from app.services.browser_capability_service import BrowserCapabilityService
from app.services.comparison_service import (
    ACTIVE_RUN_REFERENCE_ID,
    ComparisonMetricDelta,
    RunComparison,
    RunComparisonService,
)
from app.services.demo_readiness_service import DemoReadinessService
from app.services.event_log_service import EventLogService
from app.services.export_service import ExportService
from app.services.scenario_archive_service import ScenarioArchiveService
from app.services.scenario_preset_service import ScenarioPresetMutationError
from app.services.simulation_service import (
    SimulationService,
    SimulationSessionTransitionError,
)
from app.services.status_service import DashboardMetricStatus, StatusService
from app.services.validation_service import ValidationService
from app.infrastructure.settings import get_settings
from app.simulation.parameters import ControlMode, SimulationParameters
from app.simulation.scenarios import ScenarioDefinition
from app.simulation.state import (
    OperationStatus,
    SimulationResult,
    SimulationSession,
    SimulationSessionStatus,
)
from app.ui.layout import (
    _build_demo_package_entry_row,
    _build_event_log_entry_row,
    _build_run_comparison_entry_row,
    _build_result_export_entry_row,
    _build_scenario_archive_entry_row,
    _build_scenario_option,
    _format_scenario_metadata,
    build_manual_check_panel_content,
)
from app.ui.render_modes.scene3d import (
    SCENE3D_TRANSFORM_CONTROLS,
    scene3d_transform_input_id,
    scene3d_transform_slider_id,
)
from app.ui.viewmodels.control_modes import build_control_mode_view
from app.ui.scene.bindings import load_scene_bindings
from app.ui.scene.model_catalog import build_scene_model_catalog
from app.ui.scene.room_catalog import (
    build_room_catalog,
    build_room_runtime_payload,
    resolve_room_descriptor,
    resolve_room_preset,
)
from app.ui.viewmodels.browser_diagnostics import (
    build_browser_diagnostics_view,
    build_browser_profile_view,
    build_demo_browser_readiness_view,
)
from app.ui.viewmodels.demo_readiness import build_demo_package_view
from app.ui.viewmodels.event_log import build_event_log_view
from app.ui.viewmodels.export_pack import build_result_export_view
from app.ui.viewmodels.manual_check import build_manual_check_view
from app.ui.viewmodels.run_comparison import build_run_comparison_view
from app.ui.viewmodels.scenario_archive import build_scenario_archive_view
from app.ui.viewmodels.status_presenter import status_class_name, status_text
from app.ui.viewmodels.visualization import build_visualization_signal_map

EXPOSED_SCENARIO_FIELDS = (
    "outdoor_temp_c",
    "airflow_m3_h",
    "supply_temp_setpoint_c",
    "heat_recovery_efficiency",
    "heater_power_kw",
    "filter_contamination",
    "fan_speed_ratio",
    "room_temp_c",
    "room_heat_gain_kw",
    "room_volume_m3",
    "room_thermal_capacity_kwh_per_k",
    "room_loss_coeff_kw_per_k",
    "step_minutes",
    "control_mode",
)

PRESET_SHORTCUT_SCENARIO_IDS = {
    "preset-shortcut-winter": "winter",
    "preset-shortcut-summer": "summer",
    "preset-shortcut-peak-load": "peak_load",
}

MAIN_PAGE_ID = "main"
SERVICE_INDEX_PAGE_ID = "service-index"
SERVICE_PAGE_IDS = {
    "service-validation": "page-service-validation",
    "service-baseline": "page-service-baseline",
    "service-defense": "page-service-defense",
    "service-readiness": "page-service-readiness",
    "service-export": "page-service-export",
    "service-comparison": "page-service-comparison",
    "service-archive": "page-service-archive",
    "service-event-log": "page-service-event-log",
}


def register_callbacks(
    app: Dash,
    service: SimulationService,
    browser_capability_service: BrowserCapabilityService,
    validation_service: ValidationService,
    demo_readiness_service: DemoReadinessService,
    export_service: ExportService,
    scenario_archive_service: ScenarioArchiveService,
    comparison_service: RunComparisonService,
    event_log_service: EventLogService,
    status_service: StatusService,
) -> None:
    def current_scenario_map() -> dict[str, ScenarioDefinition]:
        return {scenario.id: scenario for scenario in service.list_scenarios()}

    bindings_version = load_scene_bindings().version
    browser_profile = browser_capability_service.build_profile()
    scene_model_catalog = build_scene_model_catalog()
    scene_model_map = {model.id: model for model in scene_model_catalog.models}
    room_catalog = build_room_catalog()
    developer_tools_enabled = get_settings().developer_tools_enabled

    app.clientside_callback(
        ClientsideFunction(
            namespace="pvuVisualization",
            function_name="renderMnemonic",
        ),
        Output("mnemonic-sync", "children"),
        Input("visualization-signals", "data"),
    )

    app.clientside_callback(
        ClientsideFunction(
            namespace="pvuDiagnostics",
            function_name="collectBrowserCapabilities",
        ),
        Output("browser-capabilities", "data"),
        Input("browser-capability-refresh", "n_clicks"),
    )

    app.clientside_callback(
        ClientsideFunction(
            namespace="pvu3dBridge",
            function_name="switchRenderMode",
        ),
        Output("render-mode", "data"),
        Output("scene-2d-wrapper", "style"),
        Output("scene-3d-wrapper", "style"),
        Output("render-mode-2d", "className"),
        Output("render-mode-3d", "className"),
        Output("mnemonic-panel-title", "children"),
        Input("render-mode-2d", "n_clicks"),
        Input("render-mode-3d", "n_clicks"),
        State("render-mode", "data"),
        State("scene3d-meta", "data"),
    )

    # ── Page routing: toggle 3D Studio based on URL hash ────────
    app.clientside_callback(
        """
        function(hash) {
            var isStudio = (hash === '#3d-studio');
            return [
                isStudio ? 'app-shell studio-mode' : 'app-shell',
                isStudio ? '3d' : '2d'
            ];
        }
        """,
        Output("app-shell", "className"),
        Output("render-mode", "data", allow_duplicate=True),
        Input("url", "hash"),
        prevent_initial_call=True,
    )

    # ── Studio info panel toggle ────────────────────────
    app.clientside_callback(
        """
        function(n) {
            if (!n) return 'studio-info-panel';
            return (n % 2 === 1) ? 'studio-info-panel open' : 'studio-info-panel';
        }
        """,
        Output("studio-info-panel", "className"),
        Input("studio-info-btn", "n_clicks"),
        prevent_initial_call=True,
    )

    @app.callback(
        Output("hero-panel", "style"),
        Output("section-monitoring", "style"),
        Output("section-visualization", "style"),
        Output("section-analytics", "style"),
        Output("section-service-map", "style"),
        Output("page-service-validation", "style"),
        Output("page-service-baseline", "style"),
        Output("page-service-defense", "style"),
        Output("page-service-readiness", "style"),
        Output("page-service-export", "style"),
        Output("page-service-comparison", "style"),
        Output("page-service-archive", "style"),
        Output("page-service-event-log", "style"),
        Input("url", "search"),
    )
    def toggle_page_sections(search: str | None):
        visible = {"display": "block"}
        hidden = {"display": "none"}
        page_id = _resolve_dashboard_page(search)

        if page_id == MAIN_PAGE_ID:
            return (
                visible,
                visible,
                visible,
                visible,
                hidden,
                hidden,
                hidden,
                hidden,
                hidden,
                hidden,
                hidden,
                hidden,
                hidden,
            )

        if page_id == SERVICE_INDEX_PAGE_ID:
            return (
                hidden,
                hidden,
                hidden,
                hidden,
                visible,
                hidden,
                hidden,
                hidden,
                hidden,
                hidden,
                hidden,
                hidden,
                hidden,
            )

        selected_service_styles = {
            service_page_id: hidden
            for service_page_id in SERVICE_PAGE_IDS.values()
        }
        selected_service_id = SERVICE_PAGE_IDS[page_id]
        selected_service_styles[selected_service_id] = visible
        return (
            hidden,
            hidden,
            hidden,
            hidden,
            hidden,
            selected_service_styles["page-service-validation"],
            selected_service_styles["page-service-baseline"],
            selected_service_styles["page-service-defense"],
            selected_service_styles["page-service-readiness"],
            selected_service_styles["page-service-export"],
            selected_service_styles["page-service-comparison"],
            selected_service_styles["page-service-archive"],
            selected_service_styles["page-service-event-log"],
        )

    app.clientside_callback(
        ClientsideFunction(
            namespace="pvu3dBridge",
            function_name="updateViewer3d",
        ),
        Output("viewer3d-sync", "children"),
        Input("visualization-signals", "data"),
        Input("render-mode", "data"),
        Input("scene3d-model-select", "value"),
        Input("scene3d-display-mode", "value"),
        Input("scene3d-camera-preset", "value"),
        Input("scene3d-room-config", "data"),
        Input("scene3d-scale-config", "data"),
        State("scene3d-meta", "data"),
    )

    @app.callback(
        Output("scene3d-model-tone", "children"),
        Output("scene3d-model-preview", "src"),
        Output("scene3d-model-preview", "alt"),
        Output("scene3d-model-title", "children"),
        Output("scene3d-model-description", "children"),
        Input("scene3d-model-select", "value"),
    )
    def update_scene3d_reference(model_id: str | None):
        fallback = (
            scene_model_catalog.models[0]
            if scene_model_catalog.models
            else None
        )
        model = scene_model_map.get(model_id or "", fallback)
        if model is None:
            return (
                "МОДЕЛЬ",
                None,
                "Справка по модели",
                "3D модель",
                "Выберите модель для визуализации цифрового двойника.",
            )
        return (
            model.tone.upper(),
            model.preview_url,
            model.label,
            model.label,
            model.description,
        )

    @app.callback(
        Output("scene3d-live-status", "children"),
        Output("scene3d-live-status", "className"),
        Output("scene3d-live-summary", "children"),
        Output("scene3d-live-outdoor", "children"),
        Output("scene3d-live-supply", "children"),
        Output("scene3d-live-airflow", "children"),
        Output("scene3d-live-filter", "children"),
        Output("scene3d-live-room", "children"),
        Output("scene3d-live-mode", "children"),
        Input("visualization-signals", "data"),
        Input("scene3d-model-select", "value"),
        Input("scene3d-display-mode", "value"),
    )
    def update_scene3d_live_card(
        signals,
        model_id: str | None,
        display_mode: str | None,
    ):
        fallback = (
            scene_model_catalog.models[0]
            if scene_model_catalog.models
            else None
        )
        model = scene_model_map.get(model_id or "", fallback)
        if not signals:
            return (
                status_service.status_label(OperationStatus.NORMAL),
                status_service.status_class_name(OperationStatus.NORMAL),
                "После загрузки параметров сводка сцены появится здесь.",
                "—",
                "—",
                "—",
                "—",
                "—",
                (display_mode or "studio").title(),
            )

        try:
            operation_status = OperationStatus(str(signals.get("status") or "normal"))
        except ValueError:
            operation_status = OperationStatus.NORMAL
        live_status_text = status_service.status_label(operation_status)
        live_status_class_name = status_service.status_class_name(operation_status)
        nodes = signals.get("nodes") or {}

        def _signal_value(section: dict, key: str) -> str:
            payload = section.get(key) or {}
            return str(payload.get("value") or "—")

        return (
            live_status_text,
            live_status_class_name,
            str(signals.get("summary") or "Live-сводка недоступна."),
            _signal_value(nodes, "outdoor_air"),
            _signal_value((signals.get("sensors") or {}), "sensor_supply_temp"),
            _signal_value((signals.get("sensors") or {}), "sensor_airflow"),
            _signal_value(nodes, "filter_bank"),
            _signal_value(nodes, "room_zone"),
            f"{(display_mode or 'studio').title()} / {model.label if model else '3D'}",
        )

    @app.callback(
        Output("scene3d-room-preset", "options"),
        Output("scene3d-room-preset", "value"),
        Output("scene3d-room-title", "children"),
        Output("scene3d-room-description", "children"),
        Output("scene3d-room-climate", "children"),
        Output("scene3d-room-volume", "children"),
        Output("scene3d-room-capacity", "children"),
        Output("scene3d-room-loss", "children"),
        Output("scene3d-room-design-occupancy", "children"),
        Output("scene3d-room-sensors", "children"),
        Input("scene3d-room-select", "value"),
    )
    def update_scene3d_room_catalog(
        room_id: str | None,
    ):
        room = resolve_room_descriptor(room_catalog, room_id)
        if room is None:
            return (
                [],
                None,
                "Помещение",
                "Каталог помещений пуст.",
                "Room-режим пока недоступен.",
                "—",
                "—",
                "—",
                "—",
                [
                    html.Div(
                        "После добавления room-моделей здесь появятся локальные датчики и режимы.",
                        className="capability-item",
                    )
                ],
            )

        preset = resolve_room_preset(room, room.default_preset_id)
        preset_options = [
            {"label": preset_item.label, "value": preset_item.id}
            for preset_item in room.presets
        ]
        sensor_items = [
            html.Div(
                f"CO₂: следит за качеством воздуха при загрузке {room.design_occupancy_people} чел.",
                className="capability-item",
            ),
            html.Div(
                "Влажность: показывает, насколько вентиляция справляется с влагой и теплопритоками.",
                className="capability-item",
            ),
            html.Div(
                f"Occupancy: сравнивает текущее число людей с расчётной загрузкой {room.design_occupancy_people} чел.",
                className="capability-item",
            ),
        ]
        return (
            preset_options,
            preset.id if preset else None,
            room.label,
            room.description,
            room.climate_note,
            f"{room.volume_m3:.0f} м³",
            f"{room.room_thermal_capacity_kwh_per_k:.1f} кВт·ч/К",
            f"{room.room_loss_coeff_kw_per_k:.2f} кВт/К",
            f"{room.design_occupancy_people} чел.",
            sensor_items,
        )

    @app.callback(
        Output("scene3d-room-preset-note", "children"),
        Input("scene3d-room-select", "value"),
        Input("scene3d-room-preset", "value"),
    )
    def update_scene3d_room_preset_note(
        room_id: str | None,
        preset_id: str | None,
    ):
        room = resolve_room_descriptor(room_catalog, room_id)
        if room is None:
            return "Для выбранного помещения пока нет пояснения."
        preset = resolve_room_preset(room, preset_id)
        return preset.explanation if preset else room.climate_note

    @app.callback(
        Output("scenario-select", "options"),
        Output("scene3d-scenario-select", "options"),
        Input("scenario-preset-version", "data"),
    )
    def refresh_scenario_options(_version):
        options = _scenario_selection_options(service)
        return options, options

    @app.callback(
        Output("scenario-preset-version", "data"),
        Output("scenario-select", "value", allow_duplicate=True),
        Output("scene3d-scenario-select", "value", allow_duplicate=True),
        Output("user-preset-status", "children"),
        Output("user-preset-export-payload", "children"),
        Input("user-preset-save", "n_clicks"),
        Input("user-preset-rename", "n_clicks"),
        Input("user-preset-delete", "n_clicks"),
        Input("user-preset-import", "n_clicks"),
        Input("user-preset-export", "n_clicks"),
        State("scenario-select", "value"),
        State("user-preset-title", "value"),
        State("user-preset-import-payload", "value"),
        State("outdoor-temp", "value"),
        State("airflow", "value"),
        State("setpoint", "value"),
        State("recovery-efficiency", "value"),
        State("heater-power", "value"),
        State("filter-contamination", "value"),
        State("fan-speed", "value"),
        State("room-temp", "value"),
        State("room-heat-gain", "value"),
        State("step-minutes", "value"),
        State("control-mode", "value"),
        State("scene3d-room-config", "data"),
        State("scenario-preset-version", "data"),
        State("simulation-session-state", "data"),
        prevent_initial_call=True,
    )
    def manage_user_preset(
        _save_clicks,
        _rename_clicks,
        _delete_clicks,
        _import_clicks,
        _export_clicks,
        selected_scenario_id,
        title,
        import_payload,
        outdoor_temp_c,
        airflow_m3_h,
        supply_temp_setpoint_c,
        heat_recovery_efficiency,
        heater_power_kw,
        filter_contamination,
        fan_speed_ratio,
        room_temp_c,
        room_heat_gain_kw,
        step_minutes,
        control_mode,
        room_config,
        version,
        session_payload,
    ):
        if _session_is_running(session_payload):
            return version, no_update, no_update, "Остановите сессию перед изменением пресетов.", no_update

        triggered_id = str(ctx.triggered_id)
        try:
            if triggered_id == "user-preset-save":
                parameters = _build_simulation_parameters(
                    outdoor_temp_c,
                    airflow_m3_h,
                    supply_temp_setpoint_c,
                    heat_recovery_efficiency,
                    heater_power_kw,
                    filter_contamination,
                    fan_speed_ratio,
                    room_temp_c,
                    room_heat_gain_kw,
                    step_minutes,
                    control_mode,
                    room_config,
                )
                scenario = service.create_user_preset(
                    title=(title or "Пользовательский пресет"),
                    parameters=parameters,
                )
                return (
                    int(version or 0) + 1,
                    scenario.id,
                    scenario.id,
                    f"Пользовательский пресет «{scenario.title}» сохранён.",
                    no_update,
                )
            if triggered_id == "user-preset-rename":
                scenario = service.rename_user_preset(
                    str(selected_scenario_id),
                    title=(title or ""),
                )
                return (
                    int(version or 0) + 1,
                    scenario.id,
                    scenario.id,
                    f"Пресет переименован: «{scenario.title}».",
                    no_update,
                )
            if triggered_id == "user-preset-delete":
                scenario = service.delete_user_preset(str(selected_scenario_id))
                fallback_id = get_settings().default_scenario_id
                return (
                    int(version or 0) + 1,
                    fallback_id,
                    fallback_id,
                    f"Пользовательский пресет «{scenario.title}» удалён.",
                    "",
                )
            if triggered_id == "user-preset-import":
                payload = json.loads(import_payload or "{}")
                scenario = service.import_user_preset(payload)
                return (
                    int(version or 0) + 1,
                    scenario.id,
                    scenario.id,
                    f"Пользовательский пресет «{scenario.title}» импортирован.",
                    no_update,
                )
            if triggered_id == "user-preset-export":
                payload = service.export_user_preset(str(selected_scenario_id))
                return (
                    version,
                    no_update,
                    no_update,
                    "Экспорт пользовательского пресета подготовлен.",
                    json.dumps(payload, ensure_ascii=False, indent=2),
                )
        except json.JSONDecodeError:
            return version, no_update, no_update, "Импорт ожидает корректный JSON.", no_update
        except (KeyError, ValueError, RuntimeError, ScenarioPresetMutationError) as error:
            return version, no_update, no_update, str(error), no_update
        return version, no_update, no_update, no_update, no_update

    @app.callback(
        Output("scenario-description", "children"),
        Output("scenario-preset-metadata", "children"),
        Output("outdoor-temp", "value"),
        Output("airflow", "value"),
        Output("setpoint", "value"),
        Output("recovery-efficiency", "value"),
        Output("heater-power", "value"),
        Output("filter-contamination", "value"),
        Output("fan-speed", "value"),
        Output("room-temp", "value"),
        Output("room-heat-gain", "value"),
        Output("step-minutes", "value"),
        Output("control-mode", "value"),
        Output("scene3d-outdoor-temp", "value"),
        Output("scene3d-airflow", "value"),
        Output("scene3d-setpoint", "value"),
        Output("scene3d-recovery-efficiency", "value"),
        Output("scene3d-heater-power", "value"),
        Output("scene3d-filter-contamination", "value"),
        Output("scene3d-fan-speed", "value"),
        Output("scene3d-room-temp", "value"),
        Output("scene3d-room-heat-gain", "value"),
        Output("scene3d-control-mode", "value"),
        Input("scenario-select", "value"),
    )
    def load_scenario(selected_scenario_id: str):
        scenario_map = current_scenario_map()
        scenario = scenario_map[selected_scenario_id]
        parameters = scenario.parameters
        return (
            scenario.formatted_description(),
            _format_scenario_metadata(scenario),
            parameters.outdoor_temp_c,
            parameters.airflow_m3_h,
            parameters.supply_temp_setpoint_c,
            parameters.heat_recovery_efficiency,
            parameters.heater_power_kw,
            parameters.filter_contamination,
            parameters.fan_speed_ratio,
            parameters.room_temp_c,
            parameters.room_heat_gain_kw,
            parameters.step_minutes,
            parameters.control_mode.value,
            parameters.outdoor_temp_c,
            parameters.airflow_m3_h,
            parameters.supply_temp_setpoint_c,
            parameters.heat_recovery_efficiency,
            parameters.heater_power_kw,
            parameters.filter_contamination,
            parameters.fan_speed_ratio,
            parameters.room_temp_c,
            parameters.room_heat_gain_kw,
            parameters.control_mode.value,
        )

    @app.callback(
        Output("scenario-select", "value", allow_duplicate=True),
        Output("scene3d-scenario-select", "value"),
        Input("preset-shortcut-winter", "n_clicks"),
        Input("preset-shortcut-summer", "n_clicks"),
        Input("preset-shortcut-peak-load", "n_clicks"),
        State("simulation-session-state", "data"),
        prevent_initial_call=True,
    )
    def apply_preset_shortcut(
        _winter_clicks: int,
        _summer_clicks: int,
        _peak_clicks: int,
        session_payload,
    ):
        if _session_is_running(session_payload):
            return no_update, no_update
        selected_scenario_id = _resolve_preset_shortcut(ctx.triggered_id)
        scenario_map = current_scenario_map()
        if selected_scenario_id is None or selected_scenario_id not in scenario_map:
            return no_update, no_update
        return selected_scenario_id, selected_scenario_id

    @app.callback(
        Output("scene3d-room-config", "data", allow_duplicate=True),
        Output("scene3d-outdoor-temp", "value", allow_duplicate=True),
        Output("scene3d-airflow", "value", allow_duplicate=True),
        Output("scene3d-setpoint", "value", allow_duplicate=True),
        Output("scene3d-recovery-efficiency", "value", allow_duplicate=True),
        Output("scene3d-heater-power", "value", allow_duplicate=True),
        Output("scene3d-filter-contamination", "value", allow_duplicate=True),
        Output("scene3d-fan-speed", "value", allow_duplicate=True),
        Output("scene3d-room-temp", "value", allow_duplicate=True),
        Output("scene3d-room-heat-gain", "value", allow_duplicate=True),
        Output("scene3d-room-occupancy", "value", allow_duplicate=True),
        Output("scene3d-room-humidity", "value", allow_duplicate=True),
        Input("scene3d-room-select", "value"),
        Input("scene3d-room-preset", "value"),
        State("scene3d-control-mode", "value"),
        State("simulation-session-state", "data"),
        prevent_initial_call=True,
    )
    def apply_scene3d_room_preset(
        room_id: str | None,
        preset_id: str | None,
        _current_control_mode: str | None,
        session_payload,
    ):
        if _session_is_running(session_payload):
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )
        room = resolve_room_descriptor(room_catalog, room_id)
        if room is None:
            return (
                None,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )
        preset = resolve_room_preset(room, preset_id)
        room_payload = build_room_runtime_payload(room, preset_id=preset.id if preset else None)
        if preset is None:
            return (
                room_payload,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                room_payload["occupancy_people"],
                room_payload["local_humidity_percent"],
            )
        return (
            room_payload,
            preset.outdoor_temp_c,
            preset.airflow_m3_h,
            preset.supply_temp_setpoint_c,
            preset.heat_recovery_efficiency,
            preset.heater_power_kw,
            preset.filter_contamination,
            preset.fan_speed_ratio,
            preset.room_temp_c,
            preset.room_heat_gain_kw,
            preset.occupancy_people,
            preset.local_humidity_percent,
        )

    @app.callback(
        Output("scenario-select", "value", allow_duplicate=True),
        Input("scene3d-scenario-select", "value"),
        State("scenario-select", "value"),
        State("simulation-session-state", "data"),
        prevent_initial_call=True,
    )
    def sync_scene3d_scenario_to_main(
        studio_scenario_id: str | None,
        current_scenario_id: str | None,
        session_payload,
    ):
        if _session_is_running(session_payload):
            return no_update
        if not studio_scenario_id or studio_scenario_id == current_scenario_id:
            return no_update
        return studio_scenario_id

    @app.callback(
        Output("outdoor-temp", "value", allow_duplicate=True),
        Output("airflow", "value", allow_duplicate=True),
        Output("setpoint", "value", allow_duplicate=True),
        Output("recovery-efficiency", "value", allow_duplicate=True),
        Output("heater-power", "value", allow_duplicate=True),
        Output("filter-contamination", "value", allow_duplicate=True),
        Output("fan-speed", "value", allow_duplicate=True),
        Output("room-temp", "value", allow_duplicate=True),
        Output("room-heat-gain", "value", allow_duplicate=True),
        Output("control-mode", "value", allow_duplicate=True),
        Input("scene3d-outdoor-temp", "value"),
        Input("scene3d-airflow", "value"),
        Input("scene3d-setpoint", "value"),
        Input("scene3d-recovery-efficiency", "value"),
        Input("scene3d-heater-power", "value"),
        Input("scene3d-filter-contamination", "value"),
        Input("scene3d-fan-speed", "value"),
        Input("scene3d-room-temp", "value"),
        Input("scene3d-room-heat-gain", "value"),
        Input("scene3d-control-mode", "value"),
        State("outdoor-temp", "value"),
        State("airflow", "value"),
        State("setpoint", "value"),
        State("recovery-efficiency", "value"),
        State("heater-power", "value"),
        State("filter-contamination", "value"),
        State("fan-speed", "value"),
        State("room-temp", "value"),
        State("room-heat-gain", "value"),
        State("control-mode", "value"),
        State("simulation-session-state", "data"),
        prevent_initial_call=True,
    )
    def sync_scene3d_controls_to_main(
        outdoor_temp_c,
        airflow_m3_h,
        supply_temp_setpoint_c,
        heat_recovery_efficiency,
        heater_power_kw,
        filter_contamination,
        fan_speed_ratio,
        room_temp_c,
        room_heat_gain_kw,
        control_mode,
        main_outdoor_temp_c,
        main_airflow_m3_h,
        main_supply_temp_setpoint_c,
        main_heat_recovery_efficiency,
        main_heater_power_kw,
        main_filter_contamination,
        main_fan_speed_ratio,
        main_room_temp_c,
        main_room_heat_gain_kw,
        main_control_mode,
        session_payload,
    ):
        if _session_is_running(session_payload):
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )
        source_values = (
            outdoor_temp_c,
            airflow_m3_h,
            supply_temp_setpoint_c,
            heat_recovery_efficiency,
            heater_power_kw,
            filter_contamination,
            fan_speed_ratio,
            room_temp_c,
            room_heat_gain_kw,
            control_mode,
        )
        target_values = (
            main_outdoor_temp_c,
            main_airflow_m3_h,
            main_supply_temp_setpoint_c,
            main_heat_recovery_efficiency,
            main_heater_power_kw,
            main_filter_contamination,
            main_fan_speed_ratio,
            main_room_temp_c,
            main_room_heat_gain_kw,
            main_control_mode,
        )
        return tuple(
            value if value != current else no_update
            for value, current in zip(source_values, target_values, strict=True)
        )

    @app.callback(
        Output("scene3d-room-config", "data", allow_duplicate=True),
        Input("scene3d-room-occupancy", "value"),
        Input("scene3d-room-humidity", "value"),
        State("scene3d-room-select", "value"),
        State("scene3d-room-preset", "value"),
        prevent_initial_call=True,
    )
    def update_scene3d_room_runtime(
        occupancy_people: int | None,
        local_humidity_percent: float | None,
        room_id: str | None,
        preset_id: str | None,
    ):
        room = resolve_room_descriptor(room_catalog, room_id)
        if room is None:
            return None
        return build_room_runtime_payload(
            room,
            preset_id=preset_id,
            occupancy_people=occupancy_people,
            local_humidity_percent=local_humidity_percent,
        )

    if developer_tools_enabled:
        transform_outputs = [Output("scene3d-scale-config", "data")]
        transform_inputs = []
        for transform_control in SCENE3D_TRANSFORM_CONTROLS:
            transform_key = str(transform_control["key"])
            transform_input_id = scene3d_transform_input_id(transform_key)
            transform_slider_id = scene3d_transform_slider_id(transform_key)
            transform_outputs.extend(
                [
                    Output(transform_input_id, "value"),
                    Output(transform_slider_id, "value"),
                ]
            )
            transform_inputs.extend(
                [
                    Input(transform_input_id, "value"),
                    Input(transform_slider_id, "value"),
                ]
            )
        transform_inputs.append(Input("scene3d-dev-transform-reset", "n_clicks"))

        app.clientside_callback(
            ClientsideFunction(
                namespace="pvu3dBridge",
                function_name="syncTransformControls",
            ),
            *transform_outputs,
            *transform_inputs,
        )

    @app.callback(
        Output("scene3d-room-co2", "children"),
        Output("scene3d-room-humidity-live", "children"),
        Output("scene3d-room-occupancy-live", "children"),
        Output("scene3d-room-air-quality", "children"),
        Output("scene3d-room-preset-active", "children"),
        Output("scene3d-room-fresh-air", "children"),
        Input("visualization-signals", "data"),
        Input("scene3d-room-config", "data"),
    )
    def update_scene3d_room_sensor_card(
        signals,
        room_config,
    ):
        if not signals:
            preset = (room_config or {}).get("active_preset") or {}
            return (
                "—",
                "—",
                "—",
                "—",
                str(preset.get("label") or "Пользовательский режим"),
                "—",
            )
        room_sensors = (signals or {}).get("room_sensors") or {}
        preset = (room_config or {}).get("active_preset") or {}

        def _value(key: str, fallback: str = "—") -> str:
            payload = room_sensors.get(key) or {}
            return str(payload.get("value") or fallback)

        quality_payload = room_sensors.get("sensor_room_air_quality") or {}
        quality_state = str(quality_payload.get("state") or "normal")
        quality_text = {
            "alarm": "Плохо",
            "warning": "Под наблюдением",
            "normal": "Комфортно",
        }.get(quality_state, str(quality_payload.get("value") or "Комфортно"))
        fresh_air_detail = str(
            (room_sensors.get("sensor_room_co2") or {}).get("detail") or "—"
        )
        return (
            _value("sensor_room_co2"),
            _value("sensor_room_humidity"),
            _value("sensor_room_occupancy"),
            quality_text,
            str(preset.get("label") or "Пользовательский режим"),
            fresh_air_detail,
        )

    @app.callback(
        Output("browser-capability-status", "children"),
        Output("browser-capability-status", "className"),
        Output("browser-capability-list", "children"),
        Output("browser-capability-note", "children"),
        Output("browser-profile-status", "children"),
        Output("browser-profile-status", "className"),
        Output("browser-profile-summary", "children"),
        Output("browser-profile-list", "children"),
        Output("browser-profile-note", "children"),
        Output("demo-browser-status", "children"),
        Output("demo-browser-status", "className"),
        Output("demo-browser-summary", "children"),
        Output("demo-browser-list", "children"),
        Output("demo-browser-note", "children"),
        Input("browser-capabilities", "data"),
    )
    def update_browser_diagnostics(diagnostics_payload):
        view = build_browser_diagnostics_view(diagnostics_payload)
        comparison = browser_capability_service.build_comparison(diagnostics_payload)
        profile_view = build_browser_profile_view(browser_profile, comparison)
        demo_view = build_demo_browser_readiness_view(
            diagnostics_payload,
            browser_profile,
            comparison,
        )
        items = [html.Div(item, className="capability-item") for item in view.items]
        profile_items = [
            html.Div(item, className="capability-item")
            for item in profile_view.items
        ]
        demo_items = [
            html.Div(item, className="capability-item") for item in demo_view.items
        ]
        return (
            view.status_text,
            view.status_class_name,
            items,
            view.note,
            profile_view.status_text,
            profile_view.status_class_name,
            profile_view.summary_text,
            profile_items,
            profile_view.note,
            demo_view.status_text,
            demo_view.status_class_name,
            demo_view.summary_text,
            demo_items,
            demo_view.note,
        )

    @app.callback(
        Output("demo-package-status", "children"),
        Output("demo-package-status", "className"),
        Output("demo-package-summary", "children"),
        Output("demo-package-note", "children"),
        Output("demo-package-target", "children"),
        Output("demo-package-latest", "children"),
        Output("demo-package-manifest", "children"),
        Output("demo-package-generated", "children"),
        Output("demo-package-entries", "children"),
        Input("demo-package-build", "n_clicks"),
        prevent_initial_call=True,
    )
    def build_demo_package(_n_clicks: int):
        demo_readiness_service.build_demo_package()
        package_view = build_demo_package_view(
            demo_readiness_service.build_package_snapshot()
        )
        return (
            package_view.status_text,
            package_view.summary_class_name,
            package_view.summary_text,
            package_view.note,
            package_view.target_directory_text,
            package_view.latest_bundle_text,
            package_view.latest_manifest_text,
            package_view.generated_at_text,
            [
                _build_demo_package_entry_row(entry)
                for entry in package_view.entries
            ],
        )

    @app.callback(
        Output("export-pack-status", "children"),
        Output("export-pack-status", "className"),
        Output("export-pack-summary", "children"),
        Output("export-pack-note", "children"),
        Output("export-pack-target", "children"),
        Output("export-pack-latest-report", "children"),
        Output("export-pack-latest-csv", "children"),
        Output("export-pack-latest-pdf", "children"),
        Output("export-pack-latest-manifest", "children"),
        Output("export-pack-generated", "children"),
        Output("export-pack-preview-text", "children"),
        Output("export-pack-download-csv", "href"),
        Output("export-pack-download-pdf", "href"),
        Output("export-pack-download-manifest", "href"),
        Output("export-pack-entries", "children"),
        Input("export-pack-preview", "n_clicks"),
        Input("export-pack-build", "n_clicks"),
        State("scenario-select", "value"),
        State("outdoor-temp", "value"),
        State("airflow", "value"),
        State("setpoint", "value"),
        State("recovery-efficiency", "value"),
        State("heater-power", "value"),
        State("filter-contamination", "value"),
        State("fan-speed", "value"),
        State("room-temp", "value"),
        State("room-heat-gain", "value"),
        State("step-minutes", "value"),
        State("control-mode", "value"),
        State("scene3d-room-config", "data"),
        State("simulation-session-state", "data"),
        prevent_initial_call=True,
        running=[
            (Output("export-pack-build", "disabled"), True, False),
            (
                Output("export-pack-build", "children"),
                "Собираем отчёт...",
                "Собрать отчёт PDF/CSV",
            ),
        ],
    )
    def build_result_export(
        _preview_clicks: int,
        _n_clicks: int,
        selected_scenario_id,
        outdoor_temp_c,
        airflow_m3_h,
        supply_temp_setpoint_c,
        heat_recovery_efficiency,
        heater_power_kw,
        filter_contamination,
        fan_speed_ratio,
        room_temp_c,
        room_heat_gain_kw,
        step_minutes,
        control_mode,
        room_config,
        session_payload,
    ):
        parameters = _build_simulation_parameters(
            outdoor_temp_c,
            airflow_m3_h,
            supply_temp_setpoint_c,
            heat_recovery_efficiency,
            heater_power_kw,
            filter_contamination,
            fan_speed_ratio,
            room_temp_c,
            room_heat_gain_kw,
            step_minutes,
            control_mode,
            room_config,
        )
        result = _resolve_result_for_snapshot(
            service,
            current_scenario_map(),
            selected_scenario_id,
            parameters,
            ctx.triggered_id,
            session_payload,
        )
        export_session = _resolve_export_session(session_payload, result)
        preview_text = None
        if ctx.triggered_id == "export-pack-preview":
            preview = export_service.preview_result(result, export_session)
            preview_text = preview.summary
        else:
            build_result = export_service.export_result(result, export_session)
            event_log_service.record_export_event(
                result,
                manifest_path=build_result.entry.manifest_path,
                source_type="dashboard",
            )
        export_view = build_result_export_view(export_service.build_snapshot())
        return (
            export_view.status_text,
            export_view.summary_class_name,
            export_view.summary_text,
            export_view.note,
            export_view.target_directory_text,
            export_view.latest_report_id_text,
            export_view.latest_csv_text,
            export_view.latest_pdf_text,
            export_view.latest_manifest_text,
            export_view.generated_at_text,
            preview_text or export_view.preview_text,
            export_view.latest_csv_download_url,
            export_view.latest_pdf_download_url,
            export_view.latest_manifest_download_url,
            [
                _build_result_export_entry_row(entry)
                for entry in export_view.entries
            ],
        )

    @app.callback(
        Output("scenario-archive-status", "children"),
        Output("scenario-archive-status", "className"),
        Output("scenario-archive-summary", "children"),
        Output("scenario-archive-note", "children"),
        Output("scenario-archive-target", "children"),
        Output("scenario-archive-latest", "children"),
        Output("scenario-archive-total", "children"),
        Output("scenario-archive-generated", "children"),
        Output("scenario-archive-entries", "children"),
        Input("scenario-archive-save", "n_clicks"),
        State("scenario-select", "value"),
        State("outdoor-temp", "value"),
        State("airflow", "value"),
        State("setpoint", "value"),
        State("recovery-efficiency", "value"),
        State("heater-power", "value"),
        State("filter-contamination", "value"),
        State("fan-speed", "value"),
        State("room-temp", "value"),
        State("room-heat-gain", "value"),
        State("step-minutes", "value"),
        State("control-mode", "value"),
        State("scene3d-room-config", "data"),
        State("simulation-session-state", "data"),
        prevent_initial_call=True,
    )
    def save_scenario_archive(
        _n_clicks: int,
        selected_scenario_id,
        outdoor_temp_c,
        airflow_m3_h,
        supply_temp_setpoint_c,
        heat_recovery_efficiency,
        heater_power_kw,
        filter_contamination,
        fan_speed_ratio,
        room_temp_c,
        room_heat_gain_kw,
        step_minutes,
        control_mode,
        room_config,
        session_payload,
    ):
        parameters = _build_simulation_parameters(
            outdoor_temp_c,
            airflow_m3_h,
            supply_temp_setpoint_c,
            heat_recovery_efficiency,
            heater_power_kw,
            filter_contamination,
            fan_speed_ratio,
            room_temp_c,
            room_heat_gain_kw,
            step_minutes,
            control_mode,
            room_config,
        )
        result = _resolve_result_for_snapshot(
            service,
            current_scenario_map(),
            selected_scenario_id,
            parameters,
            ctx.triggered_id,
            session_payload,
        )
        save_result = scenario_archive_service.save_result(result)
        event_log_service.record_archive_event(
            result,
            archive_path=save_result.entry.file_path,
            source_type="dashboard",
        )
        archive_view = build_scenario_archive_view(
            scenario_archive_service.build_snapshot()
        )
        return (
            archive_view.status_text,
            archive_view.summary_class_name,
            archive_view.summary_text,
            archive_view.note,
            archive_view.target_directory_text,
            archive_view.latest_entry_text,
            archive_view.total_entries_text,
            archive_view.generated_at_text,
            [
                _build_scenario_archive_entry_row(entry)
                for entry in archive_view.entries
            ],
        )

    @app.callback(
        Output("comparison-status", "children"),
        Output("comparison-status", "className"),
        Output("comparison-summary", "children"),
        Output("comparison-note", "children"),
        Output("comparison-latest-id", "children"),
        Output("comparison-latest-csv", "children"),
        Output("comparison-latest-pdf", "children"),
        Output("comparison-latest-manifest", "children"),
        Output("comparison-generated", "children"),
        Output("comparison-before-run", "options"),
        Output("comparison-after-run", "options"),
        Output("comparison-before-run", "value"),
        Output("comparison-after-run", "value"),
        Output("comparison-selected-before-label", "children"),
        Output("comparison-selected-after-label", "children"),
        Output("comparison-pair-summary", "children"),
        Output("comparison-compatibility", "children"),
        Output("comparison-compatibility", "className"),
        Output("comparison-compatibility-summary", "children"),
        Output("comparison-interpretation", "children"),
        Output("comparison-top-deltas", "children"),
        Output("comparison-metric-rows", "children"),
        Output("comparison-delta-graph", "figure"),
        Output("comparison-export-build", "disabled"),
        Output("comparison-export-entries", "children"),
        Input("simulation-session-state", "data"),
        Input("comparison-before-run", "value"),
        Input("comparison-after-run", "value"),
        Input("comparison-save-before", "n_clicks"),
        Input("comparison-save-after", "n_clicks"),
        Input("comparison-export-build", "n_clicks"),
        Input("scenario-archive-generated", "children"),
        running=[
            (
                Output("comparison-export-build", "children"),
                "Собираем сравнение...",
                "Экспорт CSV/PDF",
            ),
        ],
    )
    def update_run_comparison_panel(
        session_payload,
        before_reference_id,
        after_reference_id,
        _save_before_clicks,
        _save_after_clicks,
        _export_clicks,
        _archive_generated,
    ):
        session = _coerce_session(session_payload)
        if ctx.triggered_id == "comparison-save-before":
            comparison_service.save_before(session.current_result)
            before_reference_id = f"snapshot:before"
        elif ctx.triggered_id == "comparison-save-after":
            comparison_service.save_after(session.current_result)
            after_reference_id = f"snapshot:after"

        snapshot = comparison_service.build_snapshot(session.current_result, session)
        selected_before = _resolve_selected_comparison_reference(
            before_reference_id,
            snapshot,
            fallback_reference_id=snapshot.default_before_reference_id,
        )
        selected_after = _resolve_selected_comparison_reference(
            after_reference_id,
            snapshot,
            fallback_reference_id=snapshot.default_after_reference_id,
        )
        comparison = _build_run_comparison(
            comparison_service,
            session,
            selected_before,
            selected_after,
        )

        if (
            ctx.triggered_id == "comparison-export-build"
            and comparison is not None
            and comparison.compatibility.is_compatible
        ):
            comparison_service.export_comparison(comparison)
            snapshot = comparison_service.build_snapshot(session.current_result, session)
            selected_before = _resolve_selected_comparison_reference(
                selected_before,
                snapshot,
                fallback_reference_id=snapshot.default_before_reference_id,
            )
            selected_after = _resolve_selected_comparison_reference(
                selected_after,
                snapshot,
                fallback_reference_id=snapshot.default_after_reference_id,
            )
            comparison = _build_run_comparison(
                comparison_service,
                session,
                selected_before,
                selected_after,
            )

        view = build_run_comparison_view(snapshot)
        export_rows = [
            _build_run_comparison_entry_row(entry)
            for entry in view.entries
        ] or [
            html.Tr(
                children=[
                    html.Td("Export-история сравнения пока пуста.", colSpan=5)
                ]
            )
        ]
        pair_summary, compatibility_text, compatibility_class_name, compatibility_summary = (
            _build_run_comparison_summary(comparison)
        )
        return (
            view.status_text,
            view.summary_class_name,
            view.summary_text,
            view.note,
            view.latest_comparison_id_text,
            view.latest_csv_text,
            view.latest_pdf_text,
            view.latest_manifest_text,
            view.generated_at_text,
            view.source_options,
            view.source_options,
            selected_before,
            selected_after,
            _comparison_source_label(snapshot, selected_before, fallback=view.named_before_text),
            _comparison_source_label(snapshot, selected_after, fallback=view.named_after_text),
            pair_summary,
            compatibility_text,
            compatibility_class_name,
            compatibility_summary,
            _build_run_comparison_interpretation(comparison),
            _build_run_comparison_top_delta_items(comparison),
            _build_run_comparison_metric_rows(comparison),
            _build_run_comparison_figure(comparison),
            comparison is None or not comparison.compatibility.is_compatible,
            export_rows,
        )

    @app.callback(
        Output("status-pill", "children"),
        Output("status-pill", "className"),
        Output("metric-supply-temp", "children"),
        Output("metric-room-temp", "children"),
        Output("metric-heating-power", "children"),
        Output("metric-total-power", "children"),
        Output("metric-airflow", "children"),
        Output("metric-filter-pressure", "children"),
        Output("alarm-list", "children"),
        Output("visualization-signals", "data"),
        Output("summary-text", "children"),
        Output("trend-graph", "figure"),
        Output("control-mode-status", "children"),
        Output("control-mode-status", "className"),
        Output("control-mode-name", "children"),
        Output("control-mode-summary", "children"),
        Output("control-mode-gap", "children"),
        Output("control-mode-airflow-gap", "children"),
        Output("control-mode-heater-band", "children"),
        Output("control-mode-fan-command", "children"),
        Output("event-log-status", "children"),
        Output("event-log-status", "className"),
        Output("event-log-summary", "children"),
        Output("event-log-note", "children"),
        Output("event-log-target", "children"),
        Output("event-log-latest", "children"),
        Output("event-log-total", "children"),
        Output("event-log-generated", "children"),
        Output("event-log-entries", "children"),
        Output("manual-check-content", "children"),
        Output("simulation-session-state", "data"),
        Input("scenario-select", "value"),
        Input("outdoor-temp", "value"),
        Input("airflow", "value"),
        Input("setpoint", "value"),
        Input("recovery-efficiency", "value"),
        Input("heater-power", "value"),
        Input("filter-contamination", "value"),
        Input("fan-speed", "value"),
        Input("room-temp", "value"),
        Input("room-heat-gain", "value"),
        Input("step-minutes", "value"),
        Input("control-mode", "value"),
        Input("scene3d-room-config", "data"),
        Input("simulation-start", "n_clicks"),
        Input("simulation-pause", "n_clicks"),
        Input("simulation-step", "n_clicks"),
        Input("simulation-reset", "n_clicks"),
        Input("simulation-speed", "value"),
        Input("simulation-interval", "n_intervals"),
    )
    def update_dashboard(
        selected_scenario_id,
        outdoor_temp_c,
        airflow_m3_h,
        supply_temp_setpoint_c,
        heat_recovery_efficiency,
        heater_power_kw,
        filter_contamination,
        fan_speed_ratio,
        room_temp_c,
        room_heat_gain_kw,
        step_minutes,
        control_mode,
        room_config,
        _start_clicks,
        _pause_clicks,
        _step_clicks,
        _reset_clicks,
        playback_speed,
        _n_intervals,
    ):
        previous_result = service.get_state()
        room_payload = room_config or {}
        parameters = _build_simulation_parameters(
            outdoor_temp_c,
            airflow_m3_h,
            supply_temp_setpoint_c,
            heat_recovery_efficiency,
            heater_power_kw,
            filter_contamination,
            fan_speed_ratio,
            room_temp_c,
            room_heat_gain_kw,
            step_minutes,
            control_mode,
            room_payload,
        )
        triggered_id = ctx.triggered_id
        try:
            if triggered_id == "simulation-start":
                session = service.start()
                event_log_service.record_session_event(
                    session,
                    trigger="simulation.start",
                    source_type="dashboard",
                )
            elif triggered_id == "simulation-pause":
                session = service.pause()
                event_log_service.record_session_event(
                    session,
                    trigger="simulation.pause",
                    source_type="dashboard",
                )
            elif triggered_id == "simulation-reset":
                session = service.reset()
                event_log_service.record_session_event(
                    session,
                    trigger="simulation.reset",
                    source_type="dashboard",
                )
            elif triggered_id == "simulation-speed":
                session = service.set_playback_speed(float(playback_speed))
                event_log_service.record_session_event(
                    session,
                    trigger="simulation.speed",
                    source_type="dashboard",
                )
            elif triggered_id in {"simulation-step", "simulation-interval"}:
                session = service.tick()
                event_log_service.record_session_event(
                    session,
                    trigger=str(triggered_id),
                    source_type="dashboard",
                )
            elif triggered_id is not None:
                result = _run_dashboard_simulation(
                    service,
                    current_scenario_map(),
                    selected_scenario_id,
                    parameters,
                    triggered_id,
                )
                event_log_service.record_simulation_event(
                    result,
                    previous_result=previous_result,
                    trigger=str(triggered_id),
                    source_type="dashboard",
                )
        except SimulationSessionTransitionError:
            pass

        session = service.get_session()
        result = session.current_result
        manual_check = validation_service.build_manual_check(
            result.parameters,
            result,
        )
        control_view = build_control_mode_view(result.control)
        event_log_view = build_event_log_view(event_log_service.build_snapshot())
        return _render_result(
            result,
            session,
            bindings_version,
            room_payload,
            status_service,
        ) + (
            control_view.target_status_text,
            control_view.target_status_class_name,
            control_view.mode_text,
            control_view.summary,
            control_view.setpoint_gap_text,
            control_view.airflow_gap_text,
            control_view.heater_band_text,
            control_view.fan_command_text,
        ) + (
            event_log_view.status_text,
            event_log_view.summary_class_name,
            event_log_view.summary_text,
            event_log_view.note,
            event_log_view.target_directory_text,
            event_log_view.latest_entry_text,
            event_log_view.total_entries_text,
            event_log_view.generated_at_text,
            [
                _build_event_log_entry_row(entry)
                for entry in event_log_view.entries
            ],
        ) + (
            build_manual_check_panel_content(build_manual_check_view(manual_check)),
            session.model_dump(mode="json"),
        )

    @app.callback(
        Output("simulation-session-status", "children"),
        Output("simulation-session-status", "className"),
        Output("simulation-session-summary", "children"),
        Output("simulation-session-id", "children"),
        Output("simulation-session-step", "children"),
        Output("simulation-session-elapsed", "children"),
        Output("simulation-session-ticks", "children"),
        Output("simulation-session-speed", "children"),
        Output("simulation-session-history", "children"),
        Output("simulation-start", "disabled"),
        Output("simulation-pause", "disabled"),
        Output("simulation-step", "disabled"),
        Output("simulation-reset", "disabled"),
        Output("simulation-interval", "interval"),
        Output("simulation-interval", "disabled"),
        Output("trend-panel-tag", "children"),
        Output("scenario-select", "disabled"),
        Output("preset-shortcut-winter", "disabled"),
        Output("preset-shortcut-summer", "disabled"),
        Output("preset-shortcut-peak-load", "disabled"),
        Output("outdoor-temp", "disabled"),
        Output("airflow", "disabled"),
        Output("setpoint", "disabled"),
        Output("recovery-efficiency", "disabled"),
        Output("heater-power", "disabled"),
        Output("filter-contamination", "disabled"),
        Output("fan-speed", "disabled"),
        Output("room-temp", "disabled"),
        Output("room-heat-gain", "disabled"),
        Output("step-minutes", "disabled"),
        Output("control-mode", "disabled"),
        Output("scene3d-scenario-select", "disabled"),
        Output("scene3d-outdoor-temp", "disabled"),
        Output("scene3d-airflow", "disabled"),
        Output("scene3d-setpoint", "disabled"),
        Output("scene3d-recovery-efficiency", "disabled"),
        Output("scene3d-heater-power", "disabled"),
        Output("scene3d-filter-contamination", "disabled"),
        Output("scene3d-fan-speed", "disabled"),
        Output("scene3d-room-temp", "disabled"),
        Output("scene3d-room-heat-gain", "disabled"),
        Output("scene3d-control-mode", "disabled"),
        Output("scene3d-room-select", "disabled"),
        Output("scene3d-room-preset", "disabled"),
        Input("simulation-session-state", "data"),
    )
    def update_simulation_session_controls(session_payload):
        session = _coerce_session(session_payload)
        status_text, status_class_name = _build_session_status_badge(session.status)
        is_running = session.status == SimulationSessionStatus.RUNNING
        disabled_flags = (is_running,) * 28
        return (
            status_text,
            status_class_name,
            _build_session_summary_text(session),
            session.session_id,
            f"{session.step_minutes} мин",
            _format_session_elapsed(session),
            _format_session_ticks(session),
            f"x{session.playback_speed:g}",
            f"{len(session.history.points)} точек",
            not session.actions.can_start,
            not session.actions.can_pause,
            not session.actions.can_tick,
            not session.actions.can_reset,
            _session_interval_ms(session.playback_speed),
            not is_running,
            (
                f"История {session.elapsed_minutes} / "
                f"{session.current_result.parameters.horizon_minutes} мин"
            ),
            *disabled_flags,
        )


def _run_dashboard_simulation(
    service: SimulationService,
    scenario_map: dict[str, ScenarioDefinition],
    selected_scenario_id: str | None,
    parameters: SimulationParameters,
    triggered_id: str | None,
    ) -> SimulationResult:
    if selected_scenario_id and selected_scenario_id in scenario_map:
        selected_scenario = scenario_map[selected_scenario_id]
        if triggered_id == "scenario-select" or _matches_selected_scenario(
            parameters,
            selected_scenario,
        ):
            return service.run_scenario(selected_scenario_id)
    return service.run(parameters)


def _bounded_float(value, default: float, minimum: float, maximum: float) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        numeric_value = default
    return max(minimum, min(maximum, numeric_value))


def _resolve_preset_shortcut(triggered_id: str | None) -> str | None:
    if triggered_id is None:
        return None
    return PRESET_SHORTCUT_SCENARIO_IDS.get(str(triggered_id))


def _scenario_selection_options(service: SimulationService) -> list[dict[str, str]]:
    return [_build_scenario_option(scenario) for scenario in service.list_scenarios()]


def _resolve_dashboard_page(search: str | None) -> str:
    if not search:
        return MAIN_PAGE_ID

    parsed_query = parse_qs(search.lstrip("?"), keep_blank_values=False)
    page_values = parsed_query.get("page")
    if not page_values:
        return MAIN_PAGE_ID

    page_id = page_values[0].strip().lower()
    if page_id == MAIN_PAGE_ID or page_id == SERVICE_INDEX_PAGE_ID:
        return page_id
    if page_id in SERVICE_PAGE_IDS:
        return page_id
    return MAIN_PAGE_ID


def _matches_selected_scenario(
    parameters: SimulationParameters,
    scenario: ScenarioDefinition,
    ) -> bool:
    return all(
        getattr(parameters, field_name) == getattr(scenario.parameters, field_name)
        for field_name in EXPOSED_SCENARIO_FIELDS
    )


def _build_simulation_parameters(
    outdoor_temp_c,
    airflow_m3_h,
    supply_temp_setpoint_c,
    heat_recovery_efficiency,
    heater_power_kw,
    filter_contamination,
    fan_speed_ratio,
    room_temp_c,
    room_heat_gain_kw,
    step_minutes,
    control_mode,
    room_config: dict[str, object] | None = None,
) -> SimulationParameters:
    room_payload = room_config or {}
    return SimulationParameters(
        outdoor_temp_c=outdoor_temp_c,
        airflow_m3_h=airflow_m3_h,
        supply_temp_setpoint_c=supply_temp_setpoint_c,
        heat_recovery_efficiency=heat_recovery_efficiency,
        heater_power_kw=heater_power_kw,
        filter_contamination=filter_contamination,
        fan_speed_ratio=fan_speed_ratio,
        room_temp_c=room_temp_c,
        room_heat_gain_kw=room_heat_gain_kw,
        room_volume_m3=float(
            room_payload.get("volume_m3")
            or SimulationParameters.model_fields["room_volume_m3"].default
        ),
        room_thermal_capacity_kwh_per_k=float(
            room_payload.get("room_thermal_capacity_kwh_per_k")
            or SimulationParameters.model_fields["room_thermal_capacity_kwh_per_k"].default
        ),
        room_loss_coeff_kw_per_k=float(
            room_payload.get("room_loss_coeff_kw_per_k")
            or SimulationParameters.model_fields["room_loss_coeff_kw_per_k"].default
        ),
        step_minutes=int(
            step_minutes
            or SimulationParameters.model_fields["step_minutes"].default
        ),
        control_mode=ControlMode(control_mode),
    )


def _resolve_result_for_snapshot(
    service: SimulationService,
    scenario_map: dict[str, ScenarioDefinition],
    selected_scenario_id: str | None,
    parameters: SimulationParameters,
    triggered_id: str | None,
    session_payload,
) -> SimulationResult:
    if _session_is_running(session_payload):
        return service.get_state()
    return _run_dashboard_simulation(
        service,
        scenario_map,
        selected_scenario_id,
        parameters,
        triggered_id,
    )


def _build_run_comparison(
    comparison_service: RunComparisonService,
    session: SimulationSession,
    before_reference_id: str | None,
    after_reference_id: str | None,
) -> RunComparison | None:
    if before_reference_id is None or after_reference_id is None:
        return None
    try:
        return comparison_service.build_comparison_from_references(
            before_reference_id,
            after_reference_id,
            session.current_result,
            session,
        )
    except KeyError:
        return None


def _resolve_selected_comparison_reference(
    current_reference_id: str | None,
    snapshot,
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


def _comparison_source_label(snapshot, reference_id: str | None, *, fallback: str) -> str:
    for source in snapshot.available_sources:
        if source.reference_id == reference_id:
            return source.display_label
    return fallback


def _build_run_comparison_summary(
    comparison: RunComparison | None,
) -> tuple[str, str, str, str]:
    if comparison is None:
        return (
            "Выберите пару из текущего прогона и архива сценариев.",
            "Пара не выбрана",
            "status-pill status-muted",
            "Проверка совместимости и расчёт дельт появятся после выбора двух источников.",
        )
    if comparison.compatibility.is_compatible:
        return (
            comparison.summary,
            "Совместимо",
            "status-pill status-normal",
            (
                f"{comparison.compatibility.summary} Рассчитано "
                f"{len(comparison.metric_deltas)} метрик и "
                f"{len(comparison.trend_deltas)} точек трендовых дельт. "
                f"{comparison.interpretation.summary}"
            ),
        )
    return (
        comparison.summary,
        "Несовместимо",
        "status-pill status-warning",
        comparison.compatibility.summary,
    )


def _build_run_comparison_interpretation(comparison: RunComparison | None) -> str:
    if comparison is None:
        return "Интерпретация появится после выбора пары."
    return comparison.interpretation.summary


def _build_run_comparison_top_delta_items(
    comparison: RunComparison | None,
) -> list[html.Div]:
    if comparison is None or not comparison.compatibility.is_compatible:
        return [
            html.Div(
                "Top deltas появятся после расчёта совместимой пары.",
                className="capability-item",
            )
        ]
    return [
        html.Div(
            f"{metric.title}: {metric.delta_value:+.2f} {metric.unit}",
            className="capability-item",
        )
        for metric in comparison.interpretation.top_deltas
    ]


def _build_run_comparison_metric_rows(
    comparison: RunComparison | None,
) -> list[html.Tr]:
    if comparison is None:
        return [html.Tr(children=[html.Td("Выберите совместимую пару прогонов.", colSpan=5)])]
    if not comparison.compatibility.is_compatible:
        return [
            html.Tr(children=[html.Td(issue, colSpan=5)])
            for issue in comparison.compatibility.issues
        ]
    return [
        _build_run_comparison_metric_row(metric)
        for metric in comparison.metric_deltas
    ]


def _build_run_comparison_metric_row(metric: ComparisonMetricDelta) -> html.Tr:
    return html.Tr(
        children=[
            html.Td(metric.title),
            html.Td(f"{metric.before_value:.2f}"),
            html.Td(f"{metric.after_value:.2f}"),
            html.Td(f"{metric.delta_value:+.2f}"),
            html.Td(metric.unit),
        ]
    )


def _build_run_comparison_figure(comparison: RunComparison | None) -> go.Figure:
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.update_layout(
        paper_bgcolor="#f6f2ea",
        plot_bgcolor="#ffffff",
        font={"family": "Inter, Segoe UI, sans-serif", "color": "#1f2933"},
        margin={"l": 40, "r": 30, "t": 20, "b": 40},
        legend={"orientation": "h", "y": 1.12},
    )
    figure.update_xaxes(title="Время, мин", gridcolor="#d8dee4")
    figure.update_yaxes(
        title="Δ температуры, °C",
        secondary_y=False,
        gridcolor="#d8dee4",
    )
    figure.update_yaxes(title="Δ мощности / расхода", secondary_y=True, showgrid=False)

    if comparison is None:
        figure.add_annotation(
            text="Выберите пару прогонов для расчёта дельт.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 15, "color": "#1f2933"},
        )
        return figure

    if not comparison.compatibility.is_compatible:
        figure.add_annotation(
            text=comparison.compatibility.summary,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 13, "color": "#b45309"},
        )
        return figure

    minutes = [point.minute for point in comparison.trend_deltas]
    figure.add_trace(
        go.Scatter(
            x=minutes,
            y=[point.supply_temp_delta_c for point in comparison.trend_deltas],
            name="Δ притока",
            mode="lines+markers",
            line={"color": "#f97316", "width": 3},
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=minutes,
            y=[point.room_temp_delta_c for point in comparison.trend_deltas],
            name="Δ помещения",
            mode="lines+markers",
            line={"color": "#0891b2", "width": 3},
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Bar(
            x=minutes,
            y=[point.total_power_delta_kw for point in comparison.trend_deltas],
            name="Δ мощности, кВт",
            marker_color="#c2410c",
            opacity=0.25,
        ),
        secondary_y=True,
    )
    figure.add_trace(
        go.Scatter(
            x=minutes,
            y=[point.airflow_delta_m3_h for point in comparison.trend_deltas],
            name="Δ расхода, м³/ч",
            mode="lines",
            line={"color": "#22c55e", "width": 2, "dash": "dot"},
        ),
        secondary_y=True,
    )
    return figure


def _coerce_session(session_payload) -> SimulationSession:
    if session_payload is None:
        raise ValueError("Simulation session payload is required")
    return SimulationSession.model_validate(session_payload)


def _resolve_export_session(
    session_payload,
    result: SimulationResult,
) -> SimulationSession | None:
    session = _coerce_session(session_payload)
    if session.current_result.parameters.model_dump(mode="json") != result.parameters.model_dump(
        mode="json"
    ):
        return None
    if session.current_result.scenario_id != result.scenario_id:
        return None
    return session


def _session_is_running(session_payload) -> bool:
    return _coerce_session(session_payload).status == SimulationSessionStatus.RUNNING


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


def _build_session_summary_text(session: SimulationSession) -> str:
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


def _render_result(
    result: SimulationResult,
    session: SimulationSession,
    bindings_version: int,
    room_config: dict[str, object] | None = None,
    status_service: StatusService | None = None,
):
    status_service = status_service or StatusService()
    status_text, status_class = _status_pill(result.state.status)
    metric_map = status_service.build_metric_status_map(result)
    alarms = _build_alarm_items(result, status_service)

    state = result.state
    visualization = build_visualization_signal_map(
        result,
        bindings_version=bindings_version,
        room_context=room_config or {},
        status_service=status_service,
    )

    return (
        status_text,
        status_class,
        _build_metric_card_content(metric_map["supply_temp"]),
        _build_metric_card_content(metric_map["room_temp"]),
        _build_metric_card_content(metric_map["heating_power"]),
        _build_metric_card_content(metric_map["total_power"]),
        _build_metric_card_content(metric_map["airflow"]),
        _build_metric_card_content(metric_map["filter_pressure"]),
        alarms,
        visualization.model_dump(mode="json"),
        visualization.summary,
        _build_trend_figure(session, status_service),
    )


def _status_pill(status: OperationStatus) -> tuple[str, str]:
    return status_text(status), status_class_name(status)


def _build_metric_card_content(metric: DashboardMetricStatus) -> list:
    return [
        html.Strong(metric.value_text, className="metric-value"),
        html.Div(status_text(metric.status), className=status_class_name(metric.status)),
        html.P(metric.detail, className="metric-detail"),
    ]


def _build_alarm_items(
    result: SimulationResult,
    status_service: StatusService,
) -> list[html.Div]:
    if not result.alarms:
        return [
            html.Div(
                className="alarm-item level-info",
                children=[
                    html.Div("Норма", className="status-pill status-normal"),
                    html.Span("Активных тревог нет; блок подтверждает спокойный режим."),
                ],
            )
        ]

    items: list[html.Div] = []
    for alarm in result.alarms:
        alarm_status = status_service.alert_level_status(alarm.level)
        items.append(
            html.Div(
                className=f"alarm-item level-{alarm.level.value}",
                children=[
                    html.Div(status_text(alarm_status), className=status_class_name(alarm_status)),
                    html.Div(
                        children=[
                            html.Span(alarm.code, className="alarm-level"),
                            html.Span(alarm.message),
                        ],
                        className="alarm-copy",
                    ),
                ],
            )
        )
    return items


def _build_trend_figure(
    session: SimulationSession,
    status_service: StatusService,
) -> go.Figure:
    minutes = [point.minute for point in session.history.points]
    supply = [point.supply_temp_c for point in session.history.points]
    room = [point.room_temp_c for point in session.history.points]
    heating = [point.heating_power_kw for point in session.history.points]
    airflow = [point.airflow_m3_h for point in session.history.points]
    point_statuses = status_service.build_trend_statuses(
        session.current_result.parameters,
        session.history.points,
    )

    figure = make_subplots(specs=[[{"secondary_y": True}]])
    _apply_trend_status_bands(figure, minutes, point_statuses, session.step_minutes, status_service)
    figure.add_trace(
        go.Scatter(
            x=minutes,
            y=supply,
            name="Приток",
            mode="lines+markers",
            line={"color": "#f97316", "width": 3},
            marker={
                "size": 9,
                "color": [status_service.status_color(status) for status in point_statuses],
            },
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=minutes,
            y=room,
            name="Помещение",
            mode="lines+markers",
            line={"color": "#0891b2", "width": 3},
            marker={
                "size": 9,
                "color": [status_service.status_color(status) for status in point_statuses],
            },
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Bar(
            x=minutes,
            y=heating,
            name="Нагрев, кВт",
            marker_color="#c2410c",
            opacity=0.25,
        ),
        secondary_y=True,
    )
    figure.add_trace(
        go.Scatter(
            x=minutes,
            y=airflow,
            name="Расход, м³/ч",
            mode="lines",
            line={"color": "#22c55e", "width": 2, "dash": "dot"},
        ),
        secondary_y=True,
    )

    figure.update_layout(
        paper_bgcolor="#f6f2ea",
        plot_bgcolor="#ffffff",
        font={"family": "Inter, Segoe UI, sans-serif", "color": "#1f2933"},
        margin={"l": 40, "r": 30, "t": 10, "b": 40},
        legend={"orientation": "h", "y": 1.12},
    )
    figure.update_xaxes(title="Время, мин", gridcolor="#d8dee4")
    figure.update_yaxes(
        title="Температура, °C",
        secondary_y=False,
        gridcolor="#d8dee4",
    )
    figure.update_yaxes(title="Мощность / расход", secondary_y=True, showgrid=False)
    return figure


def _apply_trend_status_bands(
    figure: go.Figure,
    minutes: list[int],
    statuses: list[OperationStatus],
    step_minutes: int,
    status_service: StatusService,
) -> None:
    if not minutes:
        return

    half_step = max(step_minutes / 2.0, 0.5)
    for minute, status in zip(minutes, statuses, strict=True):
        figure.add_vrect(
            x0=minute - half_step,
            x1=minute + half_step,
            fillcolor=status_service.status_color(status),
            opacity=0.08,
            line_width=0,
            layer="below",
        )
