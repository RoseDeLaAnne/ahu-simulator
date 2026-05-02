# PVU Diploma Project

Интерактивная модель приточной вентиляционной установки для ВКР по теме:

«Моделирование работы приточной вентиляционной установки для ООО "НПО "Каскад-ГРУП"».

## Что уже реализовано

- собственное расчетное ядро ПВУ с рекуперацией, нагревателем, фильтром, вентилятором и упрощенной динамикой помещения;
- сценарии `winter`, `midseason`, `reduced_flow`, `dirty_filter`, `manual_mode`;
- FastAPI-слой с endpoint'ами `/health`, `/project/baseline`, `/readiness/demo`, `/readiness/package`, `/readiness/package/build`, `/events/log`, `/archive/scenarios`, `/exports/result`, `/exports/result/build`, `/simulation/run`, `/simulation/preview`, `/simulation/session/*`, `/scenarios`, `/comparison/*`, `/state`, `/trends`, `/validation/matrix`, `/validation/basis`, `/validation/manual-check`;
- Dash-панель на `/dashboard` с параметрами, мнемосхемой, карточками состояния, тревогами, трендами, Simulation Session v2, `P0 Baseline`, `Validation Pack`, `Validation Basis`, `Manual Check`, `Defense Pack`, `Demo Readiness`, встроенной сборкой `Demo Bundle`, блоками `Control Modes`, `Event Log`, `Export Pack`, `Before/After Comparison` и локальным `Scenario Archive`;
- единый пользовательский язык статусов `Норма` / `Риск` / `Авария` при сохранении технических API/enum значений `normal`, `warning`, `alarm`;
- versioned M10-M14 контракты: Simulation Session v2, `scenario-report.v2`, `run-comparison.v2`, `scenario-preset.v2`;
- пользовательские runtime-пресеты сценариев с create/update/rename/delete/import/export без изменения `data/scenarios/presets.json`;
- локальный `Event Log` для фиксации значимых расчётных переходов, смены `auto/manual`, export/build и archive/save действий;
- desktop launcher для Windows (`src/app/desktop_launcher.py`, `deploy/run-desktop.ps1`) с автоподбором порта, запуском backend без `--reload` и автооткрытием `/dashboard`;
- сборка Windows `onedir` через PyInstaller (`deploy/ahu-simulator-desktop.spec`, `deploy/build-windows-exe.ps1`) и scaffold installer-поставки на Inno Setup (`deploy/installer/ahu-simulator.iss`);
- воспроизводимый containerized-запуск через `deploy/docker-compose.yml`.
- unit-, integration- и scenario-тесты.

## Структура

- `src/app/simulation` — предметное ядро и формулы;
- `src/app/services` — orchestration расчета и трендов;
- `src/app/api` — FastAPI routers;
- `src/app/ui` — Dash layout, callbacks и стили;
- `data/validation` — контрольные точки, validation matrix, методические основания и ручная инженерная сверка;
- `data/scenarios` — пресеты сценариев;
- `config/defaults.yaml` — настройки приложения;
- `config/p0_baseline.yaml` — машиночитаемый baseline по P0 и scope первой версии;
- `docs/19_p0_baseline.md` — текстовая фиксация baseline и связи с dashboard/API;
- `deploy/run-local.ps1` — локальный запуск;
- `deploy/run-desktop.ps1` — desktop launcher без `--reload`;
- `deploy/docker-compose.yml` — воспроизводимый запуск в контейнере;
- `deploy/build-demo-package.ps1` — сборка offline/demo bundle;
- `deploy/build-windows-exe.ps1` — сборка Windows EXE (PyInstaller onedir);
- `deploy/build-windows-installer.ps1` — сборка Windows installer (Inno Setup);
- `artifacts/playwright` — ручные Playwright-скриншоты и другие UI-артефакты;
- `artifacts/event-log` — локальный журнал событий и переходов состояния;
- `artifacts/exports` — локальные `CSV/XLSX/PDF` export-наборы;
- `artifacts/scenario-archive` — локальный архив сохранённых прогонов.
- `artifacts/simulation-session.json` — runtime snapshot активной simulation session;
- `artifacts/comparison-snapshots` — runtime-снимки `До`/`После` для comparison;
- `artifacts/user-presets` — пользовательские пресеты сценариев.

