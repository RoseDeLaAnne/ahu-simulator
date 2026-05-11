# 08. Data Mapping

> Источник истины:
> - desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
> - tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
> - mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`

Этот документ — **карта связей** между UI-блоками концепта-03 и текущими
сервисами / API / domain-моделями проекта. Цель — никогда не дублировать
бизнес-логику в UI и оставить расчётное ядро (`src/app/simulation`)
неизменным.

## 1. Слои и направление потока данных

```
┌────────────────────────────────────────────────────────────┐
│  src/app/simulation/  ← physics & status policy            │
│        ↑                                                   │
│  src/app/services/    ← orchestration (read & write)       │
│        ↑                                                   │
│  src/app/api/routers/ ← FastAPI HTTP                       │
│        ↑                                                   │
│  src/app/ui/viewmodels/ ← UI-friendly DTO (read-only)      │
│        ↑                                                   │
│  src/app/ui/concept03/  ← layout + components (presentation)│
└────────────────────────────────────────────────────────────┘
                  ↓
            dcc.Stores (cache)
```

**Правило**: UI слой компонует viewmodels, не вызывает domain напрямую.

## 2. Маппинг регионов на источники данных

| Регион | UI-компонент(ы) | Backend источник | API endpoint |
|---|---|---|---|
| Header / installation title | `BrandLogoBlock`, `InstallationTitle` | `ProjectBaselineService.snapshot()` (`installation_title`, `installation_subtitle`) | `GET /project/baseline` |
| Header / status pills | `StatusPill`×2 (operator dashboard) | `StatusService.summary()` + `DemoReadinessEvaluation.overall_status` | `GET /readiness/demo` |
| Header / action toolbar | `HeaderActionToolbar` (Defense Day) | `SimulationService.session()` actions | `POST /simulation/session/start | pause | reset` |
| Header / meta pills | `HeaderMetaPills` (Defense Day) | `SimulationParameters.control_mode`, `step_minutes` | `GET /simulation/session` |
| Header / datetime | `DateTimeBlock` | clientside `Date.now()`; для frozen — `SimulationSession.updated_at` | n/a |
| Left rail / scenarios | `ScenarioCard`×N + `+` modal | `ScenarioPresetService.list_scenarios()` + `create/update/delete` | `GET /scenarios`, `POST /scenarios/users`, `PUT /scenarios/users/{id}`, `DELETE /scenarios/users/{id}` |
| Left rail / control modes | `ControlModeCard`×4 | `SimulationParameters.control_mode` | `POST /simulation/run` (через `parameters`) |
| Left rail / config | `ConfigBriefCard` | `ProjectBaselineService.snapshot().equipment_brief` | `GET /project/baseline` |
| Central canvas / 3D | `Scene3DViewport` + `CalloutTag`×N | `VisualizationSignalMap` (см. §6) | `GET /state` (или server-side render через `simulation-session-state`) |
| Central canvas / 2D | mnemonic SVG + bindings | существующая `app/ui/scene/bindings.py` | n/a (assets) |
| Central canvas / Параметры | таблица параметров | `SimulationParameters` | `POST /simulation/run` |
| Central canvas / Тренды | Plotly graph | `SimulationSession.history.points: list[TrendPoint]` | `GET /simulation/session` или `GET /trends` |
| Central canvas / Аларма | список карточек | `SimulationResult.alarms` + `EventLogService.list()` | `GET /events/log` |
| Right rail / status banner | `StatusBanner` | `StatusService.dashboard_status_summary()` | `GET /state` |
| Right rail / KPI | `KpiRow`/`KpiCard`×6 | `StatusService.build_metric_status_map()` + `SimulationState` | `GET /state` |
| Right rail / health | `HealthTile`×4 / `ComponentStatusList` | derived (`alarms` + `available_signals`) | `GET /state` |
| Right rail / alarms accordion | `AlarmsAccordion` | `SimulationResult.alarms` | `GET /state` |
| Right rail / event log accordion | `EventLogAccordion` | `EventLogService.snapshot(limit=5)` | `GET /events/log?limit=5` |
| Bottom / readiness | `ReadinessRingPanel`/`ReadinessChecksPanel` | `DemoReadinessService.build_readiness()` + `ValidationService.matrix_evaluation()` | `GET /readiness/demo`, `GET /validation/matrix` |
| Bottom / validation summary | `ValidationSummaryPanel` (Defense Day) | `ValidationService.manual_check_evaluation()` + `agreement_evaluation()` | `GET /validation/manual-check`, `GET /validation/basis` |
| Bottom / comparison | `ComparisonChartPanel` | `RunComparisonService.compare()` | `GET /comparison/snapshot`, `POST /comparison/build` |
| Bottom / event log table | `EventLogTable` | `EventLogService.snapshot(limit=5)` | `GET /events/log` |
| Bottom / reports | `ReportsPanel`/`ExportPackagePanel` | `ExportService.snapshot()` + `DemoReadinessService.build_demo_package()` | `GET /exports/result`, `POST /exports/result/build`, `POST /readiness/package/build` |
| Footer / nav | `FooterNav` (operator) | static config | n/a |
| Footer / academic | `AcademicFooter` (Defense Day) | static config | n/a |
| Footer / version | `version` | `app.__version__` (`pyproject.toml`) | `GET /health` (включает version) |
| Footer / secured-loop | `SecuredLoopPill` | `BrowserCapabilityService` + `RuntimePathResolver.is_offline()` | `GET /readiness/demo` (поле `secured_loop`) — расширение, см. §11 |

## 3. Маппинг режимов работы (макет → enum)

В концепте показано до 6 режимов. В коде `ControlMode` сейчас даёт два:
`AUTO` и `MANUAL`. План:

| UI mode (макет) | `ControlMode` enum | Реализация |
|---|---|---|
| Автоматический / АВТО | `AUTO` (existing) | как сейчас |
| Полуавтоматический | `SEMI_AUTO` (new — добавляется) | inputs частично enabled, см. §3.1 |
| Ручной / РУЧНОЙ | `MANUAL` (existing) | как сейчас |
| Тестовый / ТЕСТОВЫЙ | `TEST` (new) | инициирует test harness в `SimulationService` |
| Расписание (Defense Day only) | `SCHEDULE` (new) | использует `step_minutes`/`horizon_minutes` напрямую |
| Сервис (Defense Day only) | `SERVICE` (new) | переключает в diagnostic state |

### 3.1. Перенос на enum

```python
class ControlMode(StrEnum):
    AUTO       = "auto"
    SEMI_AUTO  = "semi_auto"
    MANUAL     = "manual"
    TEST       = "test"
    SCHEDULE   = "schedule"     # optional, Defense Day Variant
    SERVICE    = "service"      # optional, Defense Day Variant
