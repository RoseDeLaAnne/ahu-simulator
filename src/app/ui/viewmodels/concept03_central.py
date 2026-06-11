from __future__ import annotations

from dataclasses import dataclass

from app.services.status_service import StatusService
from app.simulation.state import AlarmLevel, SimulationSession
from app.ui.concept03.scene3d_overlay import (
    Concept03CalloutView,
    build_concept03_callouts,
)
from app.ui.scene.bindings import SceneBindingRegistry, load_scene_bindings
from app.ui.scene.model_catalog import SceneModelCatalog, build_scene_model_catalog
from app.ui.viewmodels.visualization import build_visualization_signal_map


@dataclass(frozen=True)
class Concept03CanvasTabView:
    tab_id: str
    label: str


@dataclass(frozen=True)
class Concept03SceneModelOptionView:
    model_id: str
    label: str


@dataclass(frozen=True)
class Concept03SceneModeOptionView:
    mode_id: str
    label: str


@dataclass(frozen=True)
class Concept03ParameterRowView:
    group: str
    label: str
    value: str


@dataclass(frozen=True)
class Concept03TrendRowView:
    metric_id: str
    label: str
    value: str
    points: tuple[float, ...]
    unit: str


@dataclass(frozen=True)
class Concept03AlarmRowView:
    code: str
    level: str
    level_text: str
    message: str
    class_name: str


@dataclass(frozen=True)
class Concept03SceneAboutView:
    title: str
    air_path: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class Concept03DocLinkView:
    title: str
    href: str
    description: str


@dataclass(frozen=True)
class Concept03CentralView:
    object_label: str
    installation_label: str
    status_text: str
    tabs: tuple[Concept03CanvasTabView, ...]
    scene_model_options: tuple[Concept03SceneModelOptionView, ...]
    selected_scene_model_id: str | None
    scene_mode_options: tuple[Concept03SceneModeOptionView, ...]
    selected_scene_mode_id: str
    scene_about: Concept03SceneAboutView
    callouts: tuple[Concept03CalloutView, ...]
    parameter_rows: tuple[Concept03ParameterRowView, ...]
    trend_rows: tuple[Concept03TrendRowView, ...]
    alarm_rows: tuple[Concept03AlarmRowView, ...]
    doc_links: tuple[Concept03DocLinkView, ...]
    empty_alarm_text: str


CENTRAL_CANVAS_TABS = (
    Concept03CanvasTabView("3d", "3D Модель"),
    Concept03CanvasTabView("2d", "Схема"),
    Concept03CanvasTabView("parameters", "Параметры"),
    Concept03CanvasTabView("trends", "Тренды"),
    Concept03CanvasTabView("alarms", "Аларма"),
    Concept03CanvasTabView("docs", "Документация"),
)

CONCEPT03_SCENE_MODE_OPTIONS = (
    Concept03SceneModeOptionView("catalog", "3D модели"),
    Concept03SceneModeOptionView("digital_twin", "Цифровой двойник"),
    Concept03SceneModeOptionView("xray", "Рентген"),
    Concept03SceneModeOptionView("schematic", "Схема узлов"),
)


def build_concept03_central_view(
    session: SimulationSession,
    *,
    bindings: SceneBindingRegistry | None = None,
    scene_model_catalog: SceneModelCatalog | None = None,
    status_service: StatusService | None = None,
) -> Concept03CentralView:
    bindings = bindings or load_scene_bindings()
    scene_model_catalog = scene_model_catalog or build_scene_model_catalog()
    status_service = status_service or StatusService()
    result = session.current_result
    signals = build_visualization_signal_map(
        result,
        bindings_version=bindings.version,
        status_service=status_service,
    )
    return Concept03CentralView(
        object_label="Учебно-производственный корпус, помещ. 1.02",
        installation_label="П1 (Приточная)",
        status_text=status_service.status_label(result.state.status),
        tabs=CENTRAL_CANVAS_TABS,
        scene_model_options=_build_scene_model_options(scene_model_catalog),
        selected_scene_model_id=scene_model_catalog.default_model_id,
        scene_mode_options=CONCEPT03_SCENE_MODE_OPTIONS,
        selected_scene_mode_id="catalog",
        scene_about=_build_scene_about(),
        callouts=build_concept03_callouts(signals, bindings),
        parameter_rows=_build_parameter_rows(session),
        trend_rows=_build_trend_rows(session),
        alarm_rows=_build_alarm_rows(session),
        doc_links=_build_doc_links(),
        empty_alarm_text="Нет активных тревог. Все системы в норме.",
    )


def _build_scene_model_options(
    scene_model_catalog: SceneModelCatalog,
) -> tuple[Concept03SceneModelOptionView, ...]:
    return tuple(
        Concept03SceneModelOptionView(model.id, model.label)
        for model in scene_model_catalog.models
    )


def _build_scene_about() -> Concept03SceneAboutView:
    """Видимое в 3D-сцене описание установки.

    Закрывает замечание рецензента «описания я твоего не увидел» и поясняет
    текстом (без замены геометрии): схематичные маркеры узлов, упрощение
    нагрева до электрического калорифера и роль вытяжной ветки как контура
    рекуперации. Описание относится к моделируемой ПВУ в целом и потому
    остаётся корректным при любом выборе 3D-меша.
    """
    return Concept03SceneAboutView(
        title="Приточная вентиляционная установка (ПВУ) с рекуперацией",
        air_path=(
            "Тракт воздуха: воздухозабор → воздушный клапан → фильтр грубой "
            "очистки (G4) → пластинчатый рекуператор → электрический калорифер "
            "→ приточный вентилятор → фильтр тонкой очистки (F7) → водяной "
            "охладитель (летний контур) → шумоглушитель → подача в помещение."
        ),
        notes=(
            "Цветные маркеры — схематичные индикаторы состояния узлов "
            "(норма / предупреждение / тревога), а не геометрия оборудования.",
            "Нагрев упрощён до электрического калорифера: водяной контур и "
            "обвязка не моделируются.",
            "Вытяжная ветка — контур рекуперации: утилизация теплоты "
            "удаляемого воздуха через пластинчатый рекуператор.",
        ),
    )


