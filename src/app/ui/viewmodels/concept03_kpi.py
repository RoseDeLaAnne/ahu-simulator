from __future__ import annotations

from dataclasses import dataclass

from app.services.status_service import StatusService
from app.simulation.state import SimulationResult, SimulationHistory


@dataclass(frozen=True)
class Concept03KpiRowView:
    kpi_id: str
    icon: str
    label: str
    value_text: str
    unit: str
    setpoint_text: str | None
    deviation_text: str
    deviation_pct: float | None
    state: str
    class_name: str
    sparkline_values: tuple[float, ...] | None = None

    @property
    def progress_style(self) -> dict[str, str]:
        progress = 0.0 if self.deviation_pct is None else self.deviation_pct
        bounded_progress = max(0.0, min(progress, 100.0))
        return {"width": f"{bounded_progress:.0f}%"}


@dataclass(frozen=True)
class Concept03KpiView:
    rows: tuple[Concept03KpiRowView, ...]


def build_concept03_kpi_view(
    result: SimulationResult,
    status_service: StatusService | None = None,
    history: SimulationHistory | None = None,
) -> Concept03KpiView:
    service = status_service or StatusService()
    status_map = service.build_metric_status_map_for_concept03(result)
    parameters = result.parameters
    state = result.state
    thresholds = service.thresholds

    airflow_deviation = _ratio_percent(
        state.actual_airflow_m3_h,
        parameters.airflow_m3_h,
    )
    pressure_deviation = _ratio_percent(
        state.filter_pressure_drop_pa,
        thresholds.filter_pressure_drop_pa.warning,
    )
    supply_gap = abs(parameters.supply_temp_setpoint_c - state.supply_temp_c)
    supply_deviation = max(
        0.0,
        100.0 - _ratio_percent(supply_gap, thresholds.supply_temp_gap_c.alarm),
    )
    recovery_deviation = _ratio_percent(
        parameters.heat_recovery_efficiency,
        0.85,
    )
    power_setpoint_kw = (
        thresholds.energy_intensity_kw_per_1000_m3_h.warning
        * parameters.airflow_m3_h
        / 1000.0
    )
    power_deviation = _ratio_percent(state.total_power_kw, power_setpoint_kw)

    recovery_state = (
        "unavailable"
        if parameters.heat_recovery_efficiency <= 0
        else status_map["kpi-row-recovery"].value
    )

    # Extract sparkline data from history (last 12 points)
    sparkline_data = _extract_sparkline_data(history) if history else None

    rows = (
        _build_row(
            kpi_id="kpi-row-airflow",
            icon="wind",
            # U+00AD: на мобильной плитке слово не влезает целиком —
            # мягкий перенос даёт «Производи-тельность» вместо разрыва «…ьнос/ть».
            label="Производи­тельность",
            value_text=_format_number(state.actual_airflow_m3_h, digits=0),
            unit="м³/ч",
            setpoint_text=(
                f"Задание: {_format_number(parameters.airflow_m3_h, digits=0)} м³/ч"
            ),
            deviation_text=f"{airflow_deviation:.0f}% от задания",
            deviation_pct=airflow_deviation,
            state=status_map["kpi-row-airflow"].value,
            sparkline_values=sparkline_data["airflow"] if sparkline_data else None,
        ),
        _build_row(
            kpi_id="kpi-row-pressure",
            icon="gauge",
            label="Статическое давление",
            value_text=_format_number(state.filter_pressure_drop_pa, digits=0),
            unit="Па",
            setpoint_text=(
                f"Порог: {_format_number(thresholds.filter_pressure_drop_pa.warning, digits=0)} Па"
            ),
            deviation_text=f"{pressure_deviation:.0f}% от порога риска",
            deviation_pct=pressure_deviation,
            state=status_map["kpi-row-pressure"].value,
            sparkline_values=sparkline_data["pressure"] if sparkline_data else None,
        ),
        _build_row(
            kpi_id="kpi-row-supply-temp",
            icon="sun",
            label="Температура притока",
            value_text=f"{state.supply_temp_c:.1f}",
            unit="°C",
            setpoint_text=f"Задание: {parameters.supply_temp_setpoint_c:.1f} °C",
            deviation_text=f"Отклонение: {supply_gap:.1f} °C",
            deviation_pct=supply_deviation,
            state=status_map["kpi-row-supply-temp"].value,
            sparkline_values=sparkline_data["supply_temp"] if sparkline_data else None,
        ),
        _build_row(
            kpi_id="kpi-row-humidity",
            icon="flask-conical",
            label="Относительная влажность",
            value_text="Недоступно",
            unit="",
            setpoint_text="Датчик влажности не подключен",
            deviation_text="Ожидает расширения доменной модели",
            deviation_pct=None,
            state="unavailable",
        ),
        _build_row(
            kpi_id="kpi-row-recovery",
            icon="refresh-cw",
            label="Эффективность рекуперации",
            value_text=(
                "Недоступно"
                if recovery_state == "unavailable"
                else f"{parameters.heat_recovery_efficiency * 100:.0f}"
            ),
            unit="" if recovery_state == "unavailable" else "%",
            setpoint_text=(
                "Рекуператор отключен"
                if recovery_state == "unavailable"
                else "Паспорт: до 85 %"
            ),
            deviation_text=(
                "Недоступно"
                if recovery_state == "unavailable"
                else f"{recovery_deviation:.0f}% паспортного предела"
            ),
            deviation_pct=None if recovery_state == "unavailable" else recovery_deviation,
            state=recovery_state,
        ),
        _build_row(
            kpi_id="kpi-row-power",
            icon="cpu",
            label="Потребляемая мощность",
            value_text=f"{state.total_power_kw:.1f}",
            unit="кВт",
            setpoint_text=f"Порог: {power_setpoint_kw:.1f} кВт",
            deviation_text=(
                f"{state.energy_intensity_kw_per_1000_m3_h:.2f} кВт/1000 м³/ч"
            ),
            deviation_pct=power_deviation,
            state=status_map["kpi-row-power"].value,
            sparkline_values=sparkline_data["power"] if sparkline_data else None,
        ),
    )
    return Concept03KpiView(rows=rows)


