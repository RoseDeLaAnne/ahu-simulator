from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.infrastructure.settings import get_settings
from app.services.comparison_service import RunComparisonService
from app.services.demo_readiness_service import DemoReadinessService
from app.services.event_log_service import EventLogService
from app.services.export_service import ExportService
from app.services.scenario_archive_service import ScenarioArchiveService
from app.services.scenario_preset_service import ScenarioPresetService
from app.services.simulation_service import SimulationService
from app.services.trend_service import TrendService
from app.simulation.scenarios import load_scenarios


def test_health_endpoint() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_mobile_profile_applies_cors_headers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config" / "mobile-test.yaml"
    _write_file(
        config_path,
        """
cors_allow_origins:
  - "https://mobile.ahu.example"
trusted_hosts:
  - "mobile.ahu.example"
enforce_https_redirect: true
""".strip()
        + "\n",
    )

    monkeypatch.setenv("AHU_SIMULATOR_SETTINGS_FILE", str(config_path))
    get_settings.cache_clear()

    try:
        with TestClient(create_app(), base_url="https://mobile.ahu.example") as client:
            response = client.get(
                "/health",
                headers={"origin": "https://mobile.ahu.example"},
            )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://mobile.ahu.example"


def test_mobile_profile_rejects_untrusted_host(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config" / "mobile-hosts.yaml"
    _write_file(
        config_path,
        """
trusted_hosts:
  - "mobile.ahu.example"
""".strip()
        + "\n",
    )

    monkeypatch.setenv("AHU_SIMULATOR_SETTINGS_FILE", str(config_path))
    get_settings.cache_clear()

    try:
        with TestClient(create_app(), base_url="https://mobile.ahu.example") as client:
            response = client.get("/health", headers={"host": "evil.ahu.example"})
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400


def test_mobile_profile_enforces_https_redirect(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config" / "mobile-https.yaml"
    _write_file(
        config_path,
        """
trusted_hosts:
  - "mobile.ahu.example"
enforce_https_redirect: true
""".strip()
        + "\n",
    )

    monkeypatch.setenv("AHU_SIMULATOR_SETTINGS_FILE", str(config_path))
    get_settings.cache_clear()

    try:
        with TestClient(create_app(), base_url="http://mobile.ahu.example") as client:
            response = client.get("/health", follow_redirects=False)
    finally:
        get_settings.cache_clear()

    assert response.status_code in {307, 308}
    assert response.headers.get("location", "").startswith("https://mobile.ahu.example")


def test_demo_readiness_endpoint_returns_preflight_snapshot() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/readiness/demo")

    body = response.json()
    assert response.status_code == 200
    assert body["overall_status"] == "normal"
    assert body["ready_checks"] == 6
    assert body["total_checks"] == 6
    assert body["launch_commands"][0]["command"] == ".\\deploy\\run-local.ps1"
    assert body["launch_commands"][-1]["command"] == ".\\deploy\\build-demo-package.ps1"
    assert any(endpoint["path"] == "/validation/agreement" for endpoint in body["endpoints"])
    assert any(endpoint["path"] == "/visualization/browser-profile" for endpoint in body["endpoints"])
    assert any(endpoint["path"] == "/project/baseline" for endpoint in body["endpoints"])
    assert body["endpoints"][-1]["path"] == "/exports/result"
    assert body["checks"][-1]["item_id"] == "demo-pc-verification"
    assert body["checks"][-1]["status"] == "normal"


def test_project_baseline_endpoint_returns_locked_scope() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/project/baseline")

    body = response.json()
    assert response.status_code == 200
    assert body["baseline_version"] == 1
    assert body["overall_status"] == "normal"
    assert body["subject"]["subject_id"] == "generalized_supply_ahu"
    assert len(body["operator_inputs"]) == 10
    assert body["defense_scenarios"][-1]["scenario_id"] == "manual_mode"
    assert any(layer["layer_id"] == "validation_basis" for layer in body["validation_layers"])


def test_demo_package_snapshot_endpoint_returns_packaging_state() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/readiness/package")

    body = response.json()
    assert response.status_code == 200
    assert body["bundle_name_pattern"] == "pvu-demo-package-ГГГГММДД-ЧЧММСС.zip"
    assert body["entries"][0]["entry_id"] == "application-source"
    assert body["entries"][-1]["entry_id"] == "exports"


def test_demo_package_build_endpoint_creates_bundle(tmp_path: Path) -> None:
    _write_demo_package_fixture(tmp_path)
    app = create_app()
    app.state.demo_readiness_service = DemoReadinessService(
        project_root=tmp_path,
        dashboard_path="/dashboard",
    )

    with TestClient(app) as client:
        response = client.post("/readiness/package/build")

    body = response.json()
    assert response.status_code == 200
    assert body["bundle_path"].endswith(".zip")
    assert body["manifest_path"].endswith(".manifest.json")
    assert (tmp_path / body["bundle_path"]).exists()
    assert (tmp_path / body["manifest_path"]).exists()


def test_scenario_archive_snapshot_endpoint_returns_empty_state(tmp_path: Path) -> None:
    app = create_app()
    app.state.scenario_archive_service = ScenarioArchiveService(project_root=tmp_path)

    with TestClient(app) as client:
        response = client.get("/archive/scenarios")

    body = response.json()
    assert response.status_code == 200
    assert body["overall_status"] == "warning"
    assert body["total_entries"] == 0
    assert body["latest_entry_path"] is None


def test_scenario_archive_save_endpoint_creates_json(tmp_path: Path) -> None:
    app = create_app()
    app.state.scenario_archive_service = ScenarioArchiveService(project_root=tmp_path)
    app.state.event_log_service = EventLogService(project_root=tmp_path)

    payload = {
        "selected_scenario_id": "winter",
        "parameters": {
            "outdoor_temp_c": -22,
            "airflow_m3_h": 3600,
            "supply_temp_setpoint_c": 21,
            "heat_recovery_efficiency": 0.62,
            "heater_power_kw": 42,
            "filter_contamination": 0.22,
            "fan_speed_ratio": 1.0,
            "room_temp_c": 20.5,
            "room_heat_gain_kw": 3.5,
        },
    }

    with TestClient(app) as client:
        response = client.post("/archive/scenarios", json=payload)

    body = response.json()
    assert response.status_code == 200
    assert body["entry"]["scenario_id"] == "winter"
    assert body["entry"]["source_type"] == "scenario"
    assert body["entry"]["file_path"].endswith(".json")
    assert (tmp_path / body["entry"]["file_path"]).exists()


def test_result_export_snapshot_endpoint_returns_empty_state(tmp_path: Path) -> None:
    app = create_app()
    app.state.export_service = ExportService(project_root=tmp_path)

    with TestClient(app) as client:
        response = client.get("/exports/result")

    body = response.json()
    assert response.status_code == 200
    assert body["overall_status"] == "warning"
    assert body["total_entries"] == 0
    assert body["latest_report_id"] is None
    assert body["latest_manifest_path"] is None


def test_result_export_preview_endpoint_returns_v2_contract(tmp_path: Path) -> None:
    app = create_app()
    app.state.export_service = ExportService(project_root=tmp_path)

    payload = {
        "selected_scenario_id": "winter",
        "parameters": {
            "outdoor_temp_c": -22,
            "airflow_m3_h": 3600,
            "supply_temp_setpoint_c": 21,
            "heat_recovery_efficiency": 0.62,
            "heater_power_kw": 42,
            "filter_contamination": 0.22,
            "fan_speed_ratio": 1.0,
            "room_temp_c": 20.5,
            "room_heat_gain_kw": 3.5,
        },
    }

    with TestClient(app) as client:
        response = client.post("/exports/result/preview", json=payload)

    body = response.json()
    assert response.status_code == 200
    assert body["report"]["schema_version"] == "scenario-report.v2"
    assert body["planned_sections"] == [
        "metadata",
        "findings",
        "parameters",
        "state",
        "status_legend",
        "status_events",
        "trend",
    ]
    assert body["planned_artifacts"] == ["csv", "pdf", "manifest"]
    assert not (tmp_path / "artifacts" / "exports").exists()


def test_result_export_build_endpoint_creates_artifacts(tmp_path: Path) -> None:
    app = create_app()
    app.state.export_service = ExportService(project_root=tmp_path)
    app.state.event_log_service = EventLogService(project_root=tmp_path)

    payload = {
        "selected_scenario_id": "winter",
        "parameters": {
            "outdoor_temp_c": -22,
            "airflow_m3_h": 3600,
            "supply_temp_setpoint_c": 21,
            "heat_recovery_efficiency": 0.62,
            "heater_power_kw": 42,
            "filter_contamination": 0.22,
            "fan_speed_ratio": 1.0,
            "room_temp_c": 20.5,
            "room_heat_gain_kw": 3.5,
        },
    }

    with TestClient(app) as client:
        response = client.post("/exports/result/build", json=payload)

    body = response.json()
    assert response.status_code == 200
    assert body["entry"]["schema_version"] == "scenario-report.v2"
    assert body["entry"]["report_id"].startswith("pvu-report-")
    assert body["entry"]["csv_path"].endswith(".csv")
    assert body["entry"]["pdf_path"].endswith(".pdf")
    assert body["entry"]["manifest_path"].endswith(".manifest.json")
    assert body["report"]["schema_version"] == "scenario-report.v2"
    assert body["report"]["metadata"]["report_id"] == body["entry"]["report_id"]
    assert body["report"]["sections"][-1]["section_id"] == "trend"
    assert body["report"]["chart_specs"][0]["chart_id"] == "trend_temperature_power"
    assert body["report"]["tables"][1]["table_id"] == "status"
    assert body["report"]["tables"][2]["table_id"] == "status_legend"
    assert body["report"]["tables"][-1]["table_id"] == "trend"
    assert (tmp_path / body["entry"]["csv_path"]).exists()
    assert (tmp_path / body["entry"]["pdf_path"]).exists()
    assert (tmp_path / body["entry"]["manifest_path"]).exists()

    with TestClient(app) as client:
        download_response = client.get(
            "/exports/result/download",
            params={"path": body["entry"]["manifest_path"]},
        )

    assert download_response.status_code == 200
    assert download_response.content.startswith(b"{")


def test_result_export_batch_endpoint_creates_one_pack_per_scenario(tmp_path: Path) -> None:
    app = create_app()
    app.state.export_service = ExportService(project_root=tmp_path)
    app.state.event_log_service = EventLogService(project_root=tmp_path)

    with TestClient(app) as client:
        response = client.post(
            "/exports/result/batch",
            json={"selected_scenario_ids": ["winter", "summer"]},
        )

    body = response.json()
    assert response.status_code == 200
    assert len(body["entries"]) == 2
    assert {entry["scenario_id"] for entry in body["entries"]} == {"winter", "summer"}
    for entry in body["entries"]:
        assert (tmp_path / entry["csv_path"]).exists()
        assert (tmp_path / entry["pdf_path"]).exists()
        assert (tmp_path / entry["manifest_path"]).exists()


def test_run_comparison_snapshot_endpoint_returns_active_source(tmp_path: Path) -> None:
    app = create_app()
    app.state.scenario_archive_service = ScenarioArchiveService(project_root=tmp_path)
    app.state.comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=app.state.scenario_archive_service,
    )

    with TestClient(app) as client:
        response = client.get("/comparison/runs")

    body = response.json()
    assert response.status_code == 200
    assert body["overall_status"] == "warning"
    assert body["default_before_reference_id"] is None
    assert body["default_after_reference_id"] == "active-run"
    assert body["available_sources"][0]["reference_id"] == "active-run"


def test_run_comparison_named_snapshot_endpoints_feed_default_pair(tmp_path: Path) -> None:
    app = create_app()
    app.state.scenario_archive_service = ScenarioArchiveService(project_root=tmp_path)
    app.state.comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=app.state.scenario_archive_service,
    )

    with TestClient(app) as client:
        before_response = client.post(
            "/comparison/runs/before",
            json={"label": "До настройки", "notes": "baseline"},
        )
        after_response = client.post(
            "/comparison/runs/after",
            json={"label": "После настройки"},
        )
        snapshot_response = client.get("/comparison/runs")
        build_response = client.post(
            "/comparison/runs/build",
            json={
                "before_reference_id": "snapshot:before",
                "after_reference_id": "snapshot:after",
            },
        )

    assert before_response.status_code == 200
    assert before_response.json()["snapshot"]["role"] == "before"
    assert before_response.json()["snapshot"]["label"] == "До настройки"
    assert after_response.status_code == 200
    snapshot = snapshot_response.json()
    assert snapshot["default_before_reference_id"] == "snapshot:before"
    assert snapshot["default_after_reference_id"] == "snapshot:after"
    assert snapshot["named_snapshots"][0]["role"] == "before"
    assert build_response.status_code == 200
    comparison = build_response.json()
    assert comparison["before_source"]["source_type"] == "snapshot"
    assert comparison["after_source"]["source_type"] == "snapshot"
    assert comparison["interpretation"]["summary"]


