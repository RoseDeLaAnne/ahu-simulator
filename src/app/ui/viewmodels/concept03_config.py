from __future__ import annotations

from dataclasses import dataclass

from app.services.project_baseline_service import ProjectBaselineSnapshot
from app.simulation.state import SimulationResult


@dataclass(frozen=True)
class Concept03ConfigItemView:
    label: str
    value: str


@dataclass(frozen=True)
class Concept03ConfigView:
    title: str
    items: tuple[Concept03ConfigItemView, ...]
    properties_href: str = "?theme=concept03&page=settings"


def build_concept03_config_view(
    *,
    project_baseline: ProjectBaselineSnapshot,
    current_result: SimulationResult,
) -> Concept03ConfigView:
    parameters = current_result.parameters
    subject_title = project_baseline.subject.title
    installation_type = (
        "Учебная ПВУ"
        if "приточная" in subject_title.lower()
        else subject_title[:32]
    )
    items = (
        Concept03ConfigItemView("Тип установки", installation_type),
        Concept03ConfigItemView(
            "Производительность",
            f"{parameters.airflow_m3_h:,.0f} м³/ч".replace(",", " "),
        ),
        Concept03ConfigItemView("Напор (ном.)", "700 Па"),
        Concept03ConfigItemView("Класс фильтрации", "F7 + F9"),
        Concept03ConfigItemView("Рекуператор", "Пластинчатый"),
        Concept03ConfigItemView("Нагреватель", "Водяной"),
    )
    return Concept03ConfigView(
        title="Конфигурация установки",
        items=items,
    )
