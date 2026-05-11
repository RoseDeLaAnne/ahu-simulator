# Материалы к защите

Дата актуализации: 2026-05-02.

## Где это доступно в приложении

- В dashboard есть блок `Defense Pack` по якорю `#defense-pack`.
- Предзапусковая проверка находится в блоке `Demo Readiness` по якорю `#demo-readiness`.
- Отдельные демонстрационные контуры доступны прямо из dashboard: Simulation Session v2, Export Pack, Before/After Comparison, Scenario Archive, User Presets и Demo Bundle.
- API-контрольные точки для быстрого старта: `GET /health`, `GET /readiness/demo`, `GET /readiness/package`, `POST /readiness/package/build`.
- Последний Phase F evidence: `artifacts/release-readiness/2026-05-02/m10-m14-phase-f-evidence.md`.
- Финальный Phase G evidence сохраняется рядом: `artifacts/release-readiness/2026-05-02/m10-m14-phase-g-evidence.md`.
- Финальный Phase H freeze evidence: `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-final-demo-pc-evidence.md`.
- Короткая freeze-памятка для показа: `docs/28_defense_freeze_note.md`.

## Demo-flow на 8-10 минут

1. `0:00-0:40` - запустить приложение через `start.bat` или `.\deploy\run-local.ps1 -OpenDashboard`, озвучить URL dashboard из консоли.
2. `0:40-1:00` - проверить `GET /health`: ожидаемый ответ `{"status":"ok","service":"pvu-diploma-project"}`.
3. `1:00-1:50` - открыть `/dashboard`, показать базовый расчет, мнемосхему, KPI, тренды и статус `Норма`.
4. `1:50-2:40` - применить `winter` или `peak_load`, показать изменение параметров, тепловой нагрузки и пользовательский язык статусов `Норма` / `Риск` / `Авария`.
5. `2:40-3:40` - показать Simulation Session v2: `Старт -> Пауза -> Шаг -> скорость x2 -> Сброс`, обратить внимание на progress `elapsed/max` и блокировку редактирования только во время `running`.
6. `3:40-4:50` - открыть Export Pack: preview, build, прямые download-ссылки CSV/PDF/manifest, упомянуть контракт `scenario-report.v2`.
7. `4:50-6:10` - показать Before/After Comparison: `Зафиксировать До`, изменить режим, `Зафиксировать После`, compatibility, interpretation/top deltas и export `run-comparison.v2`.
8. `6:10-7:10` - показать User Presets v2: сохранить временный пользовательский preset, применить, экспортировать JSON и удалить; системные пресеты остаются read-only.
9. `7:10-8:00` - открыть `Demo Readiness`: preflight, browser profile, Demo Bundle и путь к runtime-артефактам.
10. `8:00-9:00` - при вопросах о достоверности открыть `Validation Basis`, `Validation Agreement` и `Manual Check`; при вопросах об архитектуре показать таблицу модулей ниже.

## Визуальный сценарий показа 2D-модели

- Начинать с устойчивого режима, чтобы 2D SVG-мнемосхема читалась как нормальный технологический тракт.
- В режиме `winter` вести взгляд по цепочке `наружный воздух -> рекуперация -> нагреватель -> приток -> помещение`.
- В режиме `dirty_filter` акцентировать узел фильтра, перепад давления и статус `Авария` или `Риск`, если выбранные параметры попадают в соответствующую зону.
- После ручного изменения параметров показать синхронное изменение SVG, summary, трендов и `Manual Check`.
- Если возникает вопрос о точках и допусках, открыть `Validation Agreement`.
- Если возникает вопрос о формулах и сценариях, открыть `Validation Basis`.
- Если WebGL или 3D-диагностика нестабильны, не задерживаться: MVP-показ опирается на 2D SVG, dashboard, API, отчеты и тесты.

## Чеклист за 15 минут до защиты

