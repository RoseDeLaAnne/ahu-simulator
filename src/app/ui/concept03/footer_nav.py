from __future__ import annotations

from dash import html

from app.ui.concept03.defense_variant.footer import build_academic_footer
from app.ui.concept03.mobile_layout import build_mobile_shell_overlays
from app.ui.concept03.regions import Region
from app.ui.viewmodels.concept03_bottom import (
    Concept03FooterNavView,
    Concept03SecuredLoopView,
    footer_nav_class_name,
)


def build_footer_nav(view: Concept03FooterNavView) -> html.Footer:
    return html.Footer(
        id=Region.APP_FOOTER_NAV.value,
        className="c03-footer-nav",
        tabIndex=0,
        children=[
            html.Nav(
                className="c03-footer-nav__items c03-operator-only",
                **{"aria-label": "Навигация Concept03"},
                children=[
                    html.A(
                        id=f"footer-nav-{item.page_id}",
                        href=item.href,
                        className=footer_nav_class_name(
                            item.page_id,
                            item.page_id if item.is_active else "",
                        ),
                        children=[
                            html.Span(
                                className="c03-footer-nav__icon",
                                **{"data-icon": item.icon},
                            ),
                            html.Span(item.label, className="c03-footer-nav__label"),
                        ],
                    )
                    for item in view.items
                ],
            ),
            html.Div(
                className="c03-footer-nav__status c03-operator-only",
                children=[
                    html.Span(view.version_text, className="c03-footer-nav__version"),
                    build_secured_loop_pill(view.secured_loop),
                ],
            ),
            build_academic_footer(),
            *build_mobile_shell_overlays(view),
        ],
    )


def build_secured_loop_pill(view: Concept03SecuredLoopView) -> html.Div:
    return html.Div(
        className=f"c03-secured-loop-pill c03-secured-loop-pill--{view.state}",
        title=(
            f"{view.detail} Локальные сервисы: {view.local_services_text}; "
            f"внешние зависимости: {view.external_dependencies_text}."
        ),
        **{"data-secured-state": view.state},
        children=[
            html.Span(
                className="c03-secured-loop-pill__icon",
                **{"data-icon": "shield-check"},
            ),
            html.Span(view.label),
        ],
    )
