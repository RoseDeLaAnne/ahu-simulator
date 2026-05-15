# Техническая документация

Дата актуализации: 2026-05-11.

## Назначение документа

Документ описывает устройство проекта `PVU Diploma Project` с точки зрения
разработчика и сопровождающего инженера: где находится расчетное ядро, как
собирается приложение, какие есть API-контракты, где лежат настройки и
runtime-артефакты, как запускать тесты и что учитывать при доработках.

Пользовательская инструкция вынесена отдельно в `docs/35_user_manual.md`.

## 1. Краткое описание системы

Проект представляет собой локальное приложение для моделирования работы
приточной вентиляционной установки. В одном контуре собраны:

- расчетная модель ПВУ;
- сервисы для запуска сценариев, трендов, статусов и сессий;
- REST API на FastAPI;
- dashboard на Dash;
- экспорт отчетов;
- сравнение прогонов;
- локальный архив сценариев;
- validation/readiness материалы;
- Windows, Docker и Android delivery-скрипты.

Основной архитектурный принцип: предметная логика не должна жить в UI или API
routers. Формулы и ограничения находятся в `src/app/simulation`, orchestration
в `src/app/services`, а dashboard и API только используют готовые сервисные
контракты.

## 2. Технологический стек

| Компонент | Использование |
| --- | --- |
| Python 3.12+ | Основной язык проекта. |
| FastAPI | HTTP API, OpenAPI, middleware, mount dashboard. |
| Pydantic | Валидация параметров и строгие DTO. |
| Dash | Основной пользовательский dashboard. |
| Plotly | Графики и тренды. |
| SVG / JS assets | 2D-мнемосхема и клиентские обновления. |
| Three.js assets | 3D/WebGL слой, когда он доступен. |
| ReportLab | PDF-отчеты без внешнего сервиса. |
| pytest | Unit, integration и scenario-проверки. |
| PyInstaller | Windows desktop onedir-сборка. |
| Inno Setup | Installer-обертка для Windows. |
| Docker Compose | Воспроизводимый backend/dashboard запуск. |
| Capacitor / Android | Mobile shell для открытия dashboard через HTTPS backend. |

## 3. Архитектурная схема

```text
config/defaults.yaml
data/scenarios/*.json
data/validation/*.json
        |
        v
src/app/bootstrap/app_factory.py
        |
        +-- infrastructure/settings, runtime paths, logging
        +-- simulation core
        +-- application services
        +-- FastAPI routers
        +-- Dash dashboard
        +-- runtime artifacts
```

Слои проекта:

| Слой | Где находится | Ответственность |
| --- | --- | --- |
| Simulation core | `src/app/simulation` | Параметры, формулы, состояния, тревоги, сценарии, статусная политика. |
| Services | `src/app/services` | Координация расчетов, трендов, export, comparison, archive, readiness. |
| API | `src/app/api/routers` | HTTP-контракты и схемы ответов. |
| UI | `src/app/ui` | Dash layout, callbacks, viewmodels, assets, render modes. |
| Infrastructure | `src/app/infrastructure` | Настройки, logging, runtime paths. |
| Deployment | `deploy`, `tooling`, `mobile` | Запуск, сборка, packaging, mobile backend. |

## 4. Структура репозитория

| Путь | Что важно знать |
| --- | --- |
| `src/app/main.py` | Минимальная точка входа: создает FastAPI app через `create_app()`. |
| `src/app/bootstrap/app_factory.py` | Центральная сборка приложения и middleware. |
| `src/app/bootstrap/wiring.py` | Создание сервисов, подключение routers, mount dashboard/static. |
| `src/app/simulation/` | Не завязывать на Dash/FastAPI. Это предметный слой. |
| `src/app/services/` | Содержит бизнес-операции поверх расчетного ядра. |
| `src/app/api/routers/` | Тонкие routers, которые берут сервисы из `app.state`. |
| `src/app/ui/` | Dashboard, callbacks, viewmodels и визуальные assets. |
| `config/` | YAML/env конфигурация и P0 baseline. |
| `data/scenarios/` | Системные сценарии, стабильные ID. |
| `data/validation/` | Эталонные точки и методические материалы. |
| `data/visualization/` | Конфигурация 3D/визуальных сигналов. |
| `models/` | GLB-модели установки и помещений. |
| `artifacts/` | Runtime-данные локального запуска. |
| `deploy/` | Запуск, Docker, PyInstaller, installer, mobile backend. |
| `mobile/` | Android shell на Capacitor. |
| `tests/` | Автотесты по уровням: unit, integration, scenario. |
| `docs/` | Проектная, защитная, пользовательская и техническая документация. |

