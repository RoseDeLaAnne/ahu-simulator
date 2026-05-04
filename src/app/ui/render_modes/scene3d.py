from __future__ import annotations

from dash import dcc, html

from app.services.status_service import StatusService
from app.simulation.state import OperationStatus
from app.ui.scene.model_catalog import SceneModelCatalog, SceneModelDescriptor
from app.ui.scene.room_catalog import (
    RoomCatalog,
    RoomCatalogDescriptor,
)

SCENE3D_TRANSFORM_CONTROLS = (
    {
        "key": "model_scale",
        "label": "Общий масштаб установки",
        "min": 0.1,
        "max": 12,
        "step": 0.05,
        "value": 1.0,
        "section": "Модель установки",
    },
    {
        "key": "model_long_scale",
        "label": "Длина установки",
        "min": 0.1,
        "max": 5,
        "step": 0.05,
        "value": 1.0,
        "section": "Модель установки",
    },
    {
        "key": "model_side_scale",
        "label": "Ширина установки",
        "min": 0.1,
        "max": 5,
        "step": 0.05,
        "value": 1.0,
        "section": "Модель установки",
    },
    {
        "key": "model_vertical_scale",
        "label": "Высота установки",
        "min": 0.1,
        "max": 5,
        "step": 0.05,
        "value": 1.0,
        "section": "Модель установки",
    },
    {
        "key": "model_long_delta",
        "label": "Модель вдоль",
        "min": -8,
        "max": 8,
        "step": 0.01,
        "value": 0.0,
        "section": "Модель установки",
    },
    {
        "key": "model_side_delta",
        "label": "Модель вбок",
        "min": -8,
        "max": 8,
        "step": 0.01,
        "value": 0.0,
        "section": "Модель установки",
    },
    {
        "key": "model_vertical_delta",
        "label": "Модель вверх",
        "min": -5,
        "max": 5,
        "step": 0.01,
        "value": 0.0,
        "section": "Модель установки",
    },
    {
        "key": "model_rotation_delta_deg",
        "label": "Поворот модели, °",
        "min": -360,
        "max": 360,
        "step": 1,
        "value": 0.0,
        "section": "Модель установки",
    },
    {
        "key": "model_pitch_delta_deg",
        "label": "Наклон модели, °",
        "min": -90,
        "max": 90,
        "step": 1,
        "value": 0.0,
        "section": "Модель установки",
    },
    {
        "key": "model_roll_delta_deg",
        "label": "Крен модели, °",
        "min": -90,
        "max": 90,
        "step": 1,
        "value": 0.0,
        "section": "Модель установки",
    },
    {
        "key": "room_scale",
        "label": "Масштаб помещения",
        "min": 0.1,
        "max": 16,
        "step": 0.05,
        "value": 1.0,
        "section": "Помещение",
    },
    {
        "key": "room_long_delta",
        "label": "Помещение вдоль",
        "min": -8,
        "max": 8,
        "step": 0.01,
        "value": 0.0,
        "section": "Помещение",
    },
    {
        "key": "room_side_delta",
        "label": "Помещение вбок",
        "min": -8,
        "max": 8,
        "step": 0.01,
        "value": 0.0,
        "section": "Помещение",
    },
    {
        "key": "room_vertical_delta",
        "label": "Помещение вверх",
        "min": -5,
        "max": 5,
        "step": 0.01,
        "value": 0.0,
        "section": "Помещение",
    },
    {
        "key": "room_rotation_delta_deg",
        "label": "Поворот помещения, °",
        "min": -360,
        "max": 360,
        "step": 1,
        "value": 0.0,
        "section": "Помещение",
    },
)


