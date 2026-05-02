from __future__ import annotations

from dataclasses import dataclass

from app.simulation.parameters import SimulationParameters

AIR_DENSITY_KG_PER_M3 = 1.2
AIR_HEAT_CAPACITY_J_PER_KG_K = 1005.0
MIN_MASS_FLOW_KG_S = 1e-6


@dataclass(slots=True)
class OperatingPoint:
    actual_airflow_m3_h: float
    mixed_air_temp_c: float
    recovered_air_temp_c: float
    supply_temp_c: float
    room_temp_c: float
    required_heating_kw: float
    available_heater_kw: float
    heating_power_kw: float
    heater_load_ratio: float
    fan_power_kw: float
    total_power_kw: float
    energy_intensity_kw_per_1000_m3_h: float
    filter_pressure_drop_pa: float
    heat_balance_kw: float


def _round(value: float) -> float:
    return round(float(value), 2)


def compute_actual_airflow_m3_h(parameters: SimulationParameters) -> float:
    fouling_factor = max(0.45, 1.0 - 0.35 * parameters.filter_contamination)
    return parameters.airflow_m3_h * parameters.fan_speed_ratio * fouling_factor


def compute_filter_pressure_drop_pa(parameters: SimulationParameters) -> float:
    return 120.0 + 300.0 * (parameters.filter_contamination**1.35)


def calculate_operating_point(
    parameters: SimulationParameters,
    step_minutes: int,
) -> OperatingPoint:
    actual_airflow_m3_h = compute_actual_airflow_m3_h(parameters)
    filter_pressure_drop_pa = compute_filter_pressure_drop_pa(parameters)
    mixed_air_temp_c = parameters.outdoor_temp_c
    recovered_air_temp_c = mixed_air_temp_c + (
        parameters.room_temp_c - mixed_air_temp_c
    ) * parameters.heat_recovery_efficiency

    mass_flow_kg_s = actual_airflow_m3_h * AIR_DENSITY_KG_PER_M3 / 3600.0
    required_heating_kw = max(
        mass_flow_kg_s
        * AIR_HEAT_CAPACITY_J_PER_KG_K
        * (parameters.supply_temp_setpoint_c - recovered_air_temp_c)
        / 1000.0,
        0.0,
    )
    heater_available_kw = parameters.heater_power_kw * max(
        0.78, 1.0 - 0.12 * parameters.filter_contamination
    )
    heating_power_kw = min(required_heating_kw, heater_available_kw)

    if mass_flow_kg_s > MIN_MASS_FLOW_KG_S:
        supply_temp_c = recovered_air_temp_c + (
            heating_power_kw * 1000.0 / (mass_flow_kg_s * AIR_HEAT_CAPACITY_J_PER_KG_K)
        )
    else:
        supply_temp_c = recovered_air_temp_c

    flow_ratio = actual_airflow_m3_h / 3200.0
    fan_power_kw = 0.25 + 1.7 * (flow_ratio**3) * (1.0 + 0.28 * parameters.filter_contamination)

    heat_balance_kw = (
        mass_flow_kg_s
        * AIR_HEAT_CAPACITY_J_PER_KG_K
        * (supply_temp_c - parameters.room_temp_c)
        / 1000.0
        + parameters.room_heat_gain_kw
        - parameters.room_loss_coeff_kw_per_k
        * (parameters.room_temp_c - parameters.outdoor_temp_c)
    )

    if step_minutes > 0:
        room_temp_c = parameters.room_temp_c + (
            heat_balance_kw * (step_minutes / 60.0) / parameters.room_thermal_capacity_kwh_per_k
        )
    else:
        room_temp_c = parameters.room_temp_c

    total_power_kw = heating_power_kw + fan_power_kw
    energy_intensity_kw_per_1000_m3_h = total_power_kw / max(actual_airflow_m3_h / 1000.0, 0.1)
    heater_load_ratio = (
        heating_power_kw / parameters.heater_power_kw if parameters.heater_power_kw > 0 else 0.0
    )

    return OperatingPoint(
        actual_airflow_m3_h=_round(actual_airflow_m3_h),
        mixed_air_temp_c=_round(mixed_air_temp_c),
        recovered_air_temp_c=_round(recovered_air_temp_c),
        supply_temp_c=_round(supply_temp_c),
        room_temp_c=_round(room_temp_c),
        required_heating_kw=_round(required_heating_kw),
        available_heater_kw=_round(heater_available_kw),
        heating_power_kw=_round(heating_power_kw),
        heater_load_ratio=_round(heater_load_ratio),
        fan_power_kw=_round(fan_power_kw),
        total_power_kw=_round(total_power_kw),
        energy_intensity_kw_per_1000_m3_h=_round(energy_intensity_kw_per_1000_m3_h),
        filter_pressure_drop_pa=_round(filter_pressure_drop_pa),
        heat_balance_kw=_round(heat_balance_kw),
    )
