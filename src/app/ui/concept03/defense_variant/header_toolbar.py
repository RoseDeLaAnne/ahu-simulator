from __future__ import annotations

from dash import html

from app.simulation.parameters import ControlMode
from app.simulation.state import SimulationResult
from app.ui.concept03.components.icon import Icon


DEFENSE_TITLE = "МОДЕЛИРОВАНИЕ РАБОТЫ ПРИТОЧНОЙ ВЕНТИЛЯЦИОННОЙ УСТАНОВКИ"


def build_header_action_toolbar() -> html.Div:
    actions = (
        ("header-btn-start", "play", "Запустить", "primary"),
        ("header-btn-pause", "pause", "Пауза", "secondary"),
        ("header-btn-stop", "square", "Стоп", "secondary"),
        ("header-btn-reset", "rotate-ccw", "Сброс", "ghost"),
    )
    return html.Div(
        className="c03-action-toolbar c03-defense-only",
        role="toolbar",
        **{"aria-label": "Управление демонстрационной сессией"},
        children=[
            html.Button(
                id=button_id,
                type="button",
                className=f"c03-action-button c03-action-button--{variant}",
                title=label,
                children=[
                    Icon(icon, 16, class_name="c03-action-button__icon"),
                    html.Span(label),
                ],
            )
            for button_id, icon, label, variant in actions
        ],
    )


def build_header_meta_pills(result: SimulationResult | None = None) -> html.Div:
    control_mode = result.parameters.control_mode if result is not None else ControlMode.AUTO
    step_minutes = result.parameters.step_minutes if result is not None else 1
    return html.Div(
        className="c03-header-meta c03-defense-only",
        children=[
            _build_meta_pill("Режим", _control_mode_label(control_mode)),
            _build_meta_pill("Шаг модели", f"{int(step_minutes * 60)} с"),
        ],
    )


def build_header_icon_links() -> html.Nav:
    links = (
        ("download", "Экспорт", "?theme=concept03&defense=true&page=analytics#exports"),
        ("file-text", "Отчёт", "?theme=concept03&defense=true&page=library#defense"),
        ("help-circle", "Справка", "/docs"),
    )
    return html.Nav(
        className="c03-header-links c03-defense-only",
        **{"aria-label": "Материалы защиты"},
        children=[
            html.A(
                href=href,
                className="c03-header-link",
                title=label,
                children=[
                    Icon(icon, 17, class_name="c03-header-link__icon"),
                    html.Span(label),
                ],
            )
            for icon, label, href in links
        ],
    )


def build_hidden_sync_pill() -> html.Div:
    return html.Div(
        id="concept03-sync-pill",
        className="c03-status-pill c03-status-pill--muted c03-defense-sync-shadow",
        children=html.Strong(id="concept03-sync-pill-sub"),
    )


def _build_meta_pill(label: str, value: str) -> html.Div:
    return html.Div(
        className="c03-header-meta__pill",
        children=[
            html.Span(label),
            html.Strong(value),
        ],
    )


def _control_mode_label(mode: ControlMode) -> str:
    labels = {
        ControlMode.AUTO: "АВТО",
        ControlMode.SEMI_AUTO: "ПОЛУАВТО",
        ControlMode.MANUAL: "РУЧНОЙ",
        ControlMode.TEST: "ТЕСТ",
    }
    return labels.get(mode, mode.value.upper())
