"""Playwright smoke-script for Phase 2: snapshot studio/xray/schematic modes.

Run uvicorn first:
    python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8767

Then:
    python tooling/screenshots/phase2_modes.py
"""
from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE_URL = "http://127.0.0.1:8767/#3d-studio"
ARTIFACTS = Path(__file__).resolve().parents[2] / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)


def _wait_3d_ready(page: Page) -> None:
    """Wait for the canvas to appear and the GLB model to load."""
    page.wait_for_selector("#scene-3d-canvas", state="attached", timeout=20000)
    # Wait for window.pvu3d to load and report initialization.
    page.wait_for_function(
        "() => !!(window.pvu3d && window.pvu3d.isInitialized && window.pvu3d.isInitialized())",
        timeout=20000,
    )
    # Initial frame + first applySignals tick + GLB.
    page.wait_for_timeout(4000)


def _set_display_mode(page: Page, value: str) -> None:
    """Set display mode via the Dropdown control and let the renderer settle."""
    label_map = {"studio": "Студия", "xray": "Рентген", "schematic": "Схема"}
    label = label_map[value]
    # Use Dash dropdown markup (.Select-control / .Select-option)
    dropdown = page.locator("#scene3d-display-mode .Select-control")
    dropdown.click()
    page.wait_for_timeout(300)
    option = page.locator(".Select-option, .VirtualizedSelectOption", has_text=label).first
    option.click()
    page.wait_for_timeout(2200)


def _shoot(page: Page, name: str) -> None:
    target = ARTIFACTS / name
    page.screenshot(path=str(target), full_page=False)
    print(f"Saved {target}")


def _set_camera_preset(page: Page, label: str) -> bool:
    try:
        dropdown = page.locator("#scene3d-camera-preset .Select-control")
        dropdown.click()
        page.wait_for_timeout(300)
        option = page.locator(
            ".Select-option, .VirtualizedSelectOption", has_text=label
        ).first
        option.click()
        page.wait_for_timeout(1500)
        return True
    except Exception as exc:
        print(f"Camera preset '{label}' not available: {exc}")
        return False


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(1000)
        _wait_3d_ready(page)

        for mode in ("studio", "xray", "schematic"):
            _set_display_mode(page, mode)
            _shoot(page, f"scene3d-phase2-{mode}-1440x900.png")

        # Optional: top-down view in xray to verify section layout.
        if _set_camera_preset(page, "Сверху"):
            _set_display_mode(page, "xray")
            _shoot(page, "scene3d-phase2-xray-top-1440x900.png")
            _set_display_mode(page, "schematic")
            _shoot(page, "scene3d-phase2-schematic-top-1440x900.png")

        browser.close()


if __name__ == "__main__":
    main()
