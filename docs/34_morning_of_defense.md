# Morning Of Defense

Дата: 2026-05-02.

Открыть утром перед защитой. Это самый короткий лист: запустить, проверить,
показать, спокойно отступить при сбое.

## 60 секунд

1. Открыть `docs/34_morning_of_defense.md` и
   `docs/33_defense_day_checklist.md`.
2. Запустить приложение:

   ```powershell
   .\start.bat
   ```

3. Если нужен фиксированный порт:

   ```powershell
   $env:AHU_SIMULATOR_PORT=8768
   python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8768
   ```

4. Открыть `http://127.0.0.1:<порт>/health`; ожидать:

   ```json
   {"status":"ok","service":"pvu-diploma-project"}
   ```

5. Открыть `http://127.0.0.1:<порт>/dashboard`.
6. Сказать первую фразу:

   > Начинаю с health-check: backend жив, теперь показываю dashboard как
   > единый инженерный контур расчета, статусов, отчетов и сравнения режимов.

7. Идти по пяти обязательным кликам ниже.

## Открыть Первым

- `docs/34_morning_of_defense.md` - держать перед глазами утром.
- `docs/33_defense_day_checklist.md` - расширенный one-page checklist.
- `docs/30_defense_presenter_script.md` - речь и подсказки по кликам.
- `docs/31_defense_qna.md` - ответы на вопросы комиссии.
- `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md` -
  evidence и финальные артефакты.

## 5 Обязательных Кликов

1. `/health` -> `/dashboard`.
2. KPI, тренды, 2D SVG и статусы `Норма` / `Риск` / `Авария`.
3. Simulation Session v2: `Старт` -> `Пауза` -> `Шаг` -> скорость `x2` ->
   `Сброс`.
4. Export Pack: `Предпросмотр` -> `Собрать` -> CSV/PDF/manifest
   `scenario-report.v2`.
5. Before/After Comparison: `Зафиксировать До` -> `Пик нагрузки` ->
   `Зафиксировать После` -> interpretation/top deltas/export
   `run-comparison.v2`.

Если есть время: User Presets v2 `создать -> применить/экспортировать ->
удалить`, затем Demo Readiness и Demo Bundle.

## 5 Фраз

1. `Норма`, `Риск`, `Авария` - единый пользовательский язык поверх стабильных
   API-значений `normal`, `warning`, `alarm`.
2. Simulation Session v2 показывает жизненный цикл расчета: start, pause,
   manual tick, speed, horizon completion и runtime persistence.
3. `scenario-report.v2` - воспроизводимый инженерный пакет: CSV, PDF и
   manifest согласованы одним контрактом.
4. Before/After Comparison фиксирует `До` и `После`, проверяет совместимость и
   объясняет, что улучшилось или ухудшилось.
5. Модель учебно-обобщенная: она демонстрирует инженерный workflow ПВУ, но не
   является паспортной цифровой копией конкретной установки.

## Если Что-то Пошло Не Так

| Ситуация | Действие |
| --- | --- |
| Порт занят | Взять порт из консоли `start.bat` или задать другой `AHU_SIMULATOR_PORT`. |
| Dashboard не открылся | Проверить `/health`; если `ok`, открыть `/dashboard` вручную. |
| Export не скачивается | Показать готовые packs из `artifacts/exports/2026-05-02/`: `pvu-report-20260502-151838.*` и `pvu-comparison-20260502-151851.*`. |
| Browser/WebGL нестабилен | Перейти на 2D SVG, KPI, тренды, отчеты, comparison, presets и screenshots из `artifacts/release-readiness/2026-05-02/`. |
| Тесты не успевают | Не ждать full pytest; показать Phase H/I/K/L evidence и выполнить live `/health`. |

## Evidence

- Handoff index:
  `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`
- Phase H final walkthrough:
  `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-final-demo-pc-evidence.md`
- Screenshots:
  `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-dashboard-smoke.png`
  `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-session-browser.png`
  `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-readiness-browser.png`
- Scenario report pack:
  `artifacts/exports/2026-05-02/pvu-report-20260502-151838.*`
- Comparison pack:
  `artifacts/exports/2026-05-02/pvu-comparison-20260502-151851.*`
- Demo Bundle:
  `artifacts/demo-packages/2026-05-02/pvu-demo-package-20260502-151337.zip`
  and `.manifest.json`.

## Не Менять До Защиты

- Не менять код приложения и runtime contracts.
- Не менять `data/scenarios/presets.json`.
- Не пересобирать финальные report/comparison/demo artifacts без причины.
- Не добавлять зависимости.
- После ручной репетиции удалить временные user presets.

Если растерялся: `/health` -> `/dashboard` -> статусы -> Session -> Export ->
Comparison -> evidence index.
