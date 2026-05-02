from datetime import datetime, timezone

from app.services.demo_readiness_service import (
    DemoPackageEntry,
    DemoPackageSnapshot,
    DemoEndpoint,
    DemoLaunchCommand,
    DemoReadinessCheck,
    DemoReadinessEvaluation,
    DemoRuntimeVersion,
)
from app.simulation.state import OperationStatus
from app.ui.viewmodels.demo_readiness import (
    build_demo_package_view,
    build_demo_readiness_view,
)


def test_demo_readiness_view_formats_snapshot() -> None:
    evaluation = DemoReadinessEvaluation(
        generated_at=datetime(2026, 4, 4, 21, 0, tzinfo=timezone.utc),
        overall_status=OperationStatus.WARNING,
        ready_checks=4,
        total_checks=5,
        summary="4 из 5 пунктов готовы; финальная проверка на демо-ПК остаётся открытой.",
        note="Последняя ручная проверка должна пройти на целевом устройстве.",
        launch_commands=[
            DemoLaunchCommand(
                command_id="run-local-ps1",
                title="Основной локальный запуск",
                command=r".\deploy\run-local.ps1",
                note="Рекомендуемый способ.",
            )
        ],
        endpoints=[
            DemoEndpoint(
                label="Dashboard",
                path="/dashboard",
                purpose="Основной экран демонстрации.",
            )
        ],
        runtime_versions=[
            DemoRuntimeVersion(component="Python", version="3.12.4")
        ],
        checks=[
            DemoReadinessCheck(
                item_id="launch-script",
                title="Локальный стартовый скрипт",
                status=OperationStatus.NORMAL,
                detail="Скрипт присутствует.",
                evidence_path="deploy/run-local.ps1",
            ),
            DemoReadinessCheck(
                item_id="demo-pc-verification",
                title="Финальная проверка на демо-ПК",
                status=OperationStatus.WARNING,
                detail="Шаг ещё открыт.",
                evidence_path="src/app/ui/assets/browser_diagnostics.js",
            ),
        ],
    )

    view = build_demo_readiness_view(evaluation)

    assert view.summary_text == "4 из 5 пунктов готовы; финальная проверка на демо-ПК остаётся открытой."
    assert view.summary_class_name == "status-pill status-warning"
    assert view.generated_at_text == "2026-04-04T21:00:00+00:00"
    assert view.launch_commands[0].command == r".\deploy\run-local.ps1"
    assert view.endpoints[0].path == "/dashboard"
    assert view.runtime_versions[0].version == "3.12.4"
    assert view.checks[0].status_text == "Готово"
    assert view.checks[1].status_class_name == "status-pill status-warning"


def test_demo_package_view_formats_snapshot() -> None:
    snapshot = DemoPackageSnapshot(
        generated_at=datetime(2026, 4, 4, 21, 15, tzinfo=timezone.utc),
        overall_status=OperationStatus.WARNING,
        summary="Все входы для demo bundle готовы, но архив ещё не собран.",
        note="Bundle собирается в отдельный каталог артефактов.",
        target_directory="artifacts/demo-packages/2026-04-04",
        bundle_name_pattern="pvu-demo-package-YYYYMMDD-HHMMSS.zip",
        latest_bundle_path=None,
        latest_manifest_path=None,
        entries=[
            DemoPackageEntry(
                entry_id="application-source",
                title="Исходный код приложения",
                category="Код",
                note="Основной runtime-контур.",
                source_paths=["src/app"],
                present=True,
            ),
            DemoPackageEntry(
                entry_id="ui-evidence",
                title="Playwright-артефакты",
                category="Артефакты",
                note="Последние dashboard-проверки.",
                source_paths=["artifacts/playwright/README.md"],
                present=False,
            ),
        ],
    )

    view = build_demo_package_view(snapshot)

    assert view.status_text == "Готово к сборке"
    assert view.summary_class_name == "status-pill status-warning"
    assert view.target_directory_text == "artifacts/demo-packages/2026-04-04"
    assert view.latest_bundle_text == "ещё не создан"
    assert view.entries[0].status_text == "Готово"
    assert view.entries[1].status_class_name == "status-pill status-alarm"
