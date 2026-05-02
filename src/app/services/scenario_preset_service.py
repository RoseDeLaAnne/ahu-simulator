from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.infrastructure.runtime_paths import RuntimePathResolver
from app.simulation.parameters import SimulationParameters
from app.simulation.scenarios import (
    SCENARIO_PRESET_SCHEMA_VERSION,
    ScenarioDefinition,
    load_scenarios,
)


USER_PRESET_STORE_SCHEMA_VERSION = "scenario-user-presets.v1"


class ScenarioPresetMutationError(RuntimeError):
    pass


class UserPresetStorePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = USER_PRESET_STORE_SCHEMA_VERSION
    presets: list[ScenarioDefinition] = Field(default_factory=list)


class ScenarioPresetService:
    def __init__(
        self,
        system_preset_path: Path,
        project_root: Path,
        path_resolver: RuntimePathResolver | None = None,
    ) -> None:
        self._system_preset_path = system_preset_path
        self._path_resolver = path_resolver or RuntimePathResolver(project_root)
        self._storage_path = self._user_preset_root() / "presets.json"

    @property
    def storage_path(self) -> Path:
        return self._storage_path

    def list_scenarios(self) -> list[ScenarioDefinition]:
        user_map = {scenario.id: scenario for scenario in self._load_user_presets()}
        scenarios = [
            *self._load_system_presets(),
            *sorted(user_map.values(), key=lambda scenario: scenario.title.casefold()),
        ]
        return scenarios

    def get_scenario(self, scenario_id: str) -> ScenarioDefinition:
        for scenario in self.list_scenarios():
            if scenario.id == scenario_id:
                return scenario
        raise KeyError(f"Scenario '{scenario_id}' not found")

    def create_user_preset(
        self,
        *,
        title: str,
        parameters: SimulationParameters,
        preset_id: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        key_parameters: list[str] | None = None,
        expected_effect: str | None = None,
    ) -> ScenarioDefinition:
        system_ids = self._system_ids()
        user_presets = self._load_user_presets()
        existing_ids = system_ids | {scenario.id for scenario in user_presets}
        normalized_id = self._normalize_preset_id(
            preset_id or title,
            existing_ids=existing_ids,
            allow_generate=preset_id is None,
        )
        if normalized_id in system_ids:
            raise ScenarioPresetMutationError(
                f"System preset '{normalized_id}' is locked and cannot be overwritten"
            )
        if normalized_id in existing_ids:
            raise ScenarioPresetMutationError(
                f"User preset '{normalized_id}' already exists"
            )

        now = datetime.now(timezone.utc)
        scenario = self._build_user_scenario(
            preset_id=normalized_id,
            title=title,
            parameters=parameters,
            description=description,
            purpose=purpose,
            key_parameters=key_parameters,
            expected_effect=expected_effect,
            created_at=now,
            updated_at=now,
        )
        self._save_user_presets([*user_presets, scenario])
        return scenario

    def update_user_preset(
        self,
        preset_id: str,
        parameters: SimulationParameters,
    ) -> ScenarioDefinition:
        scenario = self._require_mutable_user_preset(preset_id)
        updated = scenario.model_copy(
            update={
                "parameters": parameters,
                "key_parameters": self._build_key_parameters(parameters),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._replace_user_preset(updated)
        return updated

    def rename_user_preset(self, preset_id: str, *, title: str) -> ScenarioDefinition:
        scenario = self._require_mutable_user_preset(preset_id)
        updated = scenario.model_copy(
            update={
                "title": self._clean_title(title),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._replace_user_preset(updated)
        return updated

    def delete_user_preset(self, preset_id: str) -> ScenarioDefinition:
        scenario = self._require_mutable_user_preset(preset_id)
        remaining = [
            candidate
            for candidate in self._load_user_presets()
            if candidate.id != preset_id
        ]
        self._save_user_presets(remaining)
        return scenario

    def import_user_preset(self, payload: dict[str, Any]) -> ScenarioDefinition:
        try:
            scenario = ScenarioDefinition.model_validate(payload)
        except ValidationError as error:
            raise ValueError("Invalid user preset payload") from error

        if scenario.schema_version != SCENARIO_PRESET_SCHEMA_VERSION:
            raise ValueError("Unsupported scenario preset schema version")
        if scenario.source != "user" or scenario.locked:
            raise ValueError("Imported preset must be an unlocked user preset")
        if scenario.id in self._system_ids():
            raise ScenarioPresetMutationError(
                f"System preset '{scenario.id}' is locked and cannot be overwritten"
            )

        user_presets = [
            candidate
            for candidate in self._load_user_presets()
            if candidate.id != scenario.id
        ]
        now = datetime.now(timezone.utc)
        imported = scenario.model_copy(
            update={
                "updated_at": now,
                "created_at": scenario.created_at or now,
            }
        )
        self._save_user_presets([*user_presets, imported])
        return imported

    def export_user_preset(self, preset_id: str) -> dict[str, Any]:
        scenario = self._require_mutable_user_preset(preset_id)
        return scenario.model_dump(mode="json", exclude_none=True)

    def _load_system_presets(self) -> list[ScenarioDefinition]:
        return [
            scenario.model_copy(
                update={
                    "schema_version": SCENARIO_PRESET_SCHEMA_VERSION,
                    "source": "system",
                    "locked": True,
                }
            )
            for scenario in load_scenarios(self._system_preset_path)
        ]

    def _load_user_presets(self) -> list[ScenarioDefinition]:
        if not self._storage_path.exists():
            return []

        try:
            payload = UserPresetStorePayload.model_validate_json(
                self._storage_path.read_text(encoding="utf-8")
            )
            if payload.schema_version != USER_PRESET_STORE_SCHEMA_VERSION:
                raise ValueError("Unsupported user preset store schema version")
        except (OSError, ValueError, ValidationError):
            self._clear_user_presets()
            return []

        system_ids = self._system_ids()
        valid_presets: list[ScenarioDefinition] = []
        for scenario in payload.presets:
            if (
                scenario.schema_version != SCENARIO_PRESET_SCHEMA_VERSION
                or scenario.source != "user"
                or scenario.locked
                or scenario.id in system_ids
            ):
                continue
            valid_presets.append(scenario)
        return valid_presets

    def _save_user_presets(self, presets: list[ScenarioDefinition]) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = UserPresetStorePayload(
            presets=sorted(presets, key=lambda scenario: scenario.id)
        )
        temporary_path = self._storage_path.with_suffix(".tmp")
        temporary_path.write_text(
            payload.model_dump_json(indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(self._storage_path)

    def _clear_user_presets(self) -> None:
        try:
            self._storage_path.unlink(missing_ok=True)
        except OSError:
            pass

    def _replace_user_preset(self, updated: ScenarioDefinition) -> None:
        presets = [
            updated if scenario.id == updated.id else scenario
            for scenario in self._load_user_presets()
        ]
        self._save_user_presets(presets)

    def _require_mutable_user_preset(self, preset_id: str) -> ScenarioDefinition:
        if preset_id in self._system_ids():
            raise ScenarioPresetMutationError(
                f"System preset '{preset_id}' is locked and cannot be changed"
            )

        for scenario in self._load_user_presets():
            if scenario.id == preset_id and scenario.source == "user" and not scenario.locked:
                return scenario
        raise KeyError(f"User preset '{preset_id}' not found")

    def _system_ids(self) -> set[str]:
        return {scenario.id for scenario in self._load_system_presets()}

    def _build_user_scenario(
        self,
        *,
        preset_id: str,
        title: str,
        parameters: SimulationParameters,
        description: str | None,
        purpose: str | None,
        key_parameters: list[str] | None,
        expected_effect: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> ScenarioDefinition:
        clean_title = self._clean_title(title)
        return ScenarioDefinition(
            id=preset_id,
            title=clean_title,
            description=description or f"Пользовательский пресет «{clean_title}».",
            purpose=purpose or "Сохраненный пользователем набор параметров ПВУ.",
            key_parameters=key_parameters or self._build_key_parameters(parameters),
            expected_effect=expected_effect or "Поведение соответствует сохраненным параметрам.",
            parameters=parameters,
            source="user",
            locked=False,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _build_key_parameters(
        self,
        parameters: SimulationParameters,
    ) -> list[str]:
        return [
            f"outdoor_temp_c={parameters.outdoor_temp_c:g} °C",
            f"airflow_m3_h={parameters.airflow_m3_h:g} м³/ч",
            f"heater_power_kw={parameters.heater_power_kw:g} кВт",
            f"filter_contamination={parameters.filter_contamination:g}",
        ]

    def _normalize_preset_id(
        self,
        raw_value: str,
        *,
        existing_ids: set[str],
        allow_generate: bool,
    ) -> str:
        candidate = raw_value.strip().lower()
        candidate = re.sub(r"[^a-z0-9_]+", "_", candidate)
        candidate = re.sub(r"_+", "_", candidate).strip("_")
        if not candidate:
            candidate = "user_preset"
        if not allow_generate:
            return candidate

        base = candidate
        sequence = 2
        while candidate in existing_ids:
            candidate = f"{base}_{sequence}"
            sequence += 1
        return candidate

    def _clean_title(self, title: str) -> str:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Preset title must not be empty")
        return clean_title

    def _user_preset_root(self) -> Path:
        return (
            self._path_resolver.runtime_directories.user_presets
            or self._path_resolver.runtime_directories.root / "user-presets"
        )


__all__ = [
    "SCENARIO_PRESET_SCHEMA_VERSION",
    "ScenarioPresetMutationError",
    "ScenarioPresetService",
    "USER_PRESET_STORE_SCHEMA_VERSION",
]
