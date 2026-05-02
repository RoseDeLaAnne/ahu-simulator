from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.browser_capability_service import (
    BrowserCapabilityComparison,
    BrowserCapabilityProfile,
    BrowserDiagnosticsSnapshot,
)
from app.simulation.state import OperationStatus
from app.ui.viewmodels.status_presenter import status_class_name


@dataclass(frozen=True)
class BrowserDiagnosticsView:
    status_text: str
    status_class_name: str
    items: list[str]
    note: str


@dataclass(frozen=True)
class BrowserProfileView:
    status_text: str
    status_class_name: str
    summary_text: str
    items: list[str]
    note: str


@dataclass(frozen=True)
class DemoBrowserReadinessView:
    status_text: str
    status_class_name: str
    summary_text: str
    items: list[str]
    note: str


def build_browser_diagnostics_view(
    payload: Mapping[str, Any] | None,
) -> BrowserDiagnosticsView:
    if not payload:
        return BrowserDiagnosticsView(
            status_text="Проверка",
            status_class_name="status-pill status-warning",
            items=[
                "Диагностика запускается в браузере клиента после открытия дашборда.",
                "Она не влияет на расчёт модели и нужна только для оценки будущего WebGL-режима.",
            ],
            note=(
                "2D SVG остаётся базовым режимом отображения для защиты, пока живой снимок браузера "
                "ещё не получен."
            ),
        )

    snapshot = BrowserDiagnosticsSnapshot.model_validate(payload)
    status = snapshot.readiness_status()
    status_text, status_class_name = _diagnostics_pill(status)

    items = [
        f"Браузер: {snapshot.browser_label}",
        f"Платформа: {snapshot.platform}",
        f"Сеть: {_format_online(snapshot.online)}",
        "WebGL: "
        f"{_yes_no(snapshot.webgl_supported)} / WebGL2: {_yes_no(snapshot.webgl2_supported)}",
        "Защищённый контекст: "
        f"{_yes_no(snapshot.secure_context)} / DPR: {_format_float(snapshot.device_pixel_ratio)}",
        "Потоки CPU: "
        f"{_format_optional(snapshot.hardware_concurrency)} / Память устройства: "
        f"{_format_optional(snapshot.device_memory_gb, suffix=' GB')}",
        "Окно/экран: "
        f"{_format_viewport(snapshot.viewport_width, snapshot.viewport_height)} / "
        f"{_format_viewport(snapshot.screen_width, snapshot.screen_height)}",
        f"Рендерер: {snapshot.renderer or 'не передан'}",
        "Текстуры/область вывода: "
        f"{_format_optional(snapshot.max_texture_size)} / "
        f"{_format_viewport(snapshot.max_viewport_width, snapshot.max_viewport_height)}",
    ]
    if snapshot.diagnostics_timestamp:
        items.append(f"Проверка: {snapshot.diagnostics_timestamp}")

    return BrowserDiagnosticsView(
        status_text=status_text,
        status_class_name=status_class_name,
        items=items,
        note=_build_note(snapshot),
    )


