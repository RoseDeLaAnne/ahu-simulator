from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn

from app.infrastructure.settings import get_settings


def _safe_print(message: str) -> None:
    if getattr(sys, "stdout", None) is None:
        return
    print(message)


def _is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
        candidate.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            candidate.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _resolve_port(preferred_port: int = 8000, max_attempts: int = 100) -> int:
    forced_port = os.environ.get("AHU_SIMULATOR_PORT") or os.environ.get("PORT")
    if forced_port:
        port = int(forced_port)
        if not _is_port_available(port):
            raise RuntimeError(
                f"Requested port {port} is unavailable. "
                "Set AHU_SIMULATOR_PORT or PORT to another port."
            )
        return port

    for candidate in range(preferred_port, preferred_port + max_attempts):
        if _is_port_available(candidate):
            return candidate

    raise RuntimeError(f"Unable to find a free port starting at {preferred_port}.")


def _resolve_runtime_dir() -> Path:
    override = os.environ.get("AHU_SIMULATOR_RUNTIME_DIR")
    if override:
        runtime_dir = Path(override).expanduser().resolve()
    else:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            runtime_dir = Path(local_app_data) / "AhuSimulator"
        else:
            runtime_dir = Path.home() / "AppData" / "Local" / "AhuSimulator"

    runtime_dir.mkdir(parents=True, exist_ok=True)
    return runtime_dir


def _open_dashboard_when_ready(base_url: str, dashboard_path: str) -> None:
    health_url = f"{base_url}/health"
    dashboard_url = f"{base_url}{dashboard_path}"

    for _ in range(120):
        try:
            with urlopen(health_url, timeout=1.0) as response:
                if response.status >= 500:
                    raise RuntimeError("Service is not healthy yet")
            _open_dashboard_url(dashboard_url)
            return
        except (URLError, OSError, RuntimeError):
            time.sleep(0.25)

    _open_dashboard_url(dashboard_url)


def _desktop_app_mode_requested() -> bool:
    raw_flag = os.environ.get("AHU_SIMULATOR_DESKTOP_APP_MODE", "1")
    return raw_flag.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_chromium_executable() -> Path | None:
    relative_paths = [
        Path("Microsoft") / "Edge" / "Application" / "msedge.exe",
        Path("Google") / "Chrome" / "Application" / "chrome.exe",
    ]

    roots = [
        os.environ.get("ProgramFiles(x86)"),
        os.environ.get("ProgramFiles"),
        os.environ.get("LOCALAPPDATA"),
    ]

    for root in roots:
        if not root:
            continue
        root_path = Path(root)
        for relative_path in relative_paths:
            candidate = root_path / relative_path
            if candidate.exists():
                return candidate
    return None


def _open_dashboard_url(dashboard_url: str) -> None:
    if os.name == "nt" and _desktop_app_mode_requested():
        chromium_executable = _resolve_chromium_executable()
        if chromium_executable:
            try:
                subprocess.Popen(
                    [
                        str(chromium_executable),
                        f"--app={dashboard_url}",
                        "--new-window",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except OSError as exc:
                _safe_print(f"Failed to open Chromium app window, fallback to browser: {exc}")

    webbrowser.open(dashboard_url, new=2)


def _run_without_console_streams() -> bool:
    return getattr(sys, "stdout", None) is None or getattr(sys, "stderr", None) is None


def _resolve_uvicorn_kwargs() -> dict[str, object]:
    if _run_without_console_streams():
        # Windowed executables can have no stderr/stdout streams.
        # Uvicorn default log formatter probes isatty() and crashes in that case.
        return {
            "log_config": None,
            "log_level": "warning",
            "access_log": False,
        }

    return {
        "log_level": "info",
    }


def main() -> None:
    settings = get_settings()
    runtime_dir = _resolve_runtime_dir()
    os.environ["AHU_SIMULATOR_RUNTIME_DIR"] = str(runtime_dir)
    os.environ["AHU_SIMULATOR_DESKTOP_MODE"] = "1"

    port = _resolve_port()
    base_url = f"http://127.0.0.1:{port}"

    _safe_print(f"Starting desktop backend on {base_url}")
    _safe_print(f"Runtime data directory: {runtime_dir}")

    threading.Thread(
        target=_open_dashboard_when_ready,
        args=(base_url, settings.dashboard_path),
        daemon=True,
    ).start()

    from app.main import create_app

    uvicorn.run(
        create_app(),
        host="127.0.0.1",
        port=port,
        reload=False,
        **_resolve_uvicorn_kwargs(),
    )


if __name__ == "__main__":
    main()
