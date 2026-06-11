from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.services.demo_readiness_service import DemoReadinessEvaluation
from app.services.project_baseline_service import ProjectBaselineSnapshot
from app.simulation.state import OperationStatus, SimulationResult


INSTALLATION_TITLE = "ЦИФРОВОЙ ДВОЙНИК ВЕНТИЛЯЦИОННОЙ УСТАНОВКИ П1"
INSTALLATION_SUBTITLE = "Моделирование работы приточной установки"


@dataclass(frozen=True)
class Concept03StatusPillView:
    pill_id: str
    icon: str
    title: str
    sub: str
    state: str


@dataclass(frozen=True)
class Concept03HeaderView:
    brand_short: str
    brand_full: str
    title_uppercase: str
    subtitle: str
    status_pills: tuple[Concept03StatusPillView, ...]
    generated_at: datetime
    user_initials: str = "S"

    @property
    def date_text(self) -> str:
        return self.generated_at.strftime("%d.%m.%Y")

    @property
    def time_text(self) -> str:
        return self.generated_at.strftime("%H:%M:%S")


def build_concept03_header_view(
    project_baseline: ProjectBaselineSnapshot,
    current_result: SimulationResult,
    demo_readiness: DemoReadinessEvaluation,
) -> Concept03HeaderView:
    return Concept03HeaderView(
        brand_short="К-АСКАД ГРУП",
        brand_full="ООО НПО Каскад-ГРУП",
        title_uppercase=INSTALLATION_TITLE,
        subtitle=INSTALLATION_SUBTITLE,
        status_pills=(
            Concept03StatusPillView(
                pill_id="concept03-readiness-pill",
                icon="shield-check",
                title="РЕЖИМ",
                sub="ГОТОВНОСТИ",
                state=_status_to_pill_state(demo_readiness.overall_status),
            ),
            Concept03StatusPillView(
                pill_id="concept03-sync-pill",
                icon="refresh-cw",
                title="СИНХРОНИЗАЦИЯ",
                sub=_operation_label(current_result.state.status),
                state=_status_to_pill_state(current_result.state.status),
            ),
        ),
        generated_at=max(current_result.timestamp, project_baseline.generated_at),
    )


def build_header_state_payload(result: SimulationResult) -> dict[str, str]:
    alarms = result.alarms
    critical_count = sum(1 for a in alarms if a.level.value == "critical")
    warning_count = sum(1 for a in alarms if a.level.value == "warning")
    total = len(alarms)
    highest = (
        "critical" if critical_count > 0
        else "warning" if warning_count > 0
        else "normal"
    )
    return {
        "operation_status": result.state.status.value,
        "operation_label": _operation_label(result.state.status),
        "alarm_count": str(total),
        "highest_alarm_level": highest,
    }


def _status_to_pill_state(status: OperationStatus) -> str:
    if status == OperationStatus.NORMAL:
        return "ok"
    if status == OperationStatus.WARNING:
        return "warn"
    return "alarm"


def _operation_label(status: OperationStatus) -> str:
    labels = {
        OperationStatus.NORMAL: "Активна",
        OperationStatus.WARNING: "Риск",
        OperationStatus.ALARM: "Авария",
    }
    return labels[status]
