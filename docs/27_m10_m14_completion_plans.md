# Планы доведения M10-M14 до 100%

Дата: 2026-05-01.

## Назначение

Этот документ фиксирует план полной реализации пяти задач, которые уже доведены до рабочего MVP, но требуют финальной продуктовой доводки. Подробный handoff для последующей реализации сохранен в `.omx/plans/m10_m14_100_completion_plan.md`, общий To-Do - в `.omx/plans/m10_m14_100_todo.md`, матрица приемки - в `.omx/plans/m10_m14_acceptance_matrix.md`.

## Использованные ориентиры

- Dash `dcc.Interval` подходит для периодического обновления без ручного refresh; его `n_intervals` изменяется по заданному интервалу и используется в callback: https://dash.plotly.com/live-updates.
- Dash `dcc.Slider` с `updatemode='drag'` вызывает callback при движении ручки, поэтому такой подход нужен для живого управления скоростью симуляции и фильтрами представлений: https://dash.plotly.com/dash-core-components/slider.
- FastAPI `FileResponse` асинхронно отдает файлы и поддерживает `filename`/`Content-Disposition`, что подходит для PDF/CSV артефактов: https://fastapi.tiangolo.com/advanced/custom-response/.
- ReportLab уже есть в `requirements.txt`; его PDF Toolkit и графические классы можно использовать для табличных PDF и векторных графиков без новой зависимости: https://docs.reportlab.com/ и https://www.reportlab.com/chartgallery/.

## Текущее основание в проекте

- Сессия симуляции уже имеет статусы, действия, шаг, elapsed time, tick count и историю: `src/app/simulation/state.py`.
- `SimulationService` реализует `start`, `pause`, `reset`, `tick`, автозавершение горизонта, скорость воспроизведения и runtime-восстановление активной сессии: `src/app/services/simulation_service.py`.
- API имеет `/simulation/session/start`, `/pause`, `/reset`, `/tick` и `/speed`: `src/app/api/routers/simulation.py`.
- PDF/CSV отчет уже строится из единого `ScenarioReport` и сохраняет CSV, PDF, manifest: `src/app/services/export_service.py`.
- Сравнение уже имеет источники `active-run`/`archive:*`, проверку совместимости, KPI-дельты, trend-дельты и экспорт: `src/app/services/comparison_service.py`.
- Статусы `Норма/Риск/Авария` уже централизованы в `StatusService` и `status_policy`: `src/app/services/status_service.py`, `src/app/simulation/status_policy.py`.
- Пресеты `winter`, `summer`, `peak_load` уже есть в `data/scenarios/presets.json` и покрыты сценарными тестами.

## Задача 1. Расширение симуляции до 100%

Текущее состояние: 100%.

### Цель 100%

Симуляция должна быть полноценным управляемым прогоном: `Старт`, `Пауза`, `Сброс`, ручной шаг, автоматический шаг с регулируемой скоростью, остановка по горизонту, сохранение/восстановление состояния сессии, событийная трассировка всех команд.

Статус реализации Phase B: завершено. Контракт сессии v2 включает
`completed`, скорость воспроизведения, максимальное число тиков, метаданные
достижения горизонта, последнюю команду и trace-записи. Активная сессия
сохраняется в `simulation-session.json` внутри настроенного runtime directory,
валидная сессия восстанавливается при запуске приложения, поврежденный или
несовместимый snapshot безопасно сбрасывается.

### Фазы

1. Контракт сессии v2.
   - Добавить поля `playback_speed`, `max_ticks`, `horizon_reached`, `completed_at`, `last_command`.
   - Зафиксировать переходы `idle -> running -> paused -> running -> completed/reset`.
   - Сохранить обратную совместимость старых `SimulationSession`.

2. Сервисная логика.
   - В `SimulationService.tick()` не выходить за `horizon_minutes`.
   - Автоматически переводить сессию в `completed` при достижении горизонта.
   - Добавить `set_playback_speed()` и валидацию допустимых скоростей.
   - Добавить event log для `start`, `pause`, `tick`, `reset`, `completed`.

3. UI и callback.
   - Добавить контрол скорости воспроизведения и индикатор процента завершения.
   - Использовать `dcc.Interval.disabled` и `interval` для реальной скорости прогонки.
   - Запретить редактирование входных параметров только во время `running`, но разрешить просмотр и экспорт.

4. Персистентность.
   - Сохранять активную сессию в runtime directory.
   - Восстанавливать последнюю неустаревшую сессию при запуске приложения.
   - Добавить безопасный сброс поврежденного session-файла.

5. Тесты и приемка.
   - Unit: переходы статусов, автозавершение, ограничение горизонта.
   - Integration: API endpoints и event log.
   - UI smoke: старт, пауза, смена скорости, ручной шаг, сброс.

