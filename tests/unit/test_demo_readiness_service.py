from pathlib import Path
from zipfile import ZipFile

from app.services.demo_readiness_service import DemoReadinessService
from app.simulation.state import OperationStatus


def test_demo_readiness_service_builds_demo_package_bundle(tmp_path: Path) -> None:
    _write_file(tmp_path / "README.md", "# Demo\n")
    _write_file(tmp_path / "requirements.txt", "fastapi\n")
    _write_file(tmp_path / "config" / "defaults.yaml", "default_scenario_id: midseason\n")
    _write_file(tmp_path / "config" / "p0_baseline.yaml", "baseline_version: 1\nsubject:\n  subject_id: demo\n  title: Demo\n  scope_summary: Demo\n  note: Demo\n")
    _write_file(tmp_path / "data" / "scenarios" / "presets.json", "{}\n")
    _write_file(tmp_path / "data" / "validation" / "reference_points.json", "[]\n")
    _write_file(tmp_path / "data" / "validation" / "reference_basis.json", "[]\n")
    _write_file(tmp_path / "data" / "validation" / "validation_agreement.json", "{}\n")
    _write_file(tmp_path / "data" / "visualization" / "scene3d.json", "{}\n")
    _write_file(
        tmp_path / "data" / "visualization" / "browser_capability_profile.json",
        """{
  "profile_id": "demo-browser",
  "verified_at": "2026-04-04T19:16:38.480000+00:00",
  "target_use": "future_optional_webgl_viewer",
  "verification_method": "test fixture",
  "summary": "Demo browser profile.",
  "note": "Demo browser profile.",
  "evidence_paths": [],
  "verified_environment": {
    "browser_label": "Chrome",
    "platform": "Windows",
    "secure_context": true,
    "webgl_supported": true,
    "webgl2_supported": true,
    "hardware_concurrency": 8,
    "device_memory_gb": 8,
    "screen_width": 1920,
    "screen_height": 1080,
    "max_texture_size": 16384
  },
  "recommended_viewport": {
    "min_width": 1200,
    "min_height": 680,
    "note": "Demo viewport."
  },
  "requirements": [
    {
      "requirement_id": "webgl",
      "title": "WebGL",
      "field": "webgl_supported",
      "kind": "boolean",
      "expected_bool": true,
      "expected_text": "WebGL = да",
      "rationale": "Demo"
    }
  ]
}
""",
    )
    _write_file(tmp_path / "deploy" / "run-local.ps1", "Write-Host 'run'\n")
    _write_file(tmp_path / "deploy" / "build-demo-package.ps1", "Write-Host 'package'\n")
    _write_file(tmp_path / "deploy" / "README.md", "# deploy\n")
    _write_file(tmp_path / "docs" / "05_execution_phases.md", "# phases\n")
    _write_file(tmp_path / "docs" / "06_todo.md", "# todo\n")
    _write_file(tmp_path / "docs" / "19_p0_baseline.md", "# p0\n")
    _write_file(tmp_path / "docs" / "14_defense_pack.md", "# defense\n")
    _write_file(tmp_path / "docs" / "15_demo_readiness.md", "# readiness\n")
    _write_file(tmp_path / "docs" / "16_demo_package.md", "# package\n")
    _write_file(tmp_path / "docs" / "17_scenario_archive.md", "# archive doc\n")
    _write_file(tmp_path / "docs" / "18_export_pack.md", "# export doc\n")
    _write_file(tmp_path / "src" / "app" / "__init__.py", '"""app"""\n')
    _write_file(tmp_path / "tests" / "unit" / ".keep", "")
    _write_file(tmp_path / "tests" / "integration" / ".keep", "")
    _write_file(tmp_path / "tests" / "scenario" / ".keep", "")
    _write_file(tmp_path / "artifacts" / "playwright" / "README.md", "# playwright\n")
    _write_file(tmp_path / "artifacts" / "playwright" / "manual" / "2026-04-04" / "dashboard" / "core" / "01.png", "png")
    _write_file(tmp_path / "artifacts" / "playwright" / "manual" / "2026-04-04" / "dashboard" / "browser-diagnostics" / "01.png", "png")
    _write_file(tmp_path / "artifacts" / "demo-packages" / "README.md", "# packages\n")
    _write_file(tmp_path / "artifacts" / "scenario-archive" / "README.md", "# archive\n")
    _write_file(tmp_path / "artifacts" / "exports" / "README.md", "# exports\n")

    service = DemoReadinessService(project_root=tmp_path, dashboard_path="/dashboard")

    snapshot_before_build = service.build_package_snapshot()
    assert snapshot_before_build.overall_status == OperationStatus.WARNING
    assert snapshot_before_build.latest_bundle_path is None
    assert snapshot_before_build.entries[-1].present is True

    result = service.build_demo_package()
    bundle_path = tmp_path / result.bundle_path
    manifest_path = tmp_path / result.manifest_path

    assert bundle_path.exists()
    assert manifest_path.exists()
    assert result.file_count >= 10

    snapshot_after_build = service.build_package_snapshot()
    assert snapshot_after_build.overall_status == OperationStatus.NORMAL
    assert snapshot_after_build.latest_bundle_path == result.bundle_path
    assert snapshot_after_build.latest_manifest_path == result.manifest_path

    with ZipFile(bundle_path) as archive:
        names = archive.namelist()

    assert any(name.endswith("README.md") for name in names)
    assert any(name.endswith("src/app/__init__.py") for name in names)
    assert any(name.endswith(".manifest.json") for name in names)


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