def build_scene3d_workspace(
    scene_model_catalog: SceneModelCatalog,
    selected_scene_model: SceneModelDescriptor | None,
    scenario_options: list[dict[str, str]],
    default_scenario_id: str,
    room_catalog: RoomCatalog,
    default_room: RoomCatalogDescriptor | None,
    developer_tools_enabled: bool = False,
) -> html.Div:
    status_service = StatusService()
    return html.Div(
        id="scene-3d-wrapper",
        className="scene3d-workspace",
        style={"display": "none"},
        children=[
            _scene3d_top_toolbar(scene_model_catalog),
            html.Div(
                className="scene3d-stage-grid",
                children=[
                    _scene3d_stage_column(),
                    _scene3d_kpi_sidebar(status_service),
                ],
            ),
            _scene3d_secondary_grid(
                scene_model_catalog=scene_model_catalog,
                selected_scene_model=selected_scene_model,
                scenario_options=scenario_options,
                default_scenario_id=default_scenario_id,
                room_catalog=room_catalog,
                default_room=default_room,
                developer_tools_enabled=developer_tools_enabled,
            ),
        ],
    )


def _scene3d_top_toolbar(scene_model_catalog: SceneModelCatalog) -> html.Div:
    return html.Div(
        className="scene3d-toolbar",
        children=[
            _scene3d_dropdown_card(
                "Модель установки",
                dcc.Dropdown(
                    id="scene3d-model-select",
                    options=[
                        {
                            "label": model.label,
                            "value": model.id,
                        }
                        for model in scene_model_catalog.models
                    ],
                    value=scene_model_catalog.default_model_id,
                    clearable=False,
                    searchable=False,
                    optionHeight=48,
                    maxHeight=320,
                ),
            ),
            _scene3d_dropdown_card(
                "Режим сцены",
                dcc.Dropdown(
                    id="scene3d-display-mode",
                    options=[
                        {"label": "Студия", "value": "studio"},
                        {"label": "Рентген", "value": "xray"},
                        {"label": "Схема", "value": "schematic"},
                    ],
                    value="studio",
                    clearable=False,
                    searchable=False,
                    optionHeight=48,
                    maxHeight=320,
                ),
            ),
            _scene3d_dropdown_card(
                "Камера",
                dcc.Dropdown(
                    id="scene3d-camera-preset",
                    options=[
                        {"label": "Общий план", "value": "hero"},
                        {"label": "Сервисный ракурс", "value": "service"},
                        {"label": "Вид сверху", "value": "top"},
                    ],
                    value="hero",
                    clearable=False,
                    searchable=False,
                    optionHeight=48,
                    maxHeight=320,
                ),
            ),
        ],
    )


def _scene3d_stage_column() -> html.Div:
    return html.Div(
        className="scene3d-stage-column",
        children=[
            html.Div(
                id="scene-3d-canvas",
                className="scene-3d-container",
            ),
        ],
    )


def _scene3d_kpi_sidebar(status_service: StatusService) -> html.Div:
    """Right-side compact engineering KPI deck.

    Reuses existing live-signal element IDs (scene3d-live-status,
    scene3d-live-summary, scene3d-live-outdoor, scene3d-live-supply,
    scene3d-live-airflow, scene3d-live-filter, scene3d-live-room,
    scene3d-live-mode) so that the existing callbacks in callbacks.py
    keep working unchanged. Russian terminology follows ОВК практику:
    ПВУ, расход, ΔP, температура подачи (см.
    docs/10_sources.md, раздел "Отечественная источниковая база 3D/ОВК").
    """

    return html.Div(
        className="scene3d-sidebar",
        children=[
            html.Div(
                className="scene3d-card scene3d-status-card",
                children=[
                    html.Div(
                        className="browser-panel-header",
                        children=[
                            html.H3("Состояние ПВУ"),
                            html.Div(
                                id="scene3d-live-status",
                                className=status_service.status_class_name(
                                    OperationStatus.NORMAL
                                ),
                                children=status_service.status_label(
                                    OperationStatus.NORMAL
                                ),
                            ),
                        ],
                    ),
                    html.P(
                        id="scene3d-live-summary",
                        className="scene3d-live-summary",
                        children=(
                            "После загрузки параметров здесь появится "
                            "краткая live-сводка по установке."
                        ),
                    ),
                ],
            ),
            html.Div(
                className="scene3d-card scene3d-kpi-deck",
                children=[
                    html.Div(
                        className="browser-panel-header",
                        children=[
                            html.H3("Ключевые показатели"),
                            html.Span(
                                "LIVE",
                                className="panel-tag",
                            ),
                        ],
                    ),
                    html.Div(
                        className="scene3d-kpi-grid",
                        children=[
                            _scene3d_kpi_tile(
                                "Расход воздуха",
                                "scene3d-live-airflow",
                                accent="airflow",
                            ),
                            _scene3d_kpi_tile(
                                "ΔP фильтра",
                                "scene3d-live-filter",
                                accent="pressure",
                            ),
                            _scene3d_kpi_tile(
                                "Температура подачи",
                                "scene3d-live-supply",
                                accent="temperature",
                            ),
                            _scene3d_kpi_tile(
                                "Температура помещения",
                                "scene3d-live-room",
                                accent="room",
                            ),
                            _scene3d_kpi_tile(
                                "Наружный воздух",
                                "scene3d-live-outdoor",
                                accent="outdoor",
                            ),
                            _scene3d_kpi_tile(
                                "Режим/модель",
                                "scene3d-live-mode",
                                accent="mode",
                            ),
                        ],
                    ),
                    html.P(
                        "Для возврата в 2D-режим используйте кнопку «2D» "
                        "в шапке панели «Цифровой двойник».",
                        className="scene3d-fallback-hint",
                    ),
                ],
            ),
        ],
    )


