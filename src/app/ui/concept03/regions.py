from __future__ import annotations

from enum import StrEnum


class Region(StrEnum):
    APP_HEADER = "app-header"
    LEFT_RAIL = "left-rail"
    CENTRAL_CANVAS = "central-canvas"
    RIGHT_RAIL = "right-rail"
    BOTTOM_STRIP = "bottom-strip"
    APP_FOOTER_NAV = "app-footer-nav"


REGION_IDS: tuple[str, ...] = tuple(region.value for region in Region)
