Ты работаешь в репозитории Python-проекта с FastAPI, Dash UI, desktop launcher, mobile shell и набором data/assets/tooling. Твоя задача: спроектировать и начать безопасную миграцию структуры проекта в архитектурный вариант `Hybrid Feature + Technical Core`.

Контекст:
- Проект уже использует `src`-layout.
- В кодовой базе есть слои `api`, `services`, `simulation`, `ui`, `infrastructure`.
- В репозитории смешаны production-код, runtime-артефакты, build-артефакты, временные скриншоты, 3D reference-assets и tooling.
- Нужна структура, которая улучшит навигацию, ownership, масштабирование и тестируемость, но не создаст лишнюю enterprise-сложность.

Архитектурная цель:
- Сохранить понятный технический каркас (`bootstrap`, `infrastructure`, `shared`, `ui`).
- Вынести предметное ядро в `domain`.
- Разложить пользовательские и API-возможности по feature-пакетам.
- Отделить runtime UI от tooling/generation scripts и reference-assets.
- Очистить корень репозитория от временных и runtime-файлов.

Целевой принцип декомпозиции:
1. `domain`:
   - только предметная логика и инварианты;
   - без FastAPI, Dash, CLI, mobile-specific кода;
   - без файловой оркестрации, кроме чистых доменных моделей/правил.
2. `features`:
   - каждая feature содержит свой orchestration/service/api/viewmodel слой по необходимости;
   - feature — это отдельная продуктовая область, например:
     - simulation
     - visualization
     - validation
     - export
     - archive
     - readiness
     - comparison
     - baseline
     - event_log
3. `ui`:
   - только presentation/runtime UI composition;
   - dashboard/layout/callback wiring;
   - desktop/mobile presentation-specific glue;
   - без доменной логики внутри callbacks.
4. `infrastructure`:
   - settings, runtime paths, logging, persistence, filesystem access, external adapters;
   - всё, что зависит от окружения, файловой системы, сетевых клиентов, runtime wiring.
5. `shared`:
   - общие схемы, утилиты, constants, которые реально используются несколькими feature;
   - не превращать `shared` в свалку.
6. `tooling`:
   - генераторы GLB, Blender scripts, asset-preparation scripts, migration scripts, packaging helpers;
   - всё, что не нужно для runtime-импортов приложения.

Требования к результату:
- Не делай “большой взрывной” рефакторинг.
- Сначала спроектируй целевую структуру и mapping `старый путь -> новый путь`.
- Затем предложи поэтапный migration plan с минимальным риском поломки импортов.
- Сохрани работоспособность:
  - FastAPI app entrypoint
  - Dash dashboard
  - desktop launcher
  - mobile-related backend flow
  - tests
- Если можно избежать массового переименования на первом этапе, избегай.
- При переносах оставляй совместимые import-shims там, где это уменьшает риск.
- Не удаляй артефакты или папки, если они могут использоваться рантаймом, пока это не доказано.
- Отделяй runtime assets от source/reference assets.
- Не создавай слишком глубокую вложенность без причины.
- Не вводи абстракции, которые не дают практической пользы проекту.

Ожидаемые deliverables:
1. Краткий аудит текущей структуры:
   - какие части уже хорошие;
   - какие папки перегружены;
   - где смешаны responsibilities;
   - какие элементы должны быть runtime, а какие — artifacts/tooling/reference.
2. Целевая структура репозитория:
   - полный proposed tree верхнего и среднего уровня;
   - отдельно показать `src/app` target tree;
   - отдельно показать target tree для root-level artifacts/build/reference/logs.
3. Таблица миграции:
   - `old path -> new path`
   - причина переноса
   - риск переноса
4. Правила декомпозиции по слоям:
   - что разрешено в `domain`
   - что разрешено в `features`
   - что запрещено в `ui`
   - что должно лежать в `infrastructure`
   - что выносится в `tooling`
5. План миграции по фазам:
   - Phase 1: root cleanup and artifacts segregation
   - Phase 2: ui/runtime vs tooling split
   - Phase 3: services decomposition by feature
   - Phase 4: domain extraction
   - Phase 5: api and tests realignment
   - для каждой фазы:
     - действия
     - затрагиваемые пути
     - риски
     - как проверить результат
6. Тестовая стратегия после миграции:
   - какие тесты запускать после каждой фазы;
   - где нужны дополнительные smoke/integration checks;
   - какие conftest/fixtures стоит локализовать по feature.
7. Practical naming rules:
   - когда использовать `api.py`, `service.py`, `models.py`, `schemas.py`, `viewmodel.py`, `repository.py`, `adapters.py`, `wiring.py`.
8. Итоговая рекомендация:
   - какой минимальный first step даст наибольший выигрыш;
   - что делать сейчас;
   - что отложить.

Предпочтительная целевая структура `src/app`:
- Это не догма, но используй её как базовый ориентир и адаптируй под фактический код проекта.

src/app/
  main.py
  bootstrap/
    app_factory.py
    dependencies.py
    wiring.py
  domain/
    simulation/
    scenarios/
    status/
  features/
    simulation/
      api.py
      service.py
      schemas.py
    visualization/
      api.py
      service.py
      viewmodels/
      runtime/
    validation/
      api.py
      service.py
      viewmodels/
    export/
      api.py
      service.py
    archive/
      api.py
      service.py
    readiness/
      api.py
      service.py
    comparison/
      api.py
      service.py
    baseline/
      api.py
      service.py
    event_log/
      api.py
      service.py
  ui/
    dashboard/
      app.py
      layout.py
      callbacks.py
      assets/
    desktop/
    mobile/
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
  tooling/
    scene/
    packaging/

Дополнительные требования по repo-root:
- Все временные PNG/screenshots/logs из корня должны быть классифицированы:
  - `artifacts/screenshots/...`
  - `artifacts/logs/...`
  - `artifacts/playwright/...`
- Build outputs должны быть отделены от исходников и не мешать навигации.
- Reference-материалы и source-assets для 3D должны быть отделены от runtime assets.
- Не смешивай:
  - `src/app/ui/assets` runtime assets
  - `data/...` runtime data
  - `assets-source/...` reference/input materials for generation
  - `artifacts/...` generated outputs and logs

Ограничения на стиль решения:
- Предлагай pragmatic architecture, а не textbook-clean-architecture ради самой архитектуры.
- Избегай лишних слоёв типа `use_cases`, `interactors`, `commands`, если они не дают пользы.
- Если текущий модуль уже хорошо лежит, не переноси его без причины.
- Предпочитай небольшое количество сильных пакетов вместо большого количества “тонких” папок.
- Оцени каждое перемещение с точки зрения:
  - discoverability
  - change isolation
  - testability
  - import stability
  - onboarding clarity

Формат ответа:
- Сначала дай короткий диагноз текущей структуры.
- Затем покажи рекомендованную структуру.
- Затем таблицу миграции.
- Затем phased migration plan.
- Затем конкретный “recommended first execution slice” на 1-2 итерации.
- Если видишь, что целевой tree стоит скорректировать под фактический код репозитория, скорректируй и объясни почему.
- Пиши конкретно, не абстрактно.
- Не ограничивайся общими советами; привязывай выводы к реальным каталогам и файлам проекта.
