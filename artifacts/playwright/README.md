# Playwright Artifacts

Скриншоты и другие визуальные артефакты Playwright не хранятся в корне проекта.

## Структура

```text
artifacts/playwright/
  README.md
  manual/
    YYYY-MM-DD/
      dashboard/
        core/
          01-baseline-layout.png
          02-default-live-state.png
          03-dirty-filter-alarm.png
        browser-diagnostics/
          01-webgl-profile.png
          02-demo-readiness-browser-brief.png
        defense-pack/
          01-defense-pack-expanded-full.png
          02-defense-pack-panel.png
          03-dirty-filter-defense-pack.png
        demo-package/
          01-demo-package-panel-before-build.png
          02-demo-package-panel-after-build.png
          03-dirty-filter-demo-package-full.png
        demo-readiness/
          01-demo-readiness-fullscreen-ready.png
          02-demo-readiness-compact-warning.png
          03-dirty-filter-demo-readiness.png
        p2-post-mvp/
          01-control-modes-manual.png
          02-event-log-manual-transition.png
          03-dashboard-post-mvp-full.png
        export-pack/
          01-export-pack-empty-panel.png
          02-export-pack-after-build.png
          03-export-pack-dirty-filter.png
        manual-check/
          01-default-manual-check-panel.png
          02-dirty-filter-manual-check-full.png
          03-custom-airflow-manual-check-full.png
        project-baseline/
          01-p0-baseline-panel.png
          02-p0-baseline-expanded.png
        scenario-archive/
          01-scenario-archive-empty-panel.png
          02-scenario-archive-after-save.png
          03-scenario-archive-dirty-filter-save.png
        validation-basis/
          01-validation-basis-expanded-full.png
          02-validation-basis-panel.png
          03-dirty-filter-validation-basis-full.png
        validation-agreement/
          01-validation-agreement-panel.png
          02-validation-agreement-expanded.png
        validation-pack/
          01-validation-pack-panel.png
          02-dirty-filter-validation-pack-full.png
  ci/
    ...
```

## Правила

- `manual/` используется для ручных прогонов через Playwright MCP.
- `ci/` зарезервирован под будущие автоматические e2e-прогоны.
- Внутри папки с датой скриншоты группируются по функциональным блокам интерфейса.
- В имени файла сначала идёт номер шага внутри блока, затем короткое описание сценария.
- Папка с датой отражает день проверки, чтобы прогресс по UI можно было привязать к документам и фазам проекта.
