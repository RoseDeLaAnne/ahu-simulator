from __future__ import annotations

from dash import html

from app.ui.concept03.components.icon import Icon

_EQUIPMENT = (
    ("Приточный вентилятор", "fan", "Номинальная мощность: 5.5 кВт · 1500 об/мин"),
    ("Вытяжной вентилятор", "fan", "Контур рекуперации · 4.0 кВт · удаление воздуха через рекуператор"),
    ("Пластинчатый рекуператор", "layers", "Утилизация теплоты вытяжного воздуха · КПД до 85%"),
    ("Электрический калорифер", "flame", "Мощность: до 18 кВт · упрощение модели (без водяного контура)"),
    ("Воздушный фильтр", "filter", "Класс G4 / F7 · Перепад ≤ 250 Па"),
    ("Воздушный клапан", "sliders-horizontal", "Привод 24 В · 0–100% за 90 с"),
    ("Шумоглушитель", "volume-2", "Снижение: 15 дБ · Секционная конструкция"),
    ("Контроллер автоматики", "cpu", "Siemens Climatix · Modbus RTU"),
)


def build_content() -> list:
    return [
        html.Div(
            className="c03-page c03-page--equipment",
            children=[
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
                    className="c03-page__body c03-equipment-grid",
                    children=[
                        _equipment_card(title, icon, detail)
                        for title, icon, detail in _EQUIPMENT
                    ],
                ),
            ],
        ),
    ]


def _equipment_card(title: str, icon: str, detail: str) -> html.Div:
    return html.Div(
        className="c03-equipment-card",
        children=[
            Icon(icon, size=32, class_name="c03-equipment-card__icon"),
            html.Strong(title, className="c03-equipment-card__title"),
            html.P(detail, className="c03-equipment-card__detail"),
        ],
    )
