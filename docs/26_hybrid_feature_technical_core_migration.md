# Hybrid Feature + Technical Core Migration Blueprint

Дата: 2026-04-19
Статус: Draft + Iteration 1/2 implemented

## 1) Короткий диагноз текущей структуры

### Что уже хорошо
- Проект уже на `src`-layout и имеет понятные базовые слои: `api`, `services`, `simulation`, `ui`, `infrastructure`.
- Точки входа не размазаны:
  - FastAPI entrypoint через `src/app/main.py`.
  - Dash mount через `src/app/ui/dashboard.py`.
  - Desktop launcher через `src/app/desktop_launcher.py`.
- Runtime artifacts уже частично нормализованы через `RuntimePathResolver` (`artifacts/exports`, `artifacts/event-log`, `artifacts/scenario-archive`, `artifacts/demo-packages`).

### Где перегруз и смешение ответственности
- `src/app/main.py` совмещал factory, DI/wiring, router include, static mounts, dashboard mount.
- `src/app/services` фактически содержит feature-orchestration для разных продуктовых областей, но лежит в одном пакете.
- `src/app/ui/scene` смешивает runtime-код (`bindings.py`, каталоги моделей) и tooling-скрипты генерации (`build_blender_pvu.py`, `generate_glb.py`, `generate_room_glbs.py`).
- В корне репозитория были накоплены временные файлы (PNG/log/cmd/exe), из-за чего страдала навигация и воспроизводимость запусков.

### Что относится к runtime, а что к artifacts/tooling/reference
- Runtime:
  - `src/app/**` (кроме генераторов asset-ов),
  - `config/**`, `data/**`,
  - `models/**`, `images-of-models/**`,
  - `deploy/run-*.ps1`, `deploy/docker-compose.yml`.
- Artifacts (generated output/logs/screenshots):
  - `artifacts/**`,
  - root PNG/log-файлы (должны быть перенесены/классифицированы).
- Tooling (не runtime imports):
  - build/package/migration/scripts,
  - генерация GLB/Blender-ассетов,
  - packaging helpers.
- Reference/source assets:
  - `3d-references/**`, `images-for-3d/**`, `references/**`.

## 2) Целевая структура репозитория (proposed)

### 2.1 Root-level (верхний/средний уровень)

```text
ahu-simulator/
  README.md
  AGENTS.md
  pyproject.toml
  requirements.txt

  src/
    app/
      main.py
      bootstrap/
      domain/
      features/
      ui/
      infrastructure/
      shared/

  tests/
    conftest.py
    unit/
    integration/
    scenario/

  config/
    defaults.yaml
    defaults.mobile.yaml
    p0_baseline.yaml
    README.md

  data/
    scenarios/
    validation/
    visualization/
      assets/
    exports/
    synthetic/
    README.md

  models/                    # runtime 3D models served by FastAPI static mount
  images-of-models/          # runtime preview images served by FastAPI static mount

  assets-source/             # source/reference inputs for generation (target)
    3d-references/
    images-for-3d/
    references/

  artifacts/
    demo-packages/
    event-log/
    exports/
    scenario-archive/
    playwright/
      manual/
      ci/
    screenshots/
      manual/
      playwright/
      mobile/
    logs/
      local/
      mobile/
      tunnel/

  tooling/
    migration/
    scene/
    packaging/

  deploy/
    run-local.ps1
    run-desktop.ps1
    run-mobile-backend.ps1
    build-*.ps1
    docker-compose.yml
    mobile-backend/
    installer/

  docs/
    01_*.md ...
    26_hybrid_feature_technical_core_migration.md

  mobile/
  build/
  dist/
```

### 2.2 Target tree для `src/app`

```text
src/app/
  main.py                          # compatibility shim entrypoint

  bootstrap/
    __init__.py
    app_factory.py                 # create_app + security middleware
    wiring.py                      # services wiring, router include, dashboard/static mount
    dependencies.py                # request -> app.state providers

  domain/
    simulation/                    # equations, control invariants, alarms
    scenarios/                     # scenario model + validation invariants
    status/                        # status thresholds/policies

  features/
    simulation/
      api.py
      service.py
      schemas.py
    visualization/
      api.py
      service.py
      viewmodel.py
      runtime/
    validation/
      api.py
      service.py
      viewmodel.py
    export/
      api.py
      service.py
      schemas.py
    archive/
      api.py
      service.py
      schemas.py
    readiness/
      api.py
      service.py
      schemas.py
    comparison/
      api.py
      service.py
      schemas.py
    baseline/
      api.py
      service.py
      schemas.py
    event_log/
      api.py
      service.py
      schemas.py

  ui/
    dashboard/
      app.py
      layout.py
      callbacks.py
      assets/
    desktop/
    mobile/
    scene/                         # runtime-only scene bindings/catalogs

  infrastructure/
    config/
    logging/
    runtime/
    persistence/
    external/

  shared/
    schemas/
    utils/
    constants.py
```