def _scene3d_secondary_grid(
    *,
    scene_model_catalog: SceneModelCatalog,
    selected_scene_model: SceneModelDescriptor | None,
    scenario_options: list[dict[str, str]],
    default_scenario_id: str,
    room_catalog: RoomCatalog,
    default_room: RoomCatalogDescriptor | None,
    developer_tools_enabled: bool = False,
) -> html.Div:
    """Сетка ниже основного экрана: параметры, профиль модели, помещение,
    локальные датчики. Здесь живут все элементы управления и информационные
    карточки, которые не должны соревноваться за внимание с главным
    viewport. Все существующие IDs сохраняются."""

    del scene_model_catalog  # не используется в этой сетке, оставлен для совместимости
    return html.Div(
        className="scene3d-secondary-grid",
        children=[
            _scene3d_control_deck_card(
                scenario_options=scenario_options,
                default_scenario_id=default_scenario_id,
                room_catalog=room_catalog,
                default_room=default_room,
                developer_tools_enabled=developer_tools_enabled,
            ),
            _scene3d_reference_card(selected_scene_model),
            _scene3d_room_card(default_room),
            _scene3d_room_sensors_card(),
        ],
    )


def _scene3d_control_deck_card(
    *,
    scenario_options: list[dict[str, str]],
    default_scenario_id: str,
    room_catalog: RoomCatalog,
    default_room: RoomCatalogDescriptor | None,
    developer_tools_enabled: bool = False,
) -> html.Div:
    return html.Div(
        className="scene3d-card scene3d-control-deck",
        children=[
            html.Div(
                className="browser-panel-header",
                children=[
                    html.H3("Пульт управления сценой"),
                    html.Div(
                        className="panel-tag",
                        children="ВХОДНЫЕ ПАРАМЕТРЫ",
                    ),
                ],
            ),
            html.P(
                "Меняйте входные параметры — узлы, потоки и помещение "
                "пересчитываются мгновенно.",
                className="validation-intro",
            ),
            _scene3d_dropdown_card(
                "Сценарий",
                dcc.Dropdown(
                    id="scene3d-scenario-select",
                    options=scenario_options,
                    value=default_scenario_id,
                    clearable=False,
                    searchable=False,
                    optionHeight=48,
                    maxHeight=320,
                ),
            ),
            _scene3d_dropdown_card(
                "Помещение",
                dcc.Dropdown(
                    id="scene3d-room-select",
                    options=[
                        {"label": room.label, "value": room.id}
                        for room in room_catalog.rooms
                    ],
                    value=room_catalog.default_room_id,
                    clearable=False,
                    searchable=False,
                    optionHeight=48,
                    maxHeight=320,
                ),
            ),
            _scene3d_dropdown_card(
                "Наглядный режим",
                dcc.Dropdown(
                    id="scene3d-room-preset",
                    options=[
                        {"label": preset.label, "value": preset.id}
                        for preset in (
                            default_room.presets if default_room else []
                        )
                    ],
                    value=(
                        default_room.default_preset_id
                        if default_room
                        else None
                    ),
                    clearable=False,
                    searchable=False,
                    optionHeight=48,
                    maxHeight=320,
                ),
            ),
            html.Div(
                className="scene3d-param-grid",
                children=[
                    _scene3d_number_field(
                        "Наружная температура, °C",
                        "scene3d-outdoor-temp",
                        -45,
                        45,
                        0.5,
                        0.0,
                    ),
                    _scene3d_number_field(
                        "Расход воздуха, м³/ч",
                        "scene3d-airflow",
                        200,
                        8000,
                        50,
                        3000.0,
                    ),
                    _scene3d_number_field(
                        "Уставка притока, °C",
                        "scene3d-setpoint",
                        10,
                        35,
                        0.5,
                        19.0,
                    ),
                    _scene3d_number_field(
                        "КПД рекуперации",
                        "scene3d-recovery-efficiency",
                        0,
                        0.85,
                        0.01,
                        0.45,
                    ),
                    _scene3d_number_field(
                        "Нагреватель, кВт",
                        "scene3d-heater-power",
                        0,
                        120,
                        0.5,
                        18.0,
                    ),
                    _scene3d_number_field(
                        "Загрязнение фильтра",
                        "scene3d-filter-contamination",
                        0,
                        1,
                        0.01,
                        0.15,
                    ),
                    _scene3d_number_field(
                        "Скорость вентилятора",
                        "scene3d-fan-speed",
                        0.2,
                        1.2,
                        0.01,
                        0.86,
                    ),
                    _scene3d_number_field(
                        "Температура помещения, °C",
                        "scene3d-room-temp",
                        5,
                        40,
                        0.1,
                        21.2,
                    ),
                    _scene3d_number_field(
                        "Теплопритоки, кВт",
                        "scene3d-room-heat-gain",
                        -10,
                        40,
                        0.1,
                        4.2,
                    ),
                    _scene3d_number_field(
                        "Людей в помещении",
                        "scene3d-room-occupancy",
                        0,
                        200,
                        1,
                        (
                            default_room.design_occupancy_people
                            if default_room
                            else 8
                        ),
                    ),
                    _scene3d_number_field(
                        "Влажность в помещении, %",
                        "scene3d-room-humidity",
                        20,
                        85,
                        1,
                        (
                            default_room.local_humidity_baseline_percent
                            if default_room
                            else 42
                        ),
                    ),
                ],
            ),
            _scene3d_dropdown_card(
                "Режим управления",
                dcc.Dropdown(
                    id="scene3d-control-mode",
                    options=[
                        {"label": "Авто", "value": "auto"},
                        {"label": "Ручной", "value": "manual"},
                    ],
                    value="auto",
                    clearable=False,
                    searchable=False,
                    optionHeight=48,
                    maxHeight=320,
                ),
            ),
            *(
                [_scene3d_developer_transform_controls()]
                if developer_tools_enabled
                else []
            ),
        ],
    )


