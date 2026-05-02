# Defense Handoff

Дата: 2026-05-02.

Этот файл открывать первым перед защитой. Он коротко связывает запуск,
обязательные клики, финальные артефакты и recovery-путь.

Для репетиции речи рядом подготовлены:

- `docs/30_defense_presenter_script.md` - тайминг 8-10 минут и фразы на
  каждом ключевом клике;
- `docs/31_defense_qna.md` - ожидаемые вопросы комиссии и короткие ответы.
- `docs/32_defense_seal_note.md` - финальная morning-of-defense памятка после
  dry run/seal.
- `docs/33_defense_day_checklist.md` - самый короткий operational checklist
  для дня защиты: что открыть, нажать, сказать и делать при сбое.
- `docs/34_morning_of_defense.md` - самый короткий morning-of-defense лист:
  60 секунд запуска, первая фраза, fallback и evidence.

## Статус пакета

M10-M14 находится в defense-ready/freeze состоянии:

- Phase A-M завершены;
- Phase H browser walkthrough пройден для Simulation Session v2, Export Pack,
  Before/After Comparison v2 и User Presets v2;
- последний ожидаемый full regression baseline: `198 passed`;
- финальный индекс артефактов:
  `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`.
- presenter pack для живой защиты:
  `docs/30_defense_presenter_script.md` и `docs/31_defense_qna.md`.

## Команды запуска

Основной путь:

```powershell
.\start.bat
```

Если нужен явный порт:

```powershell
$env:AHU_SIMULATOR_PORT=8768
python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8768
```

Проверить:

```powershell
python -m pytest
```

Открыть:

- `http://127.0.0.1:<порт>/health`
- `http://127.0.0.1:<порт>/dashboard`

Ожидаемый health:

```json
{"status":"ok","service":"pvu-diploma-project"}
```

## 5-7 шагов показа

1. Открыть `/health`, затем `/dashboard`; показать, что сервер жив и dashboard
   открыт.
2. На главном экране показать единый язык статусов `Норма` / `Риск` /
   `Авария`, KPI, тренды и 2D SVG-мнемосхему.
3. В Simulation Session v2 выполнить `Старт`, `Пауза`, `Шаг`, выбрать скорость
   `x2`, затем `Сброс`; проговорить progress по горизонту.
4. В Export Pack нажать `Предпросмотр`, затем `Собрать`; показать CSV, PDF и
   manifest с контрактом `scenario-report.v2`.
5. В Before/After Comparison нажать `Зафиксировать До`, применить
   `Пик нагрузки`, нажать `Зафиксировать После`; показать compatibility,
   interpretation/top deltas и export `run-comparison.v2`.
6. В User Presets сохранить временный пользовательский preset, применить или
   экспортировать JSON, затем удалить; системные presets остаются read-only.
7. В Demo Readiness показать summary и при необходимости Demo Bundle.

## Что показывать как готовые артефакты

- Phase H evidence:
  `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-final-demo-pc-evidence.md`
- Handoff index:
  `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`
- Dashboard screenshots:
  `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-dashboard-smoke.png`
  `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-session-browser.png`
  `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-readiness-browser.png`
- Scenario report pack:
  `artifacts/exports/2026-05-02/pvu-report-20260502-151838.*`
- Comparison pack:
  `artifacts/exports/2026-05-02/pvu-comparison-20260502-151851.*`
- Demo bundle:
  `artifacts/demo-packages/2026-05-02/pvu-demo-package-20260502-151337.zip`
  and `.manifest.json`.

## Recovery Pack

| Ситуация | Быстрое действие |
| --- | --- |
| Порт занят | Использовать порт, который вывел `start.bat`, или запустить с другим `AHU_SIMULATOR_PORT`. |
| Dashboard не открылся | Сначала открыть `/health`; если он `ok`, открыть `/dashboard` вручную. |
| Браузер или WebGL нестабилен | Перейти на 2D SVG, KPI, отчеты, comparison, presets и screenshots. 3D/WebGL не является обязательной частью MVP. |
| Export не скачивается | Показать уже собранные CSV/PDF/manifest из `artifacts/exports/2026-05-02/`; при времени пересобрать Export Pack. |
| Тесты не успевают | Показать Phase H/Phase I evidence и выполнить live `/health` плюс короткий dashboard click-pass. |
| Runtime artifact не появился | Проверить права на `artifacts`; для desktop/frozen режима проверить `%LOCALAPPDATA%\AhuSimulator`. |

## Что сказать про ограничения модели

Модель учебно-обобщенная: она демонстрирует структуру инженерного расчета ПВУ,
сценарии, контроль статусов, отчеты и сравнение режимов, но не является
паспортной цифровой копией конкретной установки. Валидация опирается на
синтетические сценарии, эталонные точки, ручную инженерную сверку, API smoke и
автотесты.

## После Phase I

Дальнейшие работы не входят в M10-M14 freeze. Остаются только ручной повтор
короткого click-pass на фактическом демо-ПК, если он отличается от текущей
машины, или новые scope-задачи после защиты.

## Phase J: presenter rehearsal

Phase J не меняет freeze scope и не добавляет новую разработку. Это
репетиционный слой поверх уже зафиксированного handoff: краткая речь,
пометки по кликам и Q&A для комиссии.

## Phase K: final seal

Phase K - финальная сухая репетиция упаковки перед защитой. Она сверяет
маршрут показа, речь, Q&A, evidence и recovery pack, а итоговая короткая
памятка находится в `docs/32_defense_seal_note.md`.

## Phase L: defense-day checklist

Phase L не меняет freeze/seal scope. Это одностраничный operational runbook
для момента перед выступлением: `docs/33_defense_day_checklist.md`.

## Phase M: morning sanity pass

Phase M не меняет freeze/seal scope. Это финальный утренний sanity pass и
самый короткий лист "открыть -> запустить -> показать -> fallback":
`docs/34_morning_of_defense.md`.