def test_run_comparison_build_endpoint_returns_metric_deltas(tmp_path: Path) -> None:
    app = create_app()
    app.state.scenario_archive_service = ScenarioArchiveService(project_root=tmp_path)
    app.state.comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=app.state.scenario_archive_service,
    )
    save_result = app.state.scenario_archive_service.save_result(
        app.state.simulation_service.preview_scenario("winter")
    )

    payload = {
        "before_reference_id": f"archive:{save_result.entry.archive_id}",
        "after_reference_id": "active-run",
    }

    with TestClient(app) as client:
        response = client.post("/comparison/runs/build", json=payload)

    body = response.json()
    assert response.status_code == 200
    assert body["compatibility"]["is_compatible"] is True
    assert body["before_source"]["source_type"] == "archive"
    assert body["after_source"]["source_type"] == "active"
    assert len(body["metric_deltas"]) == 12
    assert len(body["trend_deltas"]) > 0
    assert body["schema_version"] == "run-comparison.v2"
    assert body["interpretation"]["top_deltas"]


def test_run_comparison_export_endpoint_creates_artifacts(tmp_path: Path) -> None:
    app = create_app()
    app.state.scenario_archive_service = ScenarioArchiveService(project_root=tmp_path)
    app.state.comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=app.state.scenario_archive_service,
    )
    save_result = app.state.scenario_archive_service.save_result(
        app.state.simulation_service.preview_scenario("winter")
    )

    payload = {
        "before_reference_id": f"archive:{save_result.entry.archive_id}",
        "after_reference_id": "active-run",
    }

    with TestClient(app) as client:
        response = client.post("/comparison/runs/export", json=payload)

    body = response.json()
    assert response.status_code == 200
    assert body["entry"]["comparison_id"].startswith("pvu-comparison-")
    assert body["entry"]["schema_version"] == "run-comparison.v2"
    assert body["entry"]["interpretation_summary"]
    assert body["entry"]["csv_path"].endswith(".csv")
    assert body["entry"]["pdf_path"].endswith(".pdf")
    assert body["entry"]["manifest_path"].endswith(".manifest.json")
    assert (tmp_path / body["entry"]["csv_path"]).exists()
    assert (tmp_path / body["entry"]["pdf_path"]).exists()
    assert (tmp_path / body["entry"]["manifest_path"]).exists()