def _scene3d_reference_card(
    selected_scene_model: SceneModelDescriptor | None,
) -> html.Div:
    return html.Div(
        className="scene3d-card scene3d-reference-card",
        children=[
            html.Div(
                className="browser-panel-header",
                children=[
                    html.H3("Профиль модели"),
                    html.Div(
                        id="scene3d-model-tone",
                        className="panel-tag",
                        children=(
                            selected_scene_model.tone.upper()
                            if selected_scene_model
                            else "МОДЕЛЬ"
                        ),
                    ),
                ],
            ),
            html.P(
                "Для каждой GLB используется собственный профиль "
                "привязок, камеры и сцены.",
                className="validation-intro",
            ),
            html.Img(
                id="scene3d-model-preview",
                src=(
                    selected_scene_model.preview_url
                    if selected_scene_model
                    else None
                ),
                className="scene3d-reference-image",
                alt=(
                    selected_scene_model.label
                    if selected_scene_model
                    else "Справка по модели"
                ),
            ),
            html.H4(
                id="scene3d-model-title",
                className="scene3d-model-title",
                children=(
                    selected_scene_model.label
                    if selected_scene_model
                    else "3D-модель"
                ),
            ),
            html.P(
                id="scene3d-model-description",
                className="mnemonic-note",
                children=(
                    selected_scene_model.description
                    if selected_scene_model
                    else "Выберите модель для визуализации цифрового двойника."
                ),
            ),
        ],
    )