## Задача 2. Отчетность PDF/CSV до 100%

Текущее состояние: 100%.

### Цель 100%

Отчет должен быть не только файлом-дампом, а инженерным пакетом: читаемый PDF с титульной частью, KPI, статусами, таблицами, трендовыми графиками, параметрами, тревогами, метаданными и воспроизводимым CSV/manifest. Экспорт должен поддерживать preview, повторное скачивание и batch-сборку для выбранных сценариев.

Статус реализации Phase C: завершено. Контракт отчета расширен до
`scenario-report.v2`: добавлены стабильные sections/chart_specs, CSV-секции
`metadata`, `findings`, `parameters`, `state`, `status_legend`,
`status_events`, `trend`, manifest metadata/checksums/file sizes,
ReportLab PDF с таблицами и trend-графиком, preview API/dashboard flow,
прямые ссылки скачивания и batch endpoint для выбранных пресетов.

### Фазы

1. Контракт отчета v2.
   - Расширить `ScenarioReport`: `charts`, `sections`, `attachments`, `version`.
   - Явно отделить machine-readable CSV от human-readable PDF.
   - Добавить стабильный `schema_version` в manifest.

2. PDF renderer.
   - Перейти с текстового PDF на ReportLab Platypus/tables.
   - Добавить векторные trend-графики через ReportLab graphics или встроенные Plotly-изображения без новой зависимости.
   - Поддержать кириллицу шрифтом, который включен в runtime/package.

3. CSV renderer.
   - Сохранить текущий широкий CSV, но добавить отдельные CSV-секции: metadata, parameters, state, alarms, trend.
   - Добавить проверку кодировки UTF-8 и стабильного порядка строк.

4. UX/API.
   - Добавить preview отчета до записи на диск.
   - Добавить список артефактов с кнопками скачивания напрямую из dashboard.
   - Добавить batch export для нескольких пресетов.

5. Тесты и приемка.
   - Unit: report contract, CSV sections, manifest schema.
   - Integration: FastAPI `FileResponse` для CSV/PDF/manifest.
   - Artifact smoke: PDF начинается с `%PDF-`, содержит ключевые секции, CSV читается стандартным `csv`.

## Задача 3. Сравнение прогонов до/после до 100%

Текущее состояние: 100%.

### Цель 100%

Пользователь должен явно фиксировать `До` и `После`, сравнивать активный, архивный и только что рассчитанный прогон, видеть KPI/тренды/статусы/выводы, экспортировать сравнение и понимать несовместимость без ручного анализа.

Статус реализации Phase D: завершено. Сравнение поддерживает именованные
runtime-снимки `До`/`После`, сохраняет labels/notes/source metadata,
выбирает эти снимки по умолчанию, оставляет archive/active sources
доступными, строит interpretation summary и top deltas, показывает controls в
dashboard и экспортирует пакет `run-comparison.v2` с metadata,
compatibility/interpretation summary, KPI/trend deltas и русскими статусами.

### Фазы

1. Источники прогонов v2.
   - Добавить явные команды `save_as_before` и `save_as_after`.
   - Разделить transient active run и именованные snapshots.
   - Добавить пользовательские метки пары сравнения.

2. Сервис сравнения.
   - Добавить summary-интерпретацию: что улучшилось, что ухудшилось, что без изменений.
   - Добавить статус сравнения на основе худшего состояния пары и значимых дельт.
   - Сохранить текущие правила совместимости по шагу, горизонту и временной сетке.

3. UI.
   - Добавить отдельные кнопки фиксации `До`/`После`.
   - Добавить визуальный overlay трендов и таблицу top deltas.
   - Добавить понятные подсказки при несовместимости.

4. Экспорт.
   - Расширить PDF/CSV сравнения: summary, совместимость, KPI, тренды, статусы, исходные ссылки.
   - Добавить manifest schema version.

5. Тесты и приемка.
   - Unit: именованные snapshots, summary дельт, несовместимые пары.
   - UI smoke: сохранить `До`, изменить параметры, сохранить `После`, сравнить, экспортировать.
   - Integration: API build/export/download.

## Задача 4. Цветные статусы до 100%

Текущее состояние: 100%.

### Цель 100%

Статусы `Норма`, `Риск`, `Авария` должны быть единым доменным языком во всех слоях: расчет, API, dashboard, 2D/3D, отчеты, сравнение, архив, event log и документация. Никаких конкурирующих формулировок вроде `warning/предупреждение` в пользовательском тексте, кроме технических enum/API значений.

Статус реализации Phase A: завершено. `StatusService` является единым
источником пользовательских label/class/color/summary/legend, а
`src/app/ui/viewmodels/status_presenter.py` оставлен тонким compatibility-proxy.
Технические значения `normal`, `warning`, `alarm` сохранены для API/enum
контрактов, но пользовательский язык во view-model, dashboard, export,
comparison и archive закреплен как `Норма`, `Риск`, `Авария`.

