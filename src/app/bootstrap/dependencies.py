from fastapi import Request

from app.services.browser_capability_service import BrowserCapabilityService
from app.services.comparison_service import RunComparisonService
from app.services.demo_readiness_service import DemoReadinessService
from app.services.event_log_service import EventLogService
from app.services.export_service import ExportService
from app.services.project_baseline_service import ProjectBaselineService
from app.services.scenario_archive_service import ScenarioArchiveService
from app.services.scenario_preset_service import ScenarioPresetService
from app.services.simulation_service import SimulationService
from app.services.status_service import StatusService
from app.services.validation_service import ValidationService


def get_simulation_service(request: Request) -> SimulationService:
    return request.app.state.simulation_service


def get_status_service(request: Request) -> StatusService:
    return request.app.state.status_service


def get_browser_capability_service(request: Request) -> BrowserCapabilityService:
    return request.app.state.browser_capability_service


def get_comparison_service(request: Request) -> RunComparisonService:
    return request.app.state.comparison_service


def get_validation_service(request: Request) -> ValidationService:
    return request.app.state.validation_service


def get_demo_readiness_service(request: Request) -> DemoReadinessService:
    return request.app.state.demo_readiness_service


def get_project_baseline_service(request: Request) -> ProjectBaselineService:
    return request.app.state.project_baseline_service


def get_export_service(request: Request) -> ExportService:
    return request.app.state.export_service


def get_scenario_archive_service(request: Request) -> ScenarioArchiveService:
    return request.app.state.scenario_archive_service


def get_scenario_preset_service(request: Request) -> ScenarioPresetService:
    return request.app.state.scenario_preset_service


def get_event_log_service(request: Request) -> EventLogService:
    return request.app.state.event_log_service
