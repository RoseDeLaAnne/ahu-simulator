from pathlib import Path

from app.services.simulation_service import SimulationService
from app.services.trend_service import TrendService
from app.simulation.scenarios import load_scenarios
from app.simulation.state import OperationStatus
from app.ui.scene.bindings import load_scene_bindings
from app.ui.viewmodels.visualization import build_visualization_signal_map


def _build_service() -> SimulationService:
    scenario_path = Path(__file__).resolve().parents[2] / "data" / "scenarios" / "presets.json"
    return SimulationService(
        scenarios=load_scenarios(scenario_path),
        trend_service=TrendService(),
        default_scenario_id="midseason",
    )


def test_visualization_signal_map_contains_stable_visual_ids() -> None:
    service = _build_service()
    result = service.run_scenario("winter")

    signals = build_visualization_signal_map(
        result,
        bindings_version=load_scene_bindings().version,
    )

    assert signals.status == result.state.status
    assert signals.all_visual_ids() == {
        "outdoor_air",
        "filter_bank",
        "heater_coil",
        "supply_fan",
        "supply_duct",
        "room_zone",
        "sensor_outdoor_temp",
        "sensor_filter_pressure",
        "sensor_supply_temp",
        "sensor_airflow",
        "sensor_room_temp",
        "flow_outdoor_to_filter",
        "flow_filter_to_heater",
        "flow_heater_to_fan",
        "flow_fan_to_room",
    }


def test_visualization_signal_map_marks_filter_alarm() -> None:
    service = _build_service()
    result = service.run_scenario("dirty_filter")

    signals = build_visualization_signal_map(result)

    assert "FILTER_SERVICE_NOW" in signals.active_alarm_codes
    assert signals.nodes["filter_bank"].state == OperationStatus.ALARM
    assert signals.sensors["sensor_filter_pressure"].state == OperationStatus.ALARM


def test_scene_bindings_cover_visualization_signals() -> None:
    service = _build_service()
    result = service.run_scenario("midseason")
    signals = build_visualization_signal_map(
        result,
        bindings_version=load_scene_bindings().version,
    )
    bindings = load_scene_bindings()

    assert bindings.version == signals.bindings_version
    assert {binding.visual_id for binding in bindings.bindings} == signals.all_visual_ids()


def test_visualization_signal_map_builds_room_sensors_from_room_context() -> None:
    service = _build_service()
    result = service.run_scenario("midseason")

    signals = build_visualization_signal_map(
        result,
        room_context={
            "id": "classroom_wing",
            "label": "Учебная аудитория",
            "design_occupancy_people": 32,
            "occupancy_people": 30,
            "local_humidity_percent": 50.0,
            "fresh_air_target_l_s_per_person": 14.0,
            "outdoor_co2_ppm": 430,
            "active_preset": {"label": "Полная аудитория"},
        },
    )

    assert signals.room_sensors["sensor_room_co2"].label == "CO₂ помещения"
    assert "ppm" in signals.room_sensors["sensor_room_co2"].value
    assert signals.room_sensors["sensor_room_humidity"].value.endswith("%")
    assert signals.room_sensors["sensor_room_occupancy"].value.endswith("чел.")
    assert signals.room_story is not None
