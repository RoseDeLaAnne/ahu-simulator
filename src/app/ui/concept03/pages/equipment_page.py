from __future__ import annotations

from dataclasses import dataclass

from dash import dcc, html

from app.ui.concept03.components.icon import Icon


@dataclass(frozen=True)
class EquipmentItem:
    equipment_id: str
    title: str
    icon: str
    summary: str
    # visual_id связывает узел с живыми сигналами модели (None — нет датчика).
    visual_id: str | None
    specs: tuple[tuple[str, str], ...]


EQUIPMENT_ITEMS: tuple[EquipmentItem, ...] = (
    EquipmentItem(
        "supply_fan",
        "Приточный вентилятор",
        "fan",
        "Подаёт обработанный воздух в помещение.",
        "supply_fan",
        (
            ("Номинальная мощность", "5.5 кВт"),
            ("Частота вращения", "1500 об/мин"),
            ("Регулирование", "Частотный преобразователь, 20–120%"),
        ),
    ),
    EquipmentItem(
        "extract_fan",
        "Вытяжной вентилятор",
        "fan",
        "Удаляет воздух через контур рекуперации.",
        None,
        (
            ("Номинальная мощность", "4.0 кВт"),
            ("Назначение", "Контур рекуперации теплоты"),
        ),
    ),
    EquipmentItem(
        "recuperator",
        "Пластинчатый рекуператор",
        "layers",
        "Утилизирует теплоту вытяжного воздуха.",
        "recuperator_core",
        (
            ("КПД утилизации", "до 85%"),
            ("Тип", "Перекрёстноточный пластинчатый"),
        ),
    ),
    EquipmentItem(
        "heater",
        "Электрический калорифер",
        "flame",
        "Догрев приточного воздуха до уставки.",
        "heater_coil",
        (
            ("Максимальная мощность", "18 кВт"),
            ("Упрощение модели", "Без водяного контура"),
        ),
    ),
    EquipmentItem(
        "filter",
        "Воздушный фильтр",
        "filter",
        "Очистка наружного и приточного воздуха.",
        "filter_bank",
        (
            ("Класс", "G4 / F7"),
            ("Перепад давления", "≤ 250 Па"),
        ),
    ),
    EquipmentItem(
        "damper",
        "Воздушный клапан",
        "sliders-horizontal",
        "Регулирует поток наружного воздуха.",
        None,
        (
            ("Привод", "24 В"),
            ("Время хода", "0–100% за 90 с"),
        ),
    ),
    EquipmentItem(
        "silencer",
        "Шумоглушитель",
        "volume-2",
        "Снижает аэродинамический шум установки.",
        "silencer",
        (
            ("Снижение шума", "15 дБ"),
            ("Конструкция", "Секционная"),
        ),
    ),
    EquipmentItem(
        "controller",
        "Контроллер автоматики",
        "cpu",
        "Управляет режимами и уставками установки.",
        None,
        (
            ("Платформа", "Siemens Climatix"),
            ("Интерфейс", "Modbus RTU"),
        ),
    ),
)

EQUIPMENT_BY_ID = {item.equipment_id: item for item in EQUIPMENT_ITEMS}
DEFAULT_EQUIPMENT_ID = EQUIPMENT_ITEMS[0].equipment_id


def build_content() -> list:
    return [
        html.Div(
            className="c03-page c03-page--equipment",
            children=[
                dcc.Store(
                    id="concept03-equipment-selected",
                    data=DEFAULT_EQUIPMENT_ID,
                ),
                html.Div(
                    className="c03-page__header",
                    children=[
                        html.H2("Оборудование", className="c03-page__title"),
                        html.Span(
                            "Состав приточной вентиляционной установки П1",
                            className="c03-page__subtitle",
                        ),
                    ],
                ),
                html.Div(
                    className="c03-page__body c03-equipment-layout",
                    children=[
                        html.Div(
                            className="c03-equipment-grid",
                            children=[
                                _equipment_card(item)
                                for item in EQUIPMENT_ITEMS
                            ],
                        ),
                        html.Div(
                            id="concept03-equipment-detail",
                            className="c03-equipment-detail",
                            children=build_equipment_detail(DEFAULT_EQUIPMENT_ID),
                        ),
                    ],
                ),
            ],
        ),
    ]


def _equipment_card(item: EquipmentItem) -> html.Button:
    return html.Button(
        id={"type": "concept03-equipment-card", "equipment_id": item.equipment_id},
        className=equipment_card_class_name(is_active=item.equipment_id == DEFAULT_EQUIPMENT_ID),
        type="button",
        n_clicks=0,
        title=f"{item.title}: {item.summary}",
        **{"data-equipment-id": item.equipment_id, "aria-pressed": "false"},
        children=[
            Icon(item.icon, size=32, class_name="c03-equipment-card__icon"),
            html.Strong(item.title, className="c03-equipment-card__title"),
            html.P(item.summary, className="c03-equipment-card__detail"),
        ],
    )


def equipment_card_class_name(*, is_active: bool) -> str:
    return "c03-equipment-card" + (
        " c03-equipment-card--active" if is_active else ""
    )


def build_equipment_detail(
    equipment_id: str,
    *,
    live_value: str | None = None,
    live_state_label: str | None = None,
    live_state_class: str | None = None,
) -> list:
    item = EQUIPMENT_BY_ID.get(equipment_id) or EQUIPMENT_ITEMS[0]
    spec_rows: list = []
    for label, value in item.specs:
        spec_rows.extend([html.Dt(label), html.Dd(value)])

    live_block: list = []
    if item.visual_id is not None:
        if live_value is not None:
            live_block = [
                html.Div(
                    className="c03-equipment-detail__live",
                    children=[
                        html.Span("Живой сигнал", className="c03-equipment-detail__live-label"),
                        html.Strong(live_value, className="c03-equipment-detail__live-value"),
                        html.Span(
                            live_state_label or "",
                            className=live_state_class
                            or "c03-equipment-detail__live-state",
                        ),
                    ],
                )
            ]
        else:
            live_block = [
                html.Div(
                    "Запустите модель на дашборде, чтобы увидеть живой сигнал узла.",
                    className="c03-equipment-detail__live c03-equipment-detail__live--idle",
                )
            ]
    else:
        live_block = [
            html.Div(
                "Для этого узла отдельный датчик в модели не предусмотрен.",
                className="c03-equipment-detail__live c03-equipment-detail__live--idle",
            )
        ]

    return [
        html.Div(
            className="c03-equipment-detail__header",
            children=[
                Icon(item.icon, size=26, class_name="c03-equipment-detail__icon"),
                html.Div(
                    children=[
                        html.Strong(item.title, className="c03-equipment-detail__title"),
                        html.Span(item.summary, className="c03-equipment-detail__summary"),
                    ],
                ),
            ],
        ),
        *live_block,
        html.Dl(className="c03-equipment-detail__specs", children=spec_rows),
    ]
