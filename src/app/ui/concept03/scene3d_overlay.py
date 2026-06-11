from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dash import html

from app.simulation.state import OperationStatus
from app.ui.concept03.components.icon import Icon
from app.ui.scene.bindings import SceneBindingRegistry

if TYPE_CHECKING:
    from app.ui.viewmodels.visualization import (
        VisualizationSignalMap,
        VisualElementState,
    )


@dataclass(frozen=True)
class Concept03CalloutRowView:
    label: str
    value: str


@dataclass(frozen=True)
class Concept03CalloutView:
    callout_id: str
    visual_id: str
    scene_node: str
    title: str
    rows: tuple[Concept03CalloutRowView, ...]
    state: str
    side: str
    fallback_x_pct: float
    fallback_y_pct: float
    class_name: str


_CALLOUT_LAYOUTS = (
    {
        "callout_id": "outdoor-air",
        "visual_id": "outdoor_air",
        "title": "Наружный воздух",
        "side": "left",
        "x": 11.0,
        "y": 20.0,
    },
    {
        "callout_id": "filter-coarse",
        "visual_id": "filter_bank",
        "title": "Фильтр грубой очистки",
        "side": "top",
        "x": 29.0,
        "y": 17.0,
    },
    {
        "callout_id": "recuperator",
        "visual_id": "recuperator_core",
        "title": "Пластинчатый рекуператор",
        "side": "top",
        "x": 36.0,
        "y": 17.0,
    },
    {
        "callout_id": "heater-coil",
        "visual_id": "heater_coil",
        "title": "Электрический калорифер",
        "side": "top",
        "x": 43.5,
        "y": 18.0,
    },
    {
        "callout_id": "supply-fan",
        "visual_id": "supply_fan",
        "title": "Вентилятор",
        "side": "top",
        "x": 56.0,
        "y": 18.0,
    },
    {
        "callout_id": "filter-fine",
        "visual_id": "filter_fine",
        "title": "Фильтр тонкой очистки",
        "side": "top",
        "x": 68.5,
        "y": 18.0,
    },
    {
        "callout_id": "cooler-coil",
        "visual_id": "cooler_coil",
        "title": "Водяной охладитель",
        "side": "bottom",
        "x": 47.0,
        "y": 78.0,
    },
    {
        "callout_id": "silencer",
        "visual_id": "silencer",
        "title": "Шумоглушитель",
        "side": "bottom",
        "x": 74.0,
        "y": 76.0,
    },
    {
        "callout_id": "room-supply",
        "visual_id": "room_supply",
        "title": "Приточный воздух",
        "side": "right",
        "x": 89.0,
        "y": 22.0,
    },
    {
        "callout_id": "room-zone",
        "visual_id": "room_zone",
        "title": "Помещение",
        "side": "right",
        "x": 87.0,
        "y": 61.0,
        "defense_only": True,
    },
)


def build_concept03_callouts(
    signals: VisualizationSignalMap,
    bindings: SceneBindingRegistry,
) -> tuple[Concept03CalloutView, ...]:
    binding_by_visual_id = {
        binding.visual_id: binding.scene_node for binding in bindings.bindings
    }
    callouts: list[Concept03CalloutView] = []
    for layout in _CALLOUT_LAYOUTS:
        visual_id = str(layout["visual_id"])
        signal = signals.nodes.get(visual_id) or signals.sensors.get(visual_id)
        if signal is None:
            continue
        state = str(signal.state.value)
        callouts.append(
            Concept03CalloutView(
                callout_id=str(layout["callout_id"]),
                visual_id=visual_id,
                scene_node=binding_by_visual_id.get(visual_id, visual_id),
                title=str(layout["title"]),
                rows=_rows_for_signal(visual_id, signal),
                state=state,
                side=str(layout["side"]),
                fallback_x_pct=float(layout["x"]),
                fallback_y_pct=float(layout["y"]),
                class_name=callout_class_name(state)
                + (" c03-defense-only" if layout.get("defense_only") else ""),
            )
        )
    return tuple(callouts)


def callout_class_name(state: str) -> str:
    suffix = {
        OperationStatus.NORMAL.value: "normal",
        OperationStatus.WARNING.value: "warn",
        OperationStatus.ALARM.value: "alarm",
    }.get(state, "normal")
    return f"c03-callout c03-callout--{suffix}"


def build_scene3d_overlay(callouts: tuple[Concept03CalloutView, ...]) -> list:
    return [
        build_callout_layer(callouts),
        build_compass_widget(),
        html.Div(
            className="c03-webgl-fallback",
            children=[
                html.ObjectEl(
                    id="concept03-fallback-mnemonic-object",
                    data="assets/pvu_mnemonic.svg",
                    type="image/svg+xml",
                    className="c03-fallback-mnemonic",
                ),
                html.Div(
                    className="c03-webgl-fallback__copy",
                    children=[
                        html.Strong("2D fallback"),
                        html.Span("WebGL недоступен, показана мнемосхема."),
                    ],
                ),
            ],
        ),
    ]


