# 01. Информационная архитектура

> Источник истины:
> - desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
> - tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
> - mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`

## 1. Sitemap верхнего уровня

```
Защищённый контур (offline-приложение / desktop / mobile shell)
└── /dashboard ........................ Цифровой двойник П1 (ГЛАВНЫЙ ЭКРАН)
    │   tabs: 3D / Схема / Параметры / Тренды / Аларма / Документация
    ├── /dashboard?page=equipment ..... Оборудование (паспорт ПВУ, узлы)
    ├── /dashboard?page=control ...... Управление (сценарии, режимы, расписание)
    ├── /dashboard?page=analytics .... Аналитика (тренды, сравнения, отчёты)
    ├── /dashboard?page=library ...... Библиотека (пресеты, методические основания)
    └── /dashboard?page=settings ..... Настройки (профиль, статус контура, версии)
/docs (FastAPI Swagger)              .... API-документация
/health                               .... Live-проверка процесса
```

Пять пунктов нижней навигации концепта-03 — это пять разделов одного
SPA-дашборда, переключаемых через `?page=...` query parameter. Каждый раздел
живёт под единым `app-shell` и сохраняет header, footer и боковые stores.

## 2. Главный экран `/dashboard` (page=dashboard)

Главный экран — пульт «здесь и сейчас». Внутри 6 функциональных регионов:

```
┌── REGION 1. APP HEADER ─────────────────────────────────────────┐
│  Brand    Title + Subtitle    Status pills    DateTime   User   │
└─────────────────────────────────────────────────────────────────┘
┌── REGION 2. LEFT RAIL ─────┬── REGION 3. CENTRAL CANVAS ───────┬── REGION 4. RIGHT RAIL ─┐
│  СЦЕНАРИИ  (5 cards + add)  │  Tab-bar:                          │  Состояние установки    │
│  РЕЖИМЫ РАБОТЫ (4 cards)    │   3D | Схема | Параметры |         │  ─────────────────────  │
│  Configuration brief       │   Тренды | Аларма | Документация   │  Ключевые показатели    │
│  Свойства установки (CTA)   │  Sub-strip: Object · Installation │  (6 KPI rows)           │
│                              │  3D viewport with callouts        │  Общее состояние        │
│                              │  + camera tools + compass + dots  │  (4 health tiles)       │
└─────────────────────────────┴────────────────────────────────────┴─────────────────────────┘
┌── REGION 5. BOTTOM STRIP (4 panels in a row) ───────────────────────────────────────────────┐
│  Готовность к валидации │ Сравнение модель vs реальность │ Журнал событий │ Отчёты и экспорт │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
┌── REGION 6. APP FOOTER NAV (sticky) ────────────────────────────────────────────────────────┐
│  Дашборд (active) │ Оборудование │ Управление │ Аналитика │ Библиотека │ Настройки  · ver · │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

Каждый из этих регионов имеет:

- **stable id** (`#app-header`, `#left-rail`, `#central-canvas`, `#right-rail`,
  `#bottom-strip`, `#app-footer-nav`);
- **single source of truth** в backend (см. `08_data_mapping.md`);
- **acceptance criteria** в `11_acceptance_criteria.md` со ссылкой на пиксельную
  спецификацию из `03_layout_specification_desktop.md`.

## 3. Tab-bar центрального canvas

Tab-bar над сценой — ключевая часть IA. Он переключает только содержимое
центрального canvas, остальные регионы стабильны. Пять обязательных вкладок
+ одна на будущее (документация).

| Tab | Что показывает | Источник | Состояния |
|---|---|---|---|
| **3D Модель** (default) | 3D-сцена с callouts и compass | `data/visualization/scene3d.json` + GLB-ассет | loading / ok / webgl-error → fallback `Схема` |
| **Схема** | Текущая 2D SVG-мнемосхема | `assets/pvu_mnemonic.svg` + bindings | always-on (fallback) |
| **Параметры** | Таблица параметров: `manual` / `preset`, диапазоны | `SimulationParameters` + `ScenarioPresetService` | read-only / editable (по `ControlMode`) |
| **Тренды** | Plotly-графики: `supply_temp`, `room_temp`, `fan_power`, `filter_dp` | `SimulationSession.history` | empty / live / paused |
| **Аларма** | Список текущих и недавних предупреждений | `SimulationResult.alarms` + `EventLogService` | empty / warning / alarm |
| **Документация** | Карточки: «Технологическая карта», «Формулы», «Источники» | `docs/02_functionality.md`, `docs/12_validation_matrix.md`, `docs/10_sources.md` | static |

