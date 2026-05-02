# M10-M14 Phase F Evidence

Date: 2026-05-02.

## Automated Regression

Command:

```powershell
python -m pytest
```

Result: `198 passed in 19.75s`.

## Local Dashboard Smoke

Server:

```text
http://127.0.0.1:8765/dashboard
```

Verified paths:

- Simulation Session v2: `Старт -> Пауза -> Шаг -> x2 -> Сброс`.
- User Presets v2: save temporary user preset, export JSON, delete preset.
- Reporting v2: preview and build report; CSV/PDF download links populated.
- Before/After Comparison v2: save `До`, switch to `peak_load`, save `После`, compatible comparison shows interpretation and export remains enabled.

Observed smoke result:

```json
{
  "session": {
    "status": "На паузе",
    "ticks": "2 / 12",
    "elapsed": "20 / 120 мин",
    "speed": "x2"
  },
  "afterReset": "Готово",
  "userPresetSave": "Пользовательский пресет «Smoke preset 2026-05-02» сохранён.",
  "userPresetDelete": "Пользовательский пресет «Smoke preset 2026-05-02» удалён.",
  "exportBuild": {
    "status": "Норма",
    "latestReport": "pvu-report-20260502-135540",
    "csvHref": "/exports/result/download?path=artifacts%2Fexports%2F2026-05-02%2Fpvu-report-20260502-135540.csv",
    "pdfHref": "/exports/result/download?path=artifacts%2Fexports%2F2026-05-02%2Fpvu-report-20260502-135540.pdf"
  },
  "comparison": {
    "status": "Норма",
    "compatibility": "Совместимо",
    "interpretation": "Улучшилось: 5; ухудшилось: 2; без существенных изменений: 5. Статус пары: Риск. Крупнейшая дельта: Фактический расход -3921.48 м³/ч.",
    "exportDisabled": false
  }
}
```

Screenshot:

- `artifacts/release-readiness/2026-05-02/m10-m14-phase-f-comparison-smoke.png`

## Residual Manual Check

Repeat the same browser walkthrough on the target demo PC before defense to
verify viewport, browser profile and local filesystem permissions.
