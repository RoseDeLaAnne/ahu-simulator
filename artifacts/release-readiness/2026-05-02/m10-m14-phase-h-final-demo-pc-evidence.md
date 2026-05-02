# M10-M14 Phase H Final Demo PC Evidence

Date: 2026-05-02.

## Environment

- Workspace: `C:\My\Work\Diploma\ahu-simulator`
- Local server URL: `http://127.0.0.1:8767`
- Server command shape:

```powershell
python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8767
```

- Server process during smoke: `22804`
- Server process after smoke: `stopped`; no extra `python` process remained.
- Logs:
  - `artifacts/release-readiness/2026-05-02/phase-h-uvicorn-out.log`
  - `artifacts/release-readiness/2026-05-02/phase-h-uvicorn-err.log`

## Full Regression

Command:

```powershell
python -m pytest
```

Result: `198 passed in 17.01s`.

Final rerun after documentation/evidence updates: `198 passed in 16.10s`.

## Health And Dashboard

- `GET http://127.0.0.1:8767/health` returned
  `{"status":"ok","service":"pvu-diploma-project"}`.
- `GET http://127.0.0.1:8767/dashboard` returned HTTP `200`.
- `GET /readiness/demo` returned
  `6 из 6 пунктов готовы; проектный предварительный контроль закрыт, профиль браузера/WebGL подтверждён.`
- `GET /readiness/package` returned `overall_status=normal`.
- `GET /scenarios` returned locked system presets including `winter`,
  `summer`, `peak_load`.

## API Walkthrough

Verified through live API calls against `http://127.0.0.1:8767`:

- Simulation Session v2: reset, start, speed `2.0`, pause, manual tick, reset.
- Reporting v2: preview and build for `scenario-report.v2`, manifest download
  returned HTTP `200`.
- Before/After Comparison v2:
  - incompatible pair correctly blocked export with a compatibility explanation;
  - compatible `winter` -> `peak_load` pair built and exported
    `run-comparison.v2`;
  - manifest download returned HTTP `200`.
- User Presets v2: temporary API preset was created, applied, exported as
  `scenario-preset.v2` and deleted.
- Demo Bundle: API build created a zip and manifest.

Key API artifacts:

```text
artifacts/exports/2026-05-02/pvu-report-20260502-151337.csv
artifacts/exports/2026-05-02/pvu-report-20260502-151337.pdf
artifacts/exports/2026-05-02/pvu-report-20260502-151337.manifest.json
artifacts/exports/2026-05-02/pvu-comparison-20260502-151356.csv
artifacts/exports/2026-05-02/pvu-comparison-20260502-151356.pdf
artifacts/exports/2026-05-02/pvu-comparison-20260502-151356.manifest.json
artifacts/demo-packages/2026-05-02/pvu-demo-package-20260502-151337.zip
artifacts/demo-packages/2026-05-02/pvu-demo-package-20260502-151337.manifest.json
```

## Browser Walkthrough

Browser Use worked in Phase H through the in-app browser.

Verified through UI:

- `/dashboard` opened successfully.
- Simulation Session v2:
  - initial status: `Готово`;
  - after `Старт`: `Выполняется`;
  - after `Пауза`: `На паузе`;
  - after manual step: tick progress showed `2 / 12`;
  - after `Сброс`: `Готово`.
- Export Pack:
  - preview text appeared;
  - build created report `pvu-report-20260502-151838`;
  - CSV/PDF/manifest paths appeared in the UI.
- Before/After Comparison v2:
  - `До — Phase H До`;
  - `После — Phase H После`;
  - compatibility summary confirmed same step, horizon, trend grid and metric set;
  - interpretation included `Статус пары: Риск`;
  - export created `pvu-comparison-20260502-151851`.
- User Presets v2:
  - UI preset `Phase H UI temp preset` was saved;
  - export payload contained `scenario-preset.v2`;
  - preset was deleted.
- Demo Readiness page opened in browser and was captured as evidence.

Browser screenshots:

```text
artifacts/release-readiness/2026-05-02/m10-m14-phase-h-dashboard-smoke.png
artifacts/release-readiness/2026-05-02/m10-m14-phase-h-session-browser.png
artifacts/release-readiness/2026-05-02/m10-m14-phase-h-readiness-browser.png
```

UI artifact packs:

```text
artifacts/exports/2026-05-02/pvu-report-20260502-151838.csv
artifacts/exports/2026-05-02/pvu-report-20260502-151838.pdf
artifacts/exports/2026-05-02/pvu-report-20260502-151838.manifest.json
artifacts/exports/2026-05-02/pvu-comparison-20260502-151851.csv
artifacts/exports/2026-05-02/pvu-comparison-20260502-151851.pdf
artifacts/exports/2026-05-02/pvu-comparison-20260502-151851.manifest.json
```

Browser automation note: clicking `Demo Bundle` through the in-app browser
translation layer missed the button, but `POST /readiness/package/build`
successfully created the bundle. This is recorded as an automation limitation,
not an application blocker.

## Runtime And Source-Control Safety

- `data/scenarios/presets.json` last write time remained `2026-04-19 19:04:13`.
- Runtime user preset storage after cleanup contains an empty list:
  `artifacts/user-presets/presets.json`.
- Runtime artifacts were created under `artifacts/exports`,
  `artifacts/demo-packages`, `artifacts/comparison-snapshots` and
  `artifacts/release-readiness`.

## Freeze Note

The operational freeze note is in `docs/28_defense_freeze_note.md`.

## Residual Risk

If the actual defense PC is different from this local environment, repeat only
the final browser viewport check and one short click pass there. The project has
current automated regression, API smoke, UI smoke and screenshot evidence for
the current environment.