def build_browser_profile_view(
    profile: BrowserCapabilityProfile,
    comparison: BrowserCapabilityComparison | None = None,
) -> BrowserProfileView:
    if comparison is None:
        return BrowserProfileView(
            status_text=_profile_status_text(profile.overall_status, is_live=False),
            status_class_name=_status_class_name(profile.overall_status),
            summary_text=profile.summary,
            items=[
                f"Подтверждённый браузер: {profile.verified_environment.browser_label}",
                f"Платформа: {profile.verified_environment.platform}",
                "WebGL/WebGL2/защищённый контекст: "
                f"{_yes_no(profile.verified_environment.webgl_supported)} / "
                f"{_yes_no(profile.verified_environment.webgl2_supported)} / "
                f"{_yes_no(profile.verified_environment.secure_context)}",
                "CPU / память: "
                f"{_format_optional(profile.verified_environment.hardware_concurrency)} / "
                f"{_format_optional(profile.verified_environment.device_memory_gb, suffix=' GB')}",
                "Экран / текстуры: "
                f"{_format_viewport(profile.verified_environment.screen_width, profile.verified_environment.screen_height)} / "
                f"{_format_optional(profile.verified_environment.max_texture_size)}",
                f"Рендерер: {profile.verified_environment.renderer or 'не передан'}",
                f"Метод: {profile.verification_method}",
                "Рекомендуемый размер окна: "
                f"{profile.recommended_viewport.min_width}x{profile.recommended_viewport.min_height}+",
            ],
            note=profile.note,
        )

    return BrowserProfileView(
        status_text=_profile_status_text(comparison.overall_status, is_live=True),
        status_class_name=_status_class_name(comparison.overall_status),
        summary_text=comparison.summary,
        items=[
            (
                f"{'ПРОЙДЕНО' if evaluation.passed else 'НЕ ПРОЙДЕНО'} | {evaluation.title}: "
                f"факт {evaluation.actual_text}; ожидание {evaluation.expected_text}"
            )
            for evaluation in comparison.evaluations
        ],
        note=comparison.note,
    )


def build_demo_browser_readiness_view(
    payload: Mapping[str, Any] | None,
    profile: BrowserCapabilityProfile | None = None,
    comparison: BrowserCapabilityComparison | None = None,
) -> DemoBrowserReadinessView:
    if not payload:
        return DemoBrowserReadinessView(
            status_text="Ожидает браузер",
            status_class_name="status-pill status-warning",
            summary_text=(
                "Откройте дашборд в целевом браузере и дождитесь клиентской диагностики."
            ),
            items=[
                "Окно: н/д",
                "WebGL2: н/д",
                "Сеть: н/д",
            ],
            note=_pending_demo_browser_note(profile),
        )

    snapshot = BrowserDiagnosticsSnapshot.model_validate(payload)
    viewport_ready = _viewport_is_ready(snapshot)
    screen_ready = _screen_is_ready(snapshot)

    if not viewport_ready:
        return DemoBrowserReadinessView(
            status_text="Нужно больше окно",
            status_class_name="status-pill status-warning",
            summary_text=(
                "Дашборд лучше показывать в полноэкранном окне или на области не уже 1200x680."
            ),
            items=_build_demo_browser_items(snapshot),
            note=_build_viewport_note(profile),
        )

    if not screen_ready:
        return DemoBrowserReadinessView(
            status_text="Монитор с оговорками",
            status_class_name="status-pill status-warning",
            summary_text=(
                "Текущий экран меньше рекомендуемого 1366x768; основной показ лучше вести "
                "в полноэкранном режиме."
            ),
            items=_build_demo_browser_items(snapshot),
            note=_build_screen_note(profile),
        )

    if not snapshot.webgl_supported:
        return DemoBrowserReadinessView(
            status_text="Показ допустим",
            status_class_name="status-pill status-normal",
            summary_text=(
                "Текущий браузер подходит для защиты в 2D; текущий сеанс вне подтверждённого "
                "профиля WebGL, поэтому 3D подтверждать не нужно."
            ),
            items=_build_demo_browser_items(snapshot),
            note=(
                "Для MVP это допустимо: основной сценарий демо опирается на 2D SVG и не требует "
                "WebGL-поддержки."
            ),
        )

    if not snapshot.webgl2_supported or not snapshot.secure_context:
        return DemoBrowserReadinessView(
            status_text="Показ допустим",
            status_class_name="status-pill status-normal",
            summary_text=(
                "Дашборд готов к показу; 3D-режим стоит считать необязательным и держать "
                "2D как основной путь."
            ),
            items=_build_demo_browser_items(snapshot),
            note=(
                "Для дополнительной WebGL-проверки лучше использовать `http://127.0.0.1` "
                "или HTTPS и не делать 3D обязательным сценарием защиты."
            ),
        )

    if comparison is not None and comparison.overall_status == OperationStatus.NORMAL:
        return DemoBrowserReadinessView(
            status_text="Показ допустим",
            status_class_name="status-pill status-normal",
            summary_text=(
                "Текущий браузер соответствует зафиксированному профилю демо-ПК/WebGL; "
                "2D остаётся основным безопасным режимом."
            ),
            items=_build_demo_browser_items(snapshot),
            note=_build_matching_profile_note(profile, comparison),
        )

    if comparison is not None:
        return DemoBrowserReadinessView(
            status_text="Показ допустим",
            status_class_name="status-pill status-normal",
            summary_text=(
                "Дашборд готов к показу в 2D, но текущий браузер отличается от подтверждённого "
                "профиля WebGL."
            ),
            items=_build_demo_browser_items(snapshot),
            note=comparison.note,
        )

    return DemoBrowserReadinessView(
        status_text="Показ допустим",
        status_class_name="status-pill status-normal",
        summary_text=(
            "Текущий браузер пригоден для показа дашборда; 2D остаётся основным безопасным режимом."
        ),
        items=_build_demo_browser_items(snapshot),
        note=_build_demo_ready_note(snapshot),
    )