def _scene3d_room_card(
    default_room: RoomCatalogDescriptor | None,
) -> html.Div:
    return html.Div(
        className="scene3d-card scene3d-room-card",
        children=[
            html.Div(
                className="browser-panel-header",
                children=[html.H3("Каталог помещений")],
            ),
            html.H4(
                id="scene3d-room-title",
                className="scene3d-model-title",
                children=(
                    default_room.label if default_room else "Помещение"
                ),
            ),
            html.P(
                id="scene3d-room-description",
                className="mnemonic-note",
                children=(
                    default_room.description
                    if default_room
                    else "Выберите модель помещения для цифрового двойника."
                ),
            ),
            html.P(
                id="scene3d-room-climate",
                className="validation-intro",
                children=(
                    default_room.climate_note
                    if default_room
                    else "Здесь появится режим помещения."
                ),
            ),
            html.Div(
                className="scene3d-live-grid scene3d-room-meta-grid",
                children=[
                    _scene3d_stat("Объём", "scene3d-room-volume"),
                    _scene3d_stat("Теплоёмкость", "scene3d-room-capacity"),
                    _scene3d_stat("Потери", "scene3d-room-loss"),
                    _scene3d_stat(
                        "Проектная загрузка",
                        "scene3d-room-design-occupancy",
                    ),
                ],
            ),
            html.Div(
                id="scene3d-room-sensors",
                className="capability-list",
                children=[
                    html.Div(
                        (
                            "Локальные датчики CO₂, влажности и "
                            "заполненности будут показаны здесь."
                        ),
                        className="capability-item",
                    )
                ],
            ),
            html.P(
                id="scene3d-room-preset-note",
                className="validation-intro",
                children=(
                    default_room.presets[0].explanation
                    if default_room and default_room.presets
                    else "Здесь появится пояснение выбранного режима."
                ),
            ),
        ],
    )


def _scene3d_room_sensors_card() -> html.Div:
    return html.Div(
        className="scene3d-card scene3d-live-card",
        children=[
            html.Div(
                className="browser-panel-header",
                children=[html.H3("Датчики помещения")],
            ),
            html.Div(
                className="scene3d-live-grid",
                children=[
                    _scene3d_stat("CO₂", "scene3d-room-co2"),
                    _scene3d_stat(
                        "Влажность", "scene3d-room-humidity-live"
                    ),
                    _scene3d_stat(
                        "Занятость", "scene3d-room-occupancy-live"
                    ),
                    _scene3d_stat(
                        "Качество воздуха", "scene3d-room-air-quality"
                    ),
                    _scene3d_stat(
                        "Активный режим", "scene3d-room-preset-active"
                    ),
                    _scene3d_stat(
                        "Свежий воздух/чел", "scene3d-room-fresh-air"
                    ),
                ],
            ),
        ],
    )


def _scene3d_kpi_tile(label: str, element_id: str, *, accent: str) -> html.Div:
    """Compact KPI tile for the right sidebar.

    Renders a single live signal value as an emphasized engineering
    KPI block (label + value). The `accent` class hint controls colour
    accents in CSS so потоки, давление, температура и помещение
    выглядят визуально разными.
    """

    return html.Div(
        className=f"scene3d-kpi-tile scene3d-kpi-tile--{accent}",
        children=[
            html.Span(label, className="scene3d-kpi-tile__label"),
            html.Strong(
                "—",
                id=element_id,
                className="scene3d-kpi-tile__value",
            ),
        ],
    )


