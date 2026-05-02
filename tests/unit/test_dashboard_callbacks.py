from pathlib import Path

from app.services.simulation_service import SimulationService
from app.services.comparison_service import RunComparisonService
from app.services.scenario_archive_service import ScenarioArchiveService
from app.services.scenario_preset_service import ScenarioPresetService
from app.services.trend_service import TrendService
from app.simulation.scenarios import load_scenarios
from app.simulation.state import SimulationSessionStatus
from app.ui.callbacks import (
    _build_run_comparison_interpretation,
    _build_run_comparison_top_delta_items,
    _build_session_status_badge,
    _build_session_summary_text,
    _comparison_source_label,
    _format_session_elapsed,
    _format_session_ticks,
    _resolve_preset_shortcut,
    _run_dashboard_simulation,
    _scenario_selection_options,
    _session_interval_ms,
)
from app.ui.layout import _format_scenario_metadata


def _build_service() -> SimulationService:
    scenario_path = Path(__file__).resolve().parents[2] / "data" / "scenarios" / "presets.json"
    return SimulationService(
        scenarios=load_scenarios(scenario_path),
        trend_service=TrendService(),
        default_scenario_id="midseason",
    )


def _build_preset_service(tmp_path: Path) -> SimulationService:
    scenario_path = Path(__file__).resolve().parents[2] / "data" / "scenarios" / "presets.json"
    preset_service = ScenarioPresetService(
        system_preset_path=scenario_path,
        project_root=tmp_path,
    )
    return SimulationService(
        scenarios=load_scenarios(scenario_path),
        trend_service=TrendService(),
        default_scenario_id="midseason",
        scenario_preset_service=preset_service,
    )


def test_dashboard_scenario_selection_preserves_scenario_id() -> None:
    service = _build_service()
    scenario_map = {scenario.id: scenario for scenario in service.list_scenarios()}

    result = _run_dashboard_simulation(
        service=service,
        scenario_map=scenario_map,
        selected_scenario_id="winter",
        parameters=scenario_map["winter"].parameters,
        triggered_id="scenario-select",
    )

    assert result.scenario_id == "winter"
    assert result.parameter_source == "preset"


def test_dashboard_manual_change_clears_scenario_id() -> None:
    service = _build_service()
    scenario_map = {scenario.id: scenario for scenario in service.list_scenarios()}
    custom_parameters = scenario_map["winter"].parameters.model_copy(
        update={"fan_speed_ratio": 0.95}
    )

    result = _run_dashboard_simulation(
        service=service,
        scenario_map=scenario_map,
        selected_scenario_id="winter",
        parameters=custom_parameters,
        triggered_id="fan-speed",
    )

    assert result.scenario_id is None
    assert result.parameter_source == "manual"


def test_dashboard_step_change_clears_scenario_id() -> None:
    service = _build_service()
    scenario_map = {scenario.id: scenario for scenario in service.list_scenarios()}
    custom_parameters = scenario_map["winter"].parameters.model_copy(
        update={"step_minutes": 5}
    )

    result = _run_dashboard_simulation(
        service=service,
        scenario_map=scenario_map,
        selected_scenario_id="winter",
        parameters=custom_parameters,
        triggered_id="step-minutes",
    )

    assert result.scenario_id is None
    assert result.parameter_source == "manual"


def test_resolve_preset_shortcut_maps_supported_buttons() -> None:
    assert _resolve_preset_shortcut("preset-shortcut-winter") == "winter"
    assert _resolve_preset_shortcut("preset-shortcut-summer") == "summer"
    assert _resolve_preset_shortcut("preset-shortcut-peak-load") == "peak_load"


def test_resolve_preset_shortcut_returns_none_for_unknown_button() -> None:
    assert _resolve_preset_shortcut("scenario-select") is None
    assert _resolve_preset_shortcut(None) is None


def test_dashboard_scenario_options_include_user_preset_metadata(tmp_path: Path) -> None:
    service = _build_preset_service(tmp_path)
    created = service.create_user_preset(
        title="Ночной режим",
        parameters=service.get_scenario("winter").parameters,
        preset_id="night_mode",
    )

    options = _scenario_selection_options(service)
    labels = {option["value"]: option["label"] for option in options}

    assert "system" not in labels["winter"]
    assert "системный" in labels["winter"]
    assert "только чтение" in labels["winter"]
    assert "пользовательский" in labels["night_mode"]
    assert "редактируемый" in labels["night_mode"]
    assert "можно редактировать" in _format_scenario_metadata(created)


def test_dashboard_session_helpers_show_progress_speed_and_completed_state() -> None:
    service = _build_service()
    service.start()
    service.tick()
    session = service.set_playback_speed(2.0)

    assert _format_session_elapsed(session) == "10 / 120 мин"
    assert _format_session_ticks(session) == "1 / 12"
    assert _session_interval_ms(session.playback_speed) == 500
    assert _build_session_status_badge(session.status) == (
        "Выполняется",
        "status-pill status-info",
    )

    completed_session = session.model_copy(
        update={
            "status": SimulationSessionStatus.COMPLETED,
            "horizon_reached": True,
        }
    )

    assert _build_session_status_badge(completed_session.status) == (
        "Завершено",
        "status-pill status-normal",
    )
    assert "Горизонт достигнут" in _build_session_summary_text(completed_session)


def test_dashboard_comparison_helpers_show_labels_and_top_deltas(tmp_path: Path) -> None:
    service = _build_service()
    archive_service = ScenarioArchiveService(project_root=tmp_path)
    comparison_service = RunComparisonService(
        project_root=tmp_path,
        scenario_archive_service=archive_service,
    )
    comparison_service.save_before(service.preview_scenario("winter"), label="До")
    comparison_service.save_after(service.preview_scenario("midseason"), label="После")
    snapshot = comparison_service.build_snapshot(
        service.preview_scenario("midseason"),
        service.get_session(),
    )
    comparison = comparison_service.build_comparison_from_references(
        "snapshot:before",
        "snapshot:after",
        service.preview_scenario("midseason"),
        service.get_session(),
    )

    assert _comparison_source_label(snapshot, "snapshot:before", fallback="x") == "До — До"
    assert "Улучшилось" in _build_run_comparison_interpretation(comparison)
    delta_items = _build_run_comparison_top_delta_items(comparison)
    assert delta_items
    assert "ΔP фильтра" in str(delta_items)
