from app.simulation.parameters import SimulationParameters
from app.simulation.state import Alarm, AlarmLevel, OperationStatus, SimulationState
from app.simulation.status_policy import StatusThresholds


def build_alarms(
    parameters: SimulationParameters,
    state: SimulationState,
    thresholds: StatusThresholds,
) -> list[Alarm]:
    alarms: list[Alarm] = []

    temp_gap = parameters.supply_temp_setpoint_c - state.supply_temp_c
    if temp_gap >= thresholds.supply_temp_gap_c.alarm:
        alarms.append(
            Alarm(
                code="SUPPLY_TEMP_LOW",
                message="Температура притока заметно ниже уставки.",
                level=AlarmLevel.CRITICAL,
            )
        )
    elif temp_gap >= thresholds.supply_temp_gap_c.warning:
        alarms.append(
            Alarm(
                code="SUPPLY_TEMP_WARNING",
                message="Температура притока ниже целевой уставки.",
                level=AlarmLevel.WARNING,
            )
        )

    airflow_ratio = state.actual_airflow_m3_h / max(parameters.airflow_m3_h, 1.0)
    if airflow_ratio <= thresholds.airflow_ratio.alarm:
        alarms.append(
            Alarm(
                code="AIRFLOW_CRITICAL",
                message="Подача воздуха упала до аварийного уровня.",
                level=AlarmLevel.CRITICAL,
            )
        )
    elif airflow_ratio <= thresholds.airflow_ratio.warning:
        alarms.append(
            Alarm(
                code="AIRFLOW_WARNING",
                message="Расход воздуха ниже ожидаемого режима.",
                level=AlarmLevel.WARNING,
            )
        )

    if state.filter_pressure_drop_pa >= thresholds.filter_pressure_drop_pa.alarm:
        alarms.append(
            Alarm(
                code="FILTER_SERVICE_NOW",
                message="Фильтр требует немедленного обслуживания.",
                level=AlarmLevel.CRITICAL,
            )
        )
    elif state.filter_pressure_drop_pa >= thresholds.filter_pressure_drop_pa.warning:
        alarms.append(
            Alarm(
                code="FILTER_SERVICE_SOON",
                message="Фильтр загрязнен и требует обслуживания.",
                level=AlarmLevel.WARNING,
            )
        )

    if (
        state.heater_load_ratio >= thresholds.heater_load_ratio.warning
        and temp_gap > 0.5
    ):
        alarms.append(
            Alarm(
                code="HEATER_SATURATION",
                message="Нагреватель близок к пределу мощности.",
                level=AlarmLevel.WARNING,
            )
        )

    if parameters.control_mode.value == "manual":
        alarms.append(
            Alarm(
                code="MANUAL_MODE",
                message="Установка работает в ручном режиме.",
                level=AlarmLevel.INFO,
            )
        )

    return alarms


def derive_status(alarms: list[Alarm]) -> OperationStatus:
    if any(alarm.level == AlarmLevel.CRITICAL for alarm in alarms):
        return OperationStatus.ALARM
    if any(alarm.level == AlarmLevel.WARNING for alarm in alarms):
        return OperationStatus.WARNING
    return OperationStatus.NORMAL
