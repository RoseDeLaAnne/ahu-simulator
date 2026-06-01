from __future__ import annotations

from dash import html

from app.ui.concept03.components.icon import Icon
from app.ui.viewmodels.concept03_bottom import Concept03FooterNavView


MOBILE_NAV_ITEMS: tuple[tuple[str, str, str, str], ...] = (
    ("dashboard", "mobile-nav-home", "Главная", "home"),
    ("equipment", "mobile-nav-model", "Модель", "boxes"),
    ("control", "mobile-nav-scenarios", "Сценарии", "layers"),
    ("analytics", "mobile-nav-analytics", "Аналитика", "bar-chart-3"),
    ("settings", "mobile-nav-settings", "Настройки", "settings"),
)


def build_mobile_status_badge() -> html.Div:
    return html.Div(
        className="c03-mobile-status-badge c03-mobile-only",
        title="Готовность к защите",
        children=[
            Icon("shield-check", 20, class_name="c03-mobile-status-badge__icon"),
            html.Span("Готов к защите"),
        ],
    )


def build_mobile_menu_button() -> html.Button:
    return html.Button(
        Icon("menu", 22, class_name="c03-mobile-menu-button__icon"),
        id="mobile-menu-open",
        type="button",
        className="c03-mobile-menu-button c03-mobile-only",
        title="Открыть мобильное меню",
        **{
            "aria-label": "Открыть мобильное меню",
            "aria-controls": "mobile-offcanvas",
            "aria-expanded": "false",
            "data-mobile-menu-open": "true",
        },
    )


def build_mobile_bottom_nav(view: Concept03FooterNavView) -> html.Nav:
    item_by_page = {item.page_id: item for item in view.items}
    return html.Nav(
        id="mobile-bottom-nav",
        className="c03-mobile-bottom-nav c03-mobile-only",
        **{"aria-label": "Мобильная навигация Concept03"},
        children=[
            html.A(
                id=mobile_id,
                href=item_by_page[page_id].href,
                className=mobile_nav_class_name(
                    page_id,
                    _active_page_from_footer(view),
                ),
                children=[
                    html.Span(
                        className="c03-mobile-bottom-nav__icon",
                        **{"data-icon": icon},
                    ),
                    html.Span(label, className="c03-mobile-bottom-nav__label"),
                ],
            )
            for page_id, mobile_id, label, icon in MOBILE_NAV_ITEMS
            if page_id in item_by_page
        ],
    )


def mobile_nav_class_name(page_id: str, active_page: str) -> str:
    class_name = "c03-mobile-bottom-nav__link"
    if page_id == active_page:
        class_name += " c03-mobile-bottom-nav__link--active"
    return class_name


def _active_page_from_footer(view: Concept03FooterNavView) -> str:
    for item in view.items:
        if item.is_active:
            return item.page_id
    return "dashboard"