def test_run_comparison_export_endpoint_rejects_incompatible_pair(tmp_path: Path) -> None:
    app = create_app()
    app.state.scenario_archive_service = ScenarioArchiveService(project_root=tmp_path)
    app.state.comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=app.state.scenario_archive_service,
    )
    save_result = app.state.scenario_archive_service.save_result(
        app.state.simulation_service.preview(
            app.state.simulation_service.get_scenario("winter").parameters.model_copy(
                update={"step_minutes": 5}
            )
        )
    )

    payload = {
        "before_reference_id": f"archive:{save_result.entry.archive_id}",
        "after_reference_id": "active-run",
    }

    with TestClient(app) as client:
        response = client.post("/comparison/runs/export", json=payload)

    assert response.status_code == 409
    assert "Шаг времени" in response.json()["detail"]


def test_run_simulation_endpoint_returns_state_and_trend(tmp_path: Path) -> None:
    app = create_app()
    app.state.event_log_service = EventLogService(project_root=tmp_path)

    payload = {
        "outdoor_temp_c": -16,
        "airflow_m3_h": 3400,
        "supply_temp_setpoint_c": 21,
        "heat_recovery_efficiency": 0.6,
        "heater_power_kw": 36,
        "filter_contamination": 0.2,
        "fan_speed_ratio": 1.0,
        "room_temp_c": 21,
        "room_heat_gain_kw": 4,
    }

    with TestClient(app) as client:
        response = client.post("/simulation/run", json=payload)

    body = response.json()
    assert response.status_code == 200
    assert body["parameter_source"] == "manual"
    assert body["state"]["actual_airflow_m3_h"] > 0
    assert body["trend"]["points"]


