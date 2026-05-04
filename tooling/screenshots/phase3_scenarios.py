"""Phase 3 smoke: snapshot 3D viewer under different scenarios.

Requires uvicorn running on 127.0.0.1:8767.
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE_URL = "http://127.0.0.1:8767/"
ARTIFACTS = Path(__file__).resolve().parents[2] / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)


def _enable_studio(page: Page) -> None:
    """Force studio-mode without hash by adding class directly — we still want
    the fullscreen 3D layout but with sidebar scenario dropdown accessible."""
    page.evaluate(
        """
        () => {
          const shell = document.getElementById('app-shell');
          if (shell && !shell.classList.contains('studio-mode')) {
            shell.classList.add('studio-mode');
          }
        }
        """
    )


def _disable_studio(page: Page) -> None:
    page.evaluate(
        """
        () => {
          const shell = document.getElementById('app-shell');
          if (shell) { shell.classList.remove('studio-mode'); }
        }
        """
    )


def _trigger_3d_mode(page: Page) -> None:
    """Force the render-mode button click even if it is hidden via CSS."""
    page.evaluate(
        """
        () => {
          const btn = document.getElementById('render-mode-3d');
          if (btn) { btn.click(); }
        }
        """
    )
    page.wait_for_timeout(2500)


def _wait_3d(page: Page) -> None:
    page.wait_for_function(
        "() => !!(window.pvu3d && window.pvu3d.isInitialized && window.pvu3d.isInitialized())",
        timeout=20000,
    )
    page.wait_for_timeout(3500)


def _set_display_mode(page: Page, value: str) -> None:
    label_map = {"studio": "Студия", "xray": "Рентген", "schematic": "Схема"}
    label = label_map[value]
    page.locator("#scene3d-display-mode .Select-control").click()
    page.wait_for_timeout(300)
    page.locator(".Select-option, .VirtualizedSelectOption", has_text=label).first.click()
    page.wait_for_timeout(1800)


def _set_scenario(page: Page, scenario_id: str) -> None:
    """Switch scenario via the visible Dropdown (non-studio page)."""
    _disable_studio(page)
    page.wait_for_timeout(400)
    selector = page.locator("#scenario-select .Select-control")
    selector.scroll_into_view_if_needed()
    selector.click()
    page.wait_for_timeout(400)
    # Find option whose value (data-value attribute or text key) matches scenario_id.
    option_title_map = {
        "midseason": "Межсезонье",
        "winter": "Зима",
        "summer": "Лето",
        "peak_load": "Пик нагрузки",
        "reduced_flow": "Снижение подачи",
    }
    title = option_title_map.get(scenario_id, scenario_id)
    option = page.locator(".Select-option, .VirtualizedSelectOption", has_text=title).first
    option.click()
    page.wait_for_timeout(2800)
    _enable_studio(page)
    page.wait_for_timeout(1000)


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
        # Force render-mode=3d (kicks the Dash callback that swaps scenes).
        _trigger_3d_mode(page)
        _enable_studio(page)
        _wait_3d(page)

        for scenario_id, mode in [
            ("midseason", "studio"),
            ("winter", "xray"),
            ("summer", "xray"),
            ("peak_load", "schematic"),
            ("reduced_flow", "schematic"),
        ]:
            _set_scenario(page, scenario_id)
            _set_display_mode(page, mode)
            _shoot(page, f"scene3d-phase3-{scenario_id}-{mode}-1440x900.png")

        browser.close()


if __name__ == "__main__":
    main()