## Быстрый старт

```powershell
.\start.bat
```

Скрипт создаст виртуальное окружение, установит зависимости и запустит Uvicorn. Если порт `8000` уже занят, он автоматически выберет следующий свободный порт и выведет точный URL в консоль.

Контейнерный запуск:

```powershell
docker compose -f deploy/docker-compose.yml up --build
```

После старта:

- API: `http://127.0.0.1:<порт из консоли>/docs`
- Dashboard: `http://127.0.0.1:<порт из консоли>/dashboard`

One-click файлы для Windows:

- `start.bat` / `tooling/commands/windows/run-dashboard.cmd` — локальный dashboard;
- `tooling/commands/windows/run-desktop.cmd` — desktop app;
- `tooling/commands/windows/run-mobile-backend.cmd` — HTTPS backend для mobile shell;
- `tooling/commands/windows/build-mobile-debug.cmd` — сборка debug APK;
- `tooling/commands/windows/install-mobile-debug.cmd` — сборка и установка debug APK на подключенный Android.

Подробная инструкция: `docs/25_windows_run_guide.md`.

Desktop-режим из исходников:

```powershell
.\deploy\run-desktop.ps1
```

Сборка Windows EXE:

```powershell
.\deploy\build-windows-exe.ps1 -Clean
```

Android mobile shell (Capacitor):

```powershell
cd mobile
npm install
npm run add:android
npm run build:debug
```

Release-артефакты:

```powershell
npm run build:release:apk
npm run build:release:aab
```

Подготовка HTTPS backend для mobile-доступа:

```powershell
.\deploy\run-mobile-backend.ps1 -Build
```

Подробности по mobile shell: `mobile/README.md`.
Подробности по backend-профилю: `deploy/mobile-backend/README.md`.

## CI и релизная инфраструктура desktop/mobile

- Windows build pipeline: `.github/workflows/windows-pyinstaller.yml`;
- Android build pipeline: `.github/workflows/android-capacitor.yml`;
- Единый источник версии для desktop/mobile: `pyproject.toml`
	(`[project].version`) через `deploy/resolve-release-version.ps1`;
- Clean-install release checklist: `deploy/release-clean-install-checklist.md`.

Текущие ограничения поставки:

- desktop runtime-артефакты пишутся в `%LOCALAPPDATA%/AhuSimulator`;
- mobile shell требует доступного HTTPS backend.

В desktop/frozen режиме runtime-артефакты (`exports`, `event-log`, `scenario-archive`, `demo-packages`) пишутся в `%LOCALAPPDATA%/AhuSimulator`.

## Тесты

```powershell
python -m pytest
```

Последний release-readiness gate для M10-M14: full regression
`python -m pytest`; acceptance evidence описан в
`.omx/plans/m10_m14_acceptance_matrix.md`.
Локальный dashboard smoke evidence за 2026-05-02 лежит в
`artifacts/release-readiness/2026-05-02/`; перед защитой его стоит повторить на
целевом демо-ПК.

Финальный defense walkthrough и recovery plan описаны в
`docs/14_defense_pack.md`. Phase G evidence после локальной проверки
сохраняется в
`artifacts/release-readiness/2026-05-02/m10-m14-phase-g-evidence.md`.
Финальная freeze-памятка для целевого показа: `docs/28_defense_freeze_note.md`;
Phase H evidence:
`artifacts/release-readiness/2026-05-02/m10-m14-phase-h-final-demo-pc-evidence.md`.
Финальный handoff-индекс и короткий документ "open this first":
`artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`
и `docs/29_defense_handoff.md`.

## Принятые упрощения текущей версии

- расчетный тракт ориентирован на учебно-обобщенную ПВУ, а не на конкретный паспортный агрегат;
- модель помещения реализована как первый порядок с дискретным шагом;
- PID-регулятор и OpenModelica-адаптер оставлены на следующий инженерный этап после текущего P2.
