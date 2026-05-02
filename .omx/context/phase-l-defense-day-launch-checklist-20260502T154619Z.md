# Phase L: Defense Day Launch Checklist

Date: 2026-05-02.

## Task statement

Create an ultra-short defense-day operational checklist for the sealed M10-M14
package. This is documentation/evidence packaging only, not new functionality.

## Desired outcome

- `docs/33_defense_day_checklist.md` exists as the shortest "open and act"
  document for the day of defense.
- The checklist is consistent with the Phase K seal note for launch commands,
  URL template, mandatory clicks, fallback paths and evidence references.
- `docs/29_defense_handoff.md` links to the new checklist.
- `.omx/plans/m10_m14_100_todo.md` records Phase L as optional runbook work
  without changing the freeze/seal scope.
- Fresh `python -m pytest` evidence is collected.

## Known facts/evidence

- Phase K sealed the package with `198 passed in 19.14s`.
- Phase K `/health` smoke passed on `http://127.0.0.1:8769`.
- Main launch command is `.\start.bat`.
- Explicit fallback launch uses `AHU_SIMULATOR_PORT=8768`.
- Final seal note is `docs/32_defense_seal_note.md`.
- Handoff index is
  `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`.

## Constraints

- Do not change application code.
- Do not add dependencies.
- Do not run browser smoke unless necessary.
- Do not leave background processes.
- Keep changes small, reversible and documentation-only.

## Unknowns/open questions

- None blocking. The target demo PC may still need a manual click-pass if it
  differs from this local environment.

## Likely touchpoints

- `docs/33_defense_day_checklist.md`
- `docs/29_defense_handoff.md`
- `.omx/plans/m10_m14_100_todo.md`
- `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`
