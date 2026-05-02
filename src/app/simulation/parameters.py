from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ControlMode(StrEnum):
    AUTO = "auto"
    MANUAL = "manual"


class SimulationParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outdoor_temp_c: float = Field(default=6.0, ge=-45.0, le=45.0)
    airflow_m3_h: float = Field(default=3000.0, ge=200.0, le=8000.0)
    supply_temp_setpoint_c: float = Field(default=19.0, ge=10.0, le=35.0)
    heat_recovery_efficiency: float = Field(default=0.45, ge=0.0, le=0.85)
    heater_power_kw: float = Field(default=18.0, ge=0.0, le=120.0)
    filter_contamination: float = Field(default=0.15, ge=0.0, le=1.0)
    fan_speed_ratio: float = Field(default=0.86, ge=0.2, le=1.2)
    room_temp_c: float = Field(default=21.2, ge=5.0, le=40.0)
    room_heat_gain_kw: float = Field(default=4.2, ge=-10.0, le=40.0)
    room_volume_m3: float = Field(default=250.0, ge=50.0, le=2000.0)
    room_thermal_capacity_kwh_per_k: float = Field(default=14.0, ge=1.0, le=200.0)
    room_loss_coeff_kw_per_k: float = Field(default=0.18, ge=0.01, le=2.0)
    control_mode: ControlMode = Field(default=ControlMode.AUTO)
    horizon_minutes: int = Field(default=120, ge=10, le=720)
    step_minutes: int = Field(default=10, ge=1, le=60)
