"""Phase 4 smoke: snapshot 3D viewer with labels overlay + legend in different
display modes and camera presets. Also checks hover info-card.

Requires uvicorn on 127.0.0.1:8767.
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE_URL = "http://127.0.0.1:8767/#3d-studio"
ARTIFACTS = Path(__file__).resolve().parents[2] / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)


def _wait_3d(page: Page) -> None:
    page.wait_for_function(
        "() => !!(window.pvu3d && window.pvu3d.isInitialized && window.pvu3d.isInitialized())",
        timeout=20000,
    )
    page.wait_for_timeout(4000)


def _set_display_mode(page: Page, value: str) -> None:
    label_map = {"studio": "Студия", "xray": "Рентген", "schematic": "Схема"}
    label = label_map[value]
    page.locator("#scene3d-display-mode .Select-control").click()
    page.wait_for_timeout(300)
    page.locator(".Select-option, .VirtualizedSelectOption", has_text=label).first.click()
    page.wait_for_timeout(1800)


def _set_camera(page: Page, label: str) -> None:
    page.locator("#scene3d-camera-preset .Select-control").click()
    page.wait_for_timeout(300)
    page.locator(".Select-option, .VirtualizedSelectOption", has_text=label).first.click()
    page.wait_for_timeout(1500)


def _shoot(page: Page, name: str) -> None:
    target = ARTIFACTS / name
    page.screenshot(path=str(target), full_page=False)
    print(f"Saved {target}")


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(1200)
        _wait_3d(page)

        # Default camera + studio: both labels and legend should be visible.
        _set_display_mode(page, "studio")
        _shoot(page, "scene3d-phase4-studio-default-1440x900.png")

        _set_display_mode(page, "xray")
        _shoot(page, "scene3d-phase4-xray-default-1440x900.png")

        _set_display_mode(page, "schematic")
        _shoot(page, "scene3d-phase4-schematic-default-1440x900.png")

        # Top camera in xray — verify labels are clamped + readable from above.
        _set_camera(page, "Сверху")
        _set_display_mode(page, "xray")
        _shoot(page, "scene3d-phase4-xray-top-1440x900.png")
        _set_display_mode(page, "schematic")
        _shoot(page, "scene3d-phase4-schematic-top-1440x900.png")

        # Trigger an info card by hovering a sensor (raycaster intersect).
        # Pick a position roughly where a sensor marker sits in top view.
        canvas = page.locator("#scene-3d-canvas")
        box = canvas.bounding_box()
        if box:
            cx = box["x"] + box["width"] * 0.55
            cy = box["y"] + box["height"] * 0.45
            page.mouse.move(cx, cy)
            page.wait_for_timeout(800)
            _shoot(page, "scene3d-phase4-hover-info-card-1440x900.png")

        # Mobile-style viewport: shrink to portrait and verify legend collapses.
        ctx.close()
        ctx2 = browser.new_context(
            viewport={"width": 768, "height": 1024},
            has_touch=True,
            is_mobile=False,
        )
        page2 = ctx2.new_page()
        page2.goto(BASE_URL, wait_until="networkidle")
        page2.wait_for_timeout(1200)
        _wait_3d(page2)
        _shoot(page2, "scene3d-phase4-tablet-768x1024.png")

        browser.close()


if __name__ == "__main__":
    main()
