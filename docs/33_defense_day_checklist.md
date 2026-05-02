# Defense Day Checklist

Дата: 2026-05-02.

Самый короткий документ для дня защиты. Открыть рядом с
`docs/29_defense_handoff.md` и держать как операционный runbook: что проверить,
что нажать, что сказать и куда отступить при сбое.

## За 15 минут

1. Открыть `docs/33_defense_day_checklist.md`, `docs/29_defense_handoff.md` и
   `docs/30_defense_presenter_script.md`.
2. Запустить приложение:

   ```powershell
   .\start.bat
   ```

3. Если нужен явный порт:

   ```powershell
   $env:AHU_SIMULATOR_PORT=8768
   python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8768
   ```

4. Открыть `http://127.0.0.1:<порт>/health`; ожидать:

   ```json
   {"status":"ok","service":"pvu-diploma-project"}
   ```

5. Открыть `http://127.0.0.1:<порт>/dashboard` и оставить вкладку готовой.
6. Если времени достаточно, запустить `python -m pytest`. Последний baseline:
   `198 passed in 19.33s` на Phase L.
7. Проверить, что временные user presets после репетиции удалены.

## За 2 минуты

1. Консоль с сервером жива, порт виден.
2. `/health` возвращает `status=ok`.
3. `/dashboard` открыт, браузер развернут, масштаб 100%.
4. Открыт handoff index:
   `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`.
5. Лишние окна и уведомления закрыты.

## 5 обязательных кликов

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
удалить`, затем Demo Readiness/Demo Bundle.

## 5 обязательных фраз

1. `Норма`, `Риск`, `Авария` - единый пользовательский язык поверх стабильных
   API-значений `normal`, `warning`, `alarm`.
2. Simulation Session v2 показывает жизненный цикл расчета: start, pause,
   manual tick, speed, horizon completion и runtime persistence.
3. `scenario-report.v2` - воспроизводимый инженерный пакет: CSV, PDF и
   manifest согласованы одним контрактом.
4. Before/After Comparison сравнивает явно зафиксированные состояния `До` и
   `После`, проверяет совместимость и объясняет, что улучшилось или ухудшилось.
5. Модель учебно-обобщенная: она демонстрирует расчетную структуру ПВУ и
   готовый инженерный workflow, но не является паспортной цифровой копией
   конкретной установки.

## Быстрый fallback

| Ситуация | Что делать |
| --- | --- |
| Порт занят | Взять порт из консоли `start.bat` или задать другой `AHU_SIMULATOR_PORT`. |
| Dashboard не открылся | Сначала открыть `/health`; если `ok`, открыть `/dashboard` вручную. |
| Export не скачивается | Показать готовые packs из `artifacts/exports/2026-05-02/`: `pvu-report-20260502-151838.*` и `pvu-comparison-20260502-151851.*`. |
| Browser/WebGL нестабилен | Перейти на 2D SVG, KPI, тренды, отчеты, comparison, presets и screenshots из `artifacts/release-readiness/2026-05-02/`. |
| Тесты не успевают | Не ждать full pytest; показать Phase H/I/K evidence и выполнить live `/health`. |

## Не трогать до защиты

- Не менять код приложения и runtime contracts.
- Не менять `data/scenarios/presets.json`.
- Не пересобирать финальные report/comparison/demo artifacts без причины.
- Не добавлять зависимости.
- После ручной репетиции удалить временные user presets.

## Если растерялся

1. Открыть этот файл и начать с `/health`.
2. Если `/health` ok, перейти на `/dashboard`.
3. Сказать первую обязательную фразу про `Норма` / `Риск` / `Авария`.
4. Пройти 5 обязательных кликов сверху вниз.
5. Для доказательств открыть handoff index:
   `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`.
