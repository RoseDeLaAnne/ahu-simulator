from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import (
    archive,
    comparison,
    events,
    exports,
    health,
    project,
    readiness,
    scenarios,
    simulation,
    state,
    validation,
    visualization,
)
from app.infrastructure.runtime_paths import RuntimePathResolver
from app.infrastructure.settings import ApplicationSettings, get_project_root
from app.services.browser_capability_service import BrowserCapabilityService
from app.services.comparison_service import RunComparisonService
from app.services.demo_readiness_service import DemoReadinessService
from app.services.event_log_service import EventLogService
from app.services.export_service import ExportService
from app.services.project_baseline_service import ProjectBaselineService
from app.services.scenario_archive_service import ScenarioArchiveService
from app.services.scenario_preset_service import ScenarioPresetService
from app.services.simulation_service import SimulationService
from app.services.simulation_session_store import SimulationSessionStore
from app.services.status_service import StatusService
from app.services.trend_service import TrendService
from app.services.validation_service import ValidationService
from app.ui.dashboard import mount_dashboard


@dataclass(frozen=True)
class ApplicationServices:
    project_root: Path
    simulation_service: SimulationService
    browser_capability_service: BrowserCapabilityService
    validation_service: ValidationService
    demo_readiness_service: DemoReadinessService
    project_baseline_service: ProjectBaselineService
    export_service: ExportService
    scenario_archive_service: ScenarioArchiveService
    scenario_preset_service: ScenarioPresetService
    comparison_service: RunComparisonService
    event_log_service: EventLogService
    status_service: StatusService


def build_application_services(settings: ApplicationSettings) -> ApplicationServices:
    project_root = get_project_root()
    runtime_paths = RuntimePathResolver(project_root=project_root)
    scenario_path = project_root / "data" / "scenarios" / "presets.json"

    status_service = StatusService(settings)
    scenario_preset_service = ScenarioPresetService(
        system_preset_path=scenario_path,
        project_root=project_root,
        path_resolver=runtime_paths,
    )
    simulation_session_store = SimulationSessionStore(
        project_root=project_root,
        path_resolver=runtime_paths,
    )
    simulation_service = SimulationService(
        scenarios=scenario_preset_service.list_scenarios(),
        trend_service=TrendService(),
        default_scenario_id=settings.default_scenario_id,
        status_service=status_service,
        session_store=simulation_session_store,
        scenario_preset_service=scenario_preset_service,
    )
    validation_service = ValidationService(
        simulation_service=simulation_service,
        reference_points_path=project_root / "data" / "validation" / "reference_points.json",
        reference_basis_path=project_root / "data" / "validation" / "reference_basis.json",
        validation_agreement_path=project_root
        / "data"
        / "validation"
        / "validation_agreement.json",
    )
    demo_readiness_service = DemoReadinessService(
        project_root=project_root,
        dashboard_path=settings.dashboard_path,
        path_resolver=runtime_paths,
    )
    browser_capability_service = BrowserCapabilityService(project_root=project_root)
    project_baseline_service = ProjectBaselineService(project_root=project_root)
    export_service = ExportService(
        project_root=project_root,
        status_service=status_service,
        path_resolver=runtime_paths,
    )
    scenario_archive_service = ScenarioArchiveService(
        project_root=project_root,
        path_resolver=runtime_paths,
    )
    comparison_service = RunComparisonService(
        project_root=project_root,
        scenario_archive_service=scenario_archive_service,
        status_service=status_service,
        path_resolver=runtime_paths,
    )
    event_log_service = EventLogService(
        project_root=project_root,
        path_resolver=runtime_paths,
    )

    return ApplicationServices(
        project_root=project_root,
        simulation_service=simulation_service,
        browser_capability_service=browser_capability_service,
        validation_service=validation_service,
        demo_readiness_service=demo_readiness_service,
        project_baseline_service=project_baseline_service,
        export_service=export_service,
        scenario_archive_service=scenario_archive_service,
        scenario_preset_service=scenario_preset_service,
        comparison_service=comparison_service,
        event_log_service=event_log_service,
        status_service=status_service,
    )


def attach_services_to_app(app: FastAPI, services: ApplicationServices) -> None:
    app.state.simulation_service = services.simulation_service
    app.state.browser_capability_service = services.browser_capability_service
    app.state.validation_service = services.validation_service
    app.state.demo_readiness_service = services.demo_readiness_service
    app.state.project_baseline_service = services.project_baseline_service
    app.state.export_service = services.export_service
    app.state.scenario_archive_service = services.scenario_archive_service
    app.state.scenario_preset_service = services.scenario_preset_service
    app.state.comparison_service = services.comparison_service
    app.state.event_log_service = services.event_log_service
    app.state.status_service = services.status_service


def mount_runtime_static_assets(app: FastAPI, project_root: Path) -> None:
    app.mount(
        "/models",
        StaticFiles(directory=str(project_root / "models")),
        name="models",
    )
    app.mount(
        "/images-of-models",
        StaticFiles(directory=str(project_root / "images-of-models")),
        name="images-of-models",
    )


def include_api_routers(app: FastAPI) -> None:
    app.include_router(archive.router)
    app.include_router(comparison.router)
    app.include_router(events.router)
    app.include_router(exports.router)
    app.include_router(health.router)
    app.include_router(project.router)
    app.include_router(readiness.router)
    app.include_router(simulation.router)
    app.include_router(scenarios.router)
    app.include_router(state.router)
    app.include_router(validation.router)
    app.include_router(visualization.router)


def register_root_redirect(app: FastAPI, dashboard_path: str) -> None:
    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url=dashboard_path)


def mount_dashboard_ui(
    app: FastAPI,
    services: ApplicationServices,
    dashboard_path: str,
    default_scenario_id: str,
) -> None:
    mount_dashboard(
        app,
        services.simulation_service,
        services.browser_capability_service,
        services.validation_service,
        services.demo_readiness_service,
        services.project_baseline_service,
        services.export_service,
        services.scenario_archive_service,
        services.comparison_service,
        services.event_log_service,
        services.status_service,
        dashboard_path,
        default_scenario_id,
    )
