from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from app.simulation.status_policy import StatusThresholds


class ApplicationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_name: str = "PVU Diploma Project"
    api_prefix: str = ""
    dashboard_path: str = "/dashboard"
    default_scenario_id: str = "midseason"
    trend_horizon_minutes: int = Field(default=120, ge=10, le=720)
    trend_step_minutes: int = Field(default=10, ge=1, le=60)
    nominal_airflow_m3_h: float = Field(default=3200.0, ge=200.0)
    base_filter_pressure_drop_pa: float = Field(default=120.0, ge=1.0)
    max_filter_pressure_drop_pa: float = Field(default=420.0, ge=1.0)
    status_thresholds: StatusThresholds = Field(default_factory=StatusThresholds)
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1",
            "http://localhost",
            "http://127.0.0.1:8000",
            "http://localhost:8000",
        ]
    )
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["GET", "POST", "OPTIONS"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    trusted_hosts: list[str] = Field(default_factory=lambda: ["*"])
    enforce_https_redirect: bool = False
    developer_tools_enabled: bool = False


def _project_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parents[3]


def _resolve_config_path(project_root: Path) -> Path:
    override_path = os.environ.get("AHU_SIMULATOR_SETTINGS_FILE")
    if not override_path:
        return project_root / "config" / "defaults.yaml"

    candidate_path = Path(override_path).expanduser()
    if not candidate_path.is_absolute():
        candidate_path = project_root / candidate_path
    return candidate_path.resolve()


def _resolve_environment_path(project_root: Path) -> Path:
    override_path = os.environ.get("AHU_SIMULATOR_ENV_FILE")
    if not override_path:
        return project_root / "config" / "local.env"

    candidate_path = Path(override_path).expanduser()
    if not candidate_path.is_absolute():
        candidate_path = project_root / candidate_path
    return candidate_path.resolve()


def _strip_env_quotes(raw_value: str) -> str:
    value = raw_value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _load_environment_file(project_root: Path) -> None:
    environment_path = _resolve_environment_path(project_root)
    if not environment_path.exists():
        return

    with environment_path.open("r", encoding="utf-8") as environment_file:
        for line_number, raw_line in enumerate(environment_file, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                raise ValueError(f"Invalid env line {line_number} in {environment_path}. Expected KEY=VALUE.")

            key, raw_value = line.split("=", 1)
            key = key.strip()
            if not key:
                raise ValueError(f"Invalid env line {line_number} in {environment_path}. Missing key.")
            os.environ.setdefault(key, _strip_env_quotes(raw_value))


def _parse_csv_env(variable_name: str) -> list[str] | None:
    raw_value = os.environ.get(variable_name)
    if raw_value is None:
        return None
    values = [item.strip() for item in raw_value.split(",") if item.strip()]
    return values


def _parse_bool_env(variable_name: str) -> bool | None:
    raw_value = os.environ.get(variable_name)
    if raw_value is None:
        return None

    normalized_value = raw_value.strip().lower()
    truthy_values = {"1", "true", "yes", "on"}
    falsy_values = {"0", "false", "no", "off"}

    if normalized_value in truthy_values:
        return True
    if normalized_value in falsy_values:
        return False
    raise ValueError(
        f"Unsupported boolean value '{raw_value}' for {variable_name}. "
        "Use one of: 1,0,true,false,yes,no,on,off."
    )


def _apply_environment_overrides(payload: dict) -> dict:
    merged_payload = dict(payload)

    list_overrides = {
        "cors_allow_origins": "AHU_SIMULATOR_CORS_ALLOW_ORIGINS",
        "cors_allow_methods": "AHU_SIMULATOR_CORS_ALLOW_METHODS",
        "cors_allow_headers": "AHU_SIMULATOR_CORS_ALLOW_HEADERS",
        "trusted_hosts": "AHU_SIMULATOR_TRUSTED_HOSTS",
    }
    for payload_key, env_key in list_overrides.items():
        env_values = _parse_csv_env(env_key)
        if env_values is not None:
            merged_payload[payload_key] = env_values

    bool_overrides = {
        "cors_allow_credentials": "AHU_SIMULATOR_CORS_ALLOW_CREDENTIALS",
        "enforce_https_redirect": "AHU_SIMULATOR_ENFORCE_HTTPS_REDIRECT",
        "developer_tools_enabled": "AHU_SIMULATOR_DEVELOPER_TOOLS_ENABLED",
    }
    for payload_key, env_key in bool_overrides.items():
        env_value = _parse_bool_env(env_key)
        if env_value is not None:
            merged_payload[payload_key] = env_value

    dashboard_path_override = os.environ.get("AHU_SIMULATOR_DASHBOARD_PATH")
    if dashboard_path_override:
        merged_payload["dashboard_path"] = dashboard_path_override.strip()

    default_scenario_override = os.environ.get("AHU_SIMULATOR_DEFAULT_SCENARIO_ID")
    if default_scenario_override:
        merged_payload["default_scenario_id"] = default_scenario_override.strip()

    return merged_payload


@lru_cache
def get_settings() -> ApplicationSettings:
    project_root = _project_root()
    _load_environment_file(project_root)
    config_path = _resolve_config_path(project_root)
    with config_path.open("r", encoding="utf-8") as config_file:
        payload = yaml.safe_load(config_file) or {}
    payload = _apply_environment_overrides(payload)
    return ApplicationSettings.model_validate(payload)


def get_project_root() -> Path:
    return _project_root()
