from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import parse_qs

from pydantic import BaseModel, ConfigDict


class UITheme(StrEnum):
    LEGACY = "legacy"
    CONCEPT03 = "concept03"


class FeatureFlags(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: UITheme = UITheme.LEGACY
    concept03_enabled: bool = False
    defense_day_variant: bool = False


@dataclass(frozen=True)
class Concept03ThemeState:
    theme: UITheme
    concept03_active: bool
    defense_active: bool

    @property
    def body_classes(self) -> tuple[str, ...]:
        if not self.concept03_active:
            return ("theme-legacy",)
        if self.defense_active:
            return ("theme-concept03", "c03-defense")
        return ("theme-concept03", "c03-operator")


def resolve_concept03_theme_state(
    search: str | None,
    feature_flags: FeatureFlags,
) -> Concept03ThemeState:
    query = parse_qs((search or "").lstrip("?"), keep_blank_values=False)
    requested_theme = _first_query_value(query, "theme")
    requested_defense = _first_query_value(query, "defense")

    if requested_theme == UITheme.LEGACY.value:
        concept03_active = False
        theme = UITheme.LEGACY
    elif requested_theme == UITheme.CONCEPT03.value:
        concept03_active = True
        theme = UITheme.CONCEPT03
    else:
        concept03_active = (
            feature_flags.concept03_enabled
            and feature_flags.theme == UITheme.CONCEPT03
        )
        theme = UITheme.CONCEPT03 if concept03_active else UITheme.LEGACY

    defense_active = concept03_active and (
        feature_flags.defense_day_variant or _is_truthy_query_value(requested_defense)
    )
    return Concept03ThemeState(
        theme=theme,
        concept03_active=concept03_active,
        defense_active=defense_active,
    )


def get_feature_flags() -> FeatureFlags:
    from app.infrastructure.settings import get_settings

    return get_settings().feature_flags


def _first_query_value(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    if not values:
        return None
    return values[0].strip().lower()


def _is_truthy_query_value(value: str | None) -> bool:
    return value in {"1", "true", "yes", "on"}