def _build_parameter_rows(
    session: SimulationSession,
) -> tuple[Concept03ParameterRowView, ...]:
    result = session.current_result
    params = result.parameters
    state = result.state
    scenario_title = result.scenario_title or result.scenario_id or "Пользовательский"
    return (
        Concept03ParameterRowView("Входы оператора", "Сценарий", scenario_title),
        Concept03ParameterRowView("Входы оператора", "Режим", params.control_mode.value),
        Concept03ParameterRowView(
            "Входы оператора",
            "Наружный воздух",
            f"{params.outdoor_temp_c:.1f} °C",
        ),
        Concept03ParameterRowView(
            "Входы оператора",
            "Расход задания",
            f"{params.airflow_m3_h:.0f} м³/ч",
        ),
        Concept03ParameterRowView(
            "Входы оператора",
            "Уставка притока",
            f"{params.supply_temp_setpoint_c:.1f} °C",
        ),
        Concept03ParameterRowView(
            "Входы оператора",
            "КПД рекуперации",
            f"{params.heat_recovery_efficiency * 100:.0f} %",
        ),
        Concept03ParameterRowView(
            "Выходы расчёта",
            "Фактический расход",
            f"{state.actual_airflow_m3_h:.0f} м³/ч",
        ),
        Concept03ParameterRowView(
            "Выходы расчёта",
            "Температура притока",
            f"{state.supply_temp_c:.1f} °C",
        ),
        Concept03ParameterRowView(
            "Выходы расчёта",
            "Температура помещения",
            f"{state.room_temp_c:.1f} °C",
        ),
        Concept03ParameterRowView(
            "Выходы расчёта",
            "ΔP фильтра",
            f"{state.filter_pressure_drop_pa:.0f} Па",
        ),
        Concept03ParameterRowView(
            "Выходы расчёта",
            "Суммарная мощность",
            f"{state.total_power_kw:.1f} кВт",
        ),
        Concept03ParameterRowView(
            "Выходы расчёта",
            "Баланс помещения",
            f"{state.heat_balance_kw:+.1f} кВт",
        ),
    )


def _build_trend_rows(
    session: SimulationSession,
) -> tuple[Concept03TrendRowView, ...]:
    points = session.history.points or session.current_result.trend.points
    if not points:
        state = session.current_result.state
        return (
            Concept03TrendRowView("supply", "Температура притока", f"{state.supply_temp_c:.1f}", (state.supply_temp_c,), "°C"),
            Concept03TrendRowView("room", "Температура помещения", f"{state.room_temp_c:.1f}", (state.room_temp_c,), "°C"),
            Concept03TrendRowView("power", "Мощность", f"{state.total_power_kw:.1f}", (state.total_power_kw,), "кВт"),
            Concept03TrendRowView("filter", "ΔP фильтра", f"{state.filter_pressure_drop_pa:.0f}", (state.filter_pressure_drop_pa,), "Па"),
        )

    last_points = tuple(points[-12:])
    return (
        Concept03TrendRowView(
            "supply",
            "Температура притока",
            f"{last_points[-1].supply_temp_c:.1f}",
            tuple(point.supply_temp_c for point in last_points),
            "°C",
        ),
        Concept03TrendRowView(
            "room",
            "Температура помещения",
            f"{last_points[-1].room_temp_c:.1f}",
            tuple(point.room_temp_c for point in last_points),
            "°C",
        ),
        Concept03TrendRowView(
            "power",
            "Мощность",
            f"{last_points[-1].total_power_kw:.1f}",
            tuple(point.total_power_kw for point in last_points),
            "кВт",
        ),
        Concept03TrendRowView(
            "filter",
            "ΔP фильтра",
            f"{last_points[-1].filter_pressure_drop_pa:.0f}",
            tuple(point.filter_pressure_drop_pa for point in last_points),
            "Па",
        ),
    )


def _build_alarm_rows(
    session: SimulationSession,
) -> tuple[Concept03AlarmRowView, ...]:
    rows: list[Concept03AlarmRowView] = []
    for alarm in session.current_result.alarms:
        rows.append(
            Concept03AlarmRowView(
                code=alarm.code,
                level=alarm.level.value,
                level_text=_alarm_level_text(alarm.level),
                message=alarm.message,
                class_name=f"c03-alarm-row c03-alarm-row--{alarm.level.value}",
            )
        )
    return tuple(rows)


def _alarm_level_text(level: AlarmLevel) -> str:
    return {
        AlarmLevel.INFO: "Инфо",
        AlarmLevel.WARNING: "Предупр",
        AlarmLevel.CRITICAL: "Тревога",
    }[level]


def _build_doc_links() -> tuple[Concept03DocLinkView, ...]:
    return (
        Concept03DocLinkView(
            "Технологическая карта",
            "/docs/02_functionality.md",
            "Контур работы ПВУ и сценарии демонстрации.",
        ),
        Concept03DocLinkView(
            "Формулы",
            "/docs/03_architecture.md",
            "Расчётная модель, допущения и связи модулей.",
        ),
        Concept03DocLinkView(
            "Источники",
            "/docs/10_sources.md",
            "Нормативная и инженерная база проекта.",
        ),
    )
