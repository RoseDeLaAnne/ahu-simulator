from app.infrastructure.settings import ApplicationSettings, get_settings


def test_developer_tools_disabled_by_default() -> None:
    assert ApplicationSettings().developer_tools_enabled is False


def test_developer_tools_enabled_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("AHU_SIMULATOR_DEVELOPER_TOOLS_ENABLED", "true")
    get_settings.cache_clear()

    try:
        assert get_settings().developer_tools_enabled is True
    finally:
        get_settings.cache_clear()


def test_developer_tools_enabled_from_local_environment_file(tmp_path, monkeypatch) -> None:
    environment_file = tmp_path / "local.env"
    environment_file.write_text("AHU_SIMULATOR_DEVELOPER_TOOLS_ENABLED=true\n", encoding="utf-8")
    monkeypatch.setenv("AHU_SIMULATOR_ENV_FILE", str(environment_file))
    monkeypatch.delenv("AHU_SIMULATOR_DEVELOPER_TOOLS_ENABLED", raising=False)
    get_settings.cache_clear()

    try:
        assert get_settings().developer_tools_enabled is True
    finally:
        get_settings.cache_clear()


def test_real_environment_overrides_local_environment_file(tmp_path, monkeypatch) -> None:
    environment_file = tmp_path / "local.env"
    environment_file.write_text("AHU_SIMULATOR_DEVELOPER_TOOLS_ENABLED=true\n", encoding="utf-8")
    monkeypatch.setenv("AHU_SIMULATOR_ENV_FILE", str(environment_file))
    monkeypatch.setenv("AHU_SIMULATOR_DEVELOPER_TOOLS_ENABLED", "false")
    get_settings.cache_clear()

    try:
        assert get_settings().developer_tools_enabled is False
    finally:
        get_settings.cache_clear()