def _diagnostics_pill(status: OperationStatus) -> tuple[str, str]:
    mapping = {
        OperationStatus.NORMAL: "3D возможно",
        OperationStatus.WARNING: "3D с оговорками",
        OperationStatus.ALARM: "Только 2D",
    }
    return mapping[status], status_class_name(status)


def _build_note(snapshot: BrowserDiagnosticsSnapshot) -> str:
    if not snapshot.webgl_supported:
        return (
            "WebGL не обнаружен. Для демонстрации 3D-режим нельзя делать обязательным, "
            "основной показ должен оставаться на 2D SVG."
        )
    if not snapshot.webgl2_supported:
        return (
            "Доступен только WebGL 1. Это достаточно для разведки будущего 3D-визуализатора, "
            "но 2D SVG всё ещё должен оставаться основным безопасным режимом."
        )
    if not snapshot.secure_context:
        return (
            "WebGL доступен, но среда не считается защищённым контекстом. Для стабильной проверки "
            "будущего 3D-режима лучше использовать локальный `http://127.0.0.1` или HTTPS."
        )
    if snapshot.hardware_concurrency is not None and snapshot.hardware_concurrency < 4:
        return (
            "WebGL и WebGL2 доступны, но запас по CPU ограничен. На целевом демо-ПК "
            "нужно отдельно проверить производительность и оставить 2D как резервный режим."
        )
    if snapshot.device_memory_gb is not None and snapshot.device_memory_gb < 4:
        return (
            "WebGL и WebGL2 доступны, но заявленная память устройства низкая. Для защиты 3D "
            "следует считать необязательным режимом и держать 2D по умолчанию."
        )
    return (
        "Браузер выглядит пригодным для экспериментального 3D-визуализатора, но расчётный слой "
        "и основной демонстрационный сценарий по-прежнему должны опираться на 2D SVG."
    )


def _pending_demo_browser_note(profile: BrowserCapabilityProfile | None) -> str:
    if profile is None:
        return (
            "Преддемонстрационное заключение по браузеру формируется только после открытия "
            "страницы на целевом устройстве."
        )
    return (
            "Преддемонстрационное заключение по браузеру формируется после открытия страницы на "
            "целевом устройстве, но подтверждённый профиль уже зафиксирован в проекте и может служить "
        "ориентиром для будущего WebGL-режима."
    )


def _build_demo_browser_items(
    snapshot: BrowserDiagnosticsSnapshot,
) -> list[str]:
    return [
        f"Браузер: {snapshot.browser_label}",
        f"Окно: {_format_viewport(snapshot.viewport_width, snapshot.viewport_height)}",
        f"Экран: {_format_viewport(snapshot.screen_width, snapshot.screen_height)}",
        "WebGL/WebGL2: "
        f"{_yes_no(snapshot.webgl_supported)} / {_yes_no(snapshot.webgl2_supported)}",
        f"Сеть: {_format_online(snapshot.online)}",
    ]