- Запустить `python -m pytest`; признак готовности - все тесты проходят, ожидаемая база сейчас `198 passed`.
- Запустить `.\start.bat` или `powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\run-local.ps1 -OpenDashboard`.
- Зафиксировать фактический URL dashboard из консоли, особенно если порт `8000` был занят.
- Проверить `http://127.0.0.1:<порт>/health`.
- Открыть `http://127.0.0.1:<порт>/dashboard` и развернуть окно на демонстрационный viewport.
- Выполнить короткий smoke: Session controls, report build/download links, before/after comparison, user preset save/delete.
- Проверить, что новые runtime-артефакты появляются в `artifacts/exports`, `artifacts/comparison-snapshots`, `artifacts/user-presets` или в desktop runtime directory.
- Держать открытыми `docs/14_defense_pack.md`, `docs/15_demo_readiness.md` и последний evidence-файл.

## Чеклист за 2 минуты до показа

- Dashboard открыт на первой вкладке, zoom браузера 100%.
- `/health` уже проверен, серверное окно не закрыто.
- В `Demo Readiness` нет блокирующих пунктов.
- Выбран спокойный стартовый режим, например `midseason` или baseline-параметры.
- Временные user presets после репетиции удалены или не мешают списку.
- Папка `artifacts/release-readiness/2026-05-02/` доступна, если нужно показать evidence.

## План восстановления

| Ситуация | Быстрое действие |
| --- | --- |
| Порт `8000` занят | Использовать URL, который вывел `start.bat` или `run-local.ps1`; скрипт сам подбирает следующий свободный порт. |
| Нужно задать порт явно | Запустить `$env:AHU_SIMULATOR_PORT=8765; python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8765`. |
| Dashboard не открылся автоматически | Открыть вручную `http://127.0.0.1:<порт>/dashboard`; сначала проверить `/health`. |
| `/health` не отвечает | Остановить старый процесс, перезапустить `start.bat`; если времени мало, показать подготовленный evidence и docs walkthrough. |
| Browser/WebGL warning | Оставить 3D как необязательный слой, перейти к 2D SVG, отчетам, comparison и validation docs. |
| Export не скачивается | Проверить build-status в Export Pack; показать CSV/PDF/manifest из `artifacts/exports/<дата>/`; при необходимости пересобрать `Demo Bundle`. |
| Runtime artifacts не пишутся | Проверить права на папку `artifacts`; для desktop/frozen режима проверить `%LOCALAPPDATA%\AhuSimulator`. |
| Полный `pytest` не успевает | Запустить быстрый набор по M10-M14 или показать последний full regression evidence из Phase F/G, затем выполнить live `/health` и dashboard smoke. |
| Нужно показать без live browser smoke | Использовать `artifacts/release-readiness/2026-05-02/` со скриншотом и evidence, затем пройти API/docs часть показа. |

## Таблица «технология -> зачем используется»

| Технология | Зачем используется |
| --- | --- |
| `Python 3.12+` | Основной язык проекта, объединяющий расчетную модель, API и локальный запуск. |
| `FastAPI` | API-контракты, health-check и модульная серверная обвязка приложения. |
| `Pydantic` | Проверка диапазонов параметров и строгая схема обмена между слоями. |
| `Dash` | Операторский экран с реактивным layout и callbacks для локальной демонстрации. |
| `Plotly` | Тренды температуры, расхода и мощности как пояснение поведения модели во времени. |
| `SVG + Dash assets` | Адаптивная 2D-мнемосхема для офлайн-показа на защите. |
| локальный `JavaScript` + clientside callbacks | Быстрое обновление SVG-сцены и browser/WebGL-диагностики без лишней серверной нагрузки. |
| `ReportLab` | PDF-отчеты `scenario-report.v2` и comparison export без новых зависимостей. |
| `pytest` | Автоматическая проверка расчетного ядра, API, сервисов и viewmodel-логики. |

## Таблица «функция -> модуль проекта»