```

API контракт остаётся обратно совместимым: legacy clients шлющие `auto`
или `manual` работают; SDK Pydantic-валидация добавит новые literal-ы.

В Phase 0 (см. `09_implementation_phases.md`) расширение `ControlMode`
делается синхронно с новой UI-моделью; pre-существующие тесты, идущие
через `auto`/`manual`, не меняются.

### 3.2. Маппинг сценариев

В концепте scenario titles разные между макетами:

| desktop | tablet | mobile |
|---|---|---|
| Базовый офис (зима) | Номинальный режим | Зимний режим |
| Лето. Экономичный | Зимний режим | Летний режим |
| Ночь. Минимум воздуха | Летний режим | (нет) |
| Защита от замерзания | Рециркуляция | (нет) |
| Проверка 100% расхода | Пожарная вентиляция | (нет) |

Объединение: текущий `data/scenarios/presets.json` дополняется новыми
scenario-сущностями (`baseline_office_winter`, `summer_eco`,
`night_min_airflow`, `freeze_protection`, `airflow_check_100`,
`fire_smoke`, `recirculation_partial`) с шифровкой:

```json
{
  "id": "baseline_office_winter",
  "title": "Базовый офис (зима)",
  "subtitle": "Активен / Базовый сценарий",
  "icon": "layout-grid",
  "tags": ["winter","office"],
  "parameters": { ... }
}
```

Поле `icon` (lucide id) добавляется в `ScenarioDefinition` (требует
изменения в `app/simulation/scenarios.py` + миграция presets.json).

В `ScenarioPresetService` подгружается локализованный title с учётом
breakpoint UI: `?breakpoint=desktop|tablet|mobile`. Сами parameters
шарятся; меняется только UI-presentation.

Альтернатива (более простая, см. `12_migration_strategy.md`): хранить
один canonical id (`baseline_office_winter`), а title-варианты
описываются в `data/scenarios/presets.localized.json` для каждого
breakpoint. Recommended.

## 4. Контракт KPI rows (operator dashboard)

| KPI id | Источник | Формула / маппинг | Unavailable handling |
|---|---|---|---|
| `kpi-row-airflow` | `SimulationState.actual_airflow_m3_h`, setpoint = `SimulationParameters.airflow_m3_h` | `value = actual`, `setpoint_text = f"Задание: {setpoint:.0f}"`, `deviation_pct = actual/setpoint*100` | если `airflow_m3_h == 0` → `Недоступно` |
| `kpi-row-pressure` | `SimulationState.filter_pressure_drop_pa` | `value = drop`, `setpoint = thresholds.filter_pressure_drop_pa.warning` | n/a |
| `kpi-row-supply-temp` | `SimulationState.supply_temp_c`, setpoint = `SimulationParameters.supply_temp_setpoint_c` | `deviation = abs(actual − setpoint)` | n/a |
| `kpi-row-humidity` | (text «Недоступно» по умолчанию) | пока нет вычисления; можно подмешать `room_humidity_pct` после расширения domain | `Недоступно` показывается до P3 (см. §11) |
| `kpi-row-recovery` | `SimulationParameters.heat_recovery_efficiency` (как proxy) | `value_pct = efficiency * 100` | `Недоступно` если efficiency = 0 |
| `kpi-row-power` | `SimulationState.total_power_kw` | `setpoint = thresholds.energy_intensity_kw_per_1000_m3_h × airflow / 1000` | n/a |

State определяется по `StatusService.build_metric_status_map()`.

## 5. Контракт KPI cards (Defense Day Variant)

Те же 4 показателя что и в концепте desktop:

| KPI card | Источник | Sparkline |
|---|---|---|
| Производительность | `actual_airflow_m3_h` | `[trend.points[-N..].airflow_m3_h]` |
| Температура притока | `supply_temp_c` | `[..supply_temp_c]` |
| Влажность притока | (расширение) | (P3) |
| Потребляемая мощность | `total_power_kw` | `[..total_power_kw]` |

Sparkline рисуется clientside через `Sparkline`-компонент: получает
list `float`, нормирует в 0..1, рисует SVG path.

## 6. VisualizationSignalMap → callouts

Текущий `build_visualization_signal_map(result)` уже формирует
`VisualizationSignalMap.nodes`, `sensors`, `flows`. Concept-03 callouts
получаются из этой карты. Новый узел: `room_supply` (для callout
«Приточный воздух»):

```python
nodes["room_supply"] = VisualElementState(
    visual_id="room_supply",
    label="Приточный воздух",
    value=f"{state.supply_temp_c:.1f} °C",
    detail=f"{int(state.actual_airflow_m3_h/3600)} м³/с",
    state=supply_state,
)
```

Mapping callout → VisualElementState (operator dashboard):

| Callout id | `VisualElementState.visual_id` |
|---|---|
| Outdoor air | `outdoor_air` |
| Фильтр грубой очистки | `filter_bank` (фильтр одного типа сейчас, далее можно расширить до `filter_coarse`/`filter_fine`) |
| Водяной нагреватель | `heater_coil` |
| Вентилятор | `supply_fan` |
| Фильтр тонкой очистки | `filter_fine` (новый) |
| Водяной охладитель | `cooler_coil` (новый) |
| Шумоглушитель | `silencer` (новый) |
| Supply air | `room_supply` |

Для Defense Day Variant добавляются: `recovery_unit`, `humidifier`,
`fan_p2`. Это означает расширение `bindings_version` с 2 → 3 (новые
visual_id регистрируются в `app/ui/scene/bindings.py`).

## 7. EventLog: компактный формат для UI

Существующий `EventLogService.snapshot()` возвращает
`EventLogSnapshot { entries: list[EventLogEntry] }`. Для UI используем:

| UI tab | Что показываем |
|---|---|
| Bottom strip `EventLogTable` | last 5 entries, columns: time / pill / message |
| Right rail (Defense Day) `EventLogAccordion` | last 7 entries |
| Mobile `MobileEventRow` × 3 | last 3 entries |

Status mapping `EventLogEntry.level → pill color`:

| `level` | pill text | color |
|---|---|---|
| `info` | Инфо | `--c03-status-info` |
| `warning` | Предупр | `--c03-status-warn` |
| `critical` (alias `Тревога`) | Тревога | `--c03-status-alarm` |

## 8. Comparison: Model vs Reality / Scenario vs Scenario

`RunComparisonService.compare(snapshot_a, snapshot_b)` возвращает
`RunComparison { metrics: list[ComparisonMetricDelta], trend_delta: list[ComparisonTrendDeltaPoint] }`.

Для UI:
- **Model vs Reality (operator dashboard)** — берёт `RunComparisonSnapshot.before`
  как «Реальные данные» (закладывается через
  `data/validation/reference_points.json`) и `after` как «Модель»;
  series 2 цвета (cyan dashed + cyan solid).
- **Scenario vs Scenario (Defense Day)** — выбор пары `(a, b)` из
  dropdown; series compare по `metric` selector.

API: `GET /comparison/snapshot?metric=supply_temp_c` (расширение —
добавляется query param `metric`).

## 9. Readiness ring / Defense readiness checks

### 9.1. ReadinessRingPanel (operator dashboard)

| Section | Значение | Источник |
|---|---|---|
| Структура модели | 100% | `DemoReadinessService.checks` filtered `category == "structure"` |
| Параметризация | 92% | `category == "parametrization"` |
| Верификация | 78% | `category == "verification"` |
| Валидация | 85% | `ValidationService.matrix_evaluation().pass_rate` |
| Документирование | 80% | `category == "documentation"` |

`overall_pct` = средневзвешенное (см. `DemoReadinessService.build_readiness()`).

### 9.2. ReadinessChecksPanel (Defense Day)

| Check | Значение | Источник |
|---|---|---|
| Модель валидирована | Да/Нет | `ValidationService.agreement_evaluation().overall_status == NORMAL` |
| Сценарии готовы | `N/M` | `len([s for s in scenarios if s.is_ready]) / len(scenarios)` |
| Отчёты сформированы | Да/Нет | `ExportService.snapshot().has_recent_export` |
| 2D схема актуальна | Да/Нет | `ProjectBaselineService.snapshot().mnemonic_up_to_date` |

`overall_pct` = `100 * sum(check.ok)/len(checks)` (= 96% если 4 из 4
зелёные плюс расширение валидации).

## 10. Reports / Export package

### 10.1. ReportsPanel (operator)

4 strate-кнопки:

| Title | Format | Source method |
|---|---|---|
| Отчёт по сценарию | PDF | `ExportService.build_scenario_report(snapshot.id)` |
| Протокол валидации | PDF | `ValidationService.build_manual_check_pdf()` |
| Сравнительный отчёт | PDF | `RunComparisonService.export(...)` |
| Данные моделирования | CSV | `ExportService.build_session_csv(session_id)` |

### 10.2. ExportPackagePanel (Defense Day)

6 file rows + CTA «Сформировать пакет»:

| Title | Format | Source |
|---|---|---|
| Паспорт установки | PDF | `ProjectBaselineService.export_passport_pdf()` |
| Описание модели | PDF | `docs/02_functionality.md` → render PDF |
| Результаты моделирования | XLSX | `ExportService.build_session_xlsx(session_id)` |
| Графики и диаграммы | PDF | `ExportService.build_charts_pdf(session_id)` |
| 2D схема и спецификация | PDF | `app/ui/assets/pvu_mnemonic.svg` → PDF |
| 3D виды и разрезы | PNG | `viewer3d.mjs.captureViews(['overview','intake','recovery','delivery','room'])` |

CTA «Сформировать пакет» вызывает `DemoReadinessService.build_demo_package()`,
которая собирает zip из всех 6 артефактов + manifest.

## 11. Defense Day-only расширения backend (P5+)

Добавления, не входящие в operator dashboard:

| Endpoint | Why | Источник в коде |
|---|---|---|
| `GET /comparison/snapshot?metric=...` | UI-фильтр по метрике | `RunComparisonService.compare(metric=...)` |
| `GET /readiness/demo` (расширение) | поле `secured_loop` (true/false), `defense_pct` | `DemoReadinessService.build_readiness()` |
| `GET /validation/agreement?summary=true` | компактная сводка checks | существует, добавить query param |
| `POST /readiness/package/build` (existing) | сборка zip | existing |
| `POST /viewer3d/capture-views` | server-side rendering 3D snapshots | new (Phase 7) |

## 12. dcc.Store-контракт

| Store id | Schema | Кто пишет | Кто читает | TTL |
|---|---|---|---|---|
| `simulation-session-state` | `SimulationSession.dict()` | `SimulationService` callbacks | KPI / callouts / trends / status / event log | until reset |
| `visualization-signals` | `VisualizationSignalMap.dict()` | viewmodel `visualization` | 3D viewport, callouts, 2D mnemonic | derived |
| `scenario-list-version` | int | scenario CRUD callbacks | left rail | persistent (sessionStorage) |
| `dashboard-page` | str | URL parser | page router | persistent (localStorage) |
| `central-canvas-tab` | str | tab-bar callback | viewport slot | persistent |
| `defense-readiness` | `DemoReadinessEvaluation.dict()` | readiness callback | bottom strip + footer pill | TTL 60 s |
| `status-summary` | `dict[str, str]` | status callback | banner + pills | TTL 30 s |
| `event-log-snapshot` | `EventLogSnapshot.dict()` | event log callback | bottom strip + accordion | TTL 30 s |
| `comparison-snapshot` | `RunComparisonSnapshot.dict()` | comparison callback | bottom panel | until user changes |
| `viewer3d-camera` | `{preset, theta, phi, distance}` | viewer3d clientside | viewer3d, pagination dots | localStorage |

## 13. Authentication / authorization

Concept-03 не вводит RBAC. User avatar и offcanvas — статичные
единственного-пользователя-локально-запущенного workflow. Если в
будущем понадобится auth — добавляется новый сервис без изменения
текущей карты.

## 14. Связь UI-id и стабильных контрактов

Стабильные id из `01_information_architecture.md §9` плюс компонент
ids из `06_components_catalog.md` обязаны быть **стабильными** —
тесты Playwright их используют. При переименовании UI-блоков
**id не меняется**, меняется только текст label.

## 15. Ссылки

- desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
- tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
- mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`
- IA: `01_information_architecture.md`
- Каталог компонентов: `06_components_catalog.md`
- Поведение: `07_interaction_design.md`
- Стратегия миграции: `12_migration_strategy.md`
- API source: `src/app/api/routers/`
- Domain source: `src/app/simulation/`
