# M10-M14 Acceptance Matrix

Date: 2026-05-01.

## 1. Simulation Lifecycle

| Criterion | Evidence |
| --- | --- |
| Start switches session to running and disables unsafe parameter edits. | `tests/unit/test_simulation_session_service.py`; `tests/unit/test_dashboard_callbacks.py`; `tests/integration/test_api.py` |
| Pause stops automatic ticks without losing history. | `tests/unit/test_simulation_session_service.py`; `tests/integration/test_api.py` |
| Manual step works while paused/idle and appends exactly one history point. | `tests/unit/test_simulation_session_service.py`; `tests/integration/test_api.py` |
| Reset restores original seed parameters/history. | `tests/unit/test_simulation_session_service.py`; `tests/integration/test_api.py` |
| Speed control changes automatic tick interval. | `tests/unit/test_dashboard_callbacks.py`; `tests/integration/test_api.py`; browser smoke recommended |
| Simulation stops at horizon and marks completed. | `tests/unit/test_simulation_session_service.py`; `tests/integration/test_api.py` |
| Session survives app restart through runtime storage. | `tests/unit/test_simulation_session_service.py`; `tests/integration/test_api.py` |
| Start/pause/tick/reset/completed are event-logged. | `tests/unit/test_simulation_session_service.py`; `tests/integration/test_api.py` |

## 2. Scenario Reporting PDF/CSV

| Criterion | Evidence |
| --- | --- |
| Report contract has schema version and stable metadata. | `tests/unit/test_export_service.py`; `tests/integration/test_api.py` |
| CSV has deterministic section order and parses with Python `csv`. | `tests/unit/test_export_service.py` |
| PDF contains title, KPI, statuses, parameters, alarms and trend chart. | `tests/unit/test_export_service.py` artifact smoke |
| Manifest references CSV/PDF paths and schema version. | `tests/unit/test_export_service.py`; `tests/integration/test_api.py` |
| Dashboard can preview/build/list/download report artifacts. | `tests/unit/test_export_pack_viewmodel.py`; `tests/unit/test_dashboard_callbacks.py`; browser smoke recommended |
| API download uses safe file resolution and `FileResponse`. | `tests/integration/test_api.py` |
| Batch export creates separate artifacts for selected scenarios. | `tests/unit/test_export_service.py`; `tests/integration/test_api.py` |

## 3. Before/After Comparison

| Criterion | Evidence |
| --- | --- |
| User can save named `До` and `После` snapshots. | `tests/unit/test_run_comparison_service.py`; `tests/integration/test_api.py`; `tests/unit/test_dashboard_callbacks.py` |
| Archive sources still work. | `tests/unit/test_run_comparison_service.py` regression coverage |
| Compatible pair produces KPI and trend deltas. | `tests/unit/test_run_comparison_service.py`; `tests/unit/test_run_comparison_viewmodel.py` |
| Incompatible pair gives exact reasons and blocks export. | `tests/unit/test_run_comparison_service.py`; `tests/unit/test_run_comparison_viewmodel.py`; `tests/integration/test_api.py` |
| Comparison summary identifies improved/worsened/unchanged metrics. | `tests/unit/test_run_comparison_service.py`; `tests/unit/test_run_comparison_viewmodel.py` |
| Dashboard shows table, trend overlay and top-delta cards. | `tests/unit/test_run_comparison_viewmodel.py`; `tests/unit/test_dashboard_callbacks.py`; browser smoke recommended |
| CSV/PDF/manifest export contains pair metadata and deltas. | `tests/unit/test_run_comparison_service.py`; `tests/integration/test_api.py` artifact smoke |

## 4. Colored Statuses

| Criterion | Evidence |
| --- | --- |
| Labels are `Норма`, `Риск`, `Авария` in all user-facing UI/report contexts. | `tests/unit/test_status_service.py`; `tests/unit/test_status_viewmodel_consistency.py` |
| API enum values stay backward compatible. | `tests/integration/test_api.py`; technical values remain `normal`, `warning`, `alarm` |
| All thresholds have boundary tests. | `tests/unit/test_status_policy.py` |
| Status colors/classes are centralized. | `tests/unit/test_status_service.py`; `src/app/services/status_service.py` |
| Dashboard, export, comparison and archive use identical label/color mapping. | `tests/unit/test_status_viewmodel_consistency.py`; `tests/unit/test_dashboard_callbacks.py` |
| 2D/3D status colors match the same service mapping. | `tests/unit/test_visualization_viewmodel.py`; browser/visual smoke recommended |

## 5. Scenario Presets

| Criterion | Evidence |
| --- | --- |
| System presets `winter`, `summer`, `peak_load` remain present and locked. | `tests/scenario/test_scenarios.py`; `tests/scenario/test_preset_ranges.py` |
| User presets are stored in runtime directory. | `tests/unit/test_user_preset_service.py`; `RuntimePathResolver` alias `artifacts/user-presets` |
| User can create/apply/rename/delete a preset. | `tests/unit/test_user_preset_service.py`; `tests/integration/test_api.py`; `tests/unit/test_dashboard_callbacks.py` |
| Import rejects invalid payloads with clear errors. | `tests/unit/test_user_preset_service.py`; `tests/integration/test_api.py` |
| Export produces portable user preset JSON. | `tests/unit/test_user_preset_service.py`; `tests/integration/test_api.py` |
| `/scenarios` returns system and user presets with source metadata. | `tests/integration/test_api.py`; `tests/unit/test_dashboard_callbacks.py` |
| Quick preset buttons continue to apply system presets. | `tests/unit/test_dashboard_callbacks.py`; browser smoke recommended |

## Final Package Gate

| Gate | Evidence |
| --- | --- |
| Full regression passes. | Phase H `python -m pytest`: `198 passed in 17.01s` |
| Dashboard smoke passes. | Phase F local browser smoke on `http://127.0.0.1:8765/dashboard`; Phase G HTTP/API smoke on `http://127.0.0.1:8766`; Phase H browser walkthrough on `http://127.0.0.1:8767/dashboard` with screenshots in `artifacts/release-readiness/2026-05-02/` |
| Documentation synchronized. | `docs/05_execution_phases.md`; `docs/06_todo.md`; `docs/10_sources.md`; `docs/14_defense_pack.md`; `docs/15_demo_readiness.md`; `docs/25_windows_run_guide.md`; `docs/28_defense_freeze_note.md`; `README.md` |
| Runtime artifacts write outside source tree. | `tests/unit/test_user_preset_service.py`; `tests/unit/test_simulation_session_service.py`; export/archive/comparison integration tests |
| Defense hardening evidence captured. | `artifacts/release-readiness/2026-05-02/m10-m14-phase-g-evidence.md` |
| Final defense freeze evidence captured. | `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-final-demo-pc-evidence.md`; `docs/28_defense_freeze_note.md` |
| Defense handoff package captured. | `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`; `docs/29_defense_handoff.md`; Phase I `python -m pytest`: `198 passed in 16.71s`; `/health` smoke on `http://127.0.0.1:8768`: `status=ok` |
| Final presenter/seal package captured. | `docs/30_defense_presenter_script.md`; `docs/31_defense_qna.md`; `docs/32_defense_seal_note.md`; Phase K `python -m pytest`: `198 passed in 19.14s`; `/health` smoke on `http://127.0.0.1:8769`: `status=ok` |

Post-Phase-K boundary: no M10-M14 implementation work remains in the freeze
package. Further changes should be either a manual repeat of the short demo-PC
click-pass or a new explicitly scoped task.
