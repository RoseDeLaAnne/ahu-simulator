# Demo Package

Дата актуализации: 2026-04-04.

## Где это доступно

- В dashboard внутри блока `Demo Readiness` добавлена секция `Demo Bundle`.
- API-снимок packaging-ready состояния доступен через `GET /readiness/package`.
- Реальная сборка архива доступна через `POST /readiness/package/build`.
- Локальный PowerShell-entrypoint для той же операции: `.\deploy\build-demo-package.ps1`.

## Что входит в bundle

- `src/app` с расчётным ядром, API и Dash UI;
- `config/defaults.yaml`, `config/p0_baseline.yaml`, пресеты сценариев и validation-данные;
- `deploy`-скрипты и `requirements.txt`;
- README и основные документы по фазам, To-Do, P0 baseline и защите;
- `artifacts/playwright/README.md` и последняя папка ручных dashboard-проверок;
- `artifacts/exports/README.md` и последняя дата `CSV/XLSX/PDF` export-наборов, если такие выгрузки уже собирались;
- `artifacts/scenario-archive/README.md` и последняя дата JSON-снимков, если архив уже использовался;
- отдельный `manifest.json`, записываемый рядом с zip и внутрь архива.

## Куда это собирается

- Артефакты складываются в `artifacts/demo-packages/YYYY-MM-DD/`.
- Имена файлов формируются как `pvu-demo-package-YYYYMMDD-HHMMSS.zip` и `pvu-demo-package-YYYYMMDD-HHMMSS.manifest.json`.

## Как использовать

1. Убедиться, что `Demo Readiness` не показывает missing runtime/documentation items.
2. Нажать `Собрать demo bundle` в dashboard или выполнить `.\deploy\build-demo-package.ps1`.
3. Проверить, что в `artifacts/demo-packages/<дата>/` появились zip и manifest.
4. При необходимости передать этот пакет на другой ПК или использовать как фиксированный snapshot состава проекта к защите.

## Зачем это добавлено

- чтобы phase 8 закрывала не только сценарий показа, но и практическую упаковку проекта;
- чтобы не собирать вручную список файлов перед передачей проекта или офлайн-показом;
- чтобы bundle был воспроизводимым, а его состав фиксировался manifest-файлом.
