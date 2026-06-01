from __future__ import annotations

from dataclasses import dataclass

from app.simulation.parameters import ControlMode


@dataclass(frozen=True)
class Concept03ModeCardView:
    mode_id: str
    title: str
    sub: str
    icon: str
    is_active: bool
    class_name: str


@dataclass(frozen=True)
class Concept03ModesView:
    cards: tuple[Concept03ModeCardView, ...]


MODE_PRESENTATION = (
    (
        ControlMode.AUTO,
        "Автоматический",
        "Работает по заданному сценарию",
        "cpu",
    ),
    (
        ControlMode.SEMI_AUTO,
        "Полуавтоматический",
        "Операторский контроль",
        "sliders-horizontal",
    ),
    (
        ControlMode.MANUAL,
        "Ручной",
        "Ручное управление оборудованием",
        "hand",
    ),
    (
        ControlMode.TEST,
        "Тестовый",
        "Испытания и наладка",
        "flask-conical",
    ),
)


def build_concept03_modes_view(
    active_mode: ControlMode | str | None,
) -> Concept03ModesView:
    mode = _coerce_mode(active_mode)
    cards = tuple(
        Concept03ModeCardView(
            mode_id=mode_id.value,
            title=title,
            sub=sub,
            icon=icon,
            is_active=mode_id == mode,
            class_name=mode_card_class_name(is_active=mode_id == mode),
        )
        for mode_id, title, sub, icon in MODE_PRESENTATION
    )
    return Concept03ModesView(cards=cards)


def mode_card_class_name(*, is_active: bool) -> str:
    class_names = ["c03-mode-card"]
    if is_active:
        class_names.append("c03-mode-card--active")
    return " ".join(class_names)


def _coerce_mode(value: ControlMode | str | None) -> ControlMode:
    if isinstance(value, ControlMode):
        return value
    if value is not None:
        try:
            return ControlMode(value)
        except ValueError:
            pass
    return ControlMode.AUTO