### 2.3 Target tree для root artifacts/build/reference/logs

```text
artifacts/
  screenshots/
    manual/
      YYYY-MM-DD/
    playwright/
      YYYY-MM-DD/
    mobile/
      YYYY-MM-DD/
  logs/
    local/
      YYYY-MM-DD/
    mobile/
      YYYY-MM-DD/
    tunnel/
      YYYY-MM-DD/
  playwright/
    manual/
    ci/
  demo-packages/
  event-log/
  exports/
  scenario-archive/

assets-source/
  3d-references/
  images-for-3d/
  references/

build/
  pyinstaller/

dist/
  windows-exe/
```

## 3) Таблица миграции (old -> new)

| Old path | New path | Причина | Риск |
|---|---|---|---|
| `src/app/main.py` (factory/wiring logic) | `src/app/bootstrap/app_factory.py` + `src/app/bootstrap/wiring.py` | Отделить composition-root от entrypoint, упростить поддержку | Low (shim оставлен в `main.py`) |
| `src/app/api/dependencies.py` | `src/app/bootstrap/dependencies.py` (+ shim в старом пути) | Единая точка DI для API/UI runtime | Low |
| `src/app/services/simulation_service.py` | `src/app/features/simulation/service.py` | Feature ownership | Medium (много импортов в tests/ui/api) |
| `src/app/services/validation_service.py` | `src/app/features/validation/service.py` | Feature ownership + локализация схем | Medium |
| `src/app/services/export_service.py` | `src/app/features/export/service.py` | Изоляция изменений экспорта | Medium |
| `src/app/services/scenario_archive_service.py` | `src/app/features/archive/service.py` | Feature ownership | Medium |
| `src/app/services/demo_readiness_service.py` | `src/app/features/readiness/service.py` | Feature ownership | Medium |
| `src/app/services/comparison_service.py` | `src/app/features/comparison/service.py` | Feature ownership | Medium |
| `src/app/services/project_baseline_service.py` | `src/app/features/baseline/service.py` | Feature ownership | Medium |
| `src/app/services/event_log_service.py` | `src/app/features/event_log/service.py` | Feature ownership | Medium |
| `src/app/services/browser_capability_service.py` | `src/app/features/visualization/service.py` (или `infrastructure/external` часть) | Свести browser profile к visualization domain | Medium |
| `src/app/simulation/*.py` | `src/app/domain/simulation/*` (+ часть в `domain/status`, `domain/scenarios`) | Чистое доменное ядро без FastAPI/Dash | Medium |
| `src/app/ui/dashboard.py` | `src/app/ui/dashboard/app.py` | UI composition package | Low |
| `src/app/ui/layout.py` | `src/app/ui/dashboard/layout.py` | UI composition package | Medium (много импортов) |
| `src/app/ui/callbacks.py` | `src/app/ui/dashboard/callbacks.py` | UI composition package | Medium |
| `src/app/ui/scene/build_blender_pvu.py` | `tooling/scene/build_blender_pvu.py` | Это tooling, не runtime | Low (обновить deploy script path) |
| `src/app/ui/scene/generate_glb.py` | `tooling/scene/generate_glb.py` | Это tooling, не runtime | Low |
| `src/app/ui/scene/generate_room_glbs.py` | `tooling/scene/generate_room_glbs.py` | Это tooling, не runtime | Low |
| root `*.png` (временные) | `artifacts/screenshots/<channel>/<date>/` | Очистить root, улучшить навигацию | Low |
| root `*.log`, `*.err.log`, `*.out.log` | `artifacts/logs/<channel>/<date>/` | Очистить root, не терять диагностику | Low |
| root `*.cmd` | `tooling/commands/windows/` | Убрать launcher-шум из root, сохранить click-to-run скрипты | Low |
| root `*.exe` (tooling binaries) | `tooling/bin/<tool>/` | Изолировать локальные tool binaries от runtime/source | Low |
| `3d-references`, `images-for-3d`, `references` | `assets-source/...` (или оставить + alias phase) | Отделить source/reference от runtime | Medium (scripts/docs path refs) |

Примечание: переносы из `services` и `simulation` делать поэтапно с import-shims, а не массовым rename.

## 4) Правила декомпозиции по слоям

