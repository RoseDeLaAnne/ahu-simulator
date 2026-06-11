from __future__ import annotations

from collections.abc import Iterable

from dash import html

from app.ui.concept03.bottom_strip import build_bottom_strip
from app.ui.concept03.central_canvas import build_central_canvas
from app.ui.concept03.components.icon import Icon
from app.ui.concept03.footer_nav import build_footer_nav
from app.ui.concept03.header import build_header
from app.ui.concept03.left_rail import build_left_rail
from app.ui.concept03.page_router import DEFAULT_PAGE, PAGE_IDS
from app.ui.concept03.pages import (
    build_analytics_content,
    build_control_content,
    build_equipment_content,
    build_library_content,
    build_settings_content,
)
from app.ui.concept03.regions import Region
from app.ui.concept03.right_rail import build_right_rail
from app.ui.viewmodels.concept03_bottom import (
    Concept03BottomView,
    Concept03FooterNavView,
)
from app.ui.viewmodels.concept03_config import Concept03ConfigView
from app.ui.viewmodels.concept03_central import Concept03CentralView
from app.ui.viewmodels.concept03_header import Concept03HeaderView
from app.ui.viewmodels.concept03_health import Concept03HealthView
from app.ui.viewmodels.concept03_kpi import Concept03KpiView
from app.ui.viewmodels.concept03_modes import Concept03ModesView
from app.ui.viewmodels.concept03_scenarios import Concept03ScenariosView


REGION_PLACEHOLDERS = {
    Region.LEFT_RAIL: ("СЦЕНАРИИ И РЕЖИМЫ", "coming soon"),
    Region.CENTRAL_CANVAS: ("ЦЕНТРАЛЬНЫЙ CANVAS", "coming soon"),
    Region.RIGHT_RAIL: ("СТАТУС И KPI", "coming soon"),
    Region.BOTTOM_STRIP: ("АРТЕФАКТЫ ЗАЩИТЫ", "coming soon"),
}


def build_concept03_shell(
    *,
    active_page: str | None = None,
    root_id: str = "concept03-shell",
    header_view: Concept03HeaderView | None = None,
    scenarios_view: Concept03ScenariosView | None = None,
    modes_view: Concept03ModesView | None = None,
    config_view: Concept03ConfigView | None = None,
    central_view: Concept03CentralView | None = None,
    kpi_view: Concept03KpiView | None = None,
    health_view: Concept03HealthView | None = None,
    bottom_view: Concept03BottomView | None = None,
    footer_nav_view: Concept03FooterNavView | None = None,
) -> html.Div:
    page = active_page if active_page in PAGE_IDS else DEFAULT_PAGE.value
    header = (
        build_header(header_view)
        if header_view is not None
        else _build_region_placeholder(Region.APP_HEADER, "HEADER", "coming soon")
    )
    left_rail = (
        build_left_rail(
            scenarios=scenarios_view,
            modes=modes_view,
            config=config_view,
        )
        if scenarios_view is not None
        and modes_view is not None
        and config_view is not None
        else _build_region(Region.LEFT_RAIL)
    )
    right_rail = (
        build_right_rail(kpis=kpi_view, health=health_view)
        if kpi_view is not None and health_view is not None
        else _build_region(Region.RIGHT_RAIL)
    )
    central_canvas = (
        build_central_canvas(central_view)
        if central_view is not None
        else _build_region(Region.CENTRAL_CANVAS)
    )
    # Контейнер страниц: дашборд (central_canvas) + 5 дополнительных страниц.
    # Занимает grid-area: center. Внутри — alarm strip + 6 панелей, видимых по data-active-page.
    page_content = html.Div(
        id="concept03-page-content",
        className="c03-page-content",
        tabIndex=0,
        children=[
            html.Div(
                id="concept03-alarm-strip",
                className="c03-alarm-strip",
                children=[
                    Icon("shield-check", 14, class_name="c03-alarm-strip__icon"),
                    html.Span(
                        "Активные тревоги: —",
                        id="concept03-alarm-strip-text",
                        className="c03-alarm-strip__text",
                    ),
                ],
            ),
            html.Div(
                className="c03-page-panel c03-page-panel--dashboard",
                children=[central_canvas],
            ),
            html.Div(
                className="c03-page-panel c03-page-panel--equipment",
                children=build_equipment_content(),
            ),
            html.Div(
                className="c03-page-panel c03-page-panel--control",
                children=build_control_content(),
            ),
            html.Div(
                className="c03-page-panel c03-page-panel--analytics",
                children=build_analytics_content(),
            ),
            html.Div(
                className="c03-page-panel c03-page-panel--library",
                children=build_library_content(),
            ),
            html.Div(
                className="c03-page-panel c03-page-panel--settings",
                children=build_settings_content(),
            ),
        ],
    )
    bottom_strip = (
        build_bottom_strip(
            bottom_view,
            include_defense=True,
            scenarios_view=scenarios_view,
        )
        if bottom_view is not None
        else _build_region(Region.BOTTOM_STRIP)
    )
    footer = (
        build_footer_nav(footer_nav_view or bottom_view.footer_nav)
        if footer_nav_view is not None or bottom_view is not None
        else _build_footer_nav(page)
    )
    return html.Div(
        id=root_id,
        className="c03-shell",
        **{"data-active-page": page},
        children=[
            header,
            left_rail,
            page_content,
            right_rail,
            bottom_strip,
            footer,
        ],
    )


def _build_region(region: Region) -> html.Section:
    title, sub = REGION_PLACEHOLDERS[region]
    return _build_region_placeholder(region, title, sub)


def _build_region_placeholder(
    region: Region,
    title: str,
    sub: str,
) -> html.Section:
    tag = html.Header if region == Region.APP_HEADER else html.Section
    return tag(
        id=region.value,
        className=f"c03-region c03-region--{region.value}",
        tabIndex=0,
        children=[
            html.Span(title, className="c03-region__eyebrow"),
            html.Strong(sub, className="c03-region__placeholder"),
        ],
    )


def _build_footer_nav(active_page: str) -> html.Footer:
    labels = {
        "dashboard": "Дашборд",
        "equipment": "Оборудование",
        "control": "Управление",
        "analytics": "Аналитика",
        "library": "Библиотека",
        "settings": "Настройки",
    }
    return html.Footer(
        id=Region.APP_FOOTER_NAV.value,
        className="c03-footer-nav",
        tabIndex=0,
        children=[
            html.Nav(
                className="c03-footer-nav__items",
                children=list(_build_footer_links(active_page, labels)),
            ),
            html.Div(
                className="c03-secured-loop-pill",
                children=["Защищенный контур"],
            ),
        ],
    )


def _build_footer_links(
    active_page: str,
    labels: dict[str, str],
) -> Iterable[html.A]:
    for page_id in PAGE_IDS:
        is_active = page_id == active_page
        yield html.A(
            labels[page_id],
            id=f"footer-nav-{page_id}",
            href=f"?theme=concept03&page={page_id}",
            className="c03-footer-nav__link"
            + (" c03-footer-nav__link--active" if is_active else ""),
        )
