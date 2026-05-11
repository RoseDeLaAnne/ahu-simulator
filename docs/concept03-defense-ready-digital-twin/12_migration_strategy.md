# 12. Migration Strategy

> Источник истины:
> - desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
> - tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
> - mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`

Этот документ описывает **как** перевести текущий приложение
(длинный одностраничный Dash dashboard) на concept-03 без поломки
MVP-функций, без big-bang migration и с возможностью отката в любой
момент.

## 1. Принципы

1. **Параллельное сосуществование.** `theme=legacy` (default) и
   `theme=concept03` живут одновременно. Любая конкретная пользователя
   выбирает тему через query, через настройки или через feature flag.
2. **Strangler-fig pattern.** Concept-03 — отдельный пакет
   `src/app/ui/concept03/`. Старый layout (`src/app/ui/layout.py` —
   4135 строк) **не трогаем** до завершения Phase 6 + Phase 9 sign-off.
3. **Контракт API не меняется.** Расширения — только аддитивно (новые
   query params, новые поля в pydantic-моделях с дефолтами).
4. **Тесты — barrier.** На каждой фазе зелёный pytest. Если тест
   падает — фаза не закрыта.
5. **Возможность отката.** В любой момент можно отключить
   `feature.concept03_enabled = false` и продолжать работать на legacy.
6. **Никакой потери данных.** `data/scenarios/presets.json`,
   `data/validation/*`, `artifacts/*` — read-only / append-only во
   время миграции.

## 2. Архитектурный обзор миграции

```
ДО:
  /dashboard
    └── build_dashboard_layout()             4135 строк, всё в одном
        ├── header, sidebar, main, footer
        └── post-MVP блоки: Defense Pack, Demo Readiness, Validation,
            Manual Check, Project Baseline, Export Pack, Comparison,
            Event Log

ПОСЛЕ:
  /dashboard
    ├── if theme=legacy:
    │     build_dashboard_layout()           ← остаётся как fallback
    └── if theme=concept03:
          build_concept03_shell()
            ├── header        (concept03/header.py)
            ├── left_rail     (concept03/left_rail.py)
            ├── central_canvas(concept03/central_canvas.py)
            ├── right_rail    (concept03/right_rail.py)
            ├── bottom_strip  (concept03/bottom_strip.py)
            └── footer_nav    (concept03/footer_nav.py)
                ── if defense=true:
                     swap → concept03/defense_variant/*

  существующие routers / services / domain — без изменений
  только аддитивные расширения:
    - ScenarioDefinition.icon
    - VisualizationSignalMap.bindings_version: 2 → 3
    - DemoReadinessEvaluation.secured_loop, defense_pct
    - ControlMode + 4 значения (только если включено)
    - RunComparisonService.compare(metric=)
```

## 3. Что меняется в существующих файлах

Принцип: в существующих файлах — **минимум изменений**, только
аддитивные. Если нужно крупное изменение — оно идёт в новый файл.

### 3.1. `src/app/ui/dashboard.py`

**До:** просто `mount_dashboard(...)` создаёт Dash и регистрирует
callbacks из `callbacks.py`.

**После:**
1. Чтение `feature_flags.concept03_enabled` из settings.
2. Подключение `concept03_*.css` ассетов условно
   (`assets_ignore` обновляется через flag).
3. Выбор layout-builder:
   ```python
   if request.args.get("theme") == "concept03":
       layout = build_concept03_shell(...)
   else:
       layout = build_dashboard_layout(...)
   ```
4. Регистрация дополнительных callbacks из
   `concept03/callbacks/__init__.py`.

### 3.2. `src/app/ui/callbacks.py`

**До:** все callbacks существующего layout.

**После:** не меняется кроме:
- импорт `register_concept03_callbacks(...)` (no-op если flag false).

### 3.3. `src/app/ui/layout.py`

**Не меняется** до Phase 9. После — становится `legacy_layout.py`
и помечается `@deprecated` (но остаётся как fallback).

### 3.4. `src/app/services/*`

**Аддитивные изменения только.**

| Файл | Что добавляется |
|---|---|
| `simulation_service.py` | поддержка `SEMI_AUTO`, `TEST` (Phase 3); `SCHEDULE`, `SERVICE` (Phase 7) |
| `status_service.py` | метод `dashboard_status_summary_concept03(...)` если потребуется иной формат (предположительно нет) |
| `demo_readiness_service.py` | поля `secured_loop`, `defense_pct`, метод `build_defense_checks()`, `build_defense_demo_package()` |
| `comparison_service.py` | `compare(metric=...)` query param |
| `scenario_preset_service.py` | поле `icon` в `ScenarioDefinition`; локализованные titles |
| `export_service.py` | `build_session_xlsx()`, `build_charts_pdf()`, `build_defense_export_package()` |
| `validation_service.py` | `agreement_evaluation(summary=true)` query param |

### 3.5. `src/app/api/routers/*`

| Router | Что добавляется |
|---|---|
| `scenarios.py` | query param `?breakpoint=desktop|tablet|mobile` для localized titles (необязательно) |
| `comparison.py` | `?metric=...` query param |
| `readiness.py` | `?include_secured_loop=true` query param (по умолчанию true) |
| `viewer3d.py` (новый) | `POST /viewer3d/capture-views` для 3D PNG export (Phase 7) |

### 3.6. `src/app/simulation/*`

**Минимум.**

| Файл | Что меняется |
|---|---|
| `parameters.py` | `ControlMode` enum расширяется (см. `08 §3.1`) |
| `scenarios.py` | `ScenarioDefinition` получает поле `icon: str = ""` |
| `state.py` | без изменений |
| `equations.py`, `alarms.py`, `status_policy.py` | без изменений |

### 3.7. `data/`

| Файл | Что меняется |
|---|---|
| `data/scenarios/presets.json` | каждому preset добавляется поле `icon` (одноразовая миграция, не разрушающая) |
| `data/scenarios/presets.localized.json` | новый файл с локализованными titles per breakpoint (опционально) |
| `data/validation/*` | без изменений |
| `data/visualization/scene3d.json` | расширение для новых nodes (`filter_fine`, `cooler_coil`, `silencer`, `room_supply`, +Defense Day) |

## 4. Стратегия rollout

### 4.1. Internal toggle

```
Phase 0–8 (development):
  query ?theme=concept03 — только разработчик
  default theme=legacy
```

### 4.2. Settings-based

```
Phase 6 finished:
  config/defaults.yaml: ui.theme = "concept03"   (для desktop/tablet)
  config/defaults.mobile.yaml: ui.theme = "concept03"
  
  query ?theme=legacy — fallback по требованию
```

### 4.3. Defense Day rollout

```
Phase 7 finished:
  query ?defense=true (для academic single-screen)
  default theme=concept03 (operator)
  
  config/defaults.yaml: ui.defense_day_variant = false  (по умолчанию)
  на демонстрации: ui.defense_day_variant = true
```

## 5. Стратегия отката

В любой момент можно вернуться к legacy:

1. **Hot toggle.**
   - `?theme=legacy` в URL — мгновенный fallback на старый layout.
2. **Settings-level.**
   - Изменить `config/defaults.yaml.ui.theme = "legacy"` →
     restart → старый layout по умолчанию.
3. **Code-level.**
   - Удалить `src/app/ui/concept03/` package + `concept03_*.css` —
     старый код продолжает работать, никаких side-effects.

Ничего из concept-03 не пишет в shared state, общий с legacy
(stores имеют разные `id`), поэтому конфликтов между двумя темами не
бывает.

## 6. Стратегия данных

### 6.1. Scenarios

- Новые scenario id (`baseline_office_winter`, `summer_eco`,
  `night_min_airflow`, `freeze_protection`, `airflow_check_100`,
  `nominal_mode`, `winter_mode`, `summer_mode`, `recirculation_partial`,
  `fire_smoke`) добавляются в `data/scenarios/presets.json` ТОЛЬКО при
  включении concept-03 (или при регулярной миграции, если concept-03
  становится дефолтом).
- Старые scenario id (`winter`, `midseason`, `reduced_flow`,
  `dirty_filter`, `manual_mode`) **не удаляются**: они становятся
  alias-ами на новые имена.
- Пример: `winter` → alias `baseline_office_winter`.
- Тесты `tests/scenario/test_*.py` продолжают работать на старых id.

### 6.2. ControlMode enum

- Добавление `SEMI_AUTO`, `TEST` (Phase 3) — non-breaking, потому
  что StrEnum значения не пересекаются.
- API клиенты, отправляющие `auto`/`manual`, продолжают работать.
- Тесты, проверяющие `ControlMode.AUTO == "auto"`, продолжают
  работать.
- Расширение требует обновить `equations.py` для новых
  case-веток (как минимум — fall-back на `AUTO` поведение).

### 6.3. Visualization signals

- `bindings_version` 2 → 3 — non-breaking, новые узлы
  (`filter_fine`, `cooler_coil`, `silencer`, `room_supply`).
- Старая 2D mnemonic SVG продолжает работать.
- Старые callout-bindings (`outdoor_air`, `filter_bank`, `heater_coil`,
  `supply_fan`, `supply_duct`, `room`, `recovery_unit`) сохраняются.

### 6.4. EventLog

- `EventLogService` не меняется.
- UI добавляет дополнительные категории (например,
  `concept03.defense_package_built`), которые попадают в существующий
  log.

### 6.5. Demo readiness

- `DemoReadinessEvaluation` — добавляются поля с дефолтами:
  ```python
  secured_loop: Literal["active","reduced","disabled"] = "active"
  defense_pct: int | None = None
  ```
- Существующие consumer-ы не ломаются.
- Новый метод `build_defense_checks()` возвращает другой DTO,
  поэтому не конфликтует с существующим.

## 7. Стратегия тестирования

### 7.1. Регрессия

После каждой фазы:

```powershell
.venv\Scripts\Activate.ps1
python -m pytest                       # все тесты должны быть зелёные
python -m pytest tests/unit            # фокус на ядре
python -m pytest tests/integration     # фокус на API
python -m pytest tests/scenario        # фокус на сценариях
```

### 7.2. Snapshot-сверка

```powershell
# concept-03 specific
python -m pytest tests/playwright/concept03 --update-snapshots=false
```

Папка `artifacts/playwright/concept03/phase{N}/` содержит эталонные
скриншоты и diff-отчёты.

### 7.3. Smoke на финальной фазе

```powershell
.\deploy\run-local.ps1
# вручную: открыть /dashboard?theme=concept03&page=dashboard
# вручную: проверить /dashboard?theme=concept03&defense=true
# вручную: проверить /dashboard?theme=legacy (fallback)
```

## 8. Стратегия совместимости

### 8.1. С существующим документами проекта

- `docs/02_functionality.md`, `docs/03_architecture.md` — добавляется
  ссылка на concept-03, без переписывания.
- `docs/04_roadmap.md`, `docs/05_execution_phases.md`,
  `docs/06_todo.md` — добавляется блок `P5. Concept-03`.
- `docs/13_visualization_strategy.md`,
  `docs/35_3d_visualization_upgrade_plan.md` — добавляется отметка
  «расширено concept-03 callouts overlay».
- `docs/14_defense_pack.md`, `docs/15_demo_readiness.md`,
  `docs/30_defense_presenter_script.md` — обновляются при finalize
  (Phase 9).
- Остальные документы (`docs/16_*` ... `docs/38_*`) — не меняются.

### 8.2. С CI и release pipeline

- `.github/workflows/windows-pyinstaller.yml`,
  `.github/workflows/android-capacitor.yml` — не меняются.
- `pyproject.toml` — version бьём в Phase 9 (`v3.0.0-concept03-defense`).
- `deploy/build-windows-exe.ps1` — без изменений.
- `deploy/build-mobile-debug.cmd` / `build-mobile-release-apk.cmd` —
  без изменений (просто захватывают новые ассеты).

### 8.3. С runtime артефактами

- `%LOCALAPPDATA%/AhuSimulator/exports`,
  `event-log`, `scenario-archive`, `demo-packages` — без изменений
  по структуре.
- `artifacts/simulation-session.json` — без изменений.
- `artifacts/comparison-snapshots/` — без изменений.

## 9. Стратегия для Defense Day

`Defense Day Variant` (Phase 7) включается только на показе:

1. Перед защитой (за час) — выставить
   `config/defaults.yaml.ui.defense_day_variant = true`,
   restart десктоп-приложения.
2. Открыть `/dashboard?theme=concept03&defense=true`.
3. Проверить snapshot phase7-defense (`15_qa_checklist.md §F`).
4. После защиты — вернуть toggle в `false` (по желанию).

При сбое (`webgl-error` / network / etc.):
- `?defense=false` — fallback на operator dashboard.
- `?theme=legacy` — fallback на старый dashboard.
- `start.bat` — гарантированно поднимает legacy.

## 10. Стратегия для Capacitor / mobile

1. Mobile shell (`mobile/`) использует `localhost:<port>/dashboard?theme=concept03`
   через HTTPS proxy.
2. При build APK → ассеты concept-03 **включены** в bundle (`mobile/src/assets/concept03/`).
3. Capacitor splash + status bar — обновляются под concept-03 палитру
   в Phase 8 (`mobile/capacitor.config.ts`).
4. Обновление `mobile/`-сайдер не ломает Capacitor build pipeline
   (см. `.github/workflows/android-capacitor.yml`).

## 11. Стратегия для PyInstaller / Windows EXE

1. PyInstaller spec (`deploy/ahu-simulator-desktop.spec`) **не меняется**;
   `concept03_*` ассеты лежат внутри `src/app/ui/assets/`, и PyInstaller
   их захватывает автоматически.
2. После Phase 6 — `deploy/build-windows-exe.ps1 -Clean` собирает EXE
   с concept-03 dashboard.
3. Inno Setup installer (`deploy/installer/ahu-simulator.iss`) —
   без изменений.

## 12. Last-mile checklist миграции

Перед merge в `main` каждой фазы:

- [ ] `python -m pytest` зелёный.
- [ ] Playwright snapshot phase{N} сохранён.
- [ ] Acceptance criteria phase{N} помечены пройденными.
- [ ] Documentation update (если фаза меняет публичные документы).
- [ ] Tag локально (`concept03-phase{N}-done`).

Перед release `v3.0.0-concept03-defense`:

- [ ] Все фазы (0-9) пройдены.
- [ ] Acceptance §14 пройдены.
- [ ] Demo flow проигран без замечаний.
- [ ] Freeze-note подписан.
- [ ] CI pipeline зелёный.
- [ ] EXE / APK собраны и протестированы на target machines.

## 13. Альтернативные пути миграции (rejected)

### 13.1. Big-bang rewrite на React/Next.js

**Отклонено.** Высокий риск, удваивает team-cost, не нужно для ВКР,
ломает CI и Capacitor pipeline.

### 13.2. Postponed rewrite of layout.py

**Отклонено.** 4135 строк layout.py — старый код стабилен; переписывать
сейчас нет смысла. Concept-03 живёт параллельно как отдельный пакет.

### 13.3. Полная замена legacy на concept-03

**Отклонено.** Legacy остаётся как fallback. Удаление legacy — отдельная
задача после защиты ВКР, по результатам анализа.

## 14. Ссылки

- desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
- tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
- mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`
- Фазы: `09_implementation_phases.md`
- Acceptance: `11_acceptance_criteria.md`
- Risks: `13_risks_and_mitigations.md`
- QA: `15_qa_checklist.md`
- Architecture: `docs/03_architecture.md`
- Roadmap: `docs/04_roadmap.md`