def test_scenario_execution_endpoint(tmp_path: Path) -> None:
    app = create_app()
    app.state.event_log_service = EventLogService(project_root=tmp_path)

    with TestClient(app) as client:
        response = client.post("/scenarios/winter/run")

    assert response.status_code == 200
    assert response.json()["scenario_id"] == "winter"
    assert response.json()["parameter_source"] == "preset"


def test_scenarios_endpoint_returns_required_presets_with_metadata() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/scenarios")

    body = response.json()
    scenario_map = {item["id"]: item for item in body}

    assert response.status_code == 200
    for scenario_id in ("winter", "summer", "peak_load"):
        scenario = scenario_map[scenario_id]
        assert scenario["purpose"]
        assert scenario["key_parameters"]
        assert scenario["expected_effect"]
        assert scenario["schema_version"] == "scenario-preset.v2"
        assert scenario["source"] == "system"
        assert scenario["locked"] is True


def test_user_preset_api_lifecycle_and_run(tmp_path: Path) -> None:
    app = create_app()
    scenario_path = Path(__file__).resolve().parents[2] / "data" / "scenarios" / "presets.json"
    preset_service = ScenarioPresetService(
        system_preset_path=scenario_path,
        project_root=tmp_path,
    )
    app.state.simulation_service = SimulationService(
        scenarios=load_scenarios(scenario_path),
        trend_service=TrendService(),
        default_scenario_id="midseason",
        scenario_preset_service=preset_service,
    )
    app.state.event_log_service = EventLogService(project_root=tmp_path)

    payload = {
        "id": "night_mode",
        "title": "Ночной режим",
        "parameters": {"airflow_m3_h": 2400, "heater_power_kw": 14},
    }

    with TestClient(app) as client:
        create_response = client.post("/scenarios/user", json=payload)
        list_response = client.get("/scenarios")
        run_response = client.post("/scenarios/night_mode/run")
        rename_response = client.patch(
            "/scenarios/user/night_mode/rename",
            json={"title": "Ночной экономичный режим"},
        )
        update_response = client.put(
            "/scenarios/user/night_mode",
            json={"parameters": {"airflow_m3_h": 2200, "heater_power_kw": 10}},
        )
        export_response = client.get("/scenarios/user/night_mode/export")
        delete_response = client.delete("/scenarios/user/night_mode")
        locked_response = client.delete("/scenarios/user/winter")

    scenario_ids = {item["id"] for item in list_response.json()}

    assert create_response.status_code == 200
    assert create_response.json()["source"] == "user"
    assert create_response.json()["locked"] is False
    assert "night_mode" in scenario_ids
    assert run_response.status_code == 200
    assert run_response.json()["scenario_id"] == "night_mode"
    assert rename_response.status_code == 200
    assert rename_response.json()["title"] == "Ночной экономичный режим"
    assert update_response.status_code == 200
    assert update_response.json()["parameters"]["airflow_m3_h"] == 2200
    assert export_response.status_code == 200
    assert export_response.json()["schema_version"] == "scenario-preset.v2"
    assert delete_response.status_code == 200
    assert locked_response.status_code == 409


