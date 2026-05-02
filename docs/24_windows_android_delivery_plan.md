# План реализации Windows EXE и Android-приложения

Дата: 2026-04-18.

## Цель

Сделать текущий AHU Simulator удобным для использования как:

1. Windows desktop-приложение (exe/installer) без ручной установки Python.
2. Android mobile-приложение для сценария демонстрации и повседневного использования.

## Исходные вводные по текущему проекту

- Стек: FastAPI + Dash + Uvicorn + Python 3.
- Есть локальный запуск через `start.bat` и `deploy/run-local.ps1`.
- В проекте есть чтение конфигурации и данных из `config/`, `data/`, `models/`, `images-of-models/`.
- Сервисы активно пишут артефакты в `artifacts/...` (exports, event-log, scenario-archive, demo-packages).

Это означает, что при упаковке нужно отдельно решить:

- доставку data/config/assets в bundle;
- writable-путь для runtime-артефактов вне read-only каталога установки.

## Результат анализа (web + Context7)

1. `PyInstaller` подходит для Windows и поддерживает упаковку Python-приложения со всеми зависимостями.
2. `PyInstaller` не является cross-compiler: сборку Windows нужно делать на Windows.
3. Для `PyInstaller` критично явно добавить data-файлы (`--add-data` или `spec`), а путь к ним определять через `__file__`/runtime path.
4. Для Android наиболее практичный путь для web-UI сегодня: `Capacitor` (WebView shell).
5. `Capacitor` для Android поддерживает API 24+ и стандартный flow: `add android`, `sync`, `run`.
6. Для Android есть опция загрузки UI с удаленного URL (`server.url`) в `capacitor.config`.
7. `Briefcase` поддерживает Android, но для Python-пакетов с бинарными зависимостями часто возникают ограничения по Android wheels (повышенный риск для текущего стека).

## Рекомендуемая стратегия

## Трек A (рекомендуемый, основной)

- Windows: локальный self-contained desktop build через PyInstaller.
- Android: mobile shell на Capacitor, подключенный к удаленному HTTPS backend.

Плюс: минимум переписывания существующей архитектуры.

## Трек B (резервный R&D)

- Android offline-native с Python runtime (Briefcase/Chaquopy-like path).

Минус: высокий технический риск из-за совместимости Android wheels и особенностей Dash/FastAPI в mobile-runtime.

## Этапы реализации

## Этап 0. Decision Gate (2-4 дня)

Цель: формально зафиксировать требования и не уйти в неверный технологический путь.

Задачи:

- Уточнить обязательность offline-режима на Android.
- Уточнить формат Android-дистрибуции: APK для внутреннего теста или AAB для публикации.
- Уточнить модель доступа: локальная сеть, интернет, VPN.
- Зафиксировать целевые версии ОС: Windows 10/11, Android API >= 24.

Выход:

- Подписанное решение по Треку A как baseline.
- Отдельно отмечено, нужен ли Трек B.

## Этап 1. Подготовка проекта к упаковке (3-5 дней)

Цель: отделить runtime-пути и сделать приложение готовым к frozen-режиму.

Задачи:

- Ввести единый runtime-root для записи данных:
  - `%LOCALAPPDATA%/AhuSimulator/` на Windows;
  - мобильный app sandbox для Android-shell (если нужны локальные кэши/логи).
- Добавить настройки путей через env/config:
  - `AHU_SIMULATOR_RUNTIME_DIR` для writable артефактов;
  - сохранить read-only resource-root для встроенных данных.
- Обновить сервисы `export`, `event_log`, `scenario_archive`, `demo_readiness`, `comparison` на новый runtime-path.
- Проверить доступ к данным в frozen-режиме (`config`, `data`, `models`, `images-of-models`).

Выход:

- Приложение корректно работает из любого каталога, не пишет в source-tree.

## Этап 2. Windows EXE MVP (5-8 дней)

Цель: получить рабочий desktop-дистрибутив.

Задачи:

- Добавить desktop launcher (Python entrypoint):
  - выбирает порт;
  - стартует Uvicorn без `--reload`;
  - открывает `http://127.0.0.1:<port>/dashboard` в браузере.
- Подготовить `pyinstaller` spec:
  - включить необходимые каталоги данных;
  - настроить hidden imports (при необходимости);
  - сначала `onedir`, затем при желании `onefile`.
