# Phase F Release Readiness Context

Task statement: finalize M10-M14 release readiness after completed Phases A-E.

Desired outcome: synchronize docs and `.omx` plans with the implemented contracts, update acceptance evidence, verify runtime/artifact assumptions, and run full regression.

Known facts:
- Phase A-E are reported complete.
- Latest full regression before this phase was `python -m pytest`: 198 passed.
- No new dependencies are allowed.
- Runtime artifacts must remain outside source-controlled package/data inputs.

Constraints:
- Follow AGENTS.md.
- Do not revert unrelated changes.
- Use `apply_patch` for manual edits.
- Keep changes small and documentation-focused.

Open questions to resolve by inspection:
- Which existing readiness/demo docs mention stale M10-M14 status?
- Whether all M10-M14 acceptance criteria have concrete test/evidence references.
- Whether dashboard smoke infrastructure exists and is practical in the current session.

Likely touchpoints:
- `.omx/plans/m10_m14_100_completion_plan.md`
- `.omx/plans/m10_m14_100_todo.md`
- `.omx/plans/m10_m14_acceptance_matrix.md`
- `docs/05_execution_phases.md`
- `docs/06_todo.md`
- `docs/10_sources.md`
- `docs/15_demo_readiness.md`
- `README.md`