def test_user_preset_import_endpoint_rejects_invalid_payload(tmp_path: Path) -> None:
    app = create_app()
    scenario_path = Path(__file__).resolve().parents[2] / "data" / "scenarios" / "presets.json"
    preset_service = ScenarioPresetService(
        system_preset_path=scenario_path,
        project_root=tmp_path,
    )
    app.state.simulation_service = SimulationService(
        scenarios=load_scenarios(scenario_path),
        trend_service=TrendService(),
        default_scenario_id="midseason",
        scenario_preset_service=preset_service,
    )

    with TestClient(app) as client:
        response = client.post(
            "/scenarios/user/import",
            json={
                "preset": {
                    "schema_version": "scenario-preset.v2",
                    "id": "bad",
                    "title": "Bad",
                    "description": "Bad",
                    "purpose": "Bad",
                    "key_parameters": ["bad"],
                    "expected_effect": "Bad",
                    "source": "user",
                    "locked": False,
                    "parameters": {"airflow_m3_h": -1},
                }
            },
        )

    assert response.status_code == 422


def test_event_log_endpoint_returns_recorded_api_run(tmp_path: Path) -> None:
    app = create_app()
    app.state.event_log_service = EventLogService(project_root=tmp_path)

    payload = {
        "outdoor_temp_c": -16,
        "airflow_m3_h": 3400,
        "supply_temp_setpoint_c": 21,
        "heat_recovery_efficiency": 0.6,
        "heater_power_kw": 36,
        "filter_contamination": 0.2,
        "fan_speed_ratio": 1.0,
        "room_temp_c": 21,
        "room_heat_gain_kw": 4,
    }

    with TestClient(app) as client:
        run_response = client.post("/simulation/run", json=payload)
        log_response = client.get("/events/log")

    run_body = run_response.json()
    body = log_response.json()
    assert run_response.status_code == 200
    assert log_response.status_code == 200
    assert body["total_entries"] == 1
    assert body["entries"][0]["category"] == "simulation"
    assert body["entries"][0]["source_type"] == "api"
    assert body["entries"][0]["control_mode"] == run_body["parameters"]["control_mode"]


