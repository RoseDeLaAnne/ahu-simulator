from pathlib import Path

from a2wsgi import WSGIMiddleware
from dash import Dash

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
    fastapi_app,
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
    assets_folder = Path(__file__).resolve().parent / "assets"
    dash_app = Dash(
        __name__,
        requests_pathname_prefix=f"{dashboard_path}/",
        assets_folder=str(assets_folder),
        assets_ignore=r".*(?:vendor|mjs).*",
        meta_tags=[
            {
                "name": "viewport",
                "content": "width=device-width, initial-scale=1, viewport-fit=cover",
            }
        ],
        title="AHU Simulator",
        serve_locally=True,
        suppress_callback_exceptions=True,
    )
    dash_app.index_string = (
        "<!DOCTYPE html>\n<html lang=\"ru\">\n<head>\n"
        "{%metas%}\n<title>{%title%}</title>\n{%favicon%}\n"
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">\n'
        "{%css%}\n"
        '<script type="importmap">\n'
        "{\n"
        '  "imports": {\n'
        '    "three": "./assets/_vendor/three/three.module.min.mjs",\n'
        '    "three/addons/": "./assets/_vendor/three/addons/"\n'
        "  }\n"
        "}\n"
        "</script>\n"
        "<script>\n"
        "(function(){\n"
        "  const SELECT_HOSTS = [\n"
        '    "#scenario-select", "#control-mode", "#scene3d-model-select",\n'
        '    "#scene3d-display-mode", "#scene3d-camera-preset", "#scene3d-scenario-select",\n'
        '    "#scene3d-room-select", "#scene3d-room-preset", "#scene3d-control-mode"\n'
        "  ];\n"
        "  const hostSelector = SELECT_HOSTS.join(',');\n"
        "  const selectSelector = SELECT_HOSTS.map(function(selector){ return selector + ' .Select'; }).join(',');\n"
        "  function resolveSelectRoot(node){\n"
        "    if (!node || typeof node.closest !== 'function') return null;\n"
        "    const root = node.closest('.Select');\n"
        "    if (!root) return null;\n"
        "    return root.closest(hostSelector) ? root : null;\n"
        "  }\n"
        "  function hardenSelect(root){\n"
        "    if (!root) return;\n"
        "    const input = root.querySelector('input');\n"
        "    if (!input) return;\n"
        "    input.readOnly = true;\n"
        "    input.setAttribute('inputmode', 'none');\n"
        "    input.setAttribute('autocomplete', 'off');\n"
        "    input.setAttribute('autocorrect', 'off');\n"
        "    input.setAttribute('spellcheck', 'false');\n"
        "    input.setAttribute('tabindex', '-1');\n"
        "  }\n"
        "  function hardenAll(){\n"
        "    document.querySelectorAll(selectSelector).forEach(hardenSelect);\n"
        "  }\n"
        "  function blurTarget(target){\n"
        "    const root = resolveSelectRoot(target);\n"
        "    if (!root) return;\n"
        "    hardenSelect(root);\n"
        "    const input = root.querySelector('input');\n"
        "    if (!input) return;\n"
        "    [0, 40, 120].forEach(function(delay){\n"
        "      window.setTimeout(function(){\n"
        "        hardenSelect(root);\n"
        "        if (document.activeElement === input) input.blur();\n"
        "      }, delay);\n"
        "    });\n"
        "  }\n"
        "  document.addEventListener('DOMContentLoaded', hardenAll, { once: true });\n"
        "  document.addEventListener('focusin', function(event){ blurTarget(event.target); });\n"
        "  document.addEventListener('touchstart', function(event){ blurTarget(event.target); }, { passive: true });\n"
        "  new MutationObserver(hardenAll).observe(document.documentElement, { childList: true, subtree: true });\n"
        "  window.setInterval(hardenAll, 500);\n"
        "})();\n"
        "</script>\n"
        '<script type="module" src="assets/viewer3d.mjs"></script>\n'
        "</head>\n<body>\n"
        "{%app_entry%}\n"
        "<footer>\n{%config%}\n{%scripts%}\n{%renderer%}\n</footer>\n"
        "</body>\n</html>"
    )
    dash_app.layout = build_dashboard_layout(
        service.list_scenarios(),
        default_scenario_id=default_scenario_id,
        browser_profile=browser_capability_service.build_profile(),
        validation_matrix=validation_service.build_matrix(),
        validation_agreement=validation_service.build_agreement(),
        validation_basis=validation_service.build_basis(),
        manual_check=validation_service.build_manual_check(
            service.get_state().parameters,
            service.get_state(),
        ),
        project_baseline=project_baseline_service.build_snapshot(),
        demo_readiness=demo_readiness_service.build_readiness(),
        demo_package=demo_readiness_service.build_package_snapshot(),
        export_snapshot=export_service.build_snapshot(),
        scenario_archive=scenario_archive_service.build_snapshot(),
        comparison_snapshot=comparison_service.build_snapshot(
            service.get_session().current_result,
            service.get_session(),
        ),
        event_log_snapshot=event_log_service.build_snapshot(),
        status_legend=status_service.build_status_legend(),
        current_result=service.get_state(),
        current_session=service.get_session(),
        dashboard_path=dashboard_path,
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
    fastapi_app.mount(dashboard_path, WSGIMiddleware(dash_app.server))
    return dash_app
