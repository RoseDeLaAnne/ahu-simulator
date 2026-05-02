from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeDirectories:
    root: Path
    exports: Path
    event_log: Path
    scenario_archive: Path
    demo_packages: Path
    comparison_snapshots: Path | None = None
    user_presets: Path | None = None


def _default_windows_runtime_root() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "AhuSimulator"
    return Path.home() / "AppData" / "Local" / "AhuSimulator"


def resolve_runtime_root(project_root: Path) -> Path:
    override = os.environ.get("AHU_SIMULATOR_RUNTIME_DIR")
    if override:
        return Path(override).expanduser().resolve()

    if getattr(sys, "frozen", False):
        return _default_windows_runtime_root().resolve()

    return (project_root / "artifacts").resolve()


def build_runtime_directories(project_root: Path) -> RuntimeDirectories:
    root = resolve_runtime_root(project_root)
    return RuntimeDirectories(
        root=root,
        exports=root / "exports",
        event_log=root / "event-log",
        scenario_archive=root / "scenario-archive",
        demo_packages=root / "demo-packages",
        comparison_snapshots=root / "comparison-snapshots",
        user_presets=root / "user-presets",
    )


class RuntimePathResolver:
    def __init__(
        self,
        project_root: Path,
        runtime_directories: RuntimeDirectories | None = None,
    ) -> None:
        self._project_root = project_root.resolve()
        self._runtime_directories = runtime_directories or build_runtime_directories(
            self._project_root
        )
        comparison_snapshots = (
            self._runtime_directories.comparison_snapshots
            or self._runtime_directories.root / "comparison-snapshots"
        )
        user_presets = (
            self._runtime_directories.user_presets
            or self._runtime_directories.root / "user-presets"
        )
        self._runtime_aliases: tuple[tuple[str, Path], ...] = (
            ("artifacts/exports", self._runtime_directories.exports),
            ("artifacts/event-log", self._runtime_directories.event_log),
            ("artifacts/scenario-archive", self._runtime_directories.scenario_archive),
            (
                "artifacts/comparison-snapshots",
                comparison_snapshots,
            ),
            ("artifacts/user-presets", user_presets),
            ("artifacts/demo-packages", self._runtime_directories.demo_packages),
        )

    @property
    def runtime_directories(self) -> RuntimeDirectories:
        return self._runtime_directories

    def to_display_path(self, absolute_path: Path) -> str:
        normalized = absolute_path.resolve()

        for display_prefix, runtime_base in self._runtime_aliases:
            try:
                relative_part = normalized.relative_to(runtime_base)
            except ValueError:
                continue
            if not relative_part.parts:
                return display_prefix
            return f"{display_prefix}/{relative_part.as_posix()}"

        try:
            return normalized.relative_to(self._project_root).as_posix()
        except ValueError:
            return normalized.as_posix()

    def resolve_display_path(self, display_path: str) -> Path:
        normalized_display_path = display_path.replace("\\", "/").strip()

        for display_prefix, runtime_base in self._runtime_aliases:
            if normalized_display_path == display_prefix:
                return runtime_base
            if normalized_display_path.startswith(f"{display_prefix}/"):
                relative_part = normalized_display_path.removeprefix(
                    f"{display_prefix}/"
                )
                return runtime_base / Path(relative_part)

        candidate = Path(display_path)
        if candidate.is_absolute():
            return candidate
        return self._project_root / candidate
