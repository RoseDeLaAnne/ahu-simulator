from pathlib import Path

from app.infrastructure.feature_flags import (
    FeatureFlags,
    UITheme,
    get_feature_flags,
    resolve_concept03_theme_state,
)
from app.infrastructure.settings import get_settings


def test_concept03_query_overrides_disabled_default() -> None:
    flags = FeatureFlags(
        theme=UITheme.LEGACY,
        concept03_enabled=False,
        defense_day_variant=False,
    )

    state = resolve_concept03_theme_state("?theme=concept03", flags)

    assert state.concept03_active is True
    assert state.defense_active is False
    assert state.body_classes == ("theme-concept03", "c03-operator")


def test_legacy_query_overrides_enabled_default() -> None:
    flags = FeatureFlags(
        theme=UITheme.CONCEPT03,
        concept03_enabled=True,
        defense_day_variant=True,
    )

    state = resolve_concept03_theme_state("?theme=legacy&defense=true", flags)

    assert state.concept03_active is False
    assert state.defense_active is False
    assert state.body_classes == ("theme-legacy",)


def test_settings_parse_ui_feature_flags(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "defaults.yaml"
    config_path.write_text(
        """
ui:
  theme: concept03
  concept03_enabled: true
  defense_day_variant: true
""".lstrip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("AHU_SIMULATOR_SETTINGS_FILE", str(config_path))
    get_settings.cache_clear()

    try:
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert settings.feature_flags.theme == UITheme.CONCEPT03
    assert settings.feature_flags.concept03_enabled is True
    assert settings.feature_flags.defense_day_variant is True


def test_get_feature_flags_returns_settings_defaults() -> None:
    get_settings.cache_clear()

    try:
        flags = get_feature_flags()
    finally:
        get_settings.cache_clear()

    assert flags.theme == UITheme.LEGACY
    assert flags.concept03_enabled is False
    assert flags.defense_day_variant is False
