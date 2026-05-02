from __future__ import annotations

from math import ceil
from datetime import datetime, timezone
from uuid import uuid4

from app.simulation.alarms import build_alarms, derive_status
from app.simulation.control import build_control_diagnostics
from app.simulation.equations import calculate_operating_point
from app.simulation.parameters import SimulationParameters
from app.simulation.scenarios import ScenarioDefinition
from app.simulation.state import (
    ParameterSource,
    SimulationHistory,
    OperationStatus,
    SimulationResult,
    SimulationSession,
    SimulationSessionActions,
    SimulationSessionTraceEntry,
    SimulationSessionStatus,
    SimulationState,
    TrendPoint,
)
from app.services.simulation_session_store import SimulationSessionStore
from app.services.scenario_preset_service import ScenarioPresetService
from app.services.status_service import StatusService
from app.services.trend_service import TrendService


class SimulationSessionTransitionError(RuntimeError):
    pass


ALLOWED_PLAYBACK_SPEEDS = (0.25, 0.5, 1.0, 2.0, 4.0)


class SimulationService:
    def __init__(
        self,
        scenarios: list[ScenarioDefinition],
        trend_service: TrendService,
        default_scenario_id: str,
        status_service: StatusService | None = None,
        session_store: SimulationSessionStore | None = None,
        scenario_preset_service: ScenarioPresetService | None = None,
    ) -> None:
        self._trend_service = trend_service
        self._scenarios = {scenario.id: scenario for scenario in scenarios}
        self._scenario_preset_service = scenario_preset_service
        self._status_service = status_service or StatusService()
        self._session_store = session_store
        self._last_result: SimulationResult | None = None
        self._session: SimulationSession | None = None
        self._session_seed_result: SimulationResult | None = None
        default_scenario = self.get_scenario(default_scenario_id)
        default_result = self._build_result(default_scenario.parameters, default_scenario)
        self._set_prepared_session(default_result, command="prepare", persist=False)
        self._restore_session()

    def list_scenarios(self) -> list[ScenarioDefinition]:
        if self._scenario_preset_service is not None:
            return self._scenario_preset_service.list_scenarios()
        return list(self._scenarios.values())

    def get_scenario(self, scenario_id: str) -> ScenarioDefinition:
        if self._scenario_preset_service is not None:
            return self._scenario_preset_service.get_scenario(scenario_id)
        if scenario_id not in self._scenarios:
            raise KeyError(f"Scenario '{scenario_id}' not found")
        return self._scenarios[scenario_id]

    def create_user_preset(
        self,
        *,
        title: str,
        parameters: SimulationParameters,
        preset_id: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        expected_effect: str | None = None,
    ) -> ScenarioDefinition:
        preset_service = self._require_scenario_preset_service()
        return preset_service.create_user_preset(
            title=title,
            parameters=parameters,
            preset_id=preset_id,
            description=description,
            purpose=purpose,
            expected_effect=expected_effect,
        )

    def update_user_preset(
        self,
        preset_id: str,
        parameters: SimulationParameters,
    ) -> ScenarioDefinition:
        return self._require_scenario_preset_service().update_user_preset(
            preset_id,
            parameters,
        )

    def rename_user_preset(self, preset_id: str, *, title: str) -> ScenarioDefinition:
        return self._require_scenario_preset_service().rename_user_preset(
            preset_id,
            title=title,
        )

    def delete_user_preset(self, preset_id: str) -> ScenarioDefinition:
        return self._require_scenario_preset_service().delete_user_preset(preset_id)

    def import_user_preset(self, payload: dict[str, object]) -> ScenarioDefinition:
        return self._require_scenario_preset_service().import_user_preset(payload)

    def export_user_preset(self, preset_id: str) -> dict[str, object]:
        return self._require_scenario_preset_service().export_user_preset(preset_id)

    def run(self, parameters: SimulationParameters) -> SimulationResult:
        self._ensure_session_not_running("reconfigure a custom run")
        result = self._build_result(parameters)
        self._set_prepared_session(result)
        return result

    def preview(self, parameters: SimulationParameters) -> SimulationResult:
        return self._build_result(parameters)

    def run_scenario(self, scenario_id: str) -> SimulationResult:
        self._ensure_session_not_running("switch scenarios")
        scenario = self.get_scenario(scenario_id)
        result = self._build_result(scenario.parameters, scenario)
        self._set_prepared_session(result)
        return result

    def preview_scenario(self, scenario_id: str) -> SimulationResult:
        scenario = self.get_scenario(scenario_id)
        return self._build_result(scenario.parameters, scenario)

    def start(self) -> SimulationSession:
        session = self.get_session()
        if session.status == SimulationSessionStatus.RUNNING:
            raise SimulationSessionTransitionError("Simulation session is already running")
        if session.horizon_reached or session.status == SimulationSessionStatus.COMPLETED:
            raise SimulationSessionTransitionError(
                "Completed simulation session must be reset before it can be started"
            )
        now = datetime.now(timezone.utc)
        command = (
            "resume"
            if session.status == SimulationSessionStatus.PAUSED
            else "start"
        )
        self._set_session(
            session.model_copy(
                update={
                    "status": SimulationSessionStatus.RUNNING,
                    "updated_at": now,
                    "last_command": command,
                    "trace": self._append_trace(
                        session,
                        command,
                        SimulationSessionStatus.RUNNING,
                        now,
                    ),
                    "actions": self._build_actions(
                        SimulationSessionStatus.RUNNING,
                        session.tick_count,
                        session.max_ticks,
                    ),
                }
            )
        )
        return self.get_session()

    def pause(self) -> SimulationSession:
        session = self.get_session()
        if session.status != SimulationSessionStatus.RUNNING:
            raise SimulationSessionTransitionError("Only a running simulation session can be paused")
        now = datetime.now(timezone.utc)
        self._set_session(
            session.model_copy(
                update={
                    "status": SimulationSessionStatus.PAUSED,
                    "updated_at": now,
                    "last_command": "pause",
                    "trace": self._append_trace(
                        session,
                        "pause",
                        SimulationSessionStatus.PAUSED,
                        now,
                    ),
                    "actions": self._build_actions(
                        SimulationSessionStatus.PAUSED,
                        session.tick_count,
                        session.max_ticks,
                    ),
                }
            )
        )
        return self.get_session()

    def reset(self) -> SimulationSession:
        seed_result = self._require_session_seed_result()
        scenario = self._resolve_scenario(seed_result.scenario_id)
        fresh_result = self._build_result(seed_result.parameters, scenario)
        self._set_prepared_session(fresh_result, command="reset")
        return self.get_session()

    def tick(self) -> SimulationSession:
        session = self.get_session()
        if session.status == SimulationSessionStatus.COMPLETED or session.horizon_reached:
            raise SimulationSessionTransitionError(
                "Completed simulation session cannot advance beyond its horizon"
            )
        if session.tick_count >= session.max_ticks:
            completed_session = self._complete_session(session)
            self._set_session(completed_session)
            return self.get_session()

        current_result = session.current_result
        scenario = self._resolve_scenario(current_result.scenario_id)
        next_parameters = current_result.parameters.model_copy(
            update={"room_temp_c": current_result.state.room_temp_c}
        )
        next_result = self._build_result(next_parameters, scenario)
        next_elapsed_minutes = min(
            session.elapsed_minutes + session.step_minutes,
            current_result.parameters.horizon_minutes,
        )
        next_tick_count = session.tick_count + 1
        horizon_reached = (
            next_tick_count >= session.max_ticks
            or next_elapsed_minutes >= current_result.parameters.horizon_minutes
        )
        next_status = self._status_after_tick(session.status, horizon_reached)
        completed_at = next_result.timestamp if horizon_reached else None
        next_history = session.history.model_copy(
            update={
                "elapsed_minutes": next_elapsed_minutes,
                "points": [
                    *session.history.points,
                    self._build_history_point(next_result, next_elapsed_minutes),
                ],
            }
        )
        self._set_session(
            session.model_copy(
                update={
                    "status": next_status,
                    "elapsed_minutes": next_elapsed_minutes,
                    "tick_count": next_tick_count,
                    "horizon_reached": horizon_reached,
                    "completed_at": completed_at,
                    "last_command": "completed" if horizon_reached else "tick",
                    "updated_at": next_result.timestamp,
                    "current_result": next_result,
                    "history": next_history,
                    "trace": self._append_tick_trace(
                        session,
                        next_status,
                        next_result.timestamp,
                        next_elapsed_minutes,
                        next_tick_count,
                        horizon_reached,
                    ),
                    "actions": self._build_actions(
                        next_status,
                        next_tick_count,
                        session.max_ticks,
                    ),
                }
            )
        )
        return self.get_session()

    def set_playback_speed(self, speed: float) -> SimulationSession:
        normalized_speed = float(speed)
        if normalized_speed not in ALLOWED_PLAYBACK_SPEEDS:
            allowed_values = ", ".join(str(value).rstrip("0").rstrip(".") for value in ALLOWED_PLAYBACK_SPEEDS)
            raise SimulationSessionTransitionError(
                f"Unsupported playback speed {speed}. Allowed values: {allowed_values}"
            )

        session = self.get_session()
        if not session.actions.can_set_speed:
            raise SimulationSessionTransitionError(
                "Playback speed cannot be changed after the session is completed"
            )

        now = datetime.now(timezone.utc)
        self._set_session(
            session.model_copy(
                update={
                    "playback_speed": normalized_speed,
                    "updated_at": now,
                    "last_command": "speed",
                    "trace": self._append_trace(
                        session,
                        "speed",
                        session.status,
                        now,
                        summary=f"Скорость воспроизведения: x{normalized_speed:g}.",
                    ),
                    "actions": self._build_actions(
                        session.status,
                        session.tick_count,
                        session.max_ticks,
                    ),
                }
            )
        )
        return self.get_session()

    def get_state(self) -> SimulationResult:
        assert self._last_result is not None
        return self._last_result

    def get_session(self) -> SimulationSession:
        assert self._session is not None
        return self._session

    def get_trends(self):
        return self.get_state().trend

    def _set_prepared_session(
        self,
        result: SimulationResult,
        *,
        command: str = "prepare",
        persist: bool = True,
    ) -> None:
        session = self._create_session(result, command)
        self._session_seed_result = result
        self._set_session(session, persist=persist)

    def _set_session(self, session: SimulationSession, *, persist: bool = True) -> None:
        self._session = session
        self._last_result = session.current_result
        if persist:
            self._persist_session(session)

    def _create_session(
        self,
        result: SimulationResult,
        command: str,
    ) -> SimulationSession:
        max_ticks = self._calculate_max_ticks(result.parameters)
        trace_timestamp = datetime.now(timezone.utc)
        return SimulationSession(
            session_id=f"sim-{uuid4().hex[:12]}",
            status=SimulationSessionStatus.IDLE,
            step_minutes=result.parameters.step_minutes,
            elapsed_minutes=0,
            tick_count=0,
            playback_speed=1.0,
            max_ticks=max_ticks,
            horizon_reached=False,
            completed_at=None,
            last_command=command,
            created_at=result.timestamp,
            updated_at=result.timestamp,
            current_result=result,
            history=SimulationHistory(
                step_minutes=result.parameters.step_minutes,
                elapsed_minutes=0,
                points=[self._build_history_point(result, 0)],
            ),
            actions=self._build_actions(SimulationSessionStatus.IDLE, 0, max_ticks),
            trace=[
                SimulationSessionTraceEntry(
                    captured_at=trace_timestamp,
                    command=command,
                    status=SimulationSessionStatus.IDLE,
                    elapsed_minutes=0,
                    tick_count=0,
                    summary=self._trace_summary(command, SimulationSessionStatus.IDLE, 0, 0),
                )
            ],
        )

    def _build_actions(
        self,
        status: SimulationSessionStatus,
        tick_count: int,
        max_ticks: int,
    ) -> SimulationSessionActions:
        horizon_reached = tick_count >= max_ticks
        return SimulationSessionActions(
            can_start=(
                status != SimulationSessionStatus.RUNNING
                and status != SimulationSessionStatus.COMPLETED
                and not horizon_reached
            ),
            can_pause=status == SimulationSessionStatus.RUNNING,
            can_reset=status != SimulationSessionStatus.IDLE or tick_count > 0,
            can_tick=(
                status != SimulationSessionStatus.RUNNING
                and status != SimulationSessionStatus.COMPLETED
                and not horizon_reached
            ),
            can_resume=(
                status == SimulationSessionStatus.PAUSED
                and not horizon_reached
            ),
            can_set_speed=status != SimulationSessionStatus.COMPLETED,
        )

    def _build_history_point(
        self,
        result: SimulationResult,
        minute: int,
    ) -> TrendPoint:
        state = result.state
        return TrendPoint(
            minute=minute,
            outdoor_temp_c=result.parameters.outdoor_temp_c,
            supply_temp_c=state.supply_temp_c,
            room_temp_c=state.room_temp_c,
            heating_power_kw=state.heating_power_kw,
            total_power_kw=state.total_power_kw,
            airflow_m3_h=state.actual_airflow_m3_h,
            filter_pressure_drop_pa=state.filter_pressure_drop_pa,
        )

    def _require_session_seed_result(self) -> SimulationResult:
        assert self._session_seed_result is not None
        return self._session_seed_result

    def _resolve_scenario(
        self,
        scenario_id: str | None,
    ) -> ScenarioDefinition | None:
        if scenario_id is None:
            return None
        try:
            return self.get_scenario(scenario_id)
        except KeyError:
            return None

    def _require_scenario_preset_service(self) -> ScenarioPresetService:
        if self._scenario_preset_service is None:
            raise RuntimeError("User preset service is not configured")
        return self._scenario_preset_service

    def _ensure_session_not_running(self, action: str) -> None:
        if (
            self._session is not None
            and self._session.status == SimulationSessionStatus.RUNNING
        ):
            raise SimulationSessionTransitionError(
                f"Cannot {action} while the simulation session is running"
            )

    def _calculate_max_ticks(self, parameters: SimulationParameters) -> int:
        return max(1, ceil(parameters.horizon_minutes / parameters.step_minutes))

    def _status_after_tick(
        self,
        current_status: SimulationSessionStatus,
        horizon_reached: bool,
    ) -> SimulationSessionStatus:
        if horizon_reached:
            return SimulationSessionStatus.COMPLETED
        if current_status == SimulationSessionStatus.RUNNING:
            return SimulationSessionStatus.RUNNING
        return SimulationSessionStatus.PAUSED

    def _complete_session(self, session: SimulationSession) -> SimulationSession:
        now = datetime.now(timezone.utc)
        return session.model_copy(
            update={
                "status": SimulationSessionStatus.COMPLETED,
                "horizon_reached": True,
                "completed_at": session.completed_at or now,
                "updated_at": now,
                "last_command": "completed",
                "trace": self._append_trace(
                    session,
                    "completed",
                    SimulationSessionStatus.COMPLETED,
                    now,
                ),
                "actions": self._build_actions(
                    SimulationSessionStatus.COMPLETED,
                    session.tick_count,
                    session.max_ticks,
                ),
            }
        )

    def _append_tick_trace(
        self,
        session: SimulationSession,
        status: SimulationSessionStatus,
        captured_at: datetime,
        elapsed_minutes: int,
        tick_count: int,
        horizon_reached: bool,
    ) -> list[SimulationSessionTraceEntry]:
        trace = [
            *session.trace,
            SimulationSessionTraceEntry(
                captured_at=captured_at,
                command="tick",
                status=status,
                elapsed_minutes=elapsed_minutes,
                tick_count=tick_count,
                summary=self._trace_summary("tick", status, elapsed_minutes, tick_count),
            ),
        ]
        if horizon_reached:
            trace.append(
                SimulationSessionTraceEntry(
                    captured_at=captured_at,
                    command="completed",
                    status=SimulationSessionStatus.COMPLETED,
                    elapsed_minutes=elapsed_minutes,
                    tick_count=tick_count,
                    summary=self._trace_summary(
                        "completed",
                        SimulationSessionStatus.COMPLETED,
                        elapsed_minutes,
                        tick_count,
                    ),
                )
            )
        return trace[-100:]

    def _append_trace(
        self,
        session: SimulationSession,
        command: str,
        status: SimulationSessionStatus,
        captured_at: datetime,
        *,
        summary: str | None = None,
    ) -> list[SimulationSessionTraceEntry]:
        return [
            *session.trace,
            SimulationSessionTraceEntry(
                captured_at=captured_at,
                command=command,
                status=status,
                elapsed_minutes=session.elapsed_minutes,
                tick_count=session.tick_count,
                summary=summary
                or self._trace_summary(
                    command,
                    status,
                    session.elapsed_minutes,
                    session.tick_count,
                ),
            ),
        ][-100:]

    def _trace_summary(
        self,
        command: str,
        status: SimulationSessionStatus,
        elapsed_minutes: int,
        tick_count: int,
    ) -> str:
        command_labels = {
            "prepare": "Сессия подготовлена",
            "scenario": "Сценарий подготовлен",
            "configure": "Параметры обновлены",
            "start": "Сессия запущена",
            "resume": "Сессия продолжена",
            "pause": "Сессия поставлена на паузу",
            "tick": "Выполнен шаг симуляции",
            "reset": "Сессия сброшена",
            "completed": "Горизонт симуляции достигнут",
            "speed": "Скорость обновлена",
        }
        label = command_labels.get(command, command)
        return (
            f"{label}: статус {status.value}, "
            f"{elapsed_minutes} мин, тик {tick_count}."
        )

    def _persist_session(self, session: SimulationSession) -> None:
        if self._session_store is None:
            return
        if (
            session.status == SimulationSessionStatus.IDLE
            and session.tick_count == 0
        ):
            self._session_store.clear()
            return
        self._session_store.save(session, self._require_session_seed_result())

    def _restore_session(self) -> None:
        if self._session_store is None:
            return
        stored = self._session_store.load()
        if stored is None:
            return
        if not self._is_restorable_session(stored.session, stored.seed_result):
            self._session_store.clear()
            return
        self._session_seed_result = stored.seed_result
        self._set_session(
            self._normalize_restored_session(stored.session),
            persist=False,
        )

    def _is_restorable_session(
        self,
        session: SimulationSession,
        seed_result: SimulationResult,
    ) -> bool:
        return all(
            [
                session.step_minutes == session.current_result.parameters.step_minutes,
                session.history.step_minutes == session.step_minutes,
                session.max_ticks == self._calculate_max_ticks(
                    session.current_result.parameters
                ),
                session.tick_count <= session.max_ticks,
                session.elapsed_minutes <= session.current_result.parameters.horizon_minutes,
                seed_result.parameters.step_minutes == session.step_minutes,
            ]
        )

    def _normalize_restored_session(
        self,
        session: SimulationSession,
    ) -> SimulationSession:
        max_ticks = self._calculate_max_ticks(session.current_result.parameters)
        horizon_reached = (
            session.tick_count >= max_ticks
            or session.elapsed_minutes >= session.current_result.parameters.horizon_minutes
        )
        status = (
            SimulationSessionStatus.COMPLETED
            if horizon_reached
            else session.status
        )
        completed_at = session.completed_at
        if status == SimulationSessionStatus.COMPLETED and completed_at is None:
            completed_at = datetime.now(timezone.utc)
        return session.model_copy(
            update={
                "status": status,
                "max_ticks": max_ticks,
                "horizon_reached": horizon_reached,
                "completed_at": completed_at,
                "actions": self._build_actions(status, session.tick_count, max_ticks),
            }
        )

    def _build_result(
        self,
        parameters: SimulationParameters,
        scenario: ScenarioDefinition | None = None,
    ) -> SimulationResult:
        timestamp = datetime.now(timezone.utc)
        operating_point = calculate_operating_point(parameters, parameters.step_minutes)
        control = build_control_diagnostics(parameters, operating_point)
        provisional_state = SimulationState(
            timestamp=timestamp,
            control_mode=parameters.control_mode,
            actual_airflow_m3_h=operating_point.actual_airflow_m3_h,
            mixed_air_temp_c=operating_point.mixed_air_temp_c,
            recovered_air_temp_c=operating_point.recovered_air_temp_c,
            supply_temp_c=operating_point.supply_temp_c,
            room_temp_c=operating_point.room_temp_c,
            heating_power_kw=operating_point.heating_power_kw,
            heater_load_ratio=operating_point.heater_load_ratio,
            fan_power_kw=operating_point.fan_power_kw,
            total_power_kw=operating_point.total_power_kw,
            energy_intensity_kw_per_1000_m3_h=operating_point.energy_intensity_kw_per_1000_m3_h,
            filter_pressure_drop_pa=operating_point.filter_pressure_drop_pa,
            heat_balance_kw=operating_point.heat_balance_kw,
            status=OperationStatus.NORMAL,
        )
        alarms = build_alarms(
            parameters,
            provisional_state,
            self._status_service.thresholds,
        )
        state = provisional_state.model_copy(update={"status": derive_status(alarms)})
        trend = self._trend_service.generate(parameters)
        return SimulationResult(
            timestamp=timestamp,
            parameter_source=(
                ParameterSource.PRESET if scenario is not None else ParameterSource.MANUAL
            ),
            scenario_id=scenario.id if scenario else None,
            scenario_title=scenario.title if scenario else None,
            parameters=parameters,
            state=state,
            control=control,
            alarms=alarms,
            trend=trend,
        )
