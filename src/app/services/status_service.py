from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from app.infrastructure.settings import ApplicationSettings, get_settings
from app.simulation.parameters import SimulationParameters
from app.simulation.state import AlarmLevel, OperationStatus, SimulationResult, TrendPoint
from app.simulation.status_policy import (
    StatusThresholds,
    airflow_status,
    co2_status,
    energy_intensity_status,
    filter_pressure_status,
    heater_load_status,
    humidity_status,
    max_status,
    occupancy_status,
    outdoor_temp_status,
    room_temp_status,
    supply_temp_status,
)


class StatusLegendEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: OperationStatus
    label: str
    class_name: str
    color_hex: str
    summary: str


@dataclass(frozen=True)
class DashboardMetricStatus:
    metric_id: str
    title: str
    value_text: str
    status: OperationStatus
    detail: str


class StatusService:
    _STATUS_LABELS = {
        OperationStatus.NORMAL: "Норма",
        OperationStatus.WARNING: "Риск",
        OperationStatus.ALARM: "Авария",
    }
    _STATUS_CLASSES = {
        OperationStatus.NORMAL: "status-pill status-normal",
        OperationStatus.WARNING: "status-pill status-warning",
        OperationStatus.ALARM: "status-pill status-alarm",
    }
    _STATUS_COLORS = {
        OperationStatus.NORMAL: "#22c55e",
        OperationStatus.WARNING: "#facc15",
        OperationStatus.ALARM: "#ef4444",
    }

    def __init__(self, settings: ApplicationSettings | None = None) -> None:
        resolved_settings = settings or get_settings()
        self._thresholds = resolved_settings.status_thresholds

    @property
    def thresholds(self) -> StatusThresholds:
        return self._thresholds

    def status_label(self, status: OperationStatus) -> str:
        return self._STATUS_LABELS[status]

    def status_class_name(self, status: OperationStatus) -> str:
        return self._STATUS_CLASSES[status]

    def status_color(self, status: OperationStatus) -> str:
        return self._STATUS_COLORS[status]

    def status_summary(self, status: OperationStatus) -> str:
        thresholds = self.thresholds
        summaries = {
            OperationStatus.NORMAL: (
                f"Приток в пределах {thresholds.supply_temp_gap_c.warning:.1f} °C "
                f"от уставки, расход выше {thresholds.airflow_ratio.warning * 100:.0f}% "
                f"и ΔP фильтра ниже {thresholds.filter_pressure_drop_pa.warning:.0f} Па."
            ),
            OperationStatus.WARNING: (
                f"Отклонение притока от {thresholds.supply_temp_gap_c.warning:.1f} "
                f"до {thresholds.supply_temp_gap_c.alarm:.1f} °C, расход от "
                f"{thresholds.airflow_ratio.alarm * 100:.0f}% до "
                f"{thresholds.airflow_ratio.warning * 100:.0f}% или ΔP фильтра "
                f"от {thresholds.filter_pressure_drop_pa.warning:.0f} до "
                f"{thresholds.filter_pressure_drop_pa.alarm:.0f} Па."
            ),
            OperationStatus.ALARM: (
                f"Отклонение притока не меньше {thresholds.supply_temp_gap_c.alarm:.1f} °C, "
                f"расход не выше {thresholds.airflow_ratio.alarm * 100:.0f}% или "
                f"ΔP фильтра не ниже {thresholds.filter_pressure_drop_pa.alarm:.0f} Па."
            ),
        }
        return summaries[status]

    def build_status_legend(self) -> list[StatusLegendEntry]:
        return [
            StatusLegendEntry(
                status=OperationStatus.NORMAL,
                label=self.status_label(OperationStatus.NORMAL),
                class_name=self.status_class_name(OperationStatus.NORMAL),
                color_hex=self.status_color(OperationStatus.NORMAL),
                summary=self.status_summary(OperationStatus.NORMAL),
            ),
            StatusLegendEntry(
                status=OperationStatus.WARNING,
                label=self.status_label(OperationStatus.WARNING),
                class_name=self.status_class_name(OperationStatus.WARNING),
                color_hex=self.status_color(OperationStatus.WARNING),
                summary=self.status_summary(OperationStatus.WARNING),
            ),
            StatusLegendEntry(
                status=OperationStatus.ALARM,
                label=self.status_label(OperationStatus.ALARM),
                class_name=self.status_class_name(OperationStatus.ALARM),
                color_hex=self.status_color(OperationStatus.ALARM),
                summary=self.status_summary(OperationStatus.ALARM),
            ),
        ]

    def build_dashboard_metric_statuses(
        self,
        result: SimulationResult,
    ) -> list[DashboardMetricStatus]:
        parameters = result.parameters
        state = result.state
        supply_gap_c = parameters.supply_temp_setpoint_c - state.supply_temp_c
        airflow_ratio = state.actual_airflow_m3_h / max(parameters.airflow_m3_h, 1.0)
        heater_load_percent = state.heater_load_ratio * 100.0
        energy_intensity = state.energy_intensity_kw_per_1000_m3_h
        return [
            DashboardMetricStatus(
                metric_id="supply_temp",
                title="Температура притока",
                value_text=f"{state.supply_temp_c:.1f} °C",
                status=self.supply_temp_status(result),
                detail=(
                    f"Отклонение от уставки {supply_gap_c:+.1f} °C "
                    f"(цель {parameters.supply_temp_setpoint_c:.1f} °C)"
                ),
            ),
            DashboardMetricStatus(
                metric_id="room_temp",
                title="Температура помещения",
                value_text=f"{state.room_temp_c:.1f} °C",
                status=self.room_temp_status(result),
                detail=(
                    f"Комфортный диапазон "
                    f"{self.thresholds.room_temp_c.warning_low:.0f}–"
                    f"{self.thresholds.room_temp_c.warning_high:.0f} °C"
                ),
            ),
            DashboardMetricStatus(
                metric_id="heating_power",
                title="Нагрев",
                value_text=f"{state.heating_power_kw:.1f} кВт",
                status=self.heating_power_status(result),
                detail=(
                    f"Загрузка нагревателя {heater_load_percent:.0f}% "
                    f"от доступной мощности"
                ),
            ),
            DashboardMetricStatus(
                metric_id="total_power",
                title="Суммарная мощность",
                value_text=f"{state.total_power_kw:.1f} кВт",
                status=self.total_power_status(result),
                detail=f"Удельная мощность {energy_intensity:.2f} кВт/1000 м³/ч",
            ),
            DashboardMetricStatus(
                metric_id="airflow",
                title="Фактический расход",
                value_text=f"{state.actual_airflow_m3_h:.0f} м³/ч",
                status=self.airflow_status(result),
                detail=f"{airflow_ratio * 100:.0f}% от заданного расхода",
            ),
            DashboardMetricStatus(
                metric_id="filter_pressure",
                title="Перепад на фильтре",
                value_text=f"{state.filter_pressure_drop_pa:.0f} Па",
                status=self.filter_pressure_status(result),
                detail=(
                    f"Порог риска {self.thresholds.filter_pressure_drop_pa.warning:.0f} Па, "
                    f"аварии {self.thresholds.filter_pressure_drop_pa.alarm:.0f} Па"
                ),
            ),
        ]

    def build_metric_status_map(
        self,
        result: SimulationResult,
    ) -> dict[str, DashboardMetricStatus]:
        return {
            entry.metric_id: entry
            for entry in self.build_dashboard_metric_statuses(result)
        }

    def build_alert_block_status(self, result: SimulationResult) -> OperationStatus:
        if not result.alarms:
            return OperationStatus.NORMAL
        statuses = [
            self.alert_level_status(alarm.level)
            for alarm in result.alarms
        ]
        return max_status(*statuses)

    def build_export_status_rows(
        self,
        result: SimulationResult,
    ) -> list[list[str]]:
        metric_map = self.build_metric_status_map(result)
        rows = [
            [
                "overall_status",
                self.status_label(result.state.status),
                (
                    f"Интегральный статус расчёта: {self.status_summary(result.state.status)} "
                    f"Активных тревог: {len(result.alarms)}."
                ),
            ],
            [
                "alert_block",
                self.status_label(self.build_alert_block_status(result)),
                (
                    "Блок тревог агрегирует активные сигналы тревоги и подсвечивает риск/аварию "
                    "по их уровню."
                ),
            ],
        ]
        rows.extend(
            [
                entry.metric_id,
                self.status_label(entry.status),
                entry.detail,
            ]
            for entry in metric_map.values()
        )
        return rows

    def build_export_legend_rows(self) -> list[list[str]]:
        return [
            [entry.label, entry.color_hex, entry.summary]
            for entry in self.build_status_legend()
        ]

    def build_trend_statuses(
        self,
        parameters: SimulationParameters,
        history_points: list[TrendPoint],
    ) -> list[OperationStatus]:
        statuses: list[OperationStatus] = []
        for point in history_points:
            heater_ratio = (
                point.heating_power_kw / max(parameters.heater_power_kw, 1e-6)
                if parameters.heater_power_kw > 0
                else 0.0
            )
            energy_intensity = point.total_power_kw / max(point.airflow_m3_h / 1000.0, 0.1)
            statuses.append(
                max_status(
                    supply_temp_status(parameters, point.supply_temp_c, self.thresholds),
                    room_temp_status(point.room_temp_c, self.thresholds),
                    heater_load_status(heater_ratio, self.thresholds),
                    energy_intensity_status(energy_intensity, self.thresholds),
                    airflow_status(parameters, point.airflow_m3_h, self.thresholds),
                    filter_pressure_status(point.filter_pressure_drop_pa, self.thresholds),
                )
            )
        return statuses

    def supply_temp_status(self, result: SimulationResult) -> OperationStatus:
        return supply_temp_status(
            result.parameters,
            result.state.supply_temp_c,
            self.thresholds,
        )

    def airflow_status(self, result: SimulationResult) -> OperationStatus:
        return airflow_status(
            result.parameters,
            result.state.actual_airflow_m3_h,
            self.thresholds,
        )

    def filter_pressure_status(self, result: SimulationResult) -> OperationStatus:
        return filter_pressure_status(
            result.state.filter_pressure_drop_pa,
            self.thresholds,
        )

    def heating_power_status(self, result: SimulationResult) -> OperationStatus:
        return heater_load_status(result.state.heater_load_ratio, self.thresholds)

    def total_power_status(self, result: SimulationResult) -> OperationStatus:
        return energy_intensity_status(
            result.state.energy_intensity_kw_per_1000_m3_h,
            self.thresholds,
        )

    def room_temp_status(self, result: SimulationResult) -> OperationStatus:
        return room_temp_status(result.state.room_temp_c, self.thresholds)

    def outdoor_temp_status(self, result: SimulationResult) -> OperationStatus:
        return outdoor_temp_status(result.parameters.outdoor_temp_c, self.thresholds)

    def build_room_sensor_statuses(
        self,
        *,
        co2_ppm: float,
        humidity_percent: float,
        occupancy_ratio: float,
    ) -> dict[str, OperationStatus]:
        co2_metric_status = co2_status(co2_ppm, self.thresholds)
        humidity_metric_status = humidity_status(humidity_percent, self.thresholds)
        occupancy_metric_status = occupancy_status(occupancy_ratio, self.thresholds)
        return {
            "co2": co2_metric_status,
            "humidity": humidity_metric_status,
            "occupancy": occupancy_metric_status,
            "air_quality": max_status(
                co2_metric_status,
                humidity_metric_status,
                occupancy_metric_status,
            ),
        }

    def alert_level_status(self, level: AlarmLevel) -> OperationStatus:
        mapping = {
            AlarmLevel.INFO: OperationStatus.WARNING,
            AlarmLevel.WARNING: OperationStatus.WARNING,
            AlarmLevel.CRITICAL: OperationStatus.ALARM,
        }
        return mapping[level]