def test_state_endpoint_returns_default_scenario_on_startup() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/state")

    assert response.status_code == 200
    assert response.json()["scenario_id"] == get_settings().default_scenario_id
    assert response.json()["parameter_source"] == "preset"


def test_simulation_session_lifecycle_endpoints() -> None:
    payload = {
        "outdoor_temp_c": -12,
        "airflow_m3_h": 3200,
        "supply_temp_setpoint_c": 20,
        "heat_recovery_efficiency": 0.55,
        "heater_power_kw": 30,
        "filter_contamination": 0.2,
        "fan_speed_ratio": 0.92,
        "room_temp_c": 21,
        "room_heat_gain_kw": 4,
        "step_minutes": 5,
    }

    with TestClient(create_app()) as client:
        prepare_response = client.post("/simulation/run", json=payload)
        session_response = client.get("/simulation/session")
        start_response = client.post("/simulation/session/start")
        tick_response = client.post("/simulation/session/tick")
        speed_response = client.post(
            "/simulation/session/speed",
            json={"playback_speed": 2.0},
        )
        pause_response = client.post("/simulation/session/pause")
        reset_response = client.post("/simulation/session/reset")

    assert prepare_response.status_code == 200
    assert session_response.status_code == 200
    assert session_response.json()["status"] == "idle"
    assert session_response.json()["step_minutes"] == 5
    assert session_response.json()["playback_speed"] == 1.0
    assert session_response.json()["max_ticks"] == 24
    assert session_response.json()["horizon_reached"] is False
    assert session_response.json()["actions"]["can_set_speed"] is True
    assert start_response.status_code == 200
    assert start_response.json()["status"] == "running"
    assert start_response.json()["last_command"] == "start"
    assert tick_response.status_code == 200
    assert tick_response.json()["status"] == "running"
    assert tick_response.json()["elapsed_minutes"] == 5
    assert tick_response.json()["tick_count"] == 1
    assert len(tick_response.json()["history"]["points"]) == 2
    assert speed_response.status_code == 200
    assert speed_response.json()["playback_speed"] == 2.0
    assert speed_response.json()["last_command"] == "speed"
    assert pause_response.status_code == 200
    assert pause_response.json()["status"] == "paused"
    assert pause_response.json()["actions"]["can_resume"] is True
    assert reset_response.status_code == 200
    assert reset_response.json()["status"] == "idle"
    assert reset_response.json()["elapsed_minutes"] == 0
    assert reset_response.json()["tick_count"] == 0
    assert len(reset_response.json()["history"]["points"]) == 1


def test_simulation_session_completes_at_horizon_and_logs_lifecycle(
    tmp_path: Path,
) -> None:
    app = create_app()
    app.state.event_log_service = EventLogService(project_root=tmp_path)
    payload = {
        "outdoor_temp_c": -12,
        "airflow_m3_h": 3200,
        "supply_temp_setpoint_c": 20,
        "heat_recovery_efficiency": 0.55,
        "heater_power_kw": 30,
        "filter_contamination": 0.2,
        "fan_speed_ratio": 0.92,
        "room_temp_c": 21,
        "room_heat_gain_kw": 4,
        "horizon_minutes": 10,
        "step_minutes": 5,
    }

    with TestClient(app) as client:
        prepare_response = client.post("/simulation/run", json=payload)
        start_response = client.post("/simulation/session/start")
        first_tick_response = client.post("/simulation/session/tick")
        completed_response = client.post("/simulation/session/tick")
        blocked_response = client.post("/simulation/session/tick")
        log_response = client.get("/events/log")
        reset_response = client.post("/simulation/session/reset")

    completed_body = completed_response.json()
    log_triggers = {
        entry["trigger"]
        for entry in log_response.json()["entries"]
    }

    assert prepare_response.status_code == 200
    assert start_response.status_code == 200
    assert first_tick_response.status_code == 200
    assert completed_response.status_code == 200
    assert completed_body["status"] == "completed"
    assert completed_body["elapsed_minutes"] == 10
    assert completed_body["tick_count"] == 2
    assert completed_body["horizon_reached"] is True
    assert completed_body["completed_at"] is not None
    assert completed_body["actions"]["can_tick"] is False
    assert blocked_response.status_code == 409
    assert {
        "simulation.session.start",
        "simulation.session.tick",
    }.issubset(log_triggers)
    assert any(
        entry["title"] == "Горизонт сессии симуляции достигнут"
        for entry in log_response.json()["entries"]
    )
    assert reset_response.status_code == 200


