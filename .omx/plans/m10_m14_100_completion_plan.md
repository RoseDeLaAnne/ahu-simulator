# M10-M14: completion plan to 100%

Date: 2026-05-01.

## Requirements Summary

Bring five existing MVP features to product-complete state:

1. Simulation lifecycle: start, pause, reset, manual ticks, automatic ticks, speed control, horizon completion, persistence, event trace.
2. Scenario reporting: professional PDF/CSV package, preview, batch export, stable manifest.
3. Before/after comparison: explicit before/after snapshots, clearer UX, richer interpretation, export.
4. Colored statuses: one status language across domain/API/UI/export/docs.
5. Scenario presets: stable system presets plus user-managed runtime presets.

## Evidence Baseline

- Session DTOs and actions exist in `src/app/simulation/state.py` (`SimulationSessionStatus`, `SimulationHistory`, `SimulationSessionActions`, `SimulationSession`).
- `SimulationService` supports `start`, `pause`, `reset`, `tick` in `src/app/services/simulation_service.py`.
- Session API endpoints exist in `src/app/api/routers/simulation.py`.
- The dashboard uses `dcc.Interval` and `dcc.Store` in `src/app/ui/layout.py`, and `simulation-interval` triggers ticks in `src/app/ui/callbacks.py`.
- Report contract/export exists in `src/app/services/export_service.py`; API download uses FastAPI `FileResponse` in `src/app/api/routers/exports.py`.
- Run comparison service/export exists in `src/app/services/comparison_service.py`; API endpoints exist in `src/app/api/routers/comparison.py`.
- Status thresholds and mappings exist in `src/app/simulation/status_policy.py`, `src/app/services/status_service.py`, and `src/app/ui/viewmodels/status_presenter.py`.
- Required system presets exist in `data/scenarios/presets.json`; tests exist in `tests/scenario/test_scenarios.py` and `tests/scenario/test_preset_ranges.py`.

## External Documentation Notes

- Dash `dcc.Interval` is the right primitive for automatic live updates; callbacks can listen to `n_intervals`: https://dash.plotly.com/live-updates.
- Dash `dcc.Slider(updatemode='drag')` supports continuous callback updates while dragging: https://dash.plotly.com/dash-core-components/slider.
- FastAPI `FileResponse` is appropriate for downloadable generated files: https://fastapi.tiangolo.com/advanced/custom-response/.
- ReportLab is already installed and supports PDF tables/graphics, so use it before considering new dependencies: https://docs.reportlab.com/ and https://www.reportlab.com/chartgallery/.

## Plan 1: Simulation Lifecycle

Current estimate: 100%.

### Target

The simulation behaves like a controllable run engine with bounded time horizon, adjustable playback, persistence, and event trace.

Phase B implementation status: completed. The session contract now includes
`completed`, playback speed, bounded horizon metadata, command trace, runtime
JSON persistence and dashboard/API speed controls.

### Implementation Phases

1. Session contract v2.
   - Add `COMPLETED` to `SimulationSessionStatus`.
   - Add session fields: `playback_speed`, `max_ticks`, `horizon_reached`, `completed_at`, `last_command`.
   - Extend `SimulationSessionActions` with `can_resume` and `can_set_speed`.

2. Service behavior.
   - Compute `max_ticks = ceil(horizon_minutes / step_minutes)`.
   - Prevent `tick()` from adding history past the horizon.
   - Transition `RUNNING -> COMPLETED` automatically at horizon.
   - Add `set_playback_speed(speed: float)` with a small allowed catalog such as `0.25`, `0.5`, `1`, `2`, `4`.
   - Record events for start/pause/tick/reset/completed, not only reset/tick.

3. Persistence.
   - Add a `SimulationSessionStore` under `src/app/services` using `RuntimePathResolver`.
   - Persist session JSON under runtime dir, not source tree.
   - On application startup, restore a valid session or reset safely if the file is corrupt/incompatible.

