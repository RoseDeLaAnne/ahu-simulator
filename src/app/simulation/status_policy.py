from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.simulation.parameters import SimulationParameters
from app.simulation.state import OperationStatus


class UpperStatusThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    warning: float
    alarm: float

    @model_validator(mode="after")
    def _validate_order(self) -> UpperStatusThresholds:
        if self.alarm < self.warning:
            raise ValueError("alarm threshold must be greater than or equal to warning")
        return self


class LowerStatusThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    warning: float
    alarm: float

    @model_validator(mode="after")
    def _validate_order(self) -> LowerStatusThresholds:
        if self.alarm > self.warning:
            raise ValueError("alarm threshold must be less than or equal to warning")
        return self


class BandStatusThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    warning_low: float
    alarm_low: float
    warning_high: float
    alarm_high: float

    @model_validator(mode="after")
    def _validate_order(self) -> BandStatusThresholds:
        if self.alarm_low > self.warning_low:
            raise ValueError("alarm_low must be less than or equal to warning_low")
        if self.alarm_high < self.warning_high:
            raise ValueError("alarm_high must be greater than or equal to warning_high")
        return self


class StatusThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supply_temp_gap_c: UpperStatusThresholds = Field(
        default_factory=lambda: UpperStatusThresholds(warning=1.5, alarm=3.0)
    )
    airflow_ratio: LowerStatusThresholds = Field(
        default_factory=lambda: LowerStatusThresholds(warning=0.75, alarm=0.60)
    )
    filter_pressure_drop_pa: UpperStatusThresholds = Field(
        default_factory=lambda: UpperStatusThresholds(warning=280.0, alarm=360.0)
    )
    heater_load_ratio: UpperStatusThresholds = Field(
        default_factory=lambda: UpperStatusThresholds(warning=0.85, alarm=0.95)
    )
    energy_intensity_kw_per_1000_m3_h: UpperStatusThresholds = Field(
        default_factory=lambda: UpperStatusThresholds(warning=6.5, alarm=8.0)
    )
    room_temp_c: BandStatusThresholds = Field(
        default_factory=lambda: BandStatusThresholds(
            warning_low=18.0,
            alarm_low=16.0,
            warning_high=27.0,
            alarm_high=29.0,
        )
    )
    outdoor_temp_c: BandStatusThresholds = Field(
        default_factory=lambda: BandStatusThresholds(
            warning_low=-25.0,
            alarm_low=-32.0,
            warning_high=32.0,
            alarm_high=35.0,
        )
    )
    co2_ppm: UpperStatusThresholds = Field(
        default_factory=lambda: UpperStatusThresholds(warning=900.0, alarm=1200.0)
    )
    humidity_percent: BandStatusThresholds = Field(
        default_factory=lambda: BandStatusThresholds(
            warning_low=35.0,
            alarm_low=30.0,
            warning_high=60.0,
            alarm_high=65.0,
        )
    )
    occupancy_ratio: UpperStatusThresholds = Field(
        default_factory=lambda: UpperStatusThresholds(warning=0.85, alarm=1.05)
    )


_STATUS_PRIORITY = {
    OperationStatus.NORMAL: 0,
    OperationStatus.WARNING: 1,
    OperationStatus.ALARM: 2,
}


def max_status(*statuses: OperationStatus) -> OperationStatus:
    filtered_statuses = [status for status in statuses if status is not None]
    if not filtered_statuses:
        return OperationStatus.NORMAL
    return max(filtered_statuses, key=_STATUS_PRIORITY.__getitem__)


def evaluate_upper_threshold(
    value: float,
    thresholds: UpperStatusThresholds,
) -> OperationStatus:
    if value >= thresholds.alarm:
        return OperationStatus.ALARM
    if value >= thresholds.warning:
        return OperationStatus.WARNING
    return OperationStatus.NORMAL


def evaluate_lower_threshold(
    value: float,
    thresholds: LowerStatusThresholds,
) -> OperationStatus:
    if value <= thresholds.alarm:
        return OperationStatus.ALARM
    if value <= thresholds.warning:
        return OperationStatus.WARNING
    return OperationStatus.NORMAL


def evaluate_band_threshold(
    value: float,
    thresholds: BandStatusThresholds,
) -> OperationStatus:
    if value <= thresholds.alarm_low or value >= thresholds.alarm_high:
        return OperationStatus.ALARM
    if value <= thresholds.warning_low or value >= thresholds.warning_high:
        return OperationStatus.WARNING
    return OperationStatus.NORMAL


def supply_temp_status(
    parameters: SimulationParameters,
    supply_temp_c: float,
    thresholds: StatusThresholds,
) -> OperationStatus:
    gap = abs(parameters.supply_temp_setpoint_c - supply_temp_c)
    return evaluate_upper_threshold(gap, thresholds.supply_temp_gap_c)


def airflow_status(
    parameters: SimulationParameters,
    actual_airflow_m3_h: float,
    thresholds: StatusThresholds,
) -> OperationStatus:
    airflow_ratio = actual_airflow_m3_h / max(parameters.airflow_m3_h, 1.0)
    return evaluate_lower_threshold(airflow_ratio, thresholds.airflow_ratio)


def filter_pressure_status(
    filter_pressure_drop_pa: float,
    thresholds: StatusThresholds,
) -> OperationStatus:
    return evaluate_upper_threshold(
        filter_pressure_drop_pa,
        thresholds.filter_pressure_drop_pa,
    )


def heater_load_status(
    heater_load_ratio: float,
    thresholds: StatusThresholds,
) -> OperationStatus:
    return evaluate_upper_threshold(heater_load_ratio, thresholds.heater_load_ratio)


def energy_intensity_status(
    energy_intensity_kw_per_1000_m3_h: float,
    thresholds: StatusThresholds,
) -> OperationStatus:
    return evaluate_upper_threshold(
        energy_intensity_kw_per_1000_m3_h,
        thresholds.energy_intensity_kw_per_1000_m3_h,
    )


def room_temp_status(
    room_temp_c: float,
    thresholds: StatusThresholds,
) -> OperationStatus:
    return evaluate_band_threshold(room_temp_c, thresholds.room_temp_c)


def outdoor_temp_status(
    outdoor_temp_c: float,
    thresholds: StatusThresholds,
) -> OperationStatus:
    return evaluate_band_threshold(outdoor_temp_c, thresholds.outdoor_temp_c)


def co2_status(
    co2_ppm: float,
    thresholds: StatusThresholds,
) -> OperationStatus:
    return evaluate_upper_threshold(co2_ppm, thresholds.co2_ppm)


def humidity_status(
    humidity_percent: float,
    thresholds: StatusThresholds,
) -> OperationStatus:
    return evaluate_band_threshold(humidity_percent, thresholds.humidity_percent)


def occupancy_status(
    occupancy_ratio: float,
    thresholds: StatusThresholds,
) -> OperationStatus:
    return evaluate_upper_threshold(occupancy_ratio, thresholds.occupancy_ratio)