## 5. Сборка приложения при запуске

Точка входа:

```python
from app.bootstrap.app_factory import create_app

app = create_app()
```

`create_app()` выполняет последовательность:

1. Настраивает logging.
2. Загружает `ApplicationSettings`.
3. Создает все application services.
4. Подключает security middleware.
5. Сохраняет сервисы в `app.state`.
6. Монтирует статические runtime-ресурсы `/models` и `/images-of-models`.
7. Подключает API routers.
8. Регистрирует redirect `/ -> dashboard_path`.
9. Монтирует Dash dashboard.

Эта схема важна для сопровождения: API и UI используют один и тот же набор
сервисов, поэтому поведение dashboard и REST endpoints не должно расходиться.

## 6. Конфигурация

Основной конфиг: `config/defaults.yaml`.

Минимально важные настройки:

| Ключ | Назначение |
| --- | --- |
| `project_name` | Название приложения в FastAPI/OpenAPI. |
| `dashboard_path` | Путь, по которому монтируется Dash UI. |
| `default_scenario_id` | Стартовый сценарий. |
| `trend_horizon_minutes` | Горизонт временных рядов. |
| `trend_step_minutes` | Шаг временных рядов. |
| `nominal_airflow_m3_h` | Номинальный расход для диагностик. |
| `base_filter_pressure_drop_pa` | Базовое сопротивление фильтра. |
| `max_filter_pressure_drop_pa` | Верхняя граница сопротивления фильтра. |
| `status_thresholds` | Пороги пользовательских статусов. |
| `cors_allow_*` | CORS-политика для local/mobile контуров. |
| `trusted_hosts` | Настройки TrustedHostMiddleware. |
| `enforce_https_redirect` | Принудительный HTTPS redirect для proxy/mobile контуров. |
| `developer_tools_enabled` | Включение developer controls в UI. |

Поддерживаются env override:

```text
AHU_SIMULATOR_SETTINGS_FILE
AHU_SIMULATOR_ENV_FILE
AHU_SIMULATOR_CORS_ALLOW_ORIGINS
AHU_SIMULATOR_CORS_ALLOW_METHODS
AHU_SIMULATOR_CORS_ALLOW_HEADERS
AHU_SIMULATOR_CORS_ALLOW_CREDENTIALS
AHU_SIMULATOR_TRUSTED_HOSTS
AHU_SIMULATOR_ENFORCE_HTTPS_REDIRECT
AHU_SIMULATOR_DASHBOARD_PATH
AHU_SIMULATOR_DEFAULT_SCENARIO_ID
AHU_SIMULATOR_DEVELOPER_TOOLS_ENABLED
```

`config/local.env` можно использовать для локальных значений. Файл не должен
храниться в git. Реальные переменные окружения имеют приоритет над значениями
из local env, потому что загрузчик использует `os.environ.setdefault()`.

## 7. Runtime-артефакты

В режиме запуска из исходников runtime-файлы пишутся в `artifacts/`. В frozen
desktop-сборке используется writable-каталог:

```text
%LOCALAPPDATA%\AhuSimulator
```

Типовые артефакты:

| Артефакт | Назначение |
| --- | --- |
| `exports/` | CSV/PDF/manifest отчеты. |
| `event-log/` | Журнал действий и статусных переходов. |
| `scenario-archive/` | Сохраненные прогоны. |
| `user-presets/` | Пользовательские сценарии. |
| `comparison-snapshots/` | Снимки "до" и "после". |
| `demo-packages/` | Demo bundle. |
| `simulation-session.json` | Текущая simulation session. |

При добавлении новых runtime-файлов нужно использовать существующий resolver
путей, чтобы не сломать desktop/frozen режим, где каталог установки может быть
read-only.

## 8. Расчетное ядро

Основные файлы:

| Файл | Роль |
| --- | --- |
| `parameters.py` | Входная модель `SimulationParameters`, диапазоны и control mode. |
| `equations.py` | Расчетные зависимости. |
| `state.py` | Выходные модели состояния и результата. |
| `scenarios.py` | Сценарные DTO и загрузка системных сценариев. |
| `alarms.py` | Формирование предупреждений. |
| `control.py` | Упрощенная логика управления. |
| `status_policy.py` | Пороги и правила статусов. |

