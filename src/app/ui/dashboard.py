from __future__ import annotations

from pathlib import Path

from a2wsgi import WSGIMiddleware
from dash import Dash
from fastapi import FastAPI

from app.services.browser_capability_service import BrowserCapabilityService
from app.services.comparison_service import RunComparisonService
from app.services.demo_readiness_service import DemoReadinessService
from app.services.event_log_service import EventLogService
from app.services.export_service import ExportService
from app.services.project_baseline_service import ProjectBaselineService
from app.services.scenario_archive_service import ScenarioArchiveService
from app.services.simulation_service import SimulationService
from app.services.status_service import StatusService
from app.services.validation_service import ValidationService
from app.ui.callbacks import register_callbacks
from app.ui.layout import build_dashboard_layout


def mount_dashboard(
    app: FastAPI,
    service: SimulationService,
    browser_capability_service: BrowserCapabilityService,
    validation_service: ValidationService,
    demo_readiness_service: DemoReadinessService,
    project_baseline_service: ProjectBaselineService,
    export_service: ExportService,
    scenario_archive_service: ScenarioArchiveService,
    comparison_service: RunComparisonService,
    event_log_service: EventLogService,
    status_service: StatusService,
    dashboard_path: str,
    default_scenario_id: str,
) -> Dash:
    dashboard_prefix = _normalize_dashboard_path(dashboard_path)
    assets_folder = Path(__file__).resolve().parent / "assets"
    dash_app = Dash(
        __name__,
        server=True,
        assets_folder=str(assets_folder),
        assets_path_ignore=[r"^_vendor$"],
        requests_pathname_prefix=f"{dashboard_prefix}/",
        routes_pathname_prefix="/",
        suppress_callback_exceptions=True,
        title="AHU Simulator",
        update_title=None,
    )
    dash_app.index_string = _build_index_string(dashboard_prefix)

    current_result = service.get_state()
    current_session = service.get_session()
    dash_app.layout = build_dashboard_layout(
        scenarios=service.list_scenarios(),
        default_scenario_id=default_scenario_id,
        browser_profile=browser_capability_service.build_profile(),
        validation_matrix=validation_service.build_matrix(),
        validation_agreement=validation_service.build_agreement(),
        validation_basis=validation_service.build_basis(),
        manual_check=validation_service.build_manual_check(
            current_result.parameters,
            current_result,
        ),
        project_baseline=project_baseline_service.build_snapshot(),
        demo_readiness=demo_readiness_service.build_readiness(),
        demo_package=demo_readiness_service.build_package_snapshot(),
        export_snapshot=export_service.build_snapshot(),
        scenario_archive=scenario_archive_service.build_snapshot(),
        comparison_snapshot=comparison_service.build_snapshot(
            current_result,
            current_session,
        ),
        event_log_snapshot=event_log_service.build_snapshot(),
        status_legend=status_service.build_status_legend(),
        current_result=current_result,
        current_session=current_session,
        dashboard_path=dashboard_prefix,
    )
    register_callbacks(
        dash_app,
        service,
        browser_capability_service,
        validation_service,
        demo_readiness_service,
        export_service,
        scenario_archive_service,
        comparison_service,
        event_log_service,
        status_service,
    )
    app.mount(dashboard_prefix, WSGIMiddleware(dash_app.server))
    return dash_app


def _normalize_dashboard_path(dashboard_path: str) -> str:
    normalized = "/" + dashboard_path.strip("/")
    return normalized if normalized != "/" else "/dashboard"


def _build_index_string(dashboard_prefix: str) -> str:
    asset_prefix = dashboard_prefix.rstrip("/")
    return """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        <script type="importmap">
        {
            "imports": {
                "three": "__ASSET_PREFIX__/assets/_vendor/three/three.module.min.mjs",
                "three/addons/": "__ASSET_PREFIX__/assets/_vendor/three/addons/"
            }
        }
        </script>
        {%css%}
    </head>
    <body class="theme-concept03">
        <script>
        (function applyConcept03Theme() {
            var params = new URLSearchParams(window.location.search || "");
            var theme = params.get("theme") || "concept03";
            var defense = params.get("defense");
            var concept03 = theme === "concept03";
            var defenseActive = concept03 && ["1", "true", "yes", "on"].indexOf(String(defense).toLowerCase()) !== -1;
            document.body.classList.toggle("theme-legacy", !concept03);
            document.body.classList.toggle("theme-concept03", concept03);
            document.body.classList.toggle("c03-operator", concept03 && !defenseActive);
            document.body.classList.toggle("c03-defense", defenseActive);
        })();
        </script>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
""".replace("__ASSET_PREFIX__", asset_prefix)
