"""Compatibility shim for legacy dependency import path."""

from app.bootstrap.dependencies import (
    get_browser_capability_service,
    get_comparison_service,
    get_demo_readiness_service,
    get_event_log_service,
    get_export_service,
    get_project_baseline_service,
    get_scenario_archive_service,
    get_scenario_preset_service,
    get_simulation_service,
    get_status_service,
    get_validation_service,
)


__all__ = [
    "get_browser_capability_service",
    "get_comparison_service",
    "get_demo_readiness_service",
    "get_event_log_service",
    "get_export_service",
    "get_project_baseline_service",
    "get_scenario_archive_service",
    "get_scenario_preset_service",
    "get_simulation_service",
    "get_status_service",
    "get_validation_service",
]