`SimulationParameters` запрещает лишние поля (`extra="forbid"`). Это защищает
API от "молчаливого" приема неподдержанных параметров.

Основные входы:

| Поле | Диапазон | Комментарий |
| --- | --- | --- |
| `outdoor_temp_c` | `-45..45` | Наружный воздух. |
| `airflow_m3_h` | `200..8000` | Заданный расход. |
| `supply_temp_setpoint_c` | `10..35` | Уставка притока. |
| `heat_recovery_efficiency` | `0..0.85` | Эффективность рекуперации. |
| `heater_power_kw` | `0..120` | Доступная мощность нагрева. |
| `filter_contamination` | `0..1` | Загрязнение фильтра. |
| `fan_speed_ratio` | `0.2..1.2` | Относительная скорость вентилятора. |
| `room_temp_c` | `5..40` | Температура помещения. |
| `room_heat_gain_kw` | `-10..40` | Внутренние теплопритоки/потери. |
| `room_volume_m3` | `50..2000` | Объем помещения. |
| `room_thermal_capacity_kwh_per_k` | `1..200` | Теплоемкость помещения. |
| `room_loss_coeff_kw_per_k` | `0.01..2` | Коэффициент теплопотерь. |
| `control_mode` | `auto/manual` | Режим управления. |
| `horizon_minutes` | `10..720` | Горизонт тренда. |
| `step_minutes` | `1..60` | Шаг тренда. |

## 9. Сервисный слой

Сервисы создаются централизованно в `build_application_services()`.

| Сервис | Ответственность |
| --- | --- |
| `SimulationService` | Расчет, сценарии, preview, session tick/start/pause/reset. |
| `TrendService` | Временные ряды для графиков и отчетов. |
| `StatusService` | Единый слой `Норма/Риск/Авария`. |
| `ScenarioPresetService` | Системные и пользовательские пресеты. |
| `SimulationSessionStore` | Хранение состояния session. |
| `ValidationService` | Matrix, basis, agreement, manual check. |
| `ExportService` | Scenario report CSV/PDF/manifest. |
| `RunComparisonService` | Сравнение "до/после", compatibility и export. |
| `ScenarioArchiveService` | Локальный архив прогонов. |
| `EventLogService` | Журнал событий. |
| `DemoReadinessService` | Проверка готовности и demo package. |
| `BrowserCapabilityService` | Browser/WebGL profile. |
| `ProjectBaselineService` | P0 baseline snapshot. |

Сервисы прикрепляются к `app.state`, после чего routers и dashboard используют
одни и те же экземпляры.

## 10. API

OpenAPI доступен по `/docs`. Глобальный `api_prefix` сейчас пустой.

| Область | Endpoints |
| --- | --- |
| Health | `GET /health` |
| Project | `GET /project/baseline` |
| Simulation | `POST /simulation/run`, `POST /simulation/preview`, `GET /simulation/trends` |
| Session | `GET /simulation/session`, `POST /simulation/session/start`, `POST /simulation/session/pause`, `POST /simulation/session/speed`, `POST /simulation/session/reset`, `POST /simulation/session/tick` |
| State | `GET /state`, `GET /trends` |
| Scenarios | `GET /scenarios`, `POST /scenarios/{scenario_id}/run` |
| User presets | `POST /scenarios/user`, `PUT /scenarios/user/{preset_id}`, `PATCH /scenarios/user/{preset_id}/rename`, `DELETE /scenarios/user/{preset_id}`, import/export endpoints |
| Validation | `GET /validation/matrix`, `GET /validation/basis`, `GET /validation/agreement`, `POST /validation/manual-check` |
| Visualization | `GET /visualization/state`, `GET /visualization/browser-profile` |
| Export | `GET /exports/result`, `POST /exports/result/preview`, `POST /exports/result/build`, `POST /exports/result/batch`, download endpoint |
| Comparison | `GET /comparison/runs`, capture before/after, build, export, download endpoints |
| Archive | `GET /archive/scenarios`, `POST /archive/scenarios`, download endpoint |
| Events | `GET /events/log`, download endpoint |
| Readiness | `GET /readiness/demo`, `GET /readiness/package`, `POST /readiness/package/build` |

Routers должны оставаться тонкими: получить сервис, вызвать метод, вернуть DTO
или HTTP-ошибку. Новую предметную логику нужно добавлять в service/core слой.

## 11. Dashboard

