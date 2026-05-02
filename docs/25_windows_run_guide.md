# Windows Run Guide

Инструкция описывает запуск проекта на Windows без ручного набора команд и разделяет три сценария:

- локальный dashboard/API из исходников;
- desktop-приложение под Windows;
- mobile shell для Android с debug APK.

## Что подготовлено

В проекте доступны click-to-run файлы:

- `start.bat` и `tooling/commands/windows/run-dashboard.cmd` — локальный backend + автоматическое открытие `/dashboard`;
- `tooling/commands/windows/run-desktop.cmd` — desktop launcher на базе `src/app/desktop_launcher.py`;
- `tooling/commands/windows/run-mobile-backend.cmd` — запуск HTTPS mobile-backend через Docker Compose;
- `tooling/commands/windows/stop-mobile-backend.cmd` — остановка mobile-backend;
- `tooling/commands/windows/build-mobile-debug.cmd` — сборка debug APK;
- `tooling/commands/windows/install-mobile-debug.cmd` — сборка debug APK, установка на подключенный Android и запуск приложения.

## 1. Локальный запуск dashboard на Windows

Самый простой путь:

1. Дважды кликнуть `start.bat` или `tooling/commands/windows/run-dashboard.cmd`.
2. Скрипт сам:
   - создаст `.venv`, если его нет;
   - установит Python-зависимости из `requirements.txt`, если они не установлены;
   - поднимет Uvicorn;
   - откроет `http://127.0.0.1:<свободный-порт>/dashboard` в браузере.

Что нужно на машине:

- Python `3.12+`;
- доступный `python` или `py` в `PATH`.

Если `8000` занят, скрипт выберет следующий свободный порт и выведет его в консоль.

## 2. Запуск Windows desktop app

Если нужен desktop-режим в отдельном app-окне:

1. Дважды кликнуть `tooling/commands/windows/run-desktop.cmd`.
2. Скрипт подготовит Python-окружение и вызовет `deploy/run-desktop.ps1`.

Результат:

- backend стартует без `--reload`;
- launcher подберет порт;
- dashboard откроется в app-окне Edge/Chrome, либо в обычном браузере как fallback.

Runtime-артефакты desktop-режима пишутся в `%LOCALAPPDATA%\AhuSimulator`.

## 3. Запуск mobile backend для Android

Этот шаг нужен только для mobile shell, потому что Android-приложение загружает dashboard по реальному HTTPS URL.

Перед первым запуском:

1. Скопировать `deploy/mobile-backend/.env.example` в `deploy/mobile-backend/.env`.
2. Заполнить:
   - `MOBILE_PUBLIC_HOST`;
   - `MOBILE_TLS_EMAIL`;
   - `MOBILE_CORS_ORIGINS`;
   - `MOBILE_TRUSTED_HOSTS`.
3. Убедиться, что Docker Desktop запущен.

Запуск:

1. Дважды кликнуть `tooling/commands/windows/run-mobile-backend.cmd`.
2. Для остановки использовать `tooling/commands/windows/stop-mobile-backend.cmd`.

После старта нужно проверить:

- `https://<host>/health`
- `https://<host>/dashboard`
- `https://<host>/docs`

## 4. Сборка и установка Android debug APK

Что нужно на Windows-машине:

- Node.js `20+`;
- Java JDK `21+`;
- Android SDK + Platform Tools;
- `adb` в `PATH`;
- заполненный `mobile/.env` с реальным `MOBILE_BACKEND_HTTPS_URL=https://.../dashboard`.

### Сборка

1. Дважды кликнуть `tooling/commands/windows/build-mobile-debug.cmd`.
2. Скрипт:
   - проверит `npm`;
   - выполнит `npm install` в `mobile/`, если нужно;
   - синхронизирует Capacitor Android project;
   - соберет `android/app/build/outputs/apk/debug/app-debug.apk`.

### Сборка + установка на телефон

1. Включить `USB debugging` на Android-устройстве.
2. Подключить телефон по USB или ADB over Wi-Fi.
3. Дважды кликнуть `tooling/commands/windows/install-mobile-debug.cmd`.

Скрипт:

- соберет debug APK;
- установит APK через `adb install -r`;
- запустит `com.ahusimulator.mobile`.

Если устройств несколько, `mobile/scripts/install-debug-apk.ps1` нужно запускать вручную с `-DeviceId <serial>`.

## 5. Ручные команды, если нужен контроль из терминала

Локальный backend:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\bootstrap-python.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\run-local.ps1 -OpenDashboard
```

Desktop launcher:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\bootstrap-python.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\run-desktop.ps1
```

Mobile build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\bootstrap-mobile.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\mobile\scripts\build-android.ps1 -Debug
```

Mobile install:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\mobile\scripts\install-debug-apk.ps1 -Build
```

## 6. Типовые проблемы на Windows

`PowerShell script execution is disabled`

- Используйте `start.bat` или `.cmd`-скрипты из `tooling/commands/windows`: они запускают PowerShell с `-ExecutionPolicy Bypass` только для текущего процесса.

`Python not found`

- Установите Python `3.12+` и включите опцию добавления в `PATH`.

`npm not found`

- Установите Node.js `20+`.

`adb was not found`

- Установите Android SDK Platform Tools и добавьте каталог с `adb.exe` в `PATH`.

`MOBILE_BACKEND_HTTPS_URL must use HTTPS`

- Для mobile shell нужен только реальный HTTPS endpoint. Локальный `http://127.0.0.1:8000/dashboard` для APK не подходит.

## 7. Быстрый recovery перед защитой

Если времени мало, используйте самый короткий проверяемый путь:

```powershell
python -m pytest
$env:AHU_SIMULATOR_PORT=8765
python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8765
```

Затем открыть:

- `http://127.0.0.1:8765/health`
- `http://127.0.0.1:8765/dashboard`

Если порт `8765` занят, поменять только значение `AHU_SIMULATOR_PORT` и URL.
Если dashboard не открылся автоматически, но `/health` отвечает `status=ok`,
откройте `/dashboard` вручную. Если browser/WebGL-диагностика показывает
warning, продолжайте показ через 2D SVG-мнемосхему, отчеты, comparison,
validation и evidence из `artifacts/release-readiness/2026-05-02/`.

Перед закрытием терминала убедитесь, что серверный процесс остановлен. Для
обычного запуска через `start.bat` достаточно закрыть консоль или нажать
`Ctrl+C` в окне Uvicorn.

## Источники

- Python `venv` на Windows: https://docs.python.org/3/library/venv.html
- PowerShell `ExecutionPolicy`: https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_execution_policies
- Capacitor Android CLI через Context7: https://github.com/ionic-team/capacitor-docs/blob/main/docs/main/android/troubleshooting.md
- Capacitor platform workflow через Context7: https://github.com/ionic-team/capacitor-docs/blob/main/docs/plugins/tutorial/getting-started.md
- Android `adb install`: https://developer.android.com/guide/developing/tools/adb.html