def _build_viewport_note(profile: BrowserCapabilityProfile | None) -> str:
    if profile is None:
        return (
            "2D SVG остаётся работоспособным, но для защиты стоит развернуть браузер на "
            "большую область экрана."
        )
    return (
        "Аппаратный профиль браузера/WebGL уже подтверждён, но текущее окно слишком узкое для "
        "комфортного показа. Разверните дашборд минимум до "
        f"{profile.recommended_viewport.min_width}x{profile.recommended_viewport.min_height}."
    )


def _build_screen_note(profile: BrowserCapabilityProfile | None) -> str:
    if profile is None:
        return (
            "2D-дашборд остаётся пригодным, но плотность блоков и таблиц нужно проверить "
            "на реальном демонстрационном экране."
        )
    return (
        "Подтверждённый профиль для WebGL уже зафиксирован, но текущий экран меньше рекомендуемого "
        "диапазона и требует отдельной ручной проверки компоновки."
    )


def _build_matching_profile_note(
    profile: BrowserCapabilityProfile | None,
    comparison: BrowserCapabilityComparison,
) -> str:
    if profile is None:
        return comparison.note
    return (
        f"{comparison.note} Рекомендуемое окно для показа: "
        f"{profile.recommended_viewport.min_width}x{profile.recommended_viewport.min_height}+."
    )


def _build_demo_ready_note(snapshot: BrowserDiagnosticsSnapshot) -> str:
    if snapshot.online is False:
        return (
            "Браузер пригоден для локального показа. Признак офлайна не критичен: приложение "
            "запускается локально и не зависит от внешней сети."
        )
    return (
        "Браузер и размер окна выглядят пригодными для локального показа. 2D SVG остаётся "
        "основным безопасным режимом, а 3D не должен становиться обязательным без отдельного "
        "проектного решения."
    )


def _profile_status_text(status: OperationStatus, *, is_live: bool) -> str:
    if is_live:
        mapping = {
            OperationStatus.NORMAL: "Совпадает",
            OperationStatus.WARNING: "Есть отличия",
            OperationStatus.ALARM: "Вне профиля",
        }
        return mapping[status]

    mapping = {
        OperationStatus.NORMAL: "Профиль подтверждён",
        OperationStatus.WARNING: "Профиль с оговорками",
        OperationStatus.ALARM: "Профиль вне допустимых границ",
    }
    return mapping[status]


def _status_class_name(status: OperationStatus) -> str:
    return status_class_name(status)


def _yes_no(value: bool) -> str:
    return "да" if value else "нет"


def _format_online(value: bool | None) -> str:
    if value is None:
        return "н/д"
    return "в сети" if value else "офлайн"


def _format_optional(value: int | float | None, suffix: str = "") -> str:
    if value is None:
        return "н/д"
    if isinstance(value, float):
        return f"{value:.1f}{suffix}"
    return f"{value}{suffix}"


def _format_float(value: float | None) -> str:
    if value is None:
        return "н/д"
    return f"{value:.2f}"


def _format_viewport(width: int | None, height: int | None) -> str:
    if width is None or height is None:
        return "н/д"
    return f"{width}x{height}"


def _viewport_is_ready(snapshot: BrowserDiagnosticsSnapshot) -> bool:
    if snapshot.viewport_width is None or snapshot.viewport_height is None:
        return True
    return snapshot.viewport_width >= 1200 and snapshot.viewport_height >= 680


def _screen_is_ready(snapshot: BrowserDiagnosticsSnapshot) -> bool:
    if snapshot.screen_width is None or snapshot.screen_height is None:
        return True
    return snapshot.screen_width >= 1366 and snapshot.screen_height >= 768