### `domain` (разрешено)
- Чистые dataclass/Pydantic-модели предметной области.
- Формулы, инварианты, проверки диапазонов, статусные правила.
- Pure functions и deterministic business logic.

### `domain` (запрещено)
- FastAPI/Dash/uvicorn imports.
- Чтение/запись файлов, env vars, runtime path resolution.
- Сетевые клиенты и адаптеры инфраструктуры.

### `features` (разрешено)
- Оркестрация use-flow конкретной продуктовой области.
- Feature-level API handlers (через `api.py`) и схемы (`schemas.py`).
- Сборка view-model для UI при необходимости.

### `ui` (запрещено)
- Реализация формул и предметных правил в callbacks.
- Прямой filesystem orchestration и запись artifact-ов.
- Cross-feature бизнес-логика вне feature service.

### `infrastructure` (должно лежать)
- settings, logging, runtime paths, persistence adapters, external clients.
- Всё, что зависит от окружения, ОС, файловой системы, сети.

### `tooling` (выносится)
- Blender/GLB generators, asset prep scripts, migration scripts, packaging helpers.
- Любые скрипты, которые не импортируются runtime-кодом приложения.

## 5) Phased migration plan (без big-bang)

## Phase 1: root cleanup and artifacts segregation

Действия:
- Добавить `artifacts/screenshots/*` и `artifacts/logs/*` как целевые каталоги.
- Добавить dry-run migration script для root PNG/log/cmd/exe classification.
- Перенести root временные файлы пакетно по каналам и датам (после dry-run).

Затрагиваемые пути:
- `artifacts/screenshots/**`, `artifacts/logs/**`, `tooling/commands/windows/**`, `tooling/bin/**`
- `tooling/migration/**`
- root `*.png`, `*.log`, `*.err.log`, `*.out.log`, `*.cmd`, `*.exe`

Риски:
- Потеря привычных локальных путей для ручных проверок.

Как проверить:
- Команда dry-run показывает только план перемещения.
- После apply: root очищен от временных PNG/log/cmd/exe.
- `pytest tests/unit/test_demo_readiness_service.py` (проверить, что readiness snapshot не сломан).

## Phase 2: ui/runtime vs tooling split

Действия:
- Вынести `build_blender_pvu.py`, `generate_glb.py`, `generate_room_glbs.py` в `tooling/scene`.
- Оставить shim modules в старом пути `src/app/ui/scene/*` с предупреждением/deprecation.
- Обновить `deploy/build-3d-blender.ps1` на новый path.

Затрагиваемые пути:
- `src/app/ui/scene/*.py`
- `tooling/scene/*.py`
- `deploy/build-3d-blender.ps1`

Риски:
- Слом ручных команд генерации при устаревшем пути.

Как проверить:
- Запуск `deploy/build-3d-blender.ps1`.
- `pytest tests/unit/test_scene_bindings_models.py tests/unit/test_scene_model_catalog.py`.

## Phase 3: services decomposition by feature

Действия:
- Создать `src/app/features/<feature>/service.py`.
- Переносить по 1 feature за итерацию: сначала `event_log`, `archive`, `export`, затем остальные.
- В `src/app/services/*` оставить import-shim и пометку deprecation.

Затрагиваемые пути:
- `src/app/services/*.py`
- `src/app/features/**`
- частично `src/app/ui/**`, `src/app/api/**`, `tests/**` (только import rewiring).

Риски:
- Массовый дрейф импортов в тестах и callbacks.

Как проверить:
- После каждого feature: целевые unit-тесты feature + `tests/integration/test_api.py`.

## Phase 4: domain extraction

Действия:
- Выделить `domain/simulation`, `domain/scenarios`, `domain/status`.
- Переносить pure logic из `src/app/simulation` модулями, сохраняя shim-и.

Затрагиваемые пути:
- `src/app/simulation/*.py`
- `src/app/domain/**`

Риски:
- Циклические зависимости между domain и feature/infrastructure.

Как проверить:
- `pytest tests/unit/test_equations.py tests/unit/test_control_diagnostics.py tests/unit/test_status_policy.py`
- Быстрый smoke `/simulation/preview`.

## Phase 5: api and tests realignment

Действия:
- Перенести API роуты в feature-пакеты (`features/*/api.py`) по одному.
- `src/app/api/routers/*` превратить в shim-реэкспорт.
- Локализовать feature fixtures/conftest.

Затрагиваемые пути:
- `src/app/api/routers/*.py`
- `src/app/features/*/api.py`
- `tests/**`

Риски:
- Регрессия импортов в integration tests.

