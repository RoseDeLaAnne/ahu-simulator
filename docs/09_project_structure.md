# Целевая структура проекта

## Что уже создано

В этом пакете уже созданы каталоги верхнего уровня:

- `artifacts/`
- `docs/`
- `src/`
- `tests/`
- `data/`
- `config/`
- `deploy/`

## Рекомендуемая будущая структура репозитория

```text
pvu_diploma_project/
  README.md
  artifacts/
    demo-packages/
      README.md
      YYYY-MM-DD/
        pvu-demo-package-YYYYMMDD-HHMMSS.zip
        pvu-demo-package-YYYYMMDD-HHMMSS.manifest.json
    event-log/
      README.md
      YYYY-MM-DD/
        pvu-event-YYYYMMDD-HHMMSS.json
    exports/
      README.md
      YYYY-MM-DD/
        pvu-export-YYYYMMDD-HHMMSS.csv
        pvu-export-YYYYMMDD-HHMMSS.xlsx
        pvu-export-YYYYMMDD-HHMMSS.pdf
        pvu-export-YYYYMMDD-HHMMSS.manifest.json
    scenario-archive/
      README.md
      YYYY-MM-DD/
        pvu-run-YYYYMMDD-HHMMSS.json
    playwright/
      README.md
      manual/
        YYYY-MM-DD/
          dashboard/
            browser-diagnostics/
            core/
            defense-pack/
            demo-package/
            demo-readiness/
            export-pack/
            manual-check/
            p2-post-mvp/
            project-baseline/
            scenario-archive/
            validation-agreement/
            validation-basis/
            validation-pack/
  docs/
    01_stack.md
    02_functionality.md
    03_architecture.md
    04_roadmap.md
    05_execution_phases.md
    06_todo.md
    07_backlog.md
    08_risks_and_assumptions.md
    09_project_structure.md
    10_sources.md
    11_open_questions.md
    12_validation_matrix.md
    13_visualization_strategy.md
    14_defense_pack.md
    15_demo_readiness.md
    16_demo_package.md
    17_scenario_archive.md
    18_export_pack.md
    19_p0_baseline.md
    20_post_mvp.md
  src/
    app/
      main.py
      api/
        routers/
          archive.py
          events.py
          exports.py
          health.py
          project.py
          readiness.py
          scenarios.py
          simulation.py
          state.py
          validation.py
          visualization.py
      simulation/
        control.py
        parameters.py
        equations.py
        state.py
        scenarios.py
        alarms.py
      services/
        browser_capability_service.py
        demo_readiness_service.py
        event_log_service.py
        export_service.py
        project_baseline_service.py
        scenario_archive_service.py
        simulation_service.py
        trend_service.py
        validation_service.py
      ui/
        dashboard.py
        layout.py
        callbacks.py
        viewmodels/
          browser_diagnostics.py
          control_modes.py
          demo_readiness.py
          event_log.py
          export_pack.py
          defense_pack.py
          manual_check.py
          project_baseline.py
          scenario_archive.py
          validation_agreement.py
          validation_basis.py
          validation_matrix.py
          visualization.py
        scene/
          bindings.py
        assets/
          browser_diagnostics.js
          pvu_mnemonic.svg
          visualization.js
      infrastructure/
        settings.py
        logging.py
        exporters.py
  tests/
    unit/
    integration/
    scenario/
  data/
    synthetic/
    scenarios/
    validation/
      reference_points.json
      reference_basis.json
      validation_agreement.json
    visualization/
      browser_capability_profile.json
      scene3d.json
    exports/
  config/
    defaults.yaml
    p0_baseline.yaml
  deploy/
    Dockerfile
    docker-compose.yml
    build-demo-package.ps1
    run-local.ps1
```

## Назначение каталогов

