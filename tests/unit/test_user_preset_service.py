from pathlib import Path

import pytest

from app.services.scenario_preset_service import (
    SCENARIO_PRESET_SCHEMA_VERSION,
    ScenarioPresetMutationError,
    ScenarioPresetService,
)
from app.simulation.parameters import SimulationParameters


SYSTEM_PRESET_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "scenarios" / "presets.json"
)


def _build_service(tmp_path: Path) -> ScenarioPresetService:
    return ScenarioPresetService(
        system_preset_path=SYSTEM_PRESET_PATH,
        project_root=tmp_path,
    )


def test_user_presets_merge_with_locked_system_presets(tmp_path: Path) -> None:
    service = _build_service(tmp_path)

    created = service.create_user_preset(
        title="Тестовый режим",
        parameters=SimulationParameters(airflow_m3_h=2800),
    )
    scenario_map = {scenario.id: scenario for scenario in service.list_scenarios()}

    assert scenario_map["winter"].source == "system"
    assert scenario_map["winter"].locked is True
    assert scenario_map["winter"].schema_version == SCENARIO_PRESET_SCHEMA_VERSION
    assert created.id in scenario_map
    assert scenario_map[created.id].source == "user"
    assert scenario_map[created.id].locked is False
    assert scenario_map[created.id].created_at is not None
    assert scenario_map[created.id].updated_at is not None


def test_locked_system_presets_cannot_be_mutated(tmp_path: Path) -> None:
    service = _build_service(tmp_path)

    with pytest.raises(ScenarioPresetMutationError):
        service.rename_user_preset("winter", title="Новая зима")
    with pytest.raises(ScenarioPresetMutationError):
        service.update_user_preset("summer", SimulationParameters())
    with pytest.raises(ScenarioPresetMutationError):
        service.delete_user_preset("peak_load")
    with pytest.raises(ScenarioPresetMutationError):
        service.create_user_preset(
            title="Конфликт",
            parameters=SimulationParameters(),
            preset_id="winter",
        )


def test_user_preset_crud_and_runtime_persistence(tmp_path: Path) -> None:
    service = _build_service(tmp_path)
    created = service.create_user_preset(
        title="Экономичный режим",
        parameters=SimulationParameters(airflow_m3_h=2600),
        preset_id="economy",
    )

    renamed = service.rename_user_preset("economy", title="Экономичный ночной режим")
    updated = service.update_user_preset(
        "economy",
        SimulationParameters(airflow_m3_h=2400, heater_power_kw=12),
    )
    restored_service = _build_service(tmp_path)
    restored = restored_service.get_scenario("economy")

    assert created.id == "economy"
    assert renamed.title == "Экономичный ночной режим"
    assert updated.parameters.airflow_m3_h == 2400
    assert restored.title == "Экономичный ночной режим"
    assert restored.parameters.heater_power_kw == 12

    deleted = restored_service.delete_user_preset("economy")

    assert deleted.id == "economy"
    assert "economy" not in {scenario.id for scenario in restored_service.list_scenarios()}


def test_import_export_validate_user_preset_payload(tmp_path: Path) -> None:
    service = _build_service(tmp_path)
    created = service.create_user_preset(
        title="Импортируемый режим",
        parameters=SimulationParameters(airflow_m3_h=3100),
        preset_id="portable",
    )

    exported = service.export_user_preset(created.id)
    service.delete_user_preset(created.id)
    imported = service.import_user_preset(exported)

    assert exported["schema_version"] == SCENARIO_PRESET_SCHEMA_VERSION
    assert exported["source"] == "user"
    assert exported["locked"] is False
    assert imported.id == "portable"
    assert imported.parameters.airflow_m3_h == 3100

    invalid_payload = dict(exported)
    invalid_payload["parameters"] = {"airflow_m3_h": -1}
    with pytest.raises(ValueError):
        service.import_user_preset(invalid_payload)


def test_corrupt_user_preset_file_is_safely_reset(tmp_path: Path) -> None:
    service = _build_service(tmp_path)
    service.create_user_preset(
        title="Будет поврежден",
        parameters=SimulationParameters(),
        preset_id="broken",
    )
    service.storage_path.write_text("{not-json", encoding="utf-8")

    restored_service = _build_service(tmp_path)

    assert "broken" not in {scenario.id for scenario in restored_service.list_scenarios()}
    assert not restored_service.storage_path.exists()
