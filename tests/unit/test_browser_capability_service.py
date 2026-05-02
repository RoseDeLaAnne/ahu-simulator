from pathlib import Path

from app.services.browser_capability_service import BrowserCapabilityService
from app.simulation.state import OperationStatus


def _build_service() -> BrowserCapabilityService:
    project_root = Path(__file__).resolve().parents[2]
    return BrowserCapabilityService(project_root)


def test_browser_capability_service_loads_verified_profile() -> None:
    profile = _build_service().build_profile()

    assert profile.profile_id == "phase7-webgl-demo-profile-2026-04-04"
    assert profile.overall_status == OperationStatus.NORMAL
    assert profile.passed_requirements == profile.total_requirements == 8
    assert profile.verified_environment.webgl2_supported is True


def test_browser_capability_service_flags_snapshot_outside_profile() -> None:
    comparison = _build_service().build_comparison(
        {
            "browser_label": "Firefox 145",
            "platform": "Windows",
            "secure_context": True,
            "webgl_supported": False,
            "webgl2_supported": False,
            "hardware_concurrency": 8,
            "device_memory_gb": 8,
            "screen_width": 1920,
            "screen_height": 1080,
            "max_texture_size": 16384,
        }
    )

    assert comparison is not None
    assert comparison.overall_status == OperationStatus.ALARM
    assert comparison.passed_requirements < comparison.total_requirements
    assert any(
        evaluation.requirement_id == "webgl" and not evaluation.passed
        for evaluation in comparison.evaluations
    )
