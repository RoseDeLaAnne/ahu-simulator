from __future__ import annotations

from dataclasses import dataclass

from app.simulation.scenarios import ScenarioDefinition


CONCEPT03_SCENARIO_IDS = (
    "baseline_office_winter",
    "summer_eco",
    "night_min_airflow",
    "freeze_protection",
    "airflow_check_100",
)

CONCEPT03_SCENARIO_PRESENTATION = {
    "baseline_office_winter": ("Номинальный режим", "Базовый офис (зима)", "layout-grid"),
    "summer_eco": ("Зимний режим", "Лето. Экономичный", "snowflake"),
    "night_min_airflow": ("Летний режим", "Ночь. Минимум воздуха", "sun"),
    "freeze_protection": ("Рециркуляция", "Защита от замерзания", "refresh-cw"),
    "airflow_check_100": ("Пожарная вентиляция", "Проверка 100% расхода", "flame"),
}


@dataclass(frozen=True)
class Concept03ScenarioCardView:
    scenario_id: str
    title: str
    sub: str
    icon: str
    is_active: bool
    is_user_preset: bool
    class_name: str


@dataclass(frozen=True)
class Concept03ScenariosView:
    cards: tuple[Concept03ScenarioCardView, ...]
    manage_href: str = "?theme=concept03&page=control"
    add_href: str = "?theme=concept03&page=library"


def build_concept03_scenarios_view(
    scenarios: list[ScenarioDefinition],
    *,
    active_scenario_id: str | None,
) -> Concept03ScenariosView:
    scenario_map = {scenario.id: scenario for scenario in scenarios}
    visible_scenarios = [
        scenario_map[scenario_id]
        for scenario_id in CONCEPT03_SCENARIO_IDS
        if scenario_id in scenario_map
    ]
    resolved_active_id = _resolve_active_scenario_id(
        visible_scenarios,
        active_scenario_id,
    )
    cards = tuple(
        _build_card(scenario, is_active=scenario.id == resolved_active_id)
        for scenario in visible_scenarios
    )
    return Concept03ScenariosView(cards=cards)


def scenario_card_class_name(
    *,
    is_active: bool,
    is_user_preset: bool = False,
) -> str:
    class_names = ["c03-scenario-card"]
    if is_active:
        class_names.append("c03-scenario-card--active")
    if is_user_preset:
        class_names.append("c03-scenario-card--custom")
    return " ".join(class_names)


def _build_card(
    scenario: ScenarioDefinition,
    *,
    is_active: bool,
) -> Concept03ScenarioCardView:
    title, sub, fallback_icon = CONCEPT03_SCENARIO_PRESENTATION[scenario.id]
    is_user_preset = scenario.source == "user"
    return Concept03ScenarioCardView(
        scenario_id=scenario.id,
        title=title,
        sub=sub,
        icon=scenario.icon or fallback_icon,
        is_active=is_active,
        is_user_preset=is_user_preset,
        class_name=scenario_card_class_name(
            is_active=is_active,
            is_user_preset=is_user_preset,
        ),
    )


def _resolve_active_scenario_id(
    scenarios: list[ScenarioDefinition],
    active_scenario_id: str | None,
) -> str | None:
    scenario_ids = {scenario.id for scenario in scenarios}
    if active_scenario_id in scenario_ids:
        return active_scenario_id
    return None
