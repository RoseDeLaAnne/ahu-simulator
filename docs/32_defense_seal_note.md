# Defense Seal Note

Дата seal: 2026-05-02.

## Финальный статус

M10-M14 находится в состоянии `defense-ready / sealed` для текущего локального
окружения. Это закрывающая памятка: она не добавляет новую разработку, а
фиксирует, что маршрут показа, речь, Q&A, evidence и recovery pack согласованы.

Свежая проверка Phase K:

- `python -m pytest`: `198 passed in 19.14s`;
- `/health` smoke на `http://127.0.0.1:8769`: `status=ok`;
- smoke-процесс остановлен после проверки.

Итог также зафиксирован в handoff index:
`artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`.

## Открыть утром первым

1. `docs/29_defense_handoff.md` - короткий маршрут запуска, кликов и recovery.
2. `docs/30_defense_presenter_script.md` - речь на 8-10 минут и подсказки по
   каждому клику.
3. `docs/31_defense_qna.md` - короткие ответы на вероятные вопросы комиссии.
4. `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md` -
   индекс финальных evidence и артефактов.
5. `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-final-demo-pc-evidence.md` -
   финальный browser/API walkthrough evidence.

## Команды запуска

Основной путь:

```powershell
.\start.bat
```

Если нужен фиксированный порт:

```powershell
$env:AHU_SIMULATOR_PORT=8768
python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8768
```

Финальная проверка:

```powershell
python -m pytest
```

## URL-шаблон

- `http://127.0.0.1:<порт>/health`
- `http://127.0.0.1:<порт>/dashboard`

Ожидаемый `/health`:

```json
{"status":"ok","service":"pvu-diploma-project"}
```

## 5 обязательных кликов

1. Открыть `/health`, затем `/dashboard`.
2. На основном экране показать KPI, тренды, 2D SVG и статусы `Норма` /
   `Риск` / `Авария`.
3. В Simulation Session v2 выполнить `Старт`, `Пауза`, `Шаг`, скорость `x2`,
   `Сброс`.
4. В Export Pack выполнить `Предпросмотр`, `Собрать`, показать CSV/PDF/manifest
   `scenario-report.v2`.
5. В Before/After Comparison зафиксировать `До`, применить `Пик нагрузки`,
   зафиксировать `После`, показать interpretation/top deltas и export
   `run-comparison.v2`.

Дополнительные клики, если есть время: User Presets v2
`создать -> применить/экспортировать -> удалить` и Demo Readiness/Demo Bundle.

## 5 фраз, которые обязательно сказать

1. `Норма`, `Риск`, `Авария` - единый пользовательский язык поверх стабильных
   API-значений `normal`, `warning`, `alarm`.
2. Simulation Session v2 показывает жизненный цикл расчета: start, pause,
   manual tick, speed, horizon completion и runtime persistence.
3. `scenario-report.v2` - это воспроизводимый инженерный пакет: CSV, PDF и
   manifest согласованы одним контрактом.
4. Before/After Comparison сравнивает явно зафиксированные состояния `До` и
   `После`, проверяет совместимость и объясняет, что улучшилось или ухудшилось.
5. Модель учебно-обобщенная: она демонстрирует расчетную структуру ПВУ и
   готовый инженерный workflow, но не претендует на паспортную цифровую копию
   конкретной установки.

## Быстрый fallback

| Ситуация | Что делать |
| --- | --- |
| Порт занят | Использовать порт из консоли `start.bat` или задать другой `AHU_SIMULATOR_PORT`. |
| Dashboard не открылся | Проверить `/health`; если `ok`, открыть `/dashboard` вручную. |
| Браузер или WebGL нестабилен | Перейти на 2D SVG, KPI, тренды, отчеты, comparison, presets и сохраненные screenshots. |
| Export не скачивается | Показать готовые CSV/PDF/manifest из `artifacts/exports/2026-05-02/`. |
| Тесты не успевают | Показать Phase H/Phase I/Phase K evidence и выполнить live `/health`. |

## Финальные evidence и artifacts

- Release evidence:
  `artifacts/release-readiness/2026-05-02/`
- Phase H evidence:
  `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-final-demo-pc-evidence.md`
- Handoff index:
  `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`
- Scenario report pack:
  `artifacts/exports/2026-05-02/pvu-report-20260502-151838.*`
- Comparison pack:
  `artifacts/exports/2026-05-02/pvu-comparison-20260502-151851.*`
- Demo Bundle:
  `artifacts/demo-packages/2026-05-02/pvu-demo-package-20260502-151337.zip`
  and `.manifest.json`.

## Больше не менять до защиты

- Не менять код приложения и runtime contracts без реального launch/evidence
  blocker.
- Не менять `data/scenarios/presets.json`.
- Не пересобирать финальные report/comparison/demo artifacts без причины.
- После ручной репетиции удалить временные user presets, чтобы список presets
  оставался чистым.
- Если целевой демо-ПК отличается от текущего окружения, выполнить только
  короткий повтор `/health`, `/dashboard` и 5 обязательных кликов.