Как проверить:
- `pytest tests/integration`
- `pytest tests/scenario`
- Smoke desktop launcher и dashboard route.

## 6) Тестовая стратегия после миграции

После каждой фазы запускать:

- Phase 1:
  - `python -m pytest tests/unit/test_demo_readiness_service.py tests/unit/test_runtime_paths.py`
- Phase 2:
  - `python -m pytest tests/unit/test_scene_bindings_models.py tests/unit/test_scene_model_catalog.py tests/unit/test_room_catalog.py`
- Phase 3:
  - `python -m pytest tests/unit`
  - минимум по затронутому feature + `tests/integration/test_api.py`
- Phase 4:
  - `python -m pytest tests/unit/test_equations.py tests/unit/test_status_policy.py tests/unit/test_simulation_session_service.py`
- Phase 5:
  - `python -m pytest tests/integration tests/scenario`

Дополнительные smoke/integration checks:
- FastAPI app creation: `from app.main import create_app; create_app()`.
- Dashboard mount: GET `/dashboard`.
- Desktop launcher import-path check: `python -m app.desktop_launcher` (без фактического long-run в CI).
- Mobile backend profile checks: security middleware tests из `tests/integration/test_api.py`.

Локализация fixtures/conftest:
- Оставить `tests/conftest.py` только для `src` path bootstrap.
- Добавлять feature-local fixtures:
  - `tests/unit/features/simulation/conftest.py`
  - `tests/unit/features/export/conftest.py`
  - `tests/integration/features/<feature>/conftest.py`
- Общие тестовые фабрики вынести в `tests/helpers/` вместо глобального conftest-накопления.

## 7) Practical naming rules

Использовать:
- `api.py`: feature-level FastAPI router и endpoint handlers.
- `service.py`: orchestration/use-flow для feature.
- `models.py`: внутренние domain или feature модели (не transport).
- `schemas.py`: API transport schemas (request/response).
- `viewmodel.py`: подготовка UI-ready структуры без Dash callback logic.
- `repository.py`: только если есть устойчивое чтение/запись агрегатов в storage.
- `adapters.py`: интеграция со внешним API/форматом/системой.
- `wiring.py`: composition-root, DI assembly, service graph.

Правило простоты:
- Если файл < ~200 строк и нет нескольких независимых ролей, не дробить его искусственно.

## 8) Итоговая рекомендация (минимальный first step)

Максимальный выигрыш при минимальном риске дают 2 итерации:

Iteration A (выполнена в этом change-set):
- вынести composition-root в `bootstrap`;
- оставить совместимость через shim-и (`app.main`, `app.api.dependencies`);
- зафиксировать миграционный blueprint.

Iteration B (выполнена):
- вынести tooling-скрипты генерации 3D в `tooling/scene`;
- добавить shim в старом `src/app/ui/scene`;
- завершить root cleanup с переносом `.png/.cmd/.exe/.log` в `artifacts` и `tooling`.

Что делать сейчас:
- запускать Phase 3 feature-by-feature перенос (`event_log` или `archive`) с import-shim и тестами после каждого шага.

Что отложить:
- массовый перенос всех `services` и `simulation` до стабильной схемы shim и тестового контура.

## 9) Выполнено в рамках старта миграции (2026-04-19)

- Добавлен `bootstrap` technical core:
  - `src/app/bootstrap/app_factory.py`
  - `src/app/bootstrap/wiring.py`
  - `src/app/bootstrap/dependencies.py`
- `src/app/main.py` переведен в compatibility entrypoint (re-export `create_app`).
- `src/app/api/dependencies.py` переведен в compatibility shim через `bootstrap.dependencies`.
- Добавлен данный migration blueprint документ.
- Выполнен перенос scene tooling-скриптов в `tooling/scene`:
  - `tooling/scene/build_blender_pvu.py`
  - `tooling/scene/generate_glb.py`
  - `tooling/scene/generate_room_glbs.py`
- Добавлены compatibility shims в старых путях:
  - `src/app/ui/scene/build_blender_pvu.py`
  - `src/app/ui/scene/generate_glb.py`
  - `src/app/ui/scene/generate_room_glbs.py`
- Обновлены ссылки на генератор:
  - `deploy/build-3d-blender.ps1`
  - `data/visualization/scene3d.json`
- Расширен и применен root migration script (`tooling/migration/segregate_root_artifacts.ps1`):
  - перемещено 173 файла из root (`.png/.cmd/.exe/.log`) в `artifacts/**` и `tooling/**`.
- Windows launcher-скрипты вынесены из root в `tooling/commands/windows`,
  а `start.bat` и документация обновлены на новые пути.
