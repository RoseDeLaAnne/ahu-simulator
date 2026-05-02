from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.simulation.control import ControlDiagnostics
from app.simulation.parameters import ControlMode, SimulationParameters


class AlarmLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class OperationStatus(StrEnum):
    NORMAL = "normal"
    WARNING = "warning"
    ALARM = "alarm"


class ParameterSource(StrEnum):
    MANUAL = "manual"
    PRESET = "preset"


class Alarm(BaseModel):
    code: str
    message: str
    level: AlarmLevel


class TrendPoint(BaseModel):
    minute: int
    outdoor_temp_c: float
    supply_temp_c: float
    room_temp_c: float
    heating_power_kw: float
    total_power_kw: float
    airflow_m3_h: float
    filter_pressure_drop_pa: float


class TrendSeries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    horizon_minutes: int
    step_minutes: int
    points: list[TrendPoint] = Field(default_factory=list)


class SimulationSessionStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class SimulationHistory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_minutes: int
    elapsed_minutes: int
    points: list[TrendPoint] = Field(default_factory=list)


class SimulationSessionActions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    can_start: bool
    can_pause: bool
    can_reset: bool
    can_tick: bool
    can_resume: bool = False
    can_set_speed: bool = True


class SimulationSessionTraceEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    captured_at: datetime
    command: str
    status: SimulationSessionStatus
    elapsed_minutes: int
    tick_count: int
    summary: str


class SimulationState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    control_mode: ControlMode
    actual_airflow_m3_h: float
    mixed_air_temp_c: float
    recovered_air_temp_c: float
    supply_temp_c: float
    room_temp_c: float
    heating_power_kw: float
    heater_load_ratio: float
    fan_power_kw: float
    total_power_kw: float
    energy_intensity_kw_per_1000_m3_h: float
    filter_pressure_drop_pa: float
    heat_balance_kw: float
    status: OperationStatus


class SimulationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    parameter_source: ParameterSource = ParameterSource.MANUAL
    scenario_id: str | None = None
    scenario_title: str | None = None
    parameters: SimulationParameters
    state: SimulationState
    control: ControlDiagnostics | None = None
    alarms: list[Alarm] = Field(default_factory=list)
    trend: TrendSeries


class SimulationSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    status: SimulationSessionStatus
    step_minutes: int
    elapsed_minutes: int
    tick_count: int
    playback_speed: float = 1.0
    max_ticks: int = 0
    horizon_reached: bool = False
    completed_at: datetime | None = None
    last_command: str | None = None
    created_at: datetime
    updated_at: datetime
    current_result: SimulationResult
    history: SimulationHistory
    actions: SimulationSessionActions
    trace: list[SimulationSessionTraceEntry] = Field(default_factory=list)
