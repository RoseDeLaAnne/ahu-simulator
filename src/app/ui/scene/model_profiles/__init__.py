"""Профили сцены 3D-моделей — по одному модулю на модель.

Каждая модель описывается отдельным файлом `model_profiles/<model_id>.py`,
который экспортирует словарь `PROFILE` с переопределениями поверх
`_base.DEFAULT_SCENE_PROFILE`. Здесь они собираются в реестр
`MODEL_SCENE_PROFILES`, а `build_scene_profile()` сливает базовый профиль с
профилем выбранной модели.

Публичный API (`DEFAULT_SCENE_PROFILE`, `MODEL_SCENE_PROFILES`,
`build_scene_profile`) сохранён, чтобы импортирующие модули
(`model_catalog`) не менялись.
"""

from __future__ import annotations

from copy import deepcopy

from app.ui.scene.model_profiles._base import DEFAULT_SCENE_PROFILE
from app.ui.scene.model_profiles import (
    base_classic,
    base_variant_a,
    base_variant_b,
    base_variant_c,
    industrial_hvac_unit,
    industrial_machinery_unit,
    modular_ahu,
    pvu_installation,
)

__all__ = [
    "DEFAULT_SCENE_PROFILE",
    "MODEL_SCENE_PROFILES",
    "build_scene_profile",
]


MODEL_SCENE_PROFILES: dict[str, dict[str, object]] = {
    "modular_ahu": modular_ahu.PROFILE,
    "industrial_hvac_unit": industrial_hvac_unit.PROFILE,
    "industrial_machinery_unit": industrial_machinery_unit.PROFILE,
    "base_classic": base_classic.PROFILE,
    "base_variant_a": base_variant_a.PROFILE,
    "base_variant_b": base_variant_b.PROFILE,
    "base_variant_c": base_variant_c.PROFILE,
    "pvu_installation": pvu_installation.PROFILE,
}


def build_scene_profile(model_id: str | None) -> dict[str, object]:
    profile = deepcopy(DEFAULT_SCENE_PROFILE)
    _deep_merge(profile, MODEL_SCENE_PROFILES.get(model_id or "", {}))
    return profile


def _deep_merge(target: dict[str, object], updates: dict[str, object]) -> None:
    for key, value in updates.items():
        if (
            key in target
            and isinstance(target[key], dict)
            and isinstance(value, dict)
        ):
            _deep_merge(target[key], value)
            continue
        target[key] = deepcopy(value)