Dashboard монтируется из `src/app/ui/dashboard.py`. Основные части:

| Файл/каталог | Назначение |
| --- | --- |
| `layout.py` | Сборка основного layout. |
| `callbacks.py` | Реакция на пользовательские действия. |
| `viewmodels/` | Подготовка данных для UI-блоков. |
| `render_modes/` | 2D/3D рабочие области. |
| `scene/` | Scene bindings, model catalog, room catalog. |
| `assets/` | CSS, JS, SVG, vendor assets. |

Dashboard не должен напрямую повторять формулы из `simulation`. Если UI нужен
новый показатель, его лучше добавить в результат сервиса или viewmodel, а не
считать в callback.

## 12. Визуальный слой

Визуализация построена вокруг общей идеи: расчетное ядро выдает состояние, а
UI превращает его в понятные сигналы.

Ключевые элементы:

- `VisualizationSignalMap`;
- 2D SVG-мнемосхема;
- optional 3D/WebGL viewer;
- browser capability profile;
- модели и конфигурация сцены в `models/` и `data/visualization/`.

3D-слой не должен становиться обязательным для работы продукта. Базовый
демонстрационный путь должен сохраняться через 2D, KPI, графики, export,
validation и comparison.

## 13. Статусы

Пользователь видит статусы:

| API value | UI label | Смысл |
| --- | --- | --- |
| `normal` | `Норма` | Рабочий режим. |
| `warning` | `Риск` | Предупреждающее отклонение. |
| `alarm` | `Авария` | Критическое отклонение. |

Пороговые значения находятся в `config/defaults.yaml -> status_thresholds`.
Применение порогов сосредоточено в `status_policy.py` и `StatusService`.

Важно не размазывать статусные правила по dashboard, export и comparison.
Иначе одинаковый режим начнет отображаться по-разному в разных частях
приложения.

## 14. Сценарии и пользовательские пресеты

Системные сценарии хранятся в `data/scenarios/presets.json`. Их ID считаются
стабильными: на них опираются UI, тесты, документация и демонстрационные
сценарии.

Пользовательские пресеты хранятся отдельно в runtime-каталоге. Они не должны
перезаписывать системный JSON.

При добавлении нового системного сценария нужно обновить:

- `data/scenarios/presets.json`;
- scenario-тесты;
- пользовательскую документацию, если сценарий предназначен для демонстрации;
- acceptance/evidence материалы, если сценарий участвует в защите.

## 15. Отчеты

`ExportService` формирует отчет текущего прогона в формате `scenario-report.v2`.

Стандартный набор:

```text
pvu-report-YYYYMMDD-HHMMSS.csv
pvu-report-YYYYMMDD-HHMMSS.pdf
pvu-report-YYYYMMDD-HHMMSS.manifest.json
```

CSV нужен для машинной обработки, PDF - для читаемой передачи, manifest - для
связи DTO, путей, версии схемы и metadata.

При изменении структуры отчета нужно сохранить обратную понятность секций:
metadata, parameters, state, findings, status legend, events, trend.

## 16. Сравнение прогонов

`RunComparisonService` отвечает за сравнение "до/после" и export
`run-comparison.v2`.

Сравнение считается корректным только при совместимости пары:

- одинаковый `step_minutes`;
- одинаковый `horizon_minutes`;
- одинаковое число точек тренда;
- одинаковая временная сетка;
- одинаковый набор сравниваемых KPI/diagnostic fields.

Если совместимость нарушена, нужно явно показывать причину в UI и не строить
сомнительный export.

## 17. Validation и readiness

Validation subsystem опирается на:

- `data/validation/reference_points.json`;
- `data/validation/reference_basis.json`;
- `data/validation/validation_agreement.json`;
- `ValidationService`;
- validation routers;
- UI viewmodels.

Readiness subsystem опирается на `DemoReadinessService`, readiness API,
dashboard-блоки и документы защиты. Его задача - быстро ответить на вопрос:
готов ли проект к показу на конкретной машине.

## 18. Security и ограничения

В приложении есть базовая инфраструктурная защита:

- TrustedHostMiddleware;
- optional HTTPS redirect;
- CORS-настройки;
- отдельный mobile HTTPS профиль.

При этом текущий scope сознательно не включает:

- регистрацию пользователей;
- авторизацию и роли;
- хранение промышленных секретов;
- подключение к реальному оборудованию;
- production SCADA deployment.

