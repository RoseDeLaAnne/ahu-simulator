# Phase K: Final Pre-Defense Dry Run and Seal

Task statement:
- Perform the final dry run and seal for the M10-M14 defense package.
- Verify that demo route, presenter speech, Q&A, evidence links, and recovery pack are mutually consistent.
- Create a short seal note with morning-of-defense instructions.

Desired outcome:
- `docs/32_defense_seal_note.md` exists and is the final "open in the morning" note.
- `.omx/plans/m10_m14_100_todo.md` records Phase K as final dry run/seal.
- Final pytest evidence is fresh.
- Optional `/health` smoke is run only if fast and safe, with no lingering background process.

Known facts/evidence:
- Phase A-I are complete.
- Phase J presenter pack is complete.
- Last known full regression before Phase K: `198 passed`.
- Previous `/health` smoke: `status=ok`.
- Handoff index: `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`.
- Open-first doc: `docs/29_defense_handoff.md`.
- Presenter script: `docs/30_defense_presenter_script.md`.
- Q&A pack: `docs/31_defense_qna.md`.

Constraints:
- Follow AGENTS.md.
- No new dependencies.
- Do not revert unrelated changes.
- Code changes only for a real launch, evidence, or demo blocker.
- Keep changes small, document-focused, and reversible.

Unknowns/open questions:
- Whether all handoff artifact paths still exist after Phase J.
- Whether the launch commands and click route are consistent across freeze/handoff/presenter docs.

Likely touchpoints:
- `docs/32_defense_seal_note.md`
- `.omx/plans/m10_m14_100_todo.md`
- `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`
- `docs/29_defense_handoff.md`
