from app.simulation.state import OperationStatus
from app.simulation.status_policy import (
    BandStatusThresholds,
    LowerStatusThresholds,
    StatusThresholds,
    UpperStatusThresholds,
    airflow_status,
    co2_status,
    energy_intensity_status,
    evaluate_band_threshold,
    evaluate_lower_threshold,
    evaluate_upper_threshold,
    filter_pressure_status,
    heater_load_status,
    humidity_status,
    occupancy_status,
    outdoor_temp_status,
    room_temp_status,
    supply_temp_status,
)
from app.simulation.parameters import SimulationParameters


def test_upper_threshold_marks_warning_and_alarm_boundaries() -> None:
    thresholds = UpperStatusThresholds(warning=1.5, alarm=3.0)

    assert evaluate_upper_threshold(1.4, thresholds) == OperationStatus.NORMAL
    assert evaluate_upper_threshold(1.5, thresholds) == OperationStatus.WARNING
    assert evaluate_upper_threshold(3.0, thresholds) == OperationStatus.ALARM


def test_lower_threshold_marks_warning_and_alarm_boundaries() -> None:
    thresholds = LowerStatusThresholds(warning=0.75, alarm=0.60)

    assert evaluate_lower_threshold(0.8, thresholds) == OperationStatus.NORMAL
    assert evaluate_lower_threshold(0.75, thresholds) == OperationStatus.WARNING
    assert evaluate_lower_threshold(0.60, thresholds) == OperationStatus.ALARM


def test_band_threshold_marks_warning_and_alarm_on_both_sides() -> None:
    thresholds = BandStatusThresholds(
        warning_low=18.0,
        alarm_low=16.0,
        warning_high=27.0,
        alarm_high=29.0,
    )

    assert evaluate_band_threshold(22.0, thresholds) == OperationStatus.NORMAL
    assert evaluate_band_threshold(18.0, thresholds) == OperationStatus.WARNING
    assert evaluate_band_threshold(15.9, thresholds) == OperationStatus.ALARM
    assert evaluate_band_threshold(27.0, thresholds) == OperationStatus.WARNING
    assert evaluate_band_threshold(29.1, thresholds) == OperationStatus.ALARM


def test_status_thresholds_cover_all_metric_boundaries() -> None:
    thresholds = StatusThresholds()
    parameters = SimulationParameters()

    assert supply_temp_status(
        parameters,
        parameters.supply_temp_setpoint_c - 1.49,
        thresholds,
    ) == OperationStatus.NORMAL
    assert supply_temp_status(
        parameters,
        parameters.supply_temp_setpoint_c - thresholds.supply_temp_gap_c.warning,
        thresholds,
    ) == OperationStatus.WARNING
    assert supply_temp_status(
        parameters,
        parameters.supply_temp_setpoint_c - thresholds.supply_temp_gap_c.alarm,
        thresholds,
    ) == OperationStatus.ALARM

    assert airflow_status(parameters, parameters.airflow_m3_h * 0.76, thresholds) == OperationStatus.NORMAL
    assert airflow_status(
        parameters,
        parameters.airflow_m3_h * thresholds.airflow_ratio.warning,
        thresholds,
    ) == OperationStatus.WARNING
    assert airflow_status(
        parameters,
        parameters.airflow_m3_h * thresholds.airflow_ratio.alarm,
        thresholds,
    ) == OperationStatus.ALARM

    assert filter_pressure_status(279.0, thresholds) == OperationStatus.NORMAL
    assert filter_pressure_status(
        thresholds.filter_pressure_drop_pa.warning,
        thresholds,
    ) == OperationStatus.WARNING
    assert filter_pressure_status(
        thresholds.filter_pressure_drop_pa.alarm,
        thresholds,
    ) == OperationStatus.ALARM

    assert heater_load_status(0.84, thresholds) == OperationStatus.NORMAL
    assert heater_load_status(
        thresholds.heater_load_ratio.warning,
        thresholds,
    ) == OperationStatus.WARNING
    assert heater_load_status(
        thresholds.heater_load_ratio.alarm,
        thresholds,
    ) == OperationStatus.ALARM

    assert energy_intensity_status(6.49, thresholds) == OperationStatus.NORMAL
    assert energy_intensity_status(
        thresholds.energy_intensity_kw_per_1000_m3_h.warning,
        thresholds,
    ) == OperationStatus.WARNING
    assert energy_intensity_status(
        thresholds.energy_intensity_kw_per_1000_m3_h.alarm,
        thresholds,
    ) == OperationStatus.ALARM

    assert room_temp_status(22.0, thresholds) == OperationStatus.NORMAL
    assert room_temp_status(thresholds.room_temp_c.warning_low, thresholds) == OperationStatus.WARNING
    assert room_temp_status(thresholds.room_temp_c.alarm_low, thresholds) == OperationStatus.ALARM
    assert room_temp_status(thresholds.room_temp_c.warning_high, thresholds) == OperationStatus.WARNING
    assert room_temp_status(thresholds.room_temp_c.alarm_high, thresholds) == OperationStatus.ALARM

    assert outdoor_temp_status(5.0, thresholds) == OperationStatus.NORMAL
    assert outdoor_temp_status(
        thresholds.outdoor_temp_c.warning_low,
        thresholds,
    ) == OperationStatus.WARNING
    assert outdoor_temp_status(
        thresholds.outdoor_temp_c.alarm_low,
        thresholds,
    ) == OperationStatus.ALARM
    assert outdoor_temp_status(
        thresholds.outdoor_temp_c.warning_high,
        thresholds,
    ) == OperationStatus.WARNING
    assert outdoor_temp_status(
        thresholds.outdoor_temp_c.alarm_high,
        thresholds,
    ) == OperationStatus.ALARM

    assert co2_status(899.0, thresholds) == OperationStatus.NORMAL
    assert co2_status(thresholds.co2_ppm.warning, thresholds) == OperationStatus.WARNING
    assert co2_status(thresholds.co2_ppm.alarm, thresholds) == OperationStatus.ALARM

    assert humidity_status(45.0, thresholds) == OperationStatus.NORMAL
    assert humidity_status(thresholds.humidity_percent.warning_low, thresholds) == OperationStatus.WARNING
    assert humidity_status(thresholds.humidity_percent.alarm_low, thresholds) == OperationStatus.ALARM
    assert humidity_status(thresholds.humidity_percent.warning_high, thresholds) == OperationStatus.WARNING
    assert humidity_status(thresholds.humidity_percent.alarm_high, thresholds) == OperationStatus.ALARM

    assert occupancy_status(0.84, thresholds) == OperationStatus.NORMAL
    assert occupancy_status(thresholds.occupancy_ratio.warning, thresholds) == OperationStatus.WARNING
    assert occupancy_status(thresholds.occupancy_ratio.alarm, thresholds) == OperationStatus.ALARM
