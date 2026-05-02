# Export Pack

Дата актуализации: 2026-05-02.

## Что это

`Export Pack` — локальный блок экспорта текущего прогона в сценарный отчёт с единым контрактом данных:

- `CSV` для табличной обработки и передачи в сторонние инструменты;
- `PDF` для краткого переносимого отчёта по активному режиму.

Артефакты сохраняются в `artifacts/exports/<дата>/`.

## Где доступно

- dashboard: секция `#export-pack`;
- API snapshot: `GET /exports/result`;
- API preview: `POST /exports/result/preview`;
- API build: `POST /exports/result/build`.
- API download: `GET /exports/result/download/{artifact_id}`.

## Что входит в export-набор

- `pvu-report-YYYYMMDD-HHMMSS.csv`
  - schema/version metadata `scenario-report.v2`;
  - стабильные секции `metadata`, `findings`, `parameters`, `state`, `status_legend`, `status_events`, `trend`;
  - формируется из того же `ScenarioReport`, что и PDF, и парсится стандартным Python `csv`;
- `pvu-report-YYYYMMDD-HHMMSS.pdf`
  - инженерный ReportLab-отчёт по активному прогону с титульной частью, KPI/status summary, таблицами параметров/состояния, легендой статусов, статусными событиями и trend chart;
- `pvu-report-YYYYMMDD-HHMMSS.manifest.json`
  - служебный снимок отчёта с DTO, путями артефактов, schema version, checksum/file-size metadata для dashboard и API.

Статусы во всех пользовательских секциях выводятся как `Норма`, `Риск`,
`Авария`; технические значения `normal`, `warning`, `alarm` остаются только в
API/enum-контрактах.

## Зачем добавлено

- закрывает открытый пункт P2.1 по сценарной отчетности `CSV/PDF`;
- даёт переносимый след по текущему прогону без ручного копирования значений из dashboard;
- усиливает подготовку к защите и передачи проекта дальше, потому что сценарий можно быстро зафиксировать не только в JSON-архиве, но и в читаемых офисных форматах.
