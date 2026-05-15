# deploy

Каталог содержит скрипты запуска, сборки и поставки.

## Локальный запуск

- `..\setup.ps1` / `..\setup.bat` — первичная подготовка после clean clone:
  создание `.venv` и установка зависимостей. Локальный `config/local.env`
  создается только при явном `-CreateLocalEnv`.
- `run-local.ps1` — dev-режим (`uvicorn --reload`) с автоподбором порта.
- `run-desktop.ps1` — desktop launcher без `--reload`, c автоподбором порта и открытием `/dashboard` в отдельном app-окне Chromium (Edge/Chrome).

Если app-режим недоступен, launcher автоматически переключается в browser fallback.
Для принудительного fallback можно задать `AHU_SIMULATOR_DESKTOP_APP_MODE=0`.

Desktop launcher использует единый writable runtime-dir:

- `%LOCALAPPDATA%/AhuSimulator` в frozen/desktop режиме;
- override через `AHU_SIMULATOR_RUNTIME_DIR`.

В runtime-dir пишутся:

- `exports/`;
- `event-log/`;
- `scenario-archive/`;
- `demo-packages/`.

## Сборка Windows EXE (PyInstaller)

- Spec: `ahu-simulator-desktop.spec`.
- Build script: `build-windows-exe.ps1`.

Команда:

```powershell
.\deploy\build-windows-exe.ps1 -Clean
```

Результат: `dist/windows-exe/AhuSimulator/AhuSimulator.exe`.

Пост-сборочная проверка: `windows-exe-smoke-checklist.md`.

## Installer (Inno Setup)

- Скрипт Inno Setup: `installer/ahu-simulator.iss`.
- Wrapper build script: `build-windows-installer.ps1`.

Команда:

```powershell
.\deploy\build-windows-installer.ps1
```

Требование: установлен Inno Setup 6 (`ISCC.exe`) или передан `-IsccPath`.

Версия installer автоматически берется из `[project].version` в `pyproject.toml`
через `deploy/resolve-release-version.ps1`.

## Версионирование и подпись релиза

Единый источник версии: `pyproject.toml` (`[project].version`).

- `deploy/build-windows-exe.ps1` вычисляет версию через
	`deploy/resolve-release-version.ps1`;
- Windows EXE получает version metadata (PyInstaller Version resource);
- `deploy/build-windows-installer.ps1` передает ту же версию в
	`installer/ahu-simulator.iss`.

Опциональный override версии:

```powershell
$env:AHU_RELEASE_VERSION = "0.2.0"
.\deploy\build-windows-exe.ps1 -Clean
```

Подпись Windows EXE в CI включается автоматически, если заданы secrets:

- `WINDOWS_CODESIGN_CERT_BASE64`;
- `WINDOWS_CODESIGN_PASSWORD`.

Дополнительно можно задать repository variable
`WINDOWS_CODESIGN_TIMESTAMP_URL`.

## CI сборки

Workflow-файлы:

- `.github/workflows/windows-pyinstaller.yml` — Windows PyInstaller build;
- `.github/workflows/android-capacitor.yml` — Android Capacitor/Gradle build.

Оба workflow публикуют build artifacts через `actions/upload-artifact`.

## Release checklist

Clean-install checklist для desktop и mobile релиза:

- `deploy/release-clean-install-checklist.md`.

## Docker

Для контейнерного запуска:

```powershell
docker compose -f deploy/docker-compose.yml up --build
```

## Mobile backend (HTTPS)

Для Android/Capacitor shell используйте отдельный профиль
`deploy/mobile-backend/docker-compose.mobile.yml`.

Подготовка:

1. Скопировать `deploy/mobile-backend/.env.example` в
	`deploy/mobile-backend/.env`.
2. Указать реальные `MOBILE_PUBLIC_HOST`, `MOBILE_TLS_EMAIL`,
	`MOBILE_CORS_ORIGINS`, `MOBILE_TRUSTED_HOSTS`.

Запуск:

```powershell
.\deploy\run-mobile-backend.ps1 -Build
```

Остановка:

```powershell
.\deploy\run-mobile-backend.ps1 -Down
```

Детали и политика безопасности описаны в
`deploy/mobile-backend/README.md`.