Tab-bar — основной механизм «глубоких» данных без ухода с дашборда.

## 4. Боковые регионы

### 4.1. Левая панель — оперативный контекст

Содержит **только то, что меняет режим расчёта в один клик**:

1. **Сценарии** — 5 карточек (`midseason` / `winter` / `summer` /
   `recirculation` / `fire`) + кнопка «+» (создать пользовательский
   пресет, привязка к `ScenarioPresetService.create`). Активная карточка
   подсвечена бирюзой и иконкой галочки/пульса.
2. **Режимы работы** — 4 карточки (`auto` / `semi-auto` / `manual` /
   `test`). Активный режим выделен зелёным dot-индикатором (как в концепте).
3. **Конфигурация установки** (краткая карточка): Тип установки,
   Производительность, Напор (ном.), Класс фильтрации, Рекуператор,
   Нагреватель, Охладитель, Секция увлажнения. Источник —
   `ProjectBaselineSnapshot.equipment_brief`.
4. **CTA «Свойства установки»** — открывает раздел
   `?page=equipment`.

Принцип: **левая панель не даёт никаких настроек кроме «выбрать сценарий»
и «выбрать режим»**. Тонкая настройка — через `?page=control`.

### 4.2. Правая панель — состояние и KPI

Содержит то, **на что смотрят, не нажимая**:

1. **Состояние установки** — большой бейдж: «Нормальная работа /
   Внимание / Авария» с подзаголовком («Критических отклонений нет» / список
   первых отклонений). Источник — `StatusService.summary`.
2. **Ключевые показатели** — 6 строк KPI (см. `06_components_catalog.md`,
   компонент `kpi-row`):
   - Производительность (`actual_airflow_m3_h` vs setpoint),
   - Статическое давление,
   - Температура притока (`supply_temp_c`),
   - Относительная влажность (`humidity_supply_pct`, может быть «Недоступно»),
   - Эффективность рекуперации (может быть «Недоступно»),
   - Потребляемая мощность (`total_power_kw` vs допустимое).
3. **Общее состояние** — 4 tile-карточки (Оборудование / Автоматика /
   Датчики / Безопасность). Источник — производный от `alarms` + наличия
   данных.

## 5. Нижняя лента — «defense-ready» артефакты

Четыре панели в одной строке. Это сжатые версии текущих
больших post-MVP блоков, оставленные на главном экране только в виде
«сводки + одна ключевая ссылка»:

| Bottom panel | Что внутри | Полная версия |
|---|---|---|
| Готовность к валидации | Большое 86% + ring + 5 строк (Структура модели, Параметризация, Верификация, Валидация, Документирование) + статус | `?page=analytics&tab=validation` |
| Сравнение: модель vs реальность | Мини-линия с двумя сериями + подпись + ссылка «Детальный анализ» | `?page=analytics&tab=comparison` |
| Журнал событий | 5 последних записей (Инфо / Предупр / Тревога) + ссылка «Открыть журнал» | `?page=analytics&tab=event-log` |
| Отчёты и экспорт | 4 преднастроенных отчёта (PDF/CSV) + кнопка «Сформировать отчёт» | `?page=analytics&tab=exports` |

Каждая панель в нижней ленте — **сжатый view** соответствующего полного
view-model'а, никакой дублирующей бизнес-логики.

## 6. Footer-nav (нижняя глобальная навигация)

Шесть пунктов, активный — bold + bar-индикатор сверху:

