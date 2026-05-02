# Run Comparison

Дата актуализации: 2026-05-02.

## Что это

`Run Comparison` — режим сравнения двух прогонов `до/после`, который использует:

- текущий `active run` из live-сессии dashboard;
- любой сохранённый снимок из `Scenario Archive`;
- именованные runtime-снимки `До` и `После`, которые пользователь фиксирует прямо из dashboard/API.

Результат сравнения строится как единый контракт с:

- проверкой совместимости пары;
- дельтами по KPI и диагностическим метрикам;
- трендовыми дельтами по одинаковой временной сетке;
- interpretation summary: improved/worsened/unchanged/top deltas;
- export-артефактами `CSV/PDF/manifest` по контракту `run-comparison.v2`.

## Где доступно

- dashboard: секция `#run-comparison`;
- API snapshot: `GET /comparison/runs`;
- API capture before: `POST /comparison/runs/before`;
- API capture after: `POST /comparison/runs/after`;
- API build: `POST /comparison/runs/build`;
- API export: `POST /comparison/runs/export`.

## Правила совместимости

Сравнение разрешается только для пар, у которых совпадают:

- `step_minutes`;
- `horizon_minutes`;
- количество точек тренда;
- временная сетка `minute`;
- набор итоговых KPI/diagnostic fields в `SimulationState`.

Если хотя бы одно из правил не выполняется, UI показывает причину
несовместимости и блокирует export, а API export возвращает `409 Conflict`.

## Что входит в export сравнения

- `pvu-comparison-YYYYMMDD-HHMMSS.csv`
  - schema/version metadata `run-comparison.v2`;
  - метаданные пары `before/after`;
  - блок совместимости;
  - interpretation summary;
  - таблица KPI-дельт;
  - таблица трендовых дельт;
  - статусные подписи `Норма`, `Риск`, `Авария`;
- `pvu-comparison-YYYYMMDD-HHMMSS.pdf`
  - краткий переносимый отчёт по сравнению `до/после`;
- `pvu-comparison-YYYYMMDD-HHMMSS.manifest.json`
  - DTO сравнения, schema/version metadata и пути до артефактов.

Все файлы сохраняются в `artifacts/exports/<дата>/`.

## Зачем добавлено

- закрывает аналитический режим `до/после` из `P2.1`;
- даёт повторяемый способ обсуждать эффект изменений параметров без ручного пересчёта;
- позволяет быстро вынести пару прогонов в читаемые артефакты для защиты и разбора.
