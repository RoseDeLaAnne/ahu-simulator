# Phase H: Target Demo PC Final Verification and Freeze

Date: 2026-05-02.

## Task statement

Run the final M10-M14 defense verification on the closest available local
environment, capture fresh evidence, and prepare a concise freeze note for the
defense demo.

## Desired outcome

- Full regression result is current.
- Local app starts and answers `/health`.
- `/dashboard` is reachable, with browser walkthrough attempted or recorded with
  a precise blocker.
- Simulation Session v2, Reporting v2, Before/After Comparison v2, User Presets
  v2, Demo Readiness and Demo Bundle are checked through live UI/API paths.
- Phase H evidence and freeze guidance are written under release-readiness docs.

## Known facts

- Phase A-G are complete.
- Last Phase G full regression: `198 passed`.
- Phase G evidence: `artifacts/release-readiness/2026-05-02/m10-m14-phase-g-evidence.md`.
- Phase G local smoke passed over HTTP/API, but Browser Use was unavailable in
  that Codex App session.

## Constraints

- Follow AGENTS.md.
- No new dependencies.
- Do not revert unrelated changes.
- Do not leave extra server/background processes running.
- Runtime artifacts should stay in runtime/artifact directories, not source data.

## Likely touchpoints

- `docs/15_demo_readiness.md`
- `.omx/plans/m10_m14_100_todo.md`
- `.omx/plans/m10_m14_acceptance_matrix.md`
- `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-final-demo-pc-evidence.md`

## Open risk

Browser automation availability may still be limited in the current Codex App
session. If unavailable, record HTTP/API evidence and leave only the true target
demo-PC browser pass as a manual final check.