1. **Дашборд** (default) — `/dashboard?page=dashboard`.
2. **Оборудование** — `/dashboard?page=equipment`. Паспорт ПВУ, узлы,
   3D-разрезы, реестр компонентов из `ProjectBaselineSnapshot` + bindings.
3. **Управление** — `/dashboard?page=control`. Полная страница тонкой
   настройки параметров, расписание, тестовый режим, control diagnostics.
4. **Аналитика** — `/dashboard?page=analytics`. Tab’ы:
   `Тренды / Сравнение / Валидация / Отчёты / Журнал`.
5. **Библиотека** — `/dashboard?page=library`. Управление сценариями,
   методические основания, ссылки на нормативные источники, demo-bundle.
6. **Настройки** — `/dashboard?page=settings`. Профиль, статус
   «Защищённого контура», версии runtime/desktop/mobile, browser-profile,
   diagnostics.

В footer справа — версия (`Версия 2.4.1 (build 2025.05.20)` в концепте) и
status-pill **«Защищённый контур»** (зелёный = всё локально, оранжевый =
есть внешние зависимости, серый = выключено).

## 7. Глобальные stores и паттерны

В терминах Dash оставляем существующий механизм `dcc.Store`:

| Store id | Что хранит | Кто пишет | Кто читает |
|---|---|---|---|
| `simulation-session-state` | актуальная `SimulationSession` (id, status, history) | `SimulationService` | KPI rows, callouts, trends, comparison |
| `visualization-signals` | `VisualizationSignalMap` | viewmodel `visualization` | 3D scene, 2D mnemonic, callouts |
| `scenario-preset-version` | int-версия списка пресетов | callbacks scenario CRUD | sidebar scenarios |
| `dashboard-page` | `dashboard / equipment / control / analytics / library / settings` | URL parser | concept-03 page router |
| `central-canvas-tab` | `3d / mnemonic / parameters / trends / alarms / docs` | tab-bar | central canvas slot |
| `defense-readiness` | `DemoReadinessEvaluation` | `DemoReadinessService` | bottom strip + footer pill |
| `status-summary` | `StatusService.summary` | `StatusService` | right rail header, header pill, footer pill |
| `event-log-snapshot` | last N events | `EventLogService` | bottom strip event log + analytics page |

Все stores — **read-only с точки зрения UI-слоя сверху viewmodels**. UI
не имеет права менять расчётные данные напрямую; всё через services.

## 8. Управляющие потоки (data flow)

```
[ user click сценария ]
        │
        ▼
[ callback: set scenario id ]   ← /scenarios/{id}/run
        │
        ▼
[ SimulationService.apply(scenario) ]
        │
        ▼  triggers
[ simulation-session-state ]  →  KPI rows / callouts / trends / status
        │
        ▼
[ EventLogService.append() ]  →  bottom strip event log

[ user click camera preset ]
        │
        ▼
[ clientside callback ]  →  3D viewer (no backend)
```

Архитектурный принцип: **UI-обновления, не меняющие физику, идут clientside**
(переключение tab, camera preset, hover callouts, page switch). UI-обновления,
меняющие расчёт, идут через FastAPI и backend services.

## 9. Внешние ссылки и якоря

- `#app-header` / `#left-rail` / `#central-canvas` / `#right-rail` /
  `#bottom-strip` / `#app-footer-nav` — стабильные id для тестов и Playwright.
- Каждый KPI row имеет id вида `kpi-row-airflow`, `kpi-row-pressure`,
  `kpi-row-supply-temp`, `kpi-row-humidity`, `kpi-row-recovery`,
  `kpi-row-power`. Это нужно и для тестов, и для clientside-update.
- Каждая bottom-panel имеет id вида `bottom-panel-readiness`,
  `bottom-panel-comparison`, `bottom-panel-event-log`,
  `bottom-panel-reports`.
- Footer-nav пункты: `footer-nav-dashboard`, `footer-nav-equipment`,
  `footer-nav-control`, `footer-nav-analytics`, `footer-nav-library`,
  `footer-nav-settings`.

Эти id фиксируются как контракт между UI и тестами в `15_qa_checklist.md`.
