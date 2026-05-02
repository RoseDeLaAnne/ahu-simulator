from pathlib import Path

from app.simulation.parameters import SimulationParameters
from app.simulation.scenarios import load_scenarios


REQUIRED_SHORTCUT_PRESETS = ("winter", "summer", "peak_load")


def _load_presets():
    scenario_path = Path(__file__).resolve().parents[2] / "data" / "scenarios" / "presets.json"
    return load_scenarios(scenario_path)


def test_required_shortcut_presets_exist() -> None:
    scenario_ids = {scenario.id for scenario in _load_presets()}

    assert set(REQUIRED_SHORTCUT_PRESETS).issubset(scenario_ids)


def test_system_presets_are_locked_with_v2_metadata() -> None:
    for scenario in _load_presets():
        assert scenario.schema_version == "scenario-preset.v2"
        assert scenario.source == "system"
        assert scenario.locked is True


def test_required_shortcut_presets_have_descriptions() -> None:
    scenario_map = {scenario.id: scenario for scenario in _load_presets()}

    for scenario_id in REQUIRED_SHORTCUT_PRESETS:
        scenario = scenario_map[scenario_id]
        assert scenario.purpose
        assert scenario.key_parameters
        assert scenario.expected_effect


def test_all_presets_parameters_fit_declared_ranges() -> None:
    parameter_schema = SimulationParameters.model_json_schema().get("properties", {})

    for scenario in _load_presets():
        payload = scenario.parameters.model_dump(mode="json")
        for field_name, value in payload.items():
            if not isinstance(value, int | float):
                continue
            field_schema = parameter_schema.get(field_name, {})
            minimum = field_schema.get("minimum")
            maximum = field_schema.get("maximum")
            if minimum is not None:
                assert value >= minimum, (
                    f"{scenario.id}.{field_name}={value} below minimum {minimum}"
                )
            if maximum is not None:
                assert value <= maximum, (
                    f"{scenario.id}.{field_name}={value} above maximum {maximum}"
                )
