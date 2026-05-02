from datetime import datetime, timezone

from app.services.scenario_archive_service import (
    ScenarioArchiveEntry,
    ScenarioArchiveSnapshot,
)
from app.simulation.state import OperationStatus
from app.ui.viewmodels.scenario_archive import build_scenario_archive_view


def test_scenario_archive_view_formats_snapshot() -> None:
    snapshot = ScenarioArchiveSnapshot(
        generated_at=datetime(2026, 4, 4, 20, 45, tzinfo=timezone.utc),
        overall_status=OperationStatus.NORMAL,
        summary="Сохранено 2 снимка; последний доступен в архиве.",
        note="JSON-снимки лежат в artifacts/scenario-archive.",
        target_directory="artifacts/scenario-archive",
        latest_entry_path="artifacts/scenario-archive/2026-04-04/pvu-run-20260404-204500.json",
        total_entries=2,
        entries=[
            ScenarioArchiveEntry(
                archive_id="pvu-run-20260404-204500",
                captured_at=datetime(2026, 4, 4, 20, 45, tzinfo=timezone.utc),
                source_type="scenario",
                source_label="Межсезонье (midseason)",
                scenario_id="midseason",
                scenario_title="Межсезонье",
                status=OperationStatus.NORMAL,
                alarm_count=0,
                supply_temp_c=18.9,
                room_temp_c=21.2,
                actual_airflow_m3_h=3020.0,
                total_power_kw=8.4,
                file_path="artifacts/scenario-archive/2026-04-04/pvu-run-20260404-204500.json",
            )
        ],
    )

    view = build_scenario_archive_view(snapshot)

    assert view.status_text == "Норма"
    assert view.summary_class_name == "status-pill status-normal"
    assert view.latest_entry_text.endswith(".json")
    assert view.total_entries_text == "2"
    assert view.entries[0].status_text == "Норма"
    assert "3020 м³/ч" in view.entries[0].metrics_text
    assert view.entries[0].alarms_text == "нет"


def test_scenario_archive_view_formats_empty_state() -> None:
    snapshot = ScenarioArchiveSnapshot(
        generated_at=datetime(2026, 4, 4, 20, 50, tzinfo=timezone.utc),
        overall_status=OperationStatus.WARNING,
        summary="Архив пока пуст.",
        note="Сохраните текущий прогон.",
        target_directory="artifacts/scenario-archive",
        latest_entry_path=None,
        total_entries=0,
        entries=[],
    )

    view = build_scenario_archive_view(snapshot)

    assert view.status_text == "Риск"
    assert view.latest_entry_text == "ещё не сохранён"
    assert view.entries == []