- Добавить скрипт сборки: `deploy/build-windows-exe.ps1`.
- Провести smoke-тесты:
  - запуск UI;
  - `/health`, `/scenarios`, `/simulation/run`;
  - экспорт и event-log в runtime-dir.
- Подготовить installer (Inno Setup/MSIX) как отдельный шаг после стабильного `onedir`.

Выход:

- Рабочий пакет для Windows без Python у пользователя.

## Этап 3. Android MVP через Capacitor (7-10 дней)

Цель: получить Android-приложение с минимальным time-to-market.

Задачи:

- Создать каталог `mobile/` с Capacitor проектом.
- Настроить `capacitor.config`:
  - `appId`, `appName`;
  - Android platform;
  - `server.url` на удаленный HTTPS endpoint Dashboard/API.
- Подготовить backend deployment для мобильного доступа:
  - стабильный URL;
  - HTTPS;
  - CORS и basic security policy.
- Проверить mobile UX в текущем Dash:
  - адаптивность основных блоков;
  - touch-friendly control sizes;
  - устойчивость графиков на небольшом экране.
- Собрать debug APK для внутреннего теста и release AAB/APK для демонстрации.

Выход:

- Android приложение открывает dashboard, запускает сценарии и отображает результаты на устройстве.

## Этап 4. Стабилизация и релизный контур (4-6 дней)

Цель: сделать поставку повторяемой и приемлемой для демонстрации/эксплуатации.

Задачи:

- CI pipeline:
  - job для Windows build;
  - job для Android build.
- Подписывание и versioning:
  - version metadata для exe;
  - keystore/signing для Android release.
- Release checklist:
  - установка на чистой Windows машине;
  - установка на 2-3 Android устройствах;
  - smoke сценарии: run simulation, export, archive.
- Обновить документацию пользователя и оператора.

Выход:

- Повторяемая сборка и воспроизводимый release process.

## Статус реализации этапа 4 (2026-04-18)

Реализовано:

- Добавлены CI workflow:
  - `.github/workflows/windows-pyinstaller.yml`;
  - `.github/workflows/android-capacitor.yml`.
- Введено единое вычисление версии из `pyproject.toml` через
  `deploy/resolve-release-version.ps1`.
- В Windows EXE добавлен Version resource metadata через
  `deploy/build-windows-exe.ps1` + `deploy/ahu-simulator-desktop.spec`.
- В Android build добавлены:
  - автоматическая подстановка `versionName/versionCode`;
  - release signing при наличии keystore variables в
    `mobile/android/app/build.gradle`.
- Подготовлен clean-install checklist:
  - `deploy/release-clean-install-checklist.md`.
- Обновлена документация поставки:
  - `deploy/README.md`;
  - `mobile/README.md`;
  - `README.md`.

## Критичные риски и меры

- Риск: приложение в `Program Files` не сможет писать артефакты.
  - Мера: перенос всех runtime-записей в `%LOCALAPPDATA%`.
- Риск: Android shell зависит от сети и backend-доступности.
  - Мера: health-check + экран недоступности + fallback инструкция.
- Риск: часть функций Dash неудобна на телефоне.
  - Мера: отдельный mobile QA проход и точечная адаптация layout/callback UX.
- Риск: попытка полной offline-Python сборки на Android затянет сроки.
  - Мера: держать как отдельный R&D трек, не блокирующий delivery Трека A.

## Оценка сроков

- Этап 0: 2-4 дня.
- Этап 1: 3-5 дней.
- Этап 2: 5-8 дней.
- Этап 3: 7-10 дней.
- Этап 4: 4-6 дней.

Итого для рабочего baseline (Трек A): примерно 3-5 недель.

## Definition of Done

- Windows: собран и проверен установочный пакет, приложение стартует и выполняет ключевые сценарии.
- Android: собран APK/AAB, приложение работает на целевых устройствах, сценарии выполняются через mobile shell.
- Runtime-артефакты пишутся в корректный writable-путь.
- Сборка повторяется по документированным скриптам и checklist.

## Источники

- PyInstaller Manual: https://pyinstaller.org/en/stable/
- PyInstaller Spec Files: https://pyinstaller.org/en/stable/spec-files.html
- PyInstaller Runtime Information: https://pyinstaller.org/en/stable/runtime-information.html
- Capacitor Android docs: https://capacitorjs.com/docs/android
- Capacitor configuration reference (Context7): `/ionic-team/capacitor-docs`
- Briefcase docs: https://briefcase.beeware.org/en/latest/
- Briefcase package compatibility notes (Context7): `/beeware/briefcase`