| Функция | Модуль проекта |
| --- | --- |
| Сборка приложения и подключение API/Dashboard | `src/app/main.py`; `src/app/ui/dashboard.py` |
| Параметры модели и диапазоны | `src/app/simulation/parameters.py` |
| Физические зависимости и состояние | `src/app/simulation/equations.py`; `src/app/simulation/state.py` |
| Сценарии и системные пресеты | `src/app/simulation/scenarios.py`; `data/scenarios/presets.json` |
| Пользовательские runtime-пресеты | `src/app/services/user_preset_service.py`; `artifacts/user-presets` |
| Simulation Session v2 | `src/app/services/simulation_service.py`; `src/app/api/routers/simulation.py`; `src/app/ui/callbacks.py` |
| Reporting v2 | `src/app/services/export_service.py`; `src/app/api/routers/exports.py`; `src/app/ui/viewmodels/export_pack.py` |
| Before/After Comparison v2 | `src/app/services/comparison_service.py`; `src/app/api/routers/comparison.py`; `src/app/ui/viewmodels/run_comparison.py` |
| Единый статусный язык | `src/app/services/status_service.py`; `src/app/simulation/status_policy.py` |
| Validation Pack, Agreement, Basis и Manual Check | `src/app/services/validation_service.py`; `src/app/api/routers/validation.py`; `src/app/ui/viewmodels/validation_*`; `src/app/ui/viewmodels/manual_check.py` |
| Demo Readiness и Demo Bundle | `src/app/services/demo_readiness_service.py`; `src/app/api/routers/readiness.py`; `deploy/build-demo-package.ps1` |
| Desktop launcher | `src/app/desktop_launcher.py`; `deploy/run-desktop.ps1` |

## Ограничения модели для ВКР

- Текущая версия является учебно-обобщенной моделью ПВУ, а не подтвержденной паспортной копией конкретного объекта.
- Валидация ограничена синтетическими сценариями, эталонными точками, ручной инженерной сверкой и автотестами.
- Первая версия опирается на стационарный расчет и упрощенную динамику помещения.
- 3D-viewer архитектурно подготовлен, но зависит от WebGL и не является обязательной частью MVP-защиты.
- Проект не подключается к реальному оборудованию и не использует конфиденциальные данные предприятия.

## P5. Concept-03 «Defense-Ready Digital Twin»

Defense Day Variant для следующего этапа описан в пакете:
`docs/concept03-defense-ready-digital-twin/README.md`.

После завершения Phase 7 защита переходит со старого long-scroll
dashboard на **single-screen Defense Day Variant**:

- 5 вкладок canvas (`3D Модель / 2D Схема / Графики / Таблицы / Балансы`);
- header action toolbar (Запустить / Пауза / Стоп / Сброс) с hotkey
  `Space`/`Esc`/`1-5`;
- 5 нижних панелей: Валидация модели, Экспортный пакет для защиты,
  Сравнение сценариев, Журнал событий, Готовность к защите 96%;
- academic footer с метаданными ВКР (программа / специальность /
  профиль / кафедра / версия модели).

Запуск Defense Day Variant:

```
http://127.0.0.1:<port>/dashboard?theme=concept03&defense=true
```

Fallback: `?defense=false` или `?theme=legacy` (см.
`docs/concept03-defense-ready-digital-twin/12_migration_strategy.md → §5`).

Полный сценарий 5/7/10-минутного demo —
`docs/concept03-defense-ready-digital-twin/14_demo_script.md`.
Финальный QA-лист —
`docs/concept03-defense-ready-digital-twin/15_qa_checklist.md`.

Концепт-изображения:

- `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
- `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
- `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`

## Использование ИИ как вспомогательного инструмента

- ИИ используется для структурирования задач, ускорения черновых правок и поиска официальной документации.
- Формулы, диапазоны, сценарии и архитектурные решения проверяются и утверждаются автором проекта.
- Интеграция изменений, тестирование и интерпретация результатов выполняются внутри рабочего контура проекта.
- В проекте используются только синтетические или обезличенные данные.
