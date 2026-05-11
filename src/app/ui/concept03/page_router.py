from __future__ import annotations

from enum import StrEnum
from urllib.parse import parse_qs


class DashboardPage(StrEnum):
    DASHBOARD = "dashboard"
    EQUIPMENT = "equipment"
    CONTROL = "control"
    ANALYTICS = "analytics"
    LIBRARY = "library"
    SETTINGS = "settings"


DEFAULT_PAGE = DashboardPage.DASHBOARD
PAGE_IDS: tuple[str, ...] = tuple(page.value for page in DashboardPage)


def select_page(search: str | None) -> str:
    if not search:
        return DEFAULT_PAGE.value

    parsed_query = parse_qs(search.lstrip("?"), keep_blank_values=False)
    page_values = parsed_query.get("page")
    if not page_values:
        return DEFAULT_PAGE.value

    page_id = page_values[0].strip().lower()
    if page_id in PAGE_IDS:
        return page_id
    return DEFAULT_PAGE.value