def kpi_row_class_name(state: str) -> str:
    suffix = {
        "normal": "normal",
        "warning": "warn",
        "alarm": "alarm",
        "unavailable": "unavailable",
    }.get(state, "unavailable")
    return f"c03-kpi-row c03-kpi-row--{suffix}"


def _build_row(
    *,
    kpi_id: str,
    icon: str,
    label: str,
    value_text: str,
    unit: str,
    setpoint_text: str | None,
    deviation_text: str,
    deviation_pct: float | None,
    state: str,
    sparkline_values: tuple[float, ...] | None = None,
) -> Concept03KpiRowView:
    return Concept03KpiRowView(
        kpi_id=kpi_id,
        icon=icon,
        label=label,
        value_text=value_text,
        unit=unit,
        setpoint_text=setpoint_text,
        deviation_text=deviation_text,
        deviation_pct=deviation_pct,
        state=state,
        class_name=kpi_row_class_name(state),
        sparkline_values=sparkline_values,
    )


def _ratio_percent(value: float, target: float) -> float:
    return value / max(target, 1e-6) * 100.0


def _format_number(value: float, *, digits: int) -> str:
    return f"{value:,.{digits}f}".replace(",", " ")


def _extract_sparkline_data(
    history: SimulationHistory,
) -> dict[str, tuple[float, ...]]:
    """
    Extract last N points from history for sparkline visualization.

    Returns dict with keys: airflow, pressure, supply_temp, power
    """
    if not history or not history.points:
        return {
            "airflow": (),
            "pressure": (),
            "supply_temp": (),
            "power": (),
        }

    # Take last 12 points for sparkline (or all if less than 12)
    max_points = 12
    points = history.points[-max_points:] if len(history.points) > max_points else history.points

    return {
        "airflow": tuple(p.airflow_m3_h for p in points),
        "pressure": tuple(p.filter_pressure_drop_pa for p in points),
        "supply_temp": tuple(p.supply_temp_c for p in points),
        "power": tuple(p.total_power_kw for p in points),
    }