4. Dashboard.
   - Add speed slider/control in the session panel.
   - Bind `simulation-interval.interval` to speed without resetting current camera/view state.
   - Show progress: elapsed / horizon, tick count / max ticks, completed badge.
   - Keep parameter inputs disabled only while running.

5. Tests.
   - Extend `tests/unit/test_simulation_session_service.py`.
   - Add API integration tests for start/pause/tick/reset/speed/completed.
   - Add a Playwright smoke for start -> speed change -> pause -> step -> reset.

### Acceptance Criteria

- Running auto-ticks until `elapsed_minutes >= horizon_minutes`, then stops and marks session completed.
- Manual tick is blocked or no-op after completed with a clear action state.
- Speed changes update `dcc.Interval.interval` and do not reset current results/history.
- Start, pause, reset, tick, completed are visible in event log.
- Restarting the app restores the last valid session from runtime storage.

## Plan 2: Scenario Reporting PDF/CSV

Current estimate: 100%.

### Target

Reports are professional engineering artifacts: PDF with sections, tables and charts; CSV with stable machine-readable sections; manifest with schema version and checks.

Phase C implementation status: completed. The report contract now uses
`scenario-report.v2`, stable sections, chart specs, CSV/PDF/manifest artifact
validation, a ReportLab table/chart PDF renderer, preview API/dashboard flow,
direct dashboard downloads and API batch export for selected presets.

### Implementation Phases

1. Contract v2.
   - Add `schema_version`, `sections`, `chart_specs`, `artifact_checksums`.
   - Keep existing `ScenarioReport` backward compatible.
   - Add `ReportSection` and `ReportChartSpec` models.

2. PDF renderer.
   - Replace or wrap `pdf_text_renderer` with a ReportLab Platypus renderer.
   - Add title page, KPI summary, status legend, parameter table, state table, alarms, trend chart.
   - Embed a Cyrillic-capable font in packaged assets if the default renderer cannot preserve Russian text.

3. CSV renderer.
   - Keep current CSV shape for compatibility.
   - Add stable sections: `metadata`, `findings`, `parameters`, `state`, `alarms`, `trend`.
   - Add deterministic ordering and UTF-8 verification.

4. API/UI.
   - Add preview endpoint/callback returning report metadata before writing files.
   - Add direct dashboard download controls for CSV/PDF/manifest.
   - Add batch export for selected presets.

5. Tests.
   - Extend `tests/unit/test_export_service.py`.
   - Add integration tests for `/exports/result/build` and `/exports/result/download`.
   - Add artifact smoke: PDF header, section text, CSV parse, manifest schema.

### Acceptance Criteria

- One run produces CSV, PDF, manifest with matching report id and schema version.
- PDF includes readable Russian text, status legend, KPI table, trend visualization.
- CSV is parseable by Python `csv` and has deterministic section order.
- Dashboard can preview, build, list and download each artifact.
- Batch export creates one artifact set per selected scenario.

## Plan 3: Before/After Run Comparison

Current estimate: 100%.

### Target

Users can explicitly capture before/after states, compare them, understand compatibility/impact, and export the comparison.

Phase D implementation status: completed. Comparison now has runtime
`before`/`after` snapshots, snapshot/archive/active source selection,
default before/after pairing, compatibility metadata, interpretation summary,
comparison status, top deltas, dashboard capture controls and a versioned
`run-comparison.v2` CSV/PDF/manifest package.

### Implementation Phases

1. Snapshot model.
   - Add named comparison snapshots independent from generic archive records.
   - Add `before` and `after` labels, notes, captured source, scenario id, parameter hash.
   - Keep archive records as selectable sources.

2. Service behavior.
   - Add `save_before(result, label)` and `save_after(result, label)` service paths.
   - Add interpretation summary: improved, worsened, unchanged metrics.
   - Add comparison status derived from compatibility and significant deltas.

