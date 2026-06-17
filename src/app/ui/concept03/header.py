from __future__ import annotations

from dash import dcc, html

from app.ui.concept03.components.icon import Icon
from app.ui.concept03.defense_variant.header_toolbar import (
    DEFENSE_TITLE,
    build_header_action_toolbar,
    build_header_icon_links,
    build_header_meta_pills,
)
from app.ui.concept03.mobile_components import (
    build_mobile_menu_button,
    build_mobile_status_badge,
)
from app.ui.viewmodels.concept03_header import Concept03HeaderView


def build_header(view: Concept03HeaderView) -> html.Header:
    return html.Header(
        id="app-header",
        className="c03-header",
        tabIndex=0,
        children=[
            dcc.Link(
                href="?page=settings",
                refresh=False,
                className="c03-brand",
                children=[
                    Icon("building-2", 22, class_name="c03-brand__mark", title="Бренд"),
                    html.Span(
                        className="c03-brand__copy",
                        children=[
                            html.Strong(view.brand_short),
                            html.Span(view.brand_full),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="c03-installation-title c03-operator-only",
                children=[
                    html.H1(view.title_uppercase),
                    html.P(view.subtitle),
                ],
            ),
            html.Div(
                className="c03-installation-title c03-installation-title--defense c03-defense-only",
                children=[
                    html.H1(DEFENSE_TITLE),
                    html.P(view.subtitle),
                ],
            ),
            html.Div(className="c03-header__spacer"),
            build_header_action_toolbar(),
            html.Div(
                className="c03-header__pills c03-operator-only",
                children=[_build_status_pill(pill) for pill in view.status_pills],
            ),
            build_header_meta_pills(),
            build_header_icon_links(),
            build_mobile_status_badge(),
            build_mobile_menu_button(),
            html.Div(
                className="c03-datetime",
                children=[
                    html.Span(view.date_text, id="concept03-clock-date"),
                    html.Strong(view.time_text, id="concept03-clock-time"),
                ],
            ),
            dcc.Link(
                view.user_initials,
                href="?page=settings",
                refresh=False,
                className="c03-user-avatar",
                title="Профиль оператора",
            ),
        ],
    )


def _build_status_pill(pill) -> html.Div:
    return html.Div(
        id=pill.pill_id,
        className=f"c03-status-pill c03-status-pill--{pill.state}",
        **{"aria-label": f"{pill.title}: {pill.sub}"},
        children=[
            Icon(pill.icon, 18, class_name="c03-status-pill__icon"),
            html.Span(
                className="c03-status-pill__copy",
                children=[
                    html.Span(pill.title, className="c03-status-pill__title"),
                    html.Strong(
                        pill.sub,
                        id=f"{pill.pill_id}-sub",
                        className="c03-status-pill__sub",
                    ),
                ],
            ),
        ],
    )
