from __future__ import annotations

from dash import html


def Icon(
    name: str,
    size: int = 18,
    *,
    class_name: str | None = None,
    title: str | None = None,
) -> html.Span:
    accessibility_props = (
        {"role": "img", "aria-label": title}
        if title
        else {"aria-hidden": "true"}
    )
    return html.Span(
        className=class_name or "c03-icon",
        title=title,
        style={"width": size, "height": size},
        **{"data-icon": name},
        **accessibility_props,
    )
