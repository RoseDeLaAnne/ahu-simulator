# Phase G: Defense Demo Hardening

Date: 2026-05-02.

## Task

Prepare the M10-M14 package for a calm defense demo: final walkthrough,
release checklist, recovery plan, local launch verification, dashboard smoke
evidence and documentation sync.

## Known Facts

- Phase A-F are complete.
- Last full regression evidence from Phase F: `198 passed`.
- Phase F browser smoke evidence:
  - `artifacts/release-readiness/2026-05-02/m10-m14-phase-f-evidence.md`
  - `artifacts/release-readiness/2026-05-02/m10-m14-phase-f-comparison-smoke.png`
- Runtime artifacts are expected under `artifacts/` in source mode and outside
  the package in desktop/frozen mode.
- `data/scenarios/presets.json` is source-controlled input and must not be
  changed by user preset operations.

## Touchpoints

- `docs/14_defense_pack.md`
- `docs/15_demo_readiness.md`
- `docs/25_windows_run_guide.md`
- `README.md`
- `.omx/plans/m10_m14_100_todo.md`
- `.omx/plans/m10_m14_acceptance_matrix.md`
- `artifacts/release-readiness/2026-05-02/`

## Verification Plan

- Run `python -m pytest`.
- Start local app on loopback with hidden background process.
- Verify `GET /health`.
- Open `/dashboard` with the available browser tool and smoke key demo paths.
- Stop the server process and record evidence.
