from pathlib import Path

from app.services.browser_capability_service import BrowserCapabilityService
from app.ui.viewmodels.browser_diagnostics import (
    build_browser_diagnostics_view,
    build_browser_profile_view,
    build_demo_browser_readiness_view,
)


def _build_profile():
    project_root = Path(__file__).resolve().parents[2]
    return BrowserCapabilityService(project_root).build_profile()


def test_browser_diagnostics_view_defaults_to_pending_state() -> None:
    view = build_browser_diagnostics_view(None)

    assert view.status_text == "Проверка"
    assert view.status_class_name == "status-pill status-warning"
    assert "2D SVG" in view.note


def test_browser_diagnostics_view_marks_missing_webgl_as_2d_only() -> None:
    view = build_browser_diagnostics_view(
        {
            "browser_label": "Firefox 145",
            "platform": "Windows",
            "secure_context": True,
            "webgl_supported": False,
            "webgl2_supported": False,
        }
    )

    assert view.status_text == "Только 2D"
    assert view.status_class_name == "status-pill status-alarm"
    assert any("WebGL: нет / WebGL2: нет" in item for item in view.items)


def test_browser_diagnostics_view_marks_full_support_as_ready() -> None:
    view = build_browser_diagnostics_view(
        {
            "browser_label": "Chrome 135",
            "platform": "Windows",
            "online": True,
            "secure_context": True,
            "webgl_supported": True,
            "webgl2_supported": True,
            "hardware_concurrency": 8,
            "device_memory_gb": 8,
            "renderer": "ANGLE (Intel UHD Graphics)",
            "max_texture_size": 16384,
            "max_viewport_width": 16384,
            "max_viewport_height": 16384,
            "viewport_width": 1440,
            "viewport_height": 900,
            "screen_width": 1920,
            "screen_height": 1080,
            "device_pixel_ratio": 1.0,
            "diagnostics_timestamp": "2026-04-04T17:30:00.000Z",
        }
    )

    assert view.status_text == "3D возможно"
    assert view.status_class_name == "status-pill status-normal"
    assert any("Рендерер: ANGLE (Intel UHD Graphics)" in item for item in view.items)


def test_browser_profile_view_formats_verified_profile() -> None:
    profile = _build_profile()

    view = build_browser_profile_view(profile)

    assert view.status_text == "Профиль подтверждён"
    assert view.status_class_name == "status-pill status-normal"
    assert "Chromium 146" in view.summary_text
    assert any("Рекомендуемый размер окна: 1200x680+" in item for item in view.items)


def test_demo_browser_readiness_view_accepts_2d_only_demo_if_viewport_is_good() -> None:
    view = build_demo_browser_readiness_view(
        {
            "browser_label": "Firefox 145",
            "platform": "Windows",
            "online": False,
            "secure_context": True,
            "webgl_supported": False,
            "webgl2_supported": False,
            "viewport_width": 1366,
            "viewport_height": 768,
            "screen_width": 1920,
            "screen_height": 1080,
        }
    )

    assert view.status_text == "Показ допустим"
    assert view.status_class_name == "status-pill status-normal"
    assert "2D" in view.summary_text
    assert any("Сеть: офлайн" in item for item in view.items)


def test_demo_browser_readiness_view_warns_on_small_viewport() -> None:
    profile = _build_profile()
    view = build_demo_browser_readiness_view(
        {
            "browser_label": "Chrome 135",
            "platform": "Windows",
            "online": True,
            "secure_context": True,
            "webgl_supported": True,
            "webgl2_supported": True,
            "viewport_width": 1024,
            "viewport_height": 640,
            "screen_width": 1366,
            "screen_height": 768,
        },
        profile,
    )

    assert view.status_text == "Нужно больше окно"
    assert view.status_class_name == "status-pill status-warning"
    assert "1200x680" in view.summary_text
    assert "1200x680" in view.note


def test_demo_browser_readiness_view_mentions_profile_match() -> None:
    service = BrowserCapabilityService(Path(__file__).resolve().parents[2])
    profile = service.build_profile()
    payload = profile.verified_environment.model_copy(
        update={
            "viewport_width": 1280,
            "viewport_height": 720,
        }
    ).model_dump(mode="json")
    comparison = service.build_comparison(payload)

    view = build_demo_browser_readiness_view(payload, profile, comparison)

    assert comparison is not None
    assert view.status_text == "Показ допустим"
    assert "соответствует" in view.summary_text
