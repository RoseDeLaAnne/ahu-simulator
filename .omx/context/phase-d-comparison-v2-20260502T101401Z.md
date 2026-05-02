# Phase D: Before/After Comparison v2

Task statement: finish Phase D for M10-M14 by adding explicit before/after comparison snapshots, richer interpretation/status, API/UI controls, export metadata, and tests.

Desired outcome: users can capture `До` and `После`, compare snapshot/archive/active sources, see compatibility and interpretation, and export a versioned comparison package.

Known facts/evidence:
- Phase A-C are complete; full pytest previously passed with 185 tests.
- Existing comparison service supports active/archive references, compatibility checks, KPI/trend deltas, and CSV/PDF/manifest export.
- Runtime data should be stored through `RuntimePathResolver`, not directly in source-controlled data.

Constraints:
- Follow AGENTS.md; no new dependencies; keep diffs small and reversible.
- Preserve technical API values such as `normal`, `warning`, `alarm`.
- Archive-based comparison must keep working.

Unknowns/open questions:
- Exact UI polish will be limited to callback/layout tests unless a later visual Phase F smoke run is requested.

Likely codebase touchpoints:
- `src/app/services/comparison_service.py`
- `src/app/infrastructure/runtime_paths.py`
- `src/app/api/routers/comparison.py`
- `src/app/ui/viewmodels/run_comparison.py`
- `src/app/ui/layout.py`
- `src/app/ui/callbacks.py`
- `tests/unit/test_run_comparison_service.py`
- `tests/unit/test_run_comparison_viewmodel.py`
- `tests/integration/test_api.py`
- `tests/unit/test_dashboard_callbacks.py`