- `src/app/api` — внешние контракты и endpoints.
- `src/app/simulation` — предметное ядро и формулы.
- `src/app/services` — orchestration и бизнес-логика.
- `src/app/ui` — интерфейс, layout и callbacks.
- `src/app/ui/viewmodels` — преобразование расчетного результата в визуальные сигналы для 2D/3D.
- `docs/14_defense_pack.md` — конспект demo-flow и материалов для защиты ВКР.
- `docs/15_demo_readiness.md` — конспект преддемонстрационного preflight-check и офлайн-запуска.
- `docs/16_demo_package.md` — конспект состава offline/demo bundle и правил его сборки.
- `docs/17_scenario_archive.md` — конспект локального архива прогонов и JSON-снимков сценариев.
- `docs/18_export_pack.md` — конспект локального экспорта текущего прогона в `CSV/XLSX/PDF`.
- `docs/19_p0_baseline.md` — текстовая фиксация P0 baseline, обязательных входов/выходов, сценариев защиты и validation format.
- `docs/20_post_mvp.md` — фиксация post-MVP блока: `Event Log`, `Control Modes`, Docker Compose и решение по OpenModelica.
- `src/app/services/demo_readiness_service.py` — сборка snapshot преддемонстрационной готовности, runtime-версий, checklist проекта и demo bundle.
- `src/app/services/browser_capability_service.py` — загрузка и сравнение verified browser/WebGL profile с live capability snapshot клиента.
- `src/app/services/event_log_service.py` — журнал значимых расчётных переходов, смены режима управления и артефактных действий в `artifacts/event-log`.
- `src/app/services/export_service.py` — сборка локальных `CSV/XLSX/PDF` export-наборов и manifest в `artifacts/exports`.
- `src/app/services/project_baseline_service.py` — сборка машиночитаемого P0 baseline и контроль согласованности параметров, выходов и сценариев.
- `src/app/services/scenario_archive_service.py` — локальное сохранение и чтение JSON-снимков прогонов в `artifacts/scenario-archive`.
- `src/app/api/routers/project.py` — API-контракт `GET /project/baseline`.
- `src/app/api/routers/readiness.py` — API-контракты `GET /readiness/demo`, `GET /readiness/package` и `POST /readiness/package/build`.
- `src/app/api/routers/visualization.py` — API-контракты `GET /visualization/state` и `GET /visualization/browser-profile`.
- `src/app/api/routers/events.py` — API-контракт `GET /events/log`.
- `src/app/api/routers/exports.py` — API-контракты `GET /exports/result` и `POST /exports/result/build`.
- `src/app/api/routers/archive.py` — API-контракты `GET /archive/scenarios` и `POST /archive/scenarios`.
- `src/app/simulation/control.py` — построение control diagnostics для `auto/manual` поверх текущего operating point.
- `src/app/ui/viewmodels/project_baseline.py` — форматирование dashboard-блока `P0 Baseline`.
- `src/app/ui/viewmodels/demo_readiness.py` — форматирование launch checklist, runtime snapshot, browser brief и demo bundle для dashboard.
- `src/app/ui/viewmodels/browser_diagnostics.py` — форматирование live browser/WebGL snapshot, verified profile и browser brief для dashboard.
- `src/app/ui/viewmodels/control_modes.py` — форматирование live-диагностики `auto/manual` для dashboard.
- `src/app/ui/viewmodels/event_log.py` — форматирование журналируемых событий для dashboard.
- `src/app/ui/viewmodels/export_pack.py` — форматирование списка локальных export-наборов для dashboard.
- `src/app/ui/viewmodels/scenario_archive.py` — форматирование локального архива прогонов для dashboard.
- `src/app/services/validation_service.py` — сборка validation-matrix, validation agreement, реестра методических оснований и ручной инженерной сверки.
- `src/app/api/routers/validation.py` — API-контракты `GET /validation/matrix`, `GET /validation/agreement`, `GET /validation/basis` и `POST /validation/manual-check`.
- `src/app/ui/viewmodels/manual_check.py` — форматирование живой сверки «модель -> ручной расчёт» для dashboard.
- `src/app/ui/viewmodels/validation_agreement.py` — форматирование agreed control points и step tolerances для dashboard.
- `src/app/ui/viewmodels/validation_basis.py` — форматирование внешних методических оснований и трассировки шагов/контрольных точек для dashboard.
- `src/app/ui/viewmodels/validation_matrix.py` — форматирование validation-matrix для dashboard.
- `src/app/ui/scene` — bindings и адаптеры визуальных сцен.
- `src/app/ui/assets` — SVG, CSS и JS-ассеты для 2D-мнемосхемы.
- `artifacts/demo-packages` — zip/manifest сборки offline/demo bundle.
- `artifacts/event-log` — локальные JSON-записи `Event Log`.
- `artifacts/exports` — локальные CSV/XLSX/PDF-выгрузки по текущим прогонам.
- `artifacts/scenario-archive` — локальные JSON-снимки сохранённых прогонов и сценариев.
- `artifacts/playwright` — ручные и будущие CI-артефакты визуальной проверки интерфейса.
- `src/app/infrastructure` — конфигурация, логирование, экспорт.
- `tests/unit` — проверка отдельных расчетных функций.
- `tests/integration` — API и соединение слоев.
- `tests/scenario` — воспроизведение типовых режимов.
- `data/synthetic` — учебные наборы данных.
- `data/scenarios` — пресеты режимов.
- `data/validation` — контрольные точки, validation agreement, методические основания и вспомогательные таблицы валидации.
- `data/visualization` — scene-конфигурации, verified browser/WebGL profile и визуальные metadata для будущего 3D-слоя.
- `config/p0_baseline.yaml` — машиночитаемая фиксация рабочего scope первой версии.
- `deploy` — запуск, локальные entrypoint'ы и упаковка.

## Первые файлы, которые нужно будет создать при начале разработки

- `src/app/main.py`
- `src/app/simulation/parameters.py`
- `src/app/simulation/equations.py`
- `src/app/simulation/state.py`
- `src/app/api/routers/simulation.py`
- `src/app/ui/dashboard.py`
- `tests/unit/test_equations.py`
- `tests/integration/test_api.py`

## Принципы структуры

- Не смешивать формулы модели и UI-код.
- Не хранить сценарии внутри python-файлов, если их можно вынести в `data/scenarios`.
- Не завязывать Dash напрямую на детали низкоуровневых расчетов.
- Не допускать единственного «толстого файла», где живет весь проект.