### Фазы

1. Единый словарь.
   - Зафиксировать `StatusService` как единственный источник label/class/color/summary.
   - Убрать дублирующие mapping-функции или сделать их тонкими прокси.
   - Добавить статусный glossary в docs.

2. Конфигурация порогов.
   - Документировать все пороги из `StatusThresholds`.
   - Добавить runtime snapshot порогов в dashboard/API.
   - Проверить, что `config/defaults.yaml` и settings синхронизированы.

3. Покрытие UI/export.
   - Проверить все страницы dashboard, таблицы, графики, 2D и 3D.
   - Добавить цветные статусы в сравнение и архивные строки.
   - Синхронизировать PDF/CSV легенду.

4. Тесты и приемка.
   - Unit: граничные значения каждого порога.
   - Snapshot/string tests: пользовательские label только `Норма/Риск/Авария`.
   - Visual smoke: три статуса различимы и читаемы.

## Задача 5. Пресеты сценариев до 100%

Текущее состояние: 100%.

### Цель 100%

Системные пресеты `Зима`, `Лето`, `Пик нагрузки` должны оставаться стабильными, но пользователь должен уметь создавать, сохранять, переименовывать, удалять, импортировать и экспортировать собственные пресеты без изменения source-controlled `data/scenarios/presets.json`.

Статус реализации Phase E: завершено. Контракт пресетов расширен до
`scenario-preset.v2`: системные пресеты остаются `source=system` и
`locked=true`, пользовательские пресеты сохраняются в runtime-каталоге
`artifacts/user-presets`, поддерживают create/update/rename/delete/import/export,
показываются вместе с системными в `/scenarios` и доступны из dashboard без
изменения `data/scenarios/presets.json`.

### Фазы

1. Контракт пресетов v2.
   - Разделить `system` и `user` presets.
   - Добавить `schema_version`, `created_at`, `updated_at`, `source`, `locked`.
   - Запретить изменение системных пресетов из UI.

2. Сервис пользовательских пресетов.
   - Хранить user presets в runtime directory.
   - Добавить CRUD: create, update, rename, delete, import, export.
   - Валидировать параметры через `SimulationParameters`.

3. API/UI.
   - Расширить `/scenarios`: показывать system + user presets.
   - Добавить управление user presets в dashboard.
   - Оставить быстрые кнопки для `winter`, `summer`, `peak_load`.

4. Тесты и приемка.
   - Unit: загрузка system+user, защита locked presets, CRUD.
   - Integration: API сценариев.
   - UI smoke: создать пользовательский пресет из текущих параметров, применить, удалить.

## Общий порядок реализации

1. Довести статусы до единого языка, потому что они входят в отчеты, сравнение и UI.
2. Довести симуляционную сессию, потому что отчеты и сравнения должны ссылаться на стабильный прогон.
3. Довести отчеты, используя обновленные статусы и session metadata.
4. Довести сравнение, используя стабильные snapshots и улучшенный export contract.
5. Довести пользовательские пресеты как отдельный слой runtime data.

## Definition of Done пакета

- Все пять задач имеют API, UI, сервисный контракт и тесты.
- Полный `pytest` проходит.
- Для UI-задач есть unit/callback evidence и свежий browser smoke перед защитой.
- Документы `docs/05_execution_phases.md`, `docs/06_todo.md`, `docs/10_sources.md` обновлены после реализации.
- Runtime артефакты не требуют прав записи в source tree и работают через runtime directory.

## Phase F. Release readiness на 2026-05-02

Пакет M10-M14 синхронизирован как release-ready набор:

- Simulation Session v2: управление `start/pause/reset/tick/speed`, завершение горизонта, runtime persistence и event trace.
- Reporting v2: контракт `scenario-report.v2`, стабильные CSV-секции, ReportLab PDF, manifest с проверочными полями, preview/download/batch flow.
- Before/After Comparison v2: runtime-снимки `До`/`После`, default selection, compatibility summary, interpretation/top deltas и `run-comparison.v2` export package.
- Status Language Foundation: единый пользовательский словарь `Норма` / `Риск` / `Авария` при сохранении технических enum/API значений.
- User Presets v2: контракт `scenario-preset.v2`, locked system presets и runtime CRUD/import/export пользовательских пресетов.

Evidence закреплен в `.omx/plans/m10_m14_acceptance_matrix.md`. Автоматическая
база приемки: unit/integration/scenario/callback tests и полный
`python -m pytest`. Локальный browser smoke выполнен на
`http://127.0.0.1:8765/dashboard`, evidence сохранён в
`artifacts/release-readiness/2026-05-02/`; перед защитой walkthrough нужно
повторить на целевом демо-ПК.
