# M10-M14 Phase G Evidence

Date: 2026-05-02.

## Documentation

Updated defense/demo hardening documents:

- `docs/14_defense_pack.md`
- `docs/15_demo_readiness.md`
- `docs/25_windows_run_guide.md`
- `README.md`

Added context snapshot:

- `.omx/context/phase-g-defense-demo-hardening-20260502T115834Z.md`

## Automated Regression

Command:

```powershell
python -m pytest
```

Result: `198 passed in 21.52s`.

Final rerun after documentation/evidence updates: `198 passed in 21.71s`.

## Local Server Smoke

Server command shape:

```powershell
python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8766
```

Process: `18428`.

Result:

- `GET http://127.0.0.1:8766/health` returned `{"status":"ok","service":"pvu-diploma-project"}`.
- `GET http://127.0.0.1:8766/dashboard` returned HTTP `200`.
- `GET /readiness/demo` returned `6 из 6 пунктов готовы`.
- `GET /readiness/package` returned `overall_status=normal`.
- `GET /scenarios` returned merged `scenario-preset.v2` presets with locked system metadata.
- Server process was stopped after smoke: `stopped`.

Logs:

- `artifacts/release-readiness/2026-05-02/phase-g-uvicorn-out.log`
- `artifacts/release-readiness/2026-05-02/phase-g-uvicorn-err.log`

## API Demo Smoke

Verified through local API calls against `http://127.0.0.1:8766`:

- Simulation Session v2: reset, start, speed `2.0`, pause, manual tick, reset.
- Reporting v2: report build created CSV/PDF/manifest.
- Before/After Comparison v2: saved `snapshot:before` and `snapshot:after`, built a compatible comparison.

Observed result:

```json
{
  "session": {
    "start": "running",
    "speed": 2.0,
    "after_tick_status": "paused",
    "after_tick_count": 1,
    "reset": "idle"
  },
  "export": {
    "report_id": "pvu-report-20260502-150306",
    "csv": "artifacts/exports/2026-05-02/pvu-report-20260502-150306.csv",
    "pdf": "artifacts/exports/2026-05-02/pvu-report-20260502-150306.pdf",
    "manifest": "artifacts/exports/2026-05-02/pvu-report-20260502-150306.manifest.json"
  },
  "comparison": {
    "before": "before",
    "after": "after",
    "compatible": true,
    "status": "warning"
  }
}
```

## Browser Smoke

Browser Use was attempted but unavailable in this Codex App session:

- `node_repl js` execution tool was not exposed; only `js_reset` was discoverable.
- Playwright fallback returned `Target page, context or browser has been closed`.
- Ruflo browser fallback returned `spawnSync agent-browser ENOENT`.

Because of that, Phase G records HTTP/API dashboard smoke plus the existing
Phase F browser screenshot evidence. Repeat a real browser walkthrough on the
target demo PC before the defense.

Existing browser evidence:

- `artifacts/release-readiness/2026-05-02/m10-m14-phase-f-evidence.md`
- `artifacts/release-readiness/2026-05-02/m10-m14-phase-f-comparison-smoke.png`

## Residual Manual Check

Repeat the final browser walkthrough on the target demo PC:

1. Open `/dashboard`.
2. Confirm viewport and browser/WebGL profile in `Demo Readiness`.
3. Smoke Simulation Session v2, Reporting v2, Before/After Comparison v2 and User Presets v2.
4. Confirm downloads and runtime artifact write permissions.
