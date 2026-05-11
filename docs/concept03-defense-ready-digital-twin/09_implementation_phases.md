# 09. Фазы внедрения

> Источник истины:
> - desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
> - tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
> - mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`

Внедрение разбито на 9 последовательных фаз (`Phase 0` — preparatory,
`Phase 8` — closeout). Каждая фаза имеет:

- **Goal** — что должно быть готово в конце,
- **Deliverables** — артефакты,
- **Files / modules** — затрагиваемые места в коде,
- **Acceptance** — формальные критерии,
- **Exit criteria** — что должно стать «зелёным» перед переходом к
  следующей фазе.

Фазы делятся на:
- **operator dashboard** — целевая повседневная раскладка
  (`tablet`/`extended desktop`/`mobile`);
- **Defense Day Variant** — academic-defense single-screen layout
  (`desktop` концепт-изображение); выкатывается отдельно в Phase 7,
  активируется toggle.

## Phase 0 — Preparation & Foundations

**Goal.** Подготовить площадку под concept-03: токены, namespace,
feature toggle.

**Deliverables.**
- `src/app/ui/concept03/` — пустой пакет (`__init__.py`);
- `src/app/ui/assets/concept03_tokens.css` — все CSS-переменные из
  `02_visual_design_system.md` без визуальных компонентов;
- `src/app/ui/assets/concept03_dashboard.css` — пустой stub;
- `src/app/ui/assets/concept03_icons.svg` — Lucide sprite (subset из
  списка в `02 §4`);
- `src/app/infrastructure/feature_flags.py` (новый) — `feature.theme`,
  `feature.concept03_enabled`, `feature.defense_day_variant`;
- `config/defaults.yaml` — `ui.theme = "legacy"` (по умолчанию),
  `ui.concept03_enabled = false`;
- блок `body.theme-concept03 { background: var(--c03-bg-deep); ... }`
  применяется только при включенном flag.

**Files / modules.**
- new: `src/app/ui/concept03/__init__.py`,
  `src/app/ui/assets/concept03_tokens.css`,
  `src/app/ui/assets/concept03_dashboard.css`,
  `src/app/ui/assets/concept03_icons.svg`,
  `src/app/infrastructure/feature_flags.py`;
- edit: `src/app/ui/dashboard.py` (подключить css при flag),
  `config/defaults.yaml`, `config/README.md`.

**Acceptance.**
- `python -m pytest` — без регрессии.
- `body.theme-concept03` подгружается через `?theme=concept03` query
  параметр на `/dashboard`, текущая страница НЕ ломается.
- Lucide-иконки рендерятся из sprite в smoke-тесте.

**Exit criteria.**
- На `?theme=legacy` (default) UI выглядит идентично main.
- На `?theme=concept03` страница рендерит существующий layout, но с
  тёмным `--c03-bg-deep` фоном (правильность токенов, не layout).

## Phase 1 — App shell & layout grid

**Goal.** Развернуть структуру 6 регионов (header / left / center /
right / bottom / footer) на новой странице `/dashboard?theme=concept03`,
без полноценного контента.

**Deliverables.**
- `src/app/ui/concept03/shell.py` — функция `build_concept03_shell(...)`,
  возвращающая `html.Div` с шестью регионами и stable id (см.
  `01_information_architecture.md §9`);
- placeholders в каждом регионе с текстом «coming soon» и нужным
  размером;
- responsive breakpoints (`mobile/tablet/desktop`) через
  `concept03_dashboard.css` и `data-breakpoint` clientside-сетёр.

**Files / modules.**
- new: `src/app/ui/concept03/shell.py`,
  `src/app/ui/concept03/regions.py`,
  `src/app/ui/concept03/page_router.py`;
- edit: `src/app/ui/dashboard.py` — выбор layout-builder по flag,
  `src/app/ui/callbacks.py` — `dashboard-page` store + URL parsing.

**Acceptance.**
- Скриншот `/dashboard?theme=concept03&page=dashboard` показывает 6
  регионов, отделённых межрегионным gap.
- Layout не ломается на 1366×768, 1500×900, 1920×1080.
- Tab key проходит по регионам в порядке header → left → center → right
  → bottom → footer.

**Exit criteria.**
- Существующая (legacy) страница продолжает работать.
- Playwright snapshot для concept03-shell сохранён в
  `artifacts/playwright/concept03/phase1/`.

## Phase 2 — Header

**Goal.** Реализовать app header (operator dashboard pattern):
brand, title, status pills, datetime, user avatar.

**Deliverables.**
- `src/app/ui/concept03/header.py` — `build_header(viewmodel)`;
- viewmodel `concept03_header.py` (новый) — собирает данные из
  `ProjectBaselineService` + `StatusService` + `DemoReadinessService`;
- callbacks (`header_callbacks.py`) для clientside-таймера,
  status-pill цвета.

**Files / modules.**
- new: `src/app/ui/concept03/header.py`,
  `src/app/ui/viewmodels/concept03_header.py`,
  `src/app/ui/concept03/header_callbacks.py`;
- edit: `src/app/ui/concept03/shell.py` — slot для header.

**Acceptance.**
- В header стабильно отображается «ЦИФРОВОЙ ДВОЙНИК ВЕНТИЛЯЦИОННОЙ
  УСТАНОВКИ П1» + sub.
- Status pills меняют цвет при ручном изменении статуса
  (через FastAPI `/state` mock).
- Datetime обновляется каждую секунду (clientside).

**Exit criteria.**
- Acceptance §11.1 (header) из `11_acceptance_criteria.md`
  пройдена.

## Phase 3 — Left rail (scenarios + modes + config)

**Goal.** Реализовать левый rail с тремя секциями и CTA.

**Deliverables.**
- `src/app/ui/concept03/left_rail.py`;
- viewmodels: `concept03_scenarios.py`, `concept03_modes.py`,
  `concept03_config.py`;
- расширение `data/scenarios/presets.json` новыми scenario id +
  опционально `presets.localized.json` (см. `08 §3.2`);
- расширение `ControlMode` enum (см. `08 §3.1`) — `SEMI_AUTO`, `TEST`
  (Phase 3 рамок); `SCHEDULE`, `SERVICE` — Phase 7;
- интеграция с `ScenarioPresetService` для CRUD пресетов через UI.

**Files / modules.**
- new: `src/app/ui/concept03/left_rail.py`,
  `src/app/ui/viewmodels/concept03_scenarios.py`,
  `src/app/ui/viewmodels/concept03_modes.py`,
  `src/app/ui/viewmodels/concept03_config.py`;
- edit: `src/app/simulation/parameters.py` (добавить enum),
  `src/app/simulation/scenarios.py` (поле `icon`),
  `data/scenarios/presets.json`;
- tests: `tests/unit/ui/concept03/test_left_rail.py`,
  `tests/integration/test_scenarios_localized.py`.

**Acceptance.**
- 5 scenario cards отрисовываются с правильными иконками.
- Click на card вызывает `POST /scenarios/{id}/run` и обновляет
  `simulation-session-state`.
- Click на mode вызывает обновление `parameters.control_mode`.
- Active card имеет cyan glow + check icon.

**Exit criteria.**
- 0 регрессий в `tests/integration/test_scenarios_*`.
- Playwright snapshot phase3 сохранён.

## Phase 4 — Right rail (status + KPI + health)

**Goal.** Реализовать правый rail с status banner, 6 KPI rows и 4 health tiles.

**Deliverables.**
- `src/app/ui/concept03/right_rail.py`;
- viewmodel `concept03_kpi.py`, `concept03_health.py`;
- KPI binding (см. `08 §4`).

**Files / modules.**
- new: `src/app/ui/concept03/right_rail.py`,
  `src/app/ui/viewmodels/concept03_kpi.py`,
  `src/app/ui/viewmodels/concept03_health.py`;
- edit: `src/app/services/status_service.py` —
  добавить `build_metric_status_map_for_concept03(result)` (если
  отличается от существующего);
- tests: `test_concept03_kpi.py`, `test_concept03_health.py`.

**Acceptance.**
- 6 KPI rows показывают актуальные значения, deviation %,
  state-цвета.
- 4 health tiles отрисовываются как 2×2.
- Status banner меняется по `StatusService.summary()`.

**Exit criteria.**
- Snapshot phase4 совпадает с tablet-концептом по геометрии.

## Phase 5 — Central canvas (tab-bar + 3D + 2D + tabs)

**Goal.** Реализовать центральный canvas с tab-bar, 3D viewport с
callouts, и оставшимися tab-content.

**Deliverables.**
- `src/app/ui/concept03/central_canvas.py`;
- `src/app/ui/concept03/scene3d_overlay.py` —
  callouts overlay layer + compass + camera tools + pagination dots;
- `src/app/ui/assets/concept03_overlay.js` — clientside positioning;
- расширение `app/ui/scene/bindings.py` — новые visual_id
  (`filter_fine`, `cooler_coil`, `silencer`, `room_supply`);
- интеграция с существующим `viewer3d.mjs` без переписывания.

**Files / modules.**
- new: `src/app/ui/concept03/central_canvas.py`,
  `src/app/ui/concept03/scene3d_overlay.py`,
  `src/app/ui/assets/concept03_overlay.js`;
- edit: `src/app/ui/scene/bindings.py`,
  `src/app/ui/viewmodels/visualization.py`,
  `src/app/ui/render_modes/scene3d.py`;
- tests: `test_concept03_callouts_positioning.py` (clientside via
  Playwright), `test_visualization_signal_map_v3.py`.

**Acceptance.**
- 8 callouts (operator dashboard) или 9 (Defense Day) корректно
  позиционируются на 3D-сцене и при orbit.
- Compass показывает реальное направление камеры.
- Tab переключение fade-in 200 ms без потери session state.
- 2D fallback срабатывает при `webgl-error`.

**Exit criteria.**
- WebGL test on baseline machine (1366×768) показывает 60 fps.
- 0 console errors в DevTools.

## Phase 6 — Bottom strip + Footer nav

**Goal.** Реализовать нижнюю ленту (4 панели) и footer-nav (operator
dashboard).

**Deliverables.**
- `src/app/ui/concept03/bottom_strip.py` — `ReadinessRingPanel`,
  `ComparisonChartPanel`, `EventLogTable`, `ReportsPanel`;
- `src/app/ui/concept03/footer_nav.py` — `FooterNav`,
  `SecuredLoopPill`;
- viewmodel `concept03_bottom.py`;
- расширение `RunComparisonService.compare(metric=...)`;
- расширение `DemoReadinessEvaluation` полем `secured_loop`.

**Files / modules.**
- new: `src/app/ui/concept03/bottom_strip.py`,
  `src/app/ui/concept03/footer_nav.py`,
  `src/app/ui/viewmodels/concept03_bottom.py`;
- edit: `src/app/services/comparison_service.py`,
  `src/app/services/demo_readiness_service.py`,
  `src/app/api/routers/comparison.py`,
  `src/app/api/routers/readiness.py`.

**Acceptance.**
- Donut ring показывает 86% (или актуальный) с анимированным fill.
- Comparison panel рисует Plotly mini-line с двумя сериями.
- Event log table показывает 5 последних событий с правильными
  pill-цветами.
- Reports panel запускает `POST /exports/result/build` и скачивает
  результат.
- Footer-nav 6 пунктов работает; Защищённый контур pill green.

**Exit criteria.**
- Playwright snapshot phase6 совпадает с tablet-концептом.
- Все API-контракты прошли integration тесты.

## Phase 7 — Defense Day Variant

**Goal.** Реализовать вариант desktop-концепта (academic defense
single-screen): 5 tabs / 5 bottom panels / control toolbar в header /
academic footer / KPI cards со sparkline / collapsible sections в
правом rail.

**Deliverables.**
- `src/app/ui/concept03/defense_variant/` — отдельный package;
  - `header_toolbar.py` (`HeaderActionToolbar`, `HeaderMetaPills`);
  - `right_rail.py` — KPI cards со sparkline + collapsible
    `ComponentStatusList`, `AlarmsAccordion`, `EventLogAccordion`;
  - `bottom_strip.py` — 5 panels (`ValidationSummaryPanel`,
    `ExportPackagePanel`, `ComparisonChartPanel`,
    `EventLogTable`, `ReadinessChecksPanel`);
  - `footer.py` — `AcademicFooter`;
  - `central_canvas.py` — 5-tabs (`3D Модель / 2D Схема / Графики /
    Таблицы / Балансы`);
- toggle: `feature.defense_day_variant = true | false`;
- расширение `Sparkline` (clientside) и `Donut` компонентов;
- `viewer3d.mjs.captureViews(...)` для 3D PNG export;
- расширение scenarios для defense-варианта (см. `08 §3.2`):
  `baseline_office_winter`, `summer_eco`, `night_min_airflow`,
  `freeze_protection`, `airflow_check_100`.

**Files / modules.**
- new: `src/app/ui/concept03/defense_variant/*`,
  `src/app/ui/assets/concept03_sparkline.js`,
  `src/app/ui/concept03/scene3d_capture.py`;
- edit: `src/app/services/scenario_preset_service.py`,
  `data/scenarios/presets.json`,
  `src/app/services/demo_readiness_service.py` —
  `build_defense_checks()` метод,
  `src/app/services/export_service.py` —
  `build_defense_export_package()` метод.

**Acceptance.**
- При `?theme=concept03&defense=true` UI рендерит desktop-концепт
  попиксельно (см. `15_qa_checklist.md`).
- 4 KPI cards имеют sparkline и delta text.
- 5 bottom panels отрисованы по концепту.
- Header toolbar: Запустить/Пауза/Стоп/Сброс работают.
- Academic footer показывает ВКР-метаданные из
  `config/defaults.yaml.academic`.
- 96% donut ring анимируется правильно.

**Exit criteria.**
- Playwright snapshot phase7-defense совпадает с
  `concept-03-defense-ready-digital-twin.png` с отклонением ≤ 2%.
- Все Phase 0-6 features продолжают работать в operator-варианте.

## Phase 8 — Mobile / responsive polish

**Goal.** Реализовать mobile-концепт и portrait-tablet режим.

**Deliverables.**
- `src/app/ui/concept03/mobile_layout.py` (см.
  `05_layout_specification_mobile.md`);
- `src/app/ui/assets/concept03_mobile.css`;
- `src/app/ui/concept03/offcanvas.py`;
- интеграция с `mobile/` Capacitor shell — splashscreen,
  status bar, safe-area;
- E2E mobile-тесты (Playwright iOS/Android emulation + реальный
  Capacitor APK install через `tooling/commands/windows/install-mobile-debug.cmd`).

**Files / modules.**
- new: `src/app/ui/concept03/mobile_layout.py`,
  `src/app/ui/concept03/mobile_components.py`,
  `src/app/ui/concept03/offcanvas.py`,
  `src/app/ui/assets/concept03_mobile.css`;
- edit: `mobile/src/styles/`, `mobile/capacitor.config.ts`,
  `tooling/commands/windows/run-mobile-backend.cmd`.

**Acceptance.**
- Mobile concept снапшот соответствует
  `concept-03-defense-ready-digital-twin-mobile.png`.
- iOS Safari, Chrome Android, Capacitor WebView рендерят без glitches.
- Bottom-nav 5 пунктов работает; off-canvas открывается / закрывается;
  swipe-to-close работает.
- Backend через HTTPS responding в Capacitor.

**Exit criteria.**
- Mobile QA из `15_qa_checklist.md §M` пройдена.
- Capacitor APK build прошёл `npm run build:release:apk`.

## Phase 9 — Closeout (документация, демо, freeze)

**Goal.** Подготовить пакет concept-03 к защите ВКР.

**Deliverables.**
- обновлённые `docs/14_defense_pack.md`, `docs/15_demo_readiness.md`,
  `docs/30_defense_presenter_script.md` под concept-03 (см.
  `14_demo_script.md`);
- demo bundle: `python -m app.cli build-demo-bundle` создаёт
  `artifacts/demo-packages/concept03-defense-bundle-YYYYMMDD.zip`;
- видеозапись demo-flow (5-7 минут) под concept-03;
- финальный freeze-note: `docs/concept03-defense-ready-digital-twin/16_defense_freeze_note.md`
  (создаётся в этой фазе, не входит в исходную нумерацию пакета).

**Files / modules.**
- edit: `docs/14_defense_pack.md`,
  `docs/15_demo_readiness.md`,
  `docs/28_defense_freeze_note.md`,
  `docs/29_defense_handoff.md`,
  `docs/30_defense_presenter_script.md`,
  `docs/31_defense_qna.md`,
  `docs/33_defense_day_checklist.md`,
  `docs/34_morning_of_defense.md`;
- new: `docs/concept03-defense-ready-digital-twin/16_defense_freeze_note.md`,
  `docs/concept03-defense-ready-digital-twin/17_changelog.md`.

**Acceptance.**
- Demo-flow проходит за 5-7 минут без регрессий.
- All defense-day checks (см. `15_qa_checklist.md §F`) green.
- Freeze-note подписан.

**Exit criteria.**
- Defence rehearsal прошла без замечаний.
- Production tag `v3.0.0-concept03-defense` создан.

## Сводная диаграмма фаз

```
Phase 0  Foundations            ──┐
Phase 1  Shell & grid             │
Phase 2  Header                   │
Phase 3  Left rail                │   operator dashboard
Phase 4  Right rail               │
Phase 5  Central canvas           │
Phase 6  Bottom strip + footer  ──┘
Phase 7  Defense Day Variant   ────  desktop concept literal
Phase 8  Mobile / responsive   ────  mobile concept literal
Phase 9  Closeout              ────  defense readiness
```

## Оценка трудоёмкости

Не предлагаются конкретные дни/часы (см. правило по тон-стайлу), но
относительная сложность фаз:

| Фаза | Сложность | Зависимости |
|---|---|---|
| 0 | S | — |
| 1 | S | 0 |
| 2 | S | 1 |
| 3 | M | 1, расширение `ControlMode` |
| 4 | M | 1, `StatusService` |
| 5 | L | 1, существующий `viewer3d` + bindings |
| 6 | M | 1, `RunComparisonService`, `DemoReadinessService`, `ExportService` |
| 7 | L | 0–6, расширения для sparkline, академические данные |
| 8 | M | 0–6, Capacitor build pipeline |
| 9 | S | все предыдущие |

`S` — small, `M` — medium, `L` — large.

## Принципы перехода между фазами

1. **No big bang.** Между фазами `theme=concept03` toggle всегда
   доступен; в любой момент можно вернуться на `legacy`.
2. **Дополняем, не заменяем.** Existing layout живёт параллельно до
   Phase 9.
3. **Тесты — стрелка перехода.** Каждая фаза заканчивается зелёным
   тест-запуском (`python -m pytest`).
4. **Snapshot-сверка.** В конце каждой фазы — Playwright snapshot,
   сравниваемый с соответствующим макетом.

## Связь с roadmap проекта

В `docs/04_roadmap.md` и `docs/05_execution_phases.md` добавляется
новый блок `P5. Concept-03 Defense-Ready Digital Twin` с подпунктами
Phase 0–9. Текущие P0–P4 не меняются.

## Ссылки

- desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
- tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
- mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`
- Каталог компонентов: `06_components_catalog.md`
- Маппинг данных: `08_data_mapping.md`
- To-do по фазам: `10_todo.md`
- Acceptance: `11_acceptance_criteria.md`
- Migration: `12_migration_strategy.md`
