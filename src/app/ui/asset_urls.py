from __future__ import annotations

from app.infrastructure.settings import get_settings


def dashboard_asset_url(filename: str) -> str:
    """Absolute URL for a Dash asset, robust to a missing trailing slash.

    Dash serves assets under ``{dashboard_prefix}/assets/``. A relative
    ``data="assets/..."`` resolves against the page URL, so it 404s whenever the
    page is opened at the slash-less mount (``/dashboard`` instead of
    ``/dashboard/``). Building an absolute URL from the configured prefix avoids
    that entirely and honours ``AHU_SIMULATOR_DASHBOARD_PATH``.
    """
    prefix = "/" + get_settings().dashboard_path.strip("/")
    if prefix == "/":
        prefix = "/dashboard"
    return f"{prefix}/assets/{filename.lstrip('/')}"