def test_simulation_session_speed_endpoint_rejects_unknown_speed() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/simulation/session/speed",
            json={"playback_speed": 3.0},
        )

    assert response.status_code == 409
    assert "Unsupported playback speed" in response.json()["detail"]


def test_run_simulation_endpoint_returns_conflict_while_session_is_running() -> None:
    payload = {
        "outdoor_temp_c": -16,
        "airflow_m3_h": 3400,
        "supply_temp_setpoint_c": 21,
        "heat_recovery_efficiency": 0.6,
        "heater_power_kw": 36,
        "filter_contamination": 0.2,
        "fan_speed_ratio": 1.0,
        "room_temp_c": 21,
        "room_heat_gain_kw": 4,
    }

    with TestClient(create_app()) as client:
        prepare_response = client.post("/simulation/run", json=payload)
        start_response = client.post("/simulation/session/start")
        conflict_response = client.post("/simulation/run", json=payload)
        reset_response = client.post("/simulation/session/reset")

    assert prepare_response.status_code == 200
    assert start_response.status_code == 200
    assert conflict_response.status_code == 409
    assert "running" in conflict_response.json()["detail"]
    assert reset_response.status_code == 200


def test_visualization_state_endpoint_returns_signal_map() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/visualization/state")

    body = response.json()
    assert response.status_code == 200
    assert body["bindings_version"] == 2
    assert body["status"] in {"normal", "warning", "alarm"}
    assert "filter_bank" in body["nodes"]
    assert "flow_fan_to_room" in body["flows"]


def test_browser_profile_endpoint_returns_verified_demo_environment() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/visualization/browser-profile")

    body = response.json()
    assert response.status_code == 200
    assert body["profile_id"] == "phase7-webgl-demo-profile-2026-04-04"
    assert body["overall_status"] == "normal"
    assert body["passed_requirements"] == body["total_requirements"] == 8
    assert body["verified_environment"]["webgl2_supported"] is True
    assert body["recommended_viewport"]["min_width"] == 1200


def test_validation_matrix_endpoint_returns_reference_cases() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/validation/matrix")

    body = response.json()
    assert response.status_code == 200
    assert body["total_cases"] == 5
    assert body["passed_cases"] == 5
    assert body["all_passed"] is True
    assert body["agreement"]["agreement_id"] == "p1-quality-2026-04-04"
    assert len(body["cases"]) == 5
    assert body["cases"][0]["metrics"]
    assert body["cases"][0]["alarms"]["passed"] is True


def test_validation_agreement_endpoint_returns_case_and_step_contracts() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/validation/agreement")

    body = response.json()
    assert response.status_code == 200
    assert body["agreement_id"] == "p1-quality-2026-04-04"
    assert body["status"] == "normal"
    assert body["total_cases"] == 5
    assert body["total_steps"] == 9
    assert body["control_points"][0]["metrics"][0]["metric_id"] == "supply_temp_c"
    assert body["manual_steps"][0]["tolerance"] == 0.01


def test_validation_basis_endpoint_returns_traceability() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/validation/basis")

    body = response.json()
    assert response.status_code == 200
    assert body["total_sources"] == 4
    assert body["traced_manual_steps"] == 9
    assert body["traced_reference_cases"] == 5
    assert body["agreement"]["agreement_id"] == "p1-quality-2026-04-04"
    assert body["sources"][0]["source_id"] == "doe_whole_house_ventilation"
    assert body["manual_steps"][0]["item_id"] == "actual_airflow_m3_h"
    assert body["reference_cases"][0]["item_id"] == "winter_supply_heating"