Если проект будет развиваться в сторону реальной эксплуатации, эти пункты
нужно проектировать отдельно, а не "прикручивать" поверх текущего demo-контура.

## 19. Запуск для разработки

Подготовка окружения:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Запуск напрямую:

```powershell
python -m uvicorn app.main:app --app-dir src --reload
```

Запуск через проектный скрипт:

```powershell
.\deploy\run-local.ps1 -OpenDashboard
```

Проверочные адреса:

```text
http://127.0.0.1:<порт>/health
http://127.0.0.1:<порт>/dashboard
http://127.0.0.1:<порт>/docs
```

## 20. Тестирование

Полный прогон:

```powershell
python -m pytest
```

Полезные срезы:

```powershell
python -m pytest tests/unit
python -m pytest tests/integration
python -m pytest tests/scenario
```

Практическое правило:

- менялись формулы или параметры - запускать unit и scenario;
- менялись routers - запускать integration;
- менялся dashboard/viewmodels - запускать UI/viewmodel tests;
- менялась поставка - проходить соответствующий smoke checklist из `deploy/`.

## 21. Сборка и поставка

Windows EXE:

```powershell
.\deploy\build-windows-exe.ps1 -Clean
```

Результат:

```text
dist/windows-exe/AhuSimulator/AhuSimulator.exe
```

Installer:

```powershell
.\deploy\build-windows-installer.ps1
```

Требуется Inno Setup 6.

Docker:

```powershell
docker compose -f deploy/docker-compose.yml up --build
```

Mobile backend:

```powershell
.\deploy\run-mobile-backend.ps1 -Build
```

Android shell требует реальный HTTPS backend. Локальный
`http://127.0.0.1:8000/dashboard` для установленного APK не подходит.

## 22. CI и версия

Подготовлены workflow:

- `.github/workflows/windows-pyinstaller.yml`;
- `.github/workflows/android-capacitor.yml`.

Единый источник версии - `pyproject.toml`, поле `[project].version`.
Скрипты сборки получают версию через `deploy/resolve-release-version.ps1`.

## 23. Правила доработки

1. Формулы и физические ограничения держать в `simulation`.
2. Сервисные операции держать в `services`.
3. Routers оставлять тонкими.
4. Dashboard не должен дублировать расчетную логику.
5. Новые runtime-файлы писать через resolver путей.
6. Системные scenario ID менять только вместе с тестами и документацией.
7. Пользовательские пресеты не должны менять `data/scenarios/presets.json`.
8. Статусы проводить через `StatusService`.
9. 3D/WebGL оставлять усиливающим, но необязательным слоем.
10. Любое изменение контракта export/comparison сопровождать тестами и
    обновлением документации.

## 24. Быстрая карта кода

| Задача | Смотреть здесь |
| --- | --- |
| Как собирается приложение | `src/app/bootstrap/app_factory.py` |
| Где создаются сервисы | `src/app/bootstrap/wiring.py` |
| Как грузятся настройки | `src/app/infrastructure/settings.py` |
| Где выбираются runtime-пути | `src/app/infrastructure/runtime_paths.py` |
| Где входные параметры модели | `src/app/simulation/parameters.py` |
| Где расчетные формулы | `src/app/simulation/equations.py` |
| Где выходные состояния | `src/app/simulation/state.py` |
| Где системные сценарии | `data/scenarios/presets.json` |
| Где API | `src/app/api/routers/` |
| Где dashboard | `src/app/ui/dashboard.py`, `layout.py`, `callbacks.py` |
| Где UI-проекции | `src/app/ui/viewmodels/` |
| Где export | `src/app/services/export_service.py` |
| Где comparison | `src/app/services/comparison_service.py` |
| Где archive | `src/app/services/scenario_archive_service.py` |
| Где readiness | `src/app/services/demo_readiness_service.py` |
| Где validation | `src/app/services/validation_service.py` |
| Где desktop launcher | `src/app/desktop_launcher.py`, `deploy/run-desktop.ps1` |

## 25. Известные технические ограничения

- Модель учебно-обобщенная и не заменяет паспортный расчет конкретной ПВУ.
- Динамика помещения упрощена.
- Нет реального BMS/SCADA/OPC контура.
- Нет авторизации, ролей и многопользовательского режима.
- Mobile shell зависит от доступного HTTPS backend.
- 3D/WebGL зависит от браузера, драйвера и GPU.
- Runtime-артефакты локальны и не синхронизируются с внешним хранилищем.

