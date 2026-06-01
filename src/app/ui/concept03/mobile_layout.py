from __future__ import annotations

from dash import html

from app.ui.concept03.mobile_components import build_mobile_bottom_nav
from app.ui.concept03.offcanvas import build_mobile_offcanvas
from app.ui.viewmodels.concept03_bottom import Concept03FooterNavView


def build_mobile_shell_overlays(view: Concept03FooterNavView) -> list[html.Component]:
    return [
        build_mobile_bottom_nav(view),
        build_mobile_offcanvas(view),
    ]
