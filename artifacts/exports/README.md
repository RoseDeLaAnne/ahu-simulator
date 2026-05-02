# Export Artifacts

Сюда складываются локальные export-наборы по текущим прогонам dashboard.

## Структура

```text
artifacts/exports/
  README.md
  YYYY-MM-DD/
    pvu-export-YYYYMMDD-HHMMSS.csv
    pvu-export-YYYYMMDD-HHMMSS.xlsx
    pvu-export-YYYYMMDD-HHMMSS.pdf
    pvu-export-YYYYMMDD-HHMMSS.manifest.json
```

## Правила

- Один запуск `Export Pack` создаёт сразу четыре файла: `CSV`, `XLSX`, `PDF` и `manifest.json`.
- Папка с датой отражает день фактической сборки export-набора.
- `CSV` предназначен для табличной обработки и содержит все trend-point строки вместе с параметрами и итоговым состоянием.
- `XLSX` содержит листы `summary`, `parameters`, `state`, `alarms`, `trend`.
- `PDF` остаётся кратким переносимым отчётом по активному прогону без внешних зависимостей на генератор документов.