3. UI.
   - Add buttons: `Зафиксировать До`, `Зафиксировать После`.
   - Keep current dropdowns, but default to named before/after snapshots when present.
   - Add trend overlay and top-delta cards.
   - Improve incompatible-pair explanation.

4. Export.
   - Extend comparison PDF/CSV with compatibility, summary, top deltas, trend deltas, source metadata.
   - Include manifest schema version and source ids.

5. Tests.
   - Extend `tests/unit/test_run_comparison_service.py`.
   - Add tests for snapshot save/select/delete and incompatible pair messaging.
   - Add UI smoke for fixing before/after and exporting.

### Acceptance Criteria

- User can create a before snapshot, alter parameters, create an after snapshot, and compare without manually using archive first.
- Incompatible pairs show exact reasons and disable export.
- Compatible pairs show KPI deltas, trend deltas, summary interpretation, and downloadable CSV/PDF.
- Current archive-based comparison keeps working.

## Plan 4: Colored Statuses

Current estimate: 100%.

### Target

`Норма`, `Риск`, `Авария` is the only user-facing status vocabulary across the app.

Phase A implementation status: completed. `StatusService` is the single
presentation source for label, CSS class, color, summary and legend entries.
`status_presenter.py` remains only as a compatibility proxy. Dashboard,
archive, export, comparison and event-log view-models use the same Russian
labels while the technical enum/API values `normal`, `warning`, `alarm` remain
stable.

### Implementation Phases

1. Status source of truth.
   - Consolidate status labels/classes/colors in `StatusService`.
   - Convert `status_presenter.py` to call `StatusService` or remove duplication.
   - Add doc glossary for status terms and thresholds.

2. Threshold visibility.
   - Add API/dashboard snapshot for active thresholds.
   - Verify `config/defaults.yaml` documents all thresholds loaded by settings.

3. UI/export coverage.
   - Audit dashboard strings for `warning`, `предупреждение`, and inconsistent labels.
   - Add status pills to archive/comparison/export rows where missing.
   - Ensure 2D/3D visual states use the same color map.

4. Tests.
   - Add boundary tests for each threshold category.
   - Add string consistency tests for user-facing Russian labels.
   - Add visual smoke for status colors in normal/risk/alarm scenarios.

### Acceptance Criteria

- User-facing UI and reports display only `Норма`, `Риск`, `Авария`.
- Technical enum values remain stable for API compatibility.
- All threshold boundaries have unit tests.
- Status color and label are identical in dashboard, export, comparison and archive.

## Plan 5: Scenario Presets

Current estimate: 100%.

### Target

System presets remain locked and versioned; users can manage their own runtime presets.

Phase E implementation status: completed. Scenario presets now use
`scenario-preset.v2` metadata, system presets are locked/read-only, user
presets are stored under `artifacts/user-presets`, and the app supports
create, update, rename, delete, import, export, merged `/scenarios` responses,
runtime application and dashboard controls without modifying
`data/scenarios/presets.json`.

### Implementation Phases

1. Preset contract v2.
   - Add `schema_version`, `source`, `locked`, `created_at`, `updated_at`.
   - Keep loading existing `data/scenarios/presets.json`.
   - Introduce runtime user preset file under runtime dir.

2. User preset service.
   - Add CRUD methods: create, update, rename, delete, import, export.
   - Validate parameters via `SimulationParameters`.
   - Protect system presets from mutation.

3. API/UI.
   - Extend scenario list with system + user presets.
   - Add dashboard controls for save current as preset, rename, delete, import/export.
   - Keep quick buttons for `winter`, `summer`, `peak_load`.

4. Tests.
   - Add unit tests for system/user merge, locked preset protection, import/export validation.
   - Add integration tests for scenario endpoints.
   - Add UI smoke for create/apply/delete user preset.

### Acceptance Criteria

