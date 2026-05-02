from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.simulation.parameters import SimulationParameters


SCENARIO_PRESET_SCHEMA_VERSION = "scenario-preset.v2"
ScenarioPresetSource = Literal["system", "user"]


class ScenarioDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCENARIO_PRESET_SCHEMA_VERSION
    id: str
    title: str
    description: str
    purpose: str
    key_parameters: list[str] = Field(default_factory=list, min_length=1)
    expected_effect: str
    parameters: SimulationParameters
    source: ScenarioPresetSource = "system"
    locked: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def formatted_description(self) -> str:
        key_parameters_text = "; ".join(self.key_parameters)
        return (
            f"{self.description} Назначение: {self.purpose}. "
            f"Ключевые параметры: {key_parameters_text}. "
            f"Ожидаемый эффект: {self.expected_effect}"
        )


def load_scenarios(path: Path) -> list[ScenarioDefinition]:
    raw_payload = json.loads(path.read_text(encoding="utf-8"))
    return [ScenarioDefinition.model_validate(item) for item in raw_payload]
