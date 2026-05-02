# Defense Freeze Note

Дата freeze: 2026-05-02.

## Статус

Проект готов к защите в текущем локальном окружении. Phase H подтвердила:

- full regression: `198 passed in 17.01s`;
- локальный сервер: `http://127.0.0.1:8767`;
- `/health`: `{"status":"ok","service":"pvu-diploma-project"}`;
- `/dashboard`: HTTP `200`;
- browser walkthrough: Simulation Session v2, Export Pack, Before/After
  Comparison v2 и User Presets v2 пройдены через UI;
- Demo Bundle собран через API;
- системный файл `data/scenarios/presets.json` не изменялся, временный
  пользовательский preset удалён.

Evidence: `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-final-demo-pc-evidence.md`.

## Команды на защите

Основной запуск:

```powershell
.\start.bat
```

Если нужен фиксированный порт:

```powershell
$env:AHU_SIMULATOR_PORT=8768
python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8768
```

Проверка:

```powershell
python -m pytest
```

Открыть:

- `http://127.0.0.1:<порт>/health`
- `http://127.0.0.1:<порт>/dashboard`

## 5-7 обязательных кликов

1. Открыть `/health`, затем `/dashboard`.
2. На главном экране показать статусный язык `Норма` / `Риск` / `Авария`.
3. В Simulation Session v2 нажать `Старт`, `Пауза`, `Шаг`, выбрать скорость `x2`, затем `Сброс`.
4. В Export Pack нажать `Предпросмотр`, затем `Собрать`; показать CSV/PDF/manifest.
5. В Before/After Comparison нажать `Зафиксировать До`, применить `Пик нагрузки`, нажать `Зафиксировать После`, затем показать compatibility/interpretation и export.
6. В User Presets сохранить временный preset, экспортировать JSON и удалить его.
7. В Demo Readiness показать readiness summary и Demo Bundle/latest artifacts.

## Финальные артефакты

- Phase H evidence:
  `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-final-demo-pc-evidence.md`
- Dashboard screenshots:
  `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-dashboard-smoke.png`
  `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-session-browser.png`
  `artifacts/release-readiness/2026-05-02/m10-m14-phase-h-readiness-browser.png`
- Report Pack:
  `artifacts/exports/2026-05-02/pvu-report-20260502-151838.*`
- Comparison Pack:
  `artifacts/exports/2026-05-02/pvu-comparison-20260502-151851.*`
- Demo Bundle:
  `artifacts/demo-packages/2026-05-02/pvu-demo-package-20260502-151337.zip`

## Fallback

Если браузер или WebGL ведёт себя нестабильно, не тратить время на 3D:
показывать 2D SVG-мнемосхему, KPI, тренды, Session v2, Export Pack,
Comparison, User Presets, `/health`, full regression evidence и Phase H
screenshots. 3D/WebGL не является обязательной частью MVP-защиты.
