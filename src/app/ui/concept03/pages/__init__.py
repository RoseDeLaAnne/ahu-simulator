from __future__ import annotations

from .equipment_page import build_content as build_equipment_content
from .control_page import build_content as build_control_content
from .analytics_page import build_content as build_analytics_content
from .library_page import build_content as build_library_content
from .settings_page import build_content as build_settings_content

__all__ = [
    "build_equipment_content",
    "build_control_content",
    "build_analytics_content",
    "build_library_content",
    "build_settings_content",
]