def build_callout_layer(callouts: tuple[Concept03CalloutView, ...]) -> html.Div:
    return html.Div(
        id="concept03-callout-layer",
        className="c03-callout-layer",
        children=build_callout_items(callouts),
    )


def build_callout_items(callouts: tuple[Concept03CalloutView, ...]) -> list:
    return [_build_callout(callout) for callout in callouts]


def build_camera_tools() -> html.Div:
    tools = (
        ("view-orbit", "rotate-3d", "Орбита", ""),
        ("view-fit", "scan", "Вписать", ""),
        ("view-fullscreen", "maximize", "Во весь экран", ""),
        ("view-front", "layout-grid", "Фронт", " c03-defense-only"),
        ("view-section", "filter", "Сечение", " c03-defense-only"),
        ("view-split", "boxes", "Разделить", " c03-defense-only"),
        ("view-layers", "sliders-horizontal", "Слои", " c03-defense-only"),
        ("capture-png", "download", "Снимок PNG", " c03-defense-only"),
    )
    return html.Div(
        className="c03-camera-tools",
        children=[
            html.Button(
                Icon(icon, 16, class_name="c03-camera-tool__icon"),
                type="button",
                className=f"c03-camera-tool{extra_class}",
                title=label,
                **{
                    "aria-label": label,
                    "data-camera-tool": tool_id,
                },
            )
            for tool_id, icon, label, extra_class in tools
        ],
    )


def build_compass_widget() -> html.Div:
    return html.Div(
        id="concept03-compass",
        className="c03-compass",
        title="Направление камеры",
        **{"aria-label": "Направление камеры"},
        children=[
            html.Span("С", className="c03-compass__north"),
            html.Span("Ю", className="c03-compass__south"),
            html.Span("З", className="c03-compass__west"),
            html.Span("В", className="c03-compass__east"),
            html.Span(id="concept03-compass-needle", className="c03-compass__needle"),
        ],
    )


def build_pagination_dots() -> html.Div:
    presets = (
        ("hero", "Общий план"),
        ("front", "Фронт"),
        ("top", "Вид сверху"),
        ("service", "Сервис"),
        ("room", "Помещение"),
    )
    return html.Div(
        className="c03-canvas-dots",
        children=[
            html.Button(
                type="button",
                className="c03-canvas-dot"
                + (" c03-canvas-dot--active" if index == 0 else ""),
                title=label,
                **{
                    "aria-label": label,
                    "data-camera-preset": preset,
                },
            )
            for index, (preset, label) in enumerate(presets)
        ],
    )


def _build_callout(callout: Concept03CalloutView) -> html.Div:
    return html.Div(
        id=f"concept03-callout-{callout.callout_id}",
        className=f"{callout.class_name} c03-callout--{callout.side}",
        style={
            "--callout-x": f"{callout.fallback_x_pct}%",
            "--callout-y": f"{callout.fallback_y_pct}%",
        },
        **{
            "data-callout-id": callout.callout_id,
            "data-visual-id": callout.visual_id,
            "data-scene-node": callout.scene_node,
            "data-state": callout.state,
        },
        children=[
            html.Span(className="c03-callout__pin", **{"aria-hidden": "true"}),
            html.Span(
                className="c03-callout__card",
                children=[
                    html.Strong(callout.title, className="c03-callout__title"),
                    html.Span(
                        className="c03-callout__rows",
                        children=[
                            html.Span(
                                className="c03-callout__row",
                                children=[
                                    html.Span(row.label),
                                    html.Strong(row.value),
                                ],
                            )
                            for row in callout.rows
                        ],
                    ),
                ],
            ),
        ],
    )


def _rows_for_signal(
    visual_id: str,
    signal: VisualElementState,
) -> tuple[Concept03CalloutRowView, ...]:
    labels = {
        "outdoor_air": ("T", "После рекуп."),
        "filter_bank": ("ΔP", "Загрязнение"),
        "recuperator_core": ("КПД", "Приток"),
        "heater_coil": ("Мощн.", "Загрузка"),
        "supply_fan": ("P", "Режим"),
        "filter_fine": ("ΔP", "Класс"),
        "cooler_coil": ("ΔT", "Контур"),
        "silencer": ("ΔP", "Секция"),
        "room_supply": ("Подача", "Расход"),
        "room_zone": ("T room", "Баланс"),
    }.get(visual_id, ("Знач.", "Деталь"))
    rows = [Concept03CalloutRowView(labels[0], signal.value)]
    if signal.detail:
        rows.append(Concept03CalloutRowView(labels[1], signal.detail))
    return tuple(rows[:2])
