import sys
from pathlib import Path

from app.infrastructure.runtime_paths import (
    RuntimeDirectories,
    RuntimePathResolver,
    resolve_runtime_root,
)


def test_resolve_runtime_root_prefers_environment_override(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "runtime-override"
    monkeypatch.setenv("AHU_SIMULATOR_RUNTIME_DIR", str(runtime_dir))

    assert resolve_runtime_root(tmp_path) == runtime_dir.resolve()


def test_resolve_runtime_root_uses_localappdata_in_frozen_mode(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("AHU_SIMULATOR_RUNTIME_DIR", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    assert resolve_runtime_root(tmp_path) == (
        tmp_path / "LocalAppData" / "AhuSimulator"
    ).resolve()


def test_runtime_path_resolver_maps_runtime_files_to_artifacts_prefix(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_dirs = RuntimeDirectories(
        root=runtime_root,
        exports=runtime_root / "exports",
        event_log=runtime_root / "event-log",
        scenario_archive=runtime_root / "scenario-archive",
        demo_packages=runtime_root / "demo-packages",
    )
    resolver = RuntimePathResolver(tmp_path, runtime_directories=runtime_dirs)
    export_file = runtime_dirs.exports / "2026-04-18" / "sample.csv"

    assert (
        resolver.to_display_path(export_file)
        == "artifacts/exports/2026-04-18/sample.csv"
    )
    assert resolver.resolve_display_path("artifacts/exports/2026-04-18/sample.csv") == export_file
