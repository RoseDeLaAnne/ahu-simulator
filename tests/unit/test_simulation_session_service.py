from pathlib import Path

import pytest

from app.infrastructure.runtime_paths import RuntimePathResolver
from app.services.simulation_service import (
    ALLOWED_PLAYBACK_SPEEDS,
    SimulationService,
    SimulationSessionTransitionError,
)
from app.services.simulation_session_store import SimulationSessionStore
from app.services.trend_service import TrendService
from app.simulation.parameters import SimulationParameters
from app.simulation.scenarios import load_scenarios
from app.simulation.state import SimulationSessionStatus


def _build_service(
    session_store: SimulationSessionStore | None = None,
) -> SimulationService:
    scenario_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "scenarios"
        / "presets.json"
    )
    return SimulationService(
        scenarios=load_scenarios(scenario_path),
        trend_service=TrendService(),
        default_scenario_id="midseason",
        session_store=session_store,
    )


def test_session_lifecycle_updates_status_and_history() -> None:
    service = _build_service()
    prepared_session = service.get_session()

    running_session = service.start()
    ticked_session = service.tick()
    paused_session = service.pause()
    reset_session = service.reset()

    assert prepared_session.status == SimulationSessionStatus.IDLE
    assert prepared_session.playback_speed == 1.0
    assert prepared_session.max_ticks == 12
    assert prepared_session.horizon_reached is False
    assert prepared_session.completed_at is None
    assert prepared_session.actions.can_resume is False
    assert prepared_session.actions.can_set_speed is True
    assert running_session.status == SimulationSessionStatus.RUNNING
    assert running_session.last_command == "start"
    assert ticked_session.status == SimulationSessionStatus.RUNNING
    assert ticked_session.elapsed_minutes == ticked_session.step_minutes
    assert ticked_session.tick_count == 1
    assert len(ticked_session.history.points) == 2
    assert ticked_session.trace[-1].command == "tick"
    assert paused_session.status == SimulationSessionStatus.PAUSED
    assert paused_session.actions.can_resume is True
    assert reset_session.status == SimulationSessionStatus.IDLE
    assert reset_session.last_command == "reset"
    assert reset_session.tick_count == 0
    assert reset_session.elapsed_minutes == 0
    assert len(reset_session.history.points) == 1
    assert reset_session.session_id != prepared_session.session_id


def test_manual_tick_from_idle_advances_once_and_leaves_session_paused() -> None:
    service = _build_service()

    session = service.tick()

    assert session.status == SimulationSessionStatus.PAUSED
    assert session.tick_count == 1
    assert session.elapsed_minutes == session.step_minutes
    assert len(session.history.points) == 2


def test_run_is_rejected_while_session_is_running() -> None:
    service = _build_service()
    service.start()

    with pytest.raises(SimulationSessionTransitionError):
        service.run(
            SimulationParameters(
                outdoor_temp_c=-10.0,
                airflow_m3_h=3200.0,
                supply_temp_setpoint_c=20.0,
                step_minutes=5,
            )
        )


def test_session_completes_at_horizon_and_blocks_extra_ticks() -> None:
    service = _build_service()
    service.run(
        SimulationParameters(
            horizon_minutes=12,
            step_minutes=5,
        )
    )
    service.start()

    service.tick()
    service.tick()
    completed_session = service.tick()

    assert completed_session.status == SimulationSessionStatus.COMPLETED
    assert completed_session.elapsed_minutes == 12
    assert completed_session.tick_count == 3
    assert completed_session.max_ticks == 3
    assert completed_session.horizon_reached is True
    assert completed_session.completed_at is not None
    assert completed_session.last_command == "completed"
    assert completed_session.actions.can_start is False
    assert completed_session.actions.can_tick is False
    assert completed_session.actions.can_set_speed is False
    assert [point.minute for point in completed_session.history.points] == [0, 5, 10, 12]
    assert completed_session.trace[-2].command == "tick"
    assert completed_session.trace[-1].command == "completed"

    with pytest.raises(SimulationSessionTransitionError):
        service.tick()


def test_playback_speed_uses_allowed_catalog() -> None:
    service = _build_service()

    for speed in ALLOWED_PLAYBACK_SPEEDS:
        session = service.set_playback_speed(speed)
        assert session.playback_speed == speed
        assert session.last_command == "speed"

    with pytest.raises(SimulationSessionTransitionError):
        service.set_playback_speed(3.0)


def test_runtime_store_restores_valid_active_session(tmp_path: Path) -> None:
    path_resolver = RuntimePathResolver(tmp_path)
    session_store = SimulationSessionStore(tmp_path, path_resolver)
    service = _build_service(session_store)

    service.start()
    service.tick()
    service.set_playback_speed(2.0)

    restored_service = _build_service(session_store)
    restored_session = restored_service.get_session()

    assert restored_session.status == SimulationSessionStatus.RUNNING
    assert restored_session.tick_count == 1
    assert restored_session.playback_speed == 2.0
    assert restored_session.session_id == service.get_session().session_id
    assert session_store.file_path.exists()


def test_runtime_store_drops_corrupt_session_file(tmp_path: Path) -> None:
    path_resolver = RuntimePathResolver(tmp_path)
    session_store = SimulationSessionStore(tmp_path, path_resolver)
    session_store.file_path.parent.mkdir(parents=True, exist_ok=True)
    session_store.file_path.write_text("{not-json", encoding="utf-8")

    service = _build_service(session_store)
    session = service.get_session()

    assert session.status == SimulationSessionStatus.IDLE
    assert session.tick_count == 0
    assert not session_store.file_path.exists()
