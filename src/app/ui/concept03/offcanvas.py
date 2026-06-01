from __future__ import annotations

from dash import html

from app.ui.concept03.components.icon import Icon
from app.ui.concept03.mobile_components import MOBILE_NAV_ITEMS
from app.ui.viewmodels.concept03_bottom import Concept03FooterNavView


DEFENSE_MENU_ITEMS: tuple[tuple[str, str], ...] = (
    ("Готовность к защите", "?theme=concept03&page=analytics&tab=readiness"),
    ("Чек-лист защиты", "?theme=concept03&page=library&tab=checklist"),
    ("Открыть журнал событий", "?theme=concept03&page=analytics&tab=events"),
)


def build_mobile_offcanvas(view: Concept03FooterNavView) -> html.Div:
    return html.Div(
        id="mobile-offcanvas",
        className="c03-mobile-offcanvas c03-mobile-only",
        **{"data-mobile-menu-state": "closed"},
        children=[
            html.Button(
                id="mobile-offcanvas-backdrop",
                type="button",
                className="c03-mobile-offcanvas__backdrop",
                title="Закрыть мобильное меню",
                **{
                    "aria-label": "Закрыть мобильное меню",
                    "data-mobile-menu-close": "true",
                },
            ),
            html.Aside(
                className="c03-mobile-offcanvas__panel",
                role="dialog",
                **{
                    "aria-modal": "true",
                    "aria-label": "Мобильное меню Concept03",
                },
                children=[
                    html.Div(
                        className="c03-mobile-offcanvas__topline",
                        children=[
                            html.Strong("Меню"),
                            html.Button(
                                Icon("x", 20, class_name="c03-mobile-offcanvas__close-icon"),
                                id="mobile-menu-close",
                                type="button",
                                className="c03-mobile-offcanvas__close",
                                title="Закрыть",
                                **{
                                    "aria-label": "Закрыть мобильное меню",
                                    "data-mobile-menu-close": "true",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        className="c03-mobile-offcanvas__brand",
                        children=[
                            html.Span("КАСКАД ГРУП"),
                            html.Strong("ООО «НПО «Каскад-ГРУП»"),
                            html.P("ВКР: Моделирование работы ПВУ"),
                            html.Code(view.version_text),
                        ],
                    ),
                    _build_menu_section("Разделы", _navigation_links(view)),
                    _build_menu_section(
                        "Защита",
                        [
                            html.A(
                                label,
                                href=href,
                                className="c03-mobile-offcanvas__link",
                            )
                            for label, href in DEFENSE_MENU_ITEMS
                        ],
                    ),
                    html.Div(
                        className="c03-mobile-offcanvas__secured",
                        children=[
                            Icon("shield-check", 18),
                            html.Span("Защищенный контур: активен"),
                        ],
                    ),
                ],
            ),
        ],
    )


def _navigation_links(view: Concept03FooterNavView) -> list[html.A]:
    item_by_page = {item.page_id: item for item in view.items}
    links: list[html.A] = []
    for page_id, _mobile_id, label, _icon in MOBILE_NAV_ITEMS:
        item = item_by_page.get(page_id)
        if item is None:
            continue
        links.append(
            html.A(
                label,
                href=item.href,
                className="c03-mobile-offcanvas__link"
                + (" c03-mobile-offcanvas__link--active" if item.is_active else ""),
            )
        )
    library_item = item_by_page.get("library")
    if library_item is not None:
        links.append(
            html.A(
                "Библиотека",
                href=library_item.href,
                className="c03-mobile-offcanvas__link"
                + (" c03-mobile-offcanvas__link--active" if library_item.is_active else ""),
            )
        )
    return links


def _build_menu_section(title: str, links: list[html.A]) -> html.Section:
    return html.Section(
        className="c03-mobile-offcanvas__section",
        children=[
            html.Span(title, className="c03-mobile-offcanvas__section-title"),
            *links,
        ],
    )
