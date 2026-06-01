from __future__ import annotations

from dataclasses import dataclass

from app.services.status_service import StatusService
from app.simulation.control import ControlTargetState
from app.simulation.state import OperationStatus, SimulationResult
from app.simulation.status_policy import max_status


@dataclass(frozen=True)
class Concept03StatusBannerView:
    title: str
    label: str
    summary: str
    state: str
    accent_icon: str = "shield-check"
    action_href: str | None = "?theme=concept03&page=analytics&tab=alarms"

    @property
    def class_name(self) -> str:
        suffix = _state_suffix(self.state)
        return f"c03-status-banner c03-status-banner--{suffix}"


@dataclass(frozen=True)
class Concept03HealthTileView:
    health_id: str
    title: str
    sub: str
    icon: str
    state: str
    class_name: str


@dataclass(frozen=True)
class Concept03HealthView:
    banner: Concept03StatusBannerView
    tiles: tuple[Concept03HealthTileView, ...]


def build_concept03_health_view(
    result: SimulationResult,
    status_service: StatusService | None = None,
) -> Concept03HealthView:
    service = status_service or StatusService()
    metric_statuses = service.build_metric_status_map_for_concept03(result)
    equipment_status = max_status(
        metric_statuses["kpi-row-airflow"],
        metric_statuses["kpi-row-pressure"],
        metric_statuses["kpi-row-power"],
    )
    automation_status = _automation_status(result)
    sensors_status = max_status(
        service.supply_temp_status(result),
        service.room_temp_status(result),
        service.outdoor_temp_status(result),
    )
    safety_status = service.build_alert_block_status(result)
    alarm_count = len(result.alarms)

    banner_summary = (
        f"{service.status_summary(result.state.status)} "
        f"Активных тревог: {alarm_count}."
    )

    return Concept03HealthView(
        banner=Concept03StatusBannerView(
            title="Состояние установки",
            label=service.status_label(result.state.status),
            summary=banner_summary,
            state=result.state.status.value,
        ),
        tiles=(
            _build_tile(
                health_id="equipment",
                title="Оборудование",
                sub=_health_sub(equipment_status),
                icon="gauge",
                status=equipment_status,
            ),
            _build_tile(
                health_id="automation",
                title="Автоматика",
                sub=_automation_sub(result),
                icon="sliders-horizontal",
                status=automation_status,
            ),
            _build_tile(
                health_id="sensors",
                title="Датчики",
                sub=_health_sub(sensors_status),
                icon="cpu",
                status=sensors_status,
            ),
            _build_tile(
                health_id="safety",
                title="Безопасность",
                sub="Без тревог" if alarm_count == 0 else f"Тревог: {alarm_count}",
                icon="shield-check",
                status=safety_status,
            ),
        ),
    )


def health_tile_class_name(state: str) -> str:
    return f"c03-health-tile c03-health-tile--{_state_suffix(state)}"


def _build_tile(
    *,
    health_id: str,
    title: str,
    sub: str,
    icon: str,
    status: OperationStatus,
) -> Concept03HealthTileView:
    state = status.value
    return Concept03HealthTileView(
        health_id=health_id,
        title=title,
        sub=sub,
        icon=icon,
        state=state,
        class_name=health_tile_class_name(state),
    )


def _automation_status(result: SimulationResult) -> OperationStatus:
    if result.control is None:
        return OperationStatus.WARNING
    if result.control.target_state == ControlTargetState.LIMITED:
        return OperationStatus.WARNING
    if result.control.target_state == ControlTargetState.OVERRIDE:
        return OperationStatus.WARNING
    return OperationStatus.NORMAL


def _automation_sub(result: SimulationResult) -> str:
    if result.control is None:
        return "Нет диагностики"
    labels = {
        ControlTargetState.TRACKING: "Контур активен",
        ControlTargetState.LIMITED: "Ограничение",
        ControlTargetState.OVERRIDE: "Оператор",
    }
    return labels[result.control.target_state]


def _health_sub(status: OperationStatus) -> str:
    labels = {
        OperationStatus.NORMAL: "Исправно",
        OperationStatus.WARNING: "Сервис",
        OperationStatus.ALARM: "Тревога",
    }
    return labels[status]


def _state_suffix(state: str) -> str:
    return {
        "normal": "normal",
        "warning": "warn",
        "alarm": "alarm",
    }.get(state, "warn")