def test_validation_manual_check_endpoint_returns_formula_comparison() -> None:
    payload = {
        "outdoor_temp_c": -22,
        "airflow_m3_h": 3600,
        "supply_temp_setpoint_c": 21,
        "heat_recovery_efficiency": 0.62,
        "heater_power_kw": 42,
        "filter_contamination": 0.22,
        "fan_speed_ratio": 1.0,
        "room_temp_c": 20.5,
        "room_heat_gain_kw": 3.5,
    }

    with TestClient(create_app()) as client:
        response = client.post("/validation/manual-check", json=payload)

    body = response.json()
    assert response.status_code == 200
    assert body["all_passed"] is True
    assert body["total_steps"] == 9
    assert body["passed_steps"] == 9
    assert body["subject_name"] == "Пользовательский режим"
    assert body["matched_reference_case_id"] == "winter_supply_heating"
    assert body["agreement"]["agreement_id"] == "p1-quality-2026-04-04"
    assert body["steps"][0]["step_id"] == "actual_airflow_m3_h"
    assert body["steps"][0]["tolerance"] == 0.01
    assert body["steps"][0]["passed"] is True


def test_run_simulation_endpoint_rejects_invalid_airflow() -> None:
    payload = {
        "airflow_m3_h": 50,
    }

    with TestClient(create_app()) as client:
        response = client.post("/simulation/run", json=payload)

    assert response.status_code == 422
    assert any(
        error["loc"] == ["body", "airflow_m3_h"] for error in response.json()["detail"]
    )


def test_unknown_scenario_returns_not_found() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/scenarios/unknown/run")

    assert response.status_code == 404


def _write_demo_package_fixture(project_root: Path) -> None:
    _write_file(project_root / "README.md", "# Demo\n")
    _write_file(project_root / "requirements.txt", "fastapi\n")
    _write_file(project_root / "config" / "defaults.yaml", "default_scenario_id: midseason\n")
    _write_file(project_root / "config" / "p0_baseline.yaml", "baseline_version: 1\nsubject:\n  subject_id: demo\n  title: Demo\n  scope_summary: Demo\n  note: Demo\n")
    _write_file(project_root / "data" / "scenarios" / "presets.json", "{}\n")
    _write_file(project_root / "data" / "validation" / "reference_points.json", "[]\n")
    _write_file(project_root / "data" / "validation" / "reference_basis.json", "[]\n")
    _write_file(project_root / "data" / "validation" / "validation_agreement.json", "{}\n")
    _write_file(project_root / "data" / "visualization" / "scene3d.json", "{}\n")
    _write_file(
        project_root / "data" / "visualization" / "browser_capability_profile.json",
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
    _write_file(project_root / "deploy" / "run-local.ps1", "Write-Host 'run'\n")
    _write_file(project_root / "deploy" / "build-demo-package.ps1", "Write-Host 'package'\n")
    _write_file(project_root / "deploy" / "README.md", "# deploy\n")
    _write_file(project_root / "docs" / "05_execution_phases.md", "# phases\n")
    _write_file(project_root / "docs" / "06_todo.md", "# todo\n")
    _write_file(project_root / "docs" / "19_p0_baseline.md", "# p0\n")
    _write_file(project_root / "docs" / "14_defense_pack.md", "# defense\n")
    _write_file(project_root / "docs" / "15_demo_readiness.md", "# readiness\n")
    _write_file(project_root / "docs" / "16_demo_package.md", "# package\n")
    _write_file(project_root / "docs" / "17_scenario_archive.md", "# archive doc\n")
    _write_file(project_root / "docs" / "18_export_pack.md", "# export doc\n")
    _write_file(project_root / "src" / "app" / "__init__.py", '"""app"""\n')
    _write_file(project_root / "tests" / "unit" / ".keep", "")
    _write_file(project_root / "tests" / "integration" / ".keep", "")
    _write_file(project_root / "tests" / "scenario" / ".keep", "")
    _write_file(project_root / "artifacts" / "playwright" / "README.md", "# playwright\n")
    _write_file(project_root / "artifacts" / "playwright" / "manual" / "2026-04-04" / "dashboard" / "core" / "01.png", "png")
    _write_file(project_root / "artifacts" / "playwright" / "manual" / "2026-04-04" / "dashboard" / "browser-diagnostics" / "01.png", "png")
    _write_file(project_root / "artifacts" / "demo-packages" / "README.md", "# packages\n")
    _write_file(project_root / "artifacts" / "event-log" / "README.md", "# event log\n")
    _write_file(project_root / "artifacts" / "scenario-archive" / "README.md", "# archive\n")
    _write_file(project_root / "artifacts" / "exports" / "README.md", "# exports\n")


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
