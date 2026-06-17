"""Регрессионные тесты интерактивности дополнительных страниц concept03.

Страницы equipment/control/analytics/library/settings раньше были статичными
карточками. Эти тесты фиксируют, что карточки стали кнопками/ссылками с
ожидаемыми идентификаторами, а документация ведёт на встроенный /handbook.
"""
from __future__ import annotations

from dash import html

from app.simulation.parameters import ControlMode
from app.ui.concept03.pages.analytics_page import build_content as build_analytics
from app.ui.concept03.pages.control_page import build_content as build_control
from app.ui.concept03.pages.equipment_page import (
    DEFAULT_EQUIPMENT_ID,
    build_content as build_equipment,
    build_equipment_detail,
)
from app.ui.concept03.pages.library_page import build_content as build_library
from app.ui.concept03.pages.settings_page import build_content as build_settings
from app.ui.viewmodels.concept03_central import _build_doc_links
from app.ui.viewmodels.concept03_scenarios import CONCEPT03_SCENARIO_IDS


def _payload(content: list) -> str:
    return str(html.Div(content).to_plotly_json())


def test_control_page_modes_use_real_control_mode_values() -> None:
    payload = _payload(build_control())
    assert "concept03-control-page-mode" in payload
    for mode in ControlMode:
        assert f"'mode_id': '{mode.value}'" in payload
    assert "concept03-control-page-status" in payload


def test_library_page_docs_point_to_handbook_and_presets_are_buttons() -> None:
    payload = _payload(build_library())
    assert "/handbook/44_app_operation_manual" in payload
    assert "/handbook/02_functionality" in payload
    assert "concept03-library-preset" in payload
    for scenario_id in ("baseline_office_winter", "reduced_flow", "dirty_filter", "manual_mode"):
        assert f"'scenario_id': '{scenario_id}'" in payload
    assert "concept03-library-preset-status" in payload


def test_equipment_page_cards_are_selectable_buttons() -> None:
    payload = _payload(build_equipment())
    assert "concept03-equipment-card" in payload
    assert "concept03-equipment-detail" in payload
    assert "concept03-equipment-selected" in payload
    assert f"'equipment_id': '{DEFAULT_EQUIPMENT_ID}'" in payload


def test_equipment_detail_live_and_idle_states() -> None:
    # Узел с датчиком и живым значением показывает блок «Живой сигнал».
    live = _payload(build_equipment_detail("filter", live_value="141 Па", live_state_label="Норма"))
    assert "Живой сигнал" in live
    assert "141 Па" in live
    # Узел без датчика показывает пояснение об отсутствии сигнала.
    idle = _payload(build_equipment_detail("controller"))
    assert "не предусмотрен" in idle


def test_analytics_page_has_export_buttons_and_download() -> None:
    payload = _payload(build_analytics())
    assert "concept03-analytics-download" in payload
    assert "concept03-analytics-export" in payload
    for kind in ("pdf", "csv", "zip"):
        assert f"'kind': '{kind}'" in payload
    assert "concept03-analytics-export-status" in payload


def test_settings_page_theme_defense_links_and_diagnostics() -> None:
    payload = _payload(build_settings())
    assert "?theme=concept03&page=settings" in payload
    assert "?theme=legacy&page=settings" in payload
    assert "?theme=concept03&defense=1&page=settings" in payload
    assert "/handbook" in payload
    assert "concept03-settings-diagnostics" in payload


def test_doc_links_use_handbook_route() -> None:
    for link in _build_doc_links():
        assert link.href.startswith("/handbook/"), link.href


def test_concept03_scenarios_include_alarm_scenario() -> None:
    # Хотя бы один сценарий на дашборде должен выводить установку в тревогу,
    # иначе панель «Аларма» всегда пуста.
    assert "dirty_filter" in CONCEPT03_SCENARIO_IDS