def _scene3d_dropdown_card(label: str, control: dcc.Dropdown) -> html.Div:
    return html.Div(
        className="scene3d-control",
        children=[
            html.Span(label, className="field-label"),
            control,
        ],
    )


def _scene3d_number_field(
    label: str,
    component_id: str,
    min_value: float,
    max_value: float,
    step: float,
    value: float,
) -> html.Div:
    return html.Div(
        className="field-block scene3d-field-block",
        children=[
            html.Label(label, className="field-label", htmlFor=component_id),
            dcc.Input(
                id=component_id,
                type="number",
                min=min_value,
                max=max_value,
                step=step,
                value=value,
                debounce=True,
                className="number-input scene3d-number-input",
            ),
        ],
    )


def _scene3d_developer_transform_controls() -> html.Details:
    controls_by_section: dict[str, list[dict[str, object]]] = {}
    for control in SCENE3D_TRANSFORM_CONTROLS:
        controls_by_section.setdefault(str(control["section"]), []).append(control)

    return html.Details(
        className="scene3d-dev-controls",
        open=True,
        children=[
            html.Summary(
                className="scene3d-dev-controls__summary",
                children=[
                    html.Span("Dev: трансформации сцены"),
                    html.Span("только разработчик", className="detail-tag"),
                ],
            ),
            html.Div(
                className="scene3d-dev-controls__body",
                children=[
                    html.Div(
                        className="scene3d-dev-controls__toolbar",
                        children=[
                            html.Span("Live transform", className="detail-tag"),
                            html.Button(
                                "Сброс",
                                id="scene3d-dev-transform-reset",
                                n_clicks=0,
                                type="button",
                                className="action-btn scene3d-dev-reset",
                            ),
                        ],
                    ),
                    *[
                        _scene3d_transform_group(section, controls)
                        for section, controls in controls_by_section.items()
                    ],
                ],
            ),
        ],
    )


def _scene3d_transform_group(
    title: str,
    controls: list[dict[str, object]],
) -> html.Div:
    return html.Div(
        className="scene3d-transform-group",
        children=[
            html.H4(title, className="scene3d-transform-group__title"),
            html.Div(
                className="scene3d-transform-grid",
                children=[_scene3d_transform_field(control) for control in controls],
            ),
        ],
    )


def _scene3d_transform_field(control: dict[str, object]) -> html.Div:
    input_id = scene3d_transform_input_id(str(control["key"]))
    slider_id = scene3d_transform_slider_id(str(control["key"]))
    min_value = float(control["min"])
    max_value = float(control["max"])
    step = float(control["step"])
    value = float(control["value"])

    return html.Div(
        className="scene3d-transform-field",
        children=[
            html.Div(
                className="scene3d-transform-field__header",
                children=[
                    html.Label(
                        str(control["label"]),
                        className="field-label",
                        htmlFor=input_id,
                    ),
                    dcc.Input(
                        id=input_id,
                        type="number",
                        min=min_value,
                        max=max_value,
                        step=step,
                        value=value,
                        debounce=False,
                        className=(
                            "number-input scene3d-number-input "
                            "scene3d-transform-input"
                        ),
                    ),
                ],
            ),
            dcc.Slider(
                id=slider_id,
                min=min_value,
                max=max_value,
                step=step,
                value=value,
                marks=None,
                updatemode="drag",
                tooltip={"placement": "bottom", "always_visible": False},
                className="scene3d-transform-slider",
            ),
        ],
    )


def scene3d_transform_input_id(key: str) -> str:
    return f"scene3d-dev-{key.replace('_delta_deg', '-delta').replace('_', '-')}"


def scene3d_transform_slider_id(key: str) -> str:
    return f"{scene3d_transform_input_id(key)}-slider"


def _scene3d_stat(label: str, element_id: str) -> html.Div:
    return html.Div(
        className="scene3d-stat",
        children=[
            html.Span(label, className="detail-label"),
            html.Strong("—", id=element_id, className="scene3d-stat-value"),
        ],
    )