- `winter`, `summer`, `peak_load` cannot be edited from UI.
- User can create a preset from current parameters and apply it later.
- User presets survive app restart through runtime storage.
- Invalid imported presets are rejected with actionable errors.

## Phase F: Documentation and Release Readiness

Current estimate: 100%.

### Target

The M10-M14 package is synchronized across docs, plans, acceptance evidence and
regression checks.

Phase F implementation status: completed. Documentation now records the
implemented contracts `scenario-report.v2`, `run-comparison.v2`,
`scenario-preset.v2`, Simulation Session v2 and the shared status language
`Норма` / `Риск` / `Авария`. The acceptance matrix references concrete
automated tests and calls out the remaining manual/browser evidence boundary.

### Evidence Summary

- Full regression gate: `python -m pytest`.
- Status language: `tests/unit/test_status_policy.py`,
  `tests/unit/test_status_service.py`,
  `tests/unit/test_status_viewmodel_consistency.py`.
- Simulation Session v2: `tests/unit/test_simulation_session_service.py`,
  `tests/integration/test_api.py`,
  `tests/unit/test_dashboard_callbacks.py`.
- Reporting v2: `tests/unit/test_export_service.py`,
  `tests/unit/test_export_pack_viewmodel.py`, `tests/integration/test_api.py`.
- Comparison v2: `tests/unit/test_run_comparison_service.py`,
  `tests/unit/test_run_comparison_viewmodel.py`, `tests/integration/test_api.py`.
- User Presets v2: `tests/unit/test_user_preset_service.py`,
  `tests/scenario/test_scenarios.py`, `tests/scenario/test_preset_ranges.py`,
  `tests/integration/test_api.py`.
- Runtime storage: covered through services using `RuntimePathResolver` for
  exports, event log, archive, simulation session, comparison snapshots and user
  presets.

### Browser Smoke

Browser smoke is tracked separately from unit/integration evidence because it
depends on a running local dashboard and browser environment. On 2026-05-02 a
local smoke was run against `http://127.0.0.1:8765/dashboard`: session
start/pause/step/speed/reset, user preset save/export/delete, report
preview/build/download links and before/after comparison all returned expected
visible states. Screenshot evidence is stored under
`artifacts/release-readiness/2026-05-02/`.

Before the defense, repeat the same walkthrough on the target demo PC to verify
viewport, browser profile and local filesystem permissions.

## Cross-Feature Execution Order

1. Status language cleanup.
2. Simulation session v2.
3. Report contract and PDF/CSV renderer v2.
4. Comparison snapshots and richer export.
5. User preset management.
6. Documentation sync and final regression.

## Verification Plan

- Unit: session service, export service, comparison service, status policy/service, scenarios/user presets.
- Integration: simulation/scenarios/exports/comparison endpoints.
- Scenario: winter, summer, peak_load, dirty_filter, manual_mode.
- UI smoke: dashboard session controls, report build/download, before/after compare/export, preset CRUD.
- Full regression: `python -m pytest`.

## Risks and Mitigations

- Risk: session persistence introduces stale/corrupt runtime state. Mitigation: schema version, defensive load, reset fallback.
- Risk: PDF formatting increases brittleness. Mitigation: keep report contract separate from renderer and smoke-test sections rather than pixel layout.
- Risk: status label cleanup breaks API clients. Mitigation: keep enum values, change only presentation labels.
- Risk: user presets conflict with system ids. Mitigation: reserve system ids and validate uniqueness by source.

## Implementation Handoff

Recommended lane:

- Solo or `ralph` for Task 4 first.
- Solo or `executor` for Task 1 service/API.
- UI-heavy follow-up after service contracts are stable.
- Use Playwright only for final dashboard smoke, not for every service-only iteration.

## Done

The package is release-ready when every acceptance criterion in
`.omx/plans/m10_m14_acceptance_matrix.md` has automated evidence or an explicit
manual smoke note, full `python -m pytest` passes, and a fresh dashboard
walkthrough has no blocking issues.
