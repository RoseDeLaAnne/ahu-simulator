# Phase E: User Presets v2 Context Snapshot

Task statement:
- Complete Phase E for M10-M14 by adding runtime-managed user scenario presets while keeping source-controlled system presets locked.

Desired outcome:
- `/scenarios` returns merged system and user presets with `schema_version`, `source`, `locked`, `created_at`, `updated_at`.
- Users can create, apply, rename, update, delete, import and export runtime presets.
- System presets, including `winter`, `summer`, `peak_load`, remain read-only and unchanged in `data/scenarios/presets.json`.
- Tests cover merge, locked protection, CRUD, import/export validation, corrupt runtime fallback, API and dashboard helper behavior.

Known facts/evidence:
- System presets are loaded from `data/scenarios/presets.json` by `app.simulation.scenarios.load_scenarios`.
- `SimulationService` currently stores scenarios in an in-memory dictionary at construction.
- Runtime directories are centralized by `RuntimePathResolver`.
- Dashboard scenario dropdown and shortcut buttons are wired in `src/app/ui/layout.py` and `src/app/ui/callbacks.py`.
- Previous phases pass full pytest: 189 tests.

Constraints:
- Do not add dependencies.
- Store user preset JSON under runtime directory, not source tree.
- Preserve old system preset JSON compatibility.
- Keep changes small and reversible.
- Do not use Codex subagents unless explicitly requested by the user.

Unknowns/open questions:
- Exact UI polish is not screenshot-verified yet; Phase E should at minimum expose functional controls and tests.

Likely codebase touchpoints:
- `src/app/simulation/scenarios.py`
- `src/app/services/simulation_service.py`
- `src/app/services/scenario_preset_service.py`
- `src/app/infrastructure/runtime_paths.py`
- `src/app/bootstrap/wiring.py`
- `src/app/bootstrap/dependencies.py`
- `src/app/api/routers/scenarios.py`
- `src/app/ui/layout.py`
- `src/app/ui/callbacks.py`
- `tests/scenario/test_scenarios.py`
- `tests/scenario/test_preset_ranges.py`
- `tests/unit/test_dashboard_callbacks.py`
- `tests/integration/test_api.py`
