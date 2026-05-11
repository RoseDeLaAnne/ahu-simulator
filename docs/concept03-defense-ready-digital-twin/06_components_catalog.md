# 06. Каталог UI-компонентов

> Источник истины:
> - desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
> - tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
> - mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`

Этот каталог — контракт между UI-кодом и спецификациями раскладок
(`03/04/05_layout_specification_*.md`). Все компоненты живут в
`src/app/ui/concept03/` и опираются на токены из
`02_visual_design_system.md`.

В каждом разделе:
- **Назначение** — для чего компонент;
- **Props** — параметры (Pythonic snake_case);
- **States** — визуальные состояния;
- **HTML/Dash mapping** — целевые элементы;
- **CSS hooks** — классы для тестов;
- **Источники концепта** — где увидеть в макете.

---

## A. Контейнеры верхнего уровня

### A.1. `AppShell`

**Назначение.** Корневой layout c CSS-grid из 6 областей.

**Props.**
```python
class AppShellProps:
    page: Literal["dashboard","equipment","control","analytics","library","settings"]
    breakpoint: Literal["mobile","tablet","desktop"]
    theme: Literal["concept03","legacy"]    # для миграции (см. 12)
    defense_variant: bool = False           # включает Defense Day Variant
    children: dict[str, list]               # header / left / center / right / bottom / footer
```

**States.** `loading`, `ready`, `error`, `defense-mode`.

**Mapping.**
```python
html.Div(
    id="app-shell",
    className=f"c03-shell c03-shell--{breakpoint} theme-concept03",
    children=[
        children["header"],
        html.Div(className="c03-main-row", children=[
            children["left"], children["center"], children["right"]
        ]),
        children["bottom"],
        children["footer"],
    ],
)
```

CSS hook: `body.theme-concept03 .c03-shell`.

Источник: все три макета.

---

### A.2. `Region`

Слот для каждой из 6 областей. Тривиально оборачивает `html.Div` с
правильным id и `data-region` атрибутом для тестов.

```python
def Region(region_id: str, *, label: str, children) -> html.Div: ...
```

States: `default`, `disabled` (на mobile при `safe-area`).

---

## B. Header

### B.1. `BrandLogoBlock`

**Props.**
```python
brand_short: str = "К-АСКАД ГРУП"
brand_full: str  = "ООО «НПО «Каскад-ГРУП»"
href: str | None = "?page=settings"
size: Literal["sm","md","lg"] = "md"
```

States: `static`, `link-hover`, `compact` (mobile).

Mapping: SVG иконка слева + 2-line text block; на mobile compact — иконка
без сопровождающего текста.

CSS hook: `.c03-brand`, `.c03-brand--compact`.

Источник: header в desktop/tablet/mobile.

---

### B.2. `InstallationTitle`

**Props.**
```python
title_uppercase: str       # «ЦИФРОВОЙ ДВОЙНИК ВЕНТИЛЯЦИОННОЙ УСТАНОВКИ П1»
subtitle: str | None       # «Моделирование работы приточной установки»
status_dot: Literal["normal","warning","alarm"] | None  # для mobile
```

States: `static`, `truncated` (на 1024+).

Mapping: 2-line block; на mobile — `display:flex` row с dot + sub.

CSS hook: `.c03-installation-title`.

Источник: header center в desktop/tablet, hero-section в mobile.

---

### B.3. `HeaderActionToolbar`  *(Defense Day Variant)*

**Назначение.** Блок «Запустить / Пауза / Стоп / Сброс» в header desktop
макета.

**Props.**
```python
session_status: SimulationSessionStatus
on_start: Callable
on_pause: Callable
on_stop: Callable
on_reset: Callable
disabled_when_running: bool = True
```

States: derived from `session.actions` (`can_start`, `can_pause`,
`can_reset`, `can_resume`).

Mapping:
```python
html.Div(className="c03-action-toolbar", children=[
    Button("Запустить", icon="play",  variant="primary",   id="header-btn-start"),
    Button("Пауза",     icon="pause", variant="secondary", id="header-btn-pause"),
    Button("Стоп",      icon="square",variant="secondary", id="header-btn-stop"),
    Button("Сброс",     icon="rotate-ccw", variant="ghost",  id="header-btn-reset"),
])
```

CSS hook: `.c03-action-toolbar`, `[data-defense-variant="true"] .c03-action-toolbar`.

Источник: header в desktop макете (только Defense Day Variant).

---

### B.4. `HeaderMetaPills`

**Назначение.** Двухрядный блок справа от toolbar в desktop:
«Режим: АВТО», «Шаг модели: 60 с».

**Props.**
```python
control_mode: ControlMode
step_minutes: int
```

States: `normal`, `manual` (highlight value).

Mapping: 2 «pill»-блока, label muted, value 13px 700.

CSS hook: `.c03-header-meta`.

Источник: header в desktop.

---

### B.5. `StatusPill` *(operator dashboard pattern)*

**Назначение.** «Режим готовности» / «Синхронизация» — header pills
tablet-варианта.

**Props.**
```python
class StatusPillProps:
    icon: str                 # lucide id
    title: str                # «РЕЖИМ» / «СИНХРОНИЗАЦИЯ»
    sub: str                  # «ГОТОВНОСТИ» / «Активна»
    state: Literal["ok","warn","alarm","muted"]
```

States: `ok` (green), `warn` (amber), `alarm` (red), `muted` (grey).

Mapping: pill 36×… с иконкой слева 18 px и 2-line label.

CSS hook: `.c03-status-pill`, `.c03-status-pill--ok|warn|alarm|muted`.

Источник: header в tablet.

---

### B.6. `DateTimeBlock`

**Props.** `now: datetime`, `format: str = "DD.MM.YYYY HH:MM:SS"`.

States: `live` (clientside-tick), `frozen` (paused).

Mapping: 2-line block (date 13px / time 18px) или 1-line (`08.05.2026 14:35:22`)
в зависимости от breakpoint.

CSS hook: `.c03-datetime`.

---

### B.7. `UserAvatar`

**Props.**
```python
initials: str = "S"           # от user-name
href: str | None = "?page=settings"
```

States: `default`, `hover`, `with-status-dot` (если active session).

Mapping: круг 36 (desktop/tablet) / 32 (mobile) с инициалами или
lucide `user`.

---

### B.8. `HeaderIconLink`  *(Defense Day Variant)*

«Экспорт / Отчёт / Справка» — три иконки-ссылки справа в desktop.

**Props.** `icon: str`, `label: str`, `href: str`.

States: `default`, `hover`, `active` (current page).

Mapping: lucide icon 18 + label 11px under-bar.

---

## C. Left rail

### C.1. `SectionEyebrow`

**Назначение.** Заголовок секции uppercase (`СЦЕНАРИИ`, `РЕЖИМЫ РАБОТЫ`,
`КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ` …).

**Props.** `label: str`, `right_slot: ReactNode | None`.

States: `static`.

Mapping: row с label 11px ls 0.18em uppercase muted + right slot
(кнопка `+` или dropdown).

CSS hook: `.c03-section-eyebrow`.

---

### C.2. `ScenarioCard`

**Назначение.** Карточка сценария в `СЦЕНАРИИ` секции.

**Props.**
```python
class ScenarioCardProps:
    scenario_id: str
    title: str
    sub: str                              # «Активен», «Изменён: 07.05.2026»
    icon: str                             # lucide id
    is_active: bool
    is_user_preset: bool                  # rendered chip «Custom»
    on_click: Callable
```

States: `default`, `hover`, `active` (cyan glow + check icon),
`user-preset` (small chip).

Mapping:
```html
<div class="c03-scenario-card c03-scenario-card--active">
  <i class="lucide lucide-snowflake"></i>
  <div class="title">Зимний режим</div>
  <div class="sub">Низкие температуры</div>
  <i class="active-check lucide lucide-check"></i>
</div>
```

CSS hook: `.c03-scenario-card`.

Источники: tablet — «Номинальный режим (Базовый сценарий)»,
desktop — «Базовый офис (зима)», mobile — dropdown picker.

---

### C.3. `ControlModeCard`

**Назначение.** Карточка режима работы.

**Props.**
```python
class ControlModeCardProps:
    mode_id: Literal["auto","semi_auto","manual","test","schedule","service"]
    title: str
    sub: str
    icon: str
    is_active: bool
    has_pulse: bool = False                # для active mode
```

States: `default`, `hover`, `active` (green dot + pulse), `disabled`.

Mapping: аналогичен `ScenarioCard`, но dot 8 px справа.

CSS hook: `.c03-mode-card`.

Источники: tablet — 4 mode cards (`Автоматический`, `Полуавтоматический`,
`Ручной`, `Тестовый`); desktop — `АВТО`, `РУЧНОЙ`, `РАСПИСАНИЕ`,
`СЕРВИС`. Маппинг между макетами и текущими `ControlMode`-enum-ами
описан в `08_data_mapping.md §3`.

---

### C.4. `ConfigBriefCard`

**Назначение.** «Конфигурация установки» — kv-список.

**Props.**
```python
items: list[tuple[str, str]]              # (key, value)
collapsible: bool = False                  # tablet: True
```

States: `expanded`, `collapsed` (tablet).

Mapping: `dl > dt/dd`-список; на tablet оборачивается в `<details>`.

CSS hook: `.c03-config-brief`.

---

### C.5. `CtaButton`  (used as «Свойства установки» / «Управление сценариями»)

**Props.**
```python
label: str
icon_right: str | None = "arrow-right"
variant: Literal["primary","secondary","tertiary"] = "secondary"
href: str | None = None
on_click: Callable | None = None
disabled: bool = False
```

States: `default`, `hover`, `pressed`, `disabled`.

CSS hook: `.c03-btn`, `.c03-btn--primary`, `.c03-btn--secondary`, `.c03-btn--tertiary`.

---

## D. Central canvas

### D.1. `CanvasSubStrip`

«Объект … | Установка …» + camera tools + compass.

**Props.**
```python
object_label: str                         # «Учебно-производственный корпус, помещ. 1.02»
installation_label: str                   # «П1 (Приточная)»
camera_tools: list[CameraToolProps]
compass: bool = True
```

States: `static`.

CSS hook: `.c03-canvas-substrip`.

---

### D.2. `CanvasTabBar`

**Props.**
```python
tabs: list[TabItem]                       # [{id, label, disabled}]
active_id: str
on_change: Callable
```

States: `default`, `active` (bottom-bar 2px), `disabled`.

CSS hook: `.c03-canvas-tabbar`, `.c03-canvas-tabbar__item--active`.

В operator dashboard pattern — 6 tabs; в Defense Day Variant — 5 tabs
(`3D Модель / 2D Схема / Графики / Таблицы / Балансы`).

---

### D.3. `Scene3DViewport`

Wrapper над текущим `viewer3d.mjs` с поддержкой callouts overlay.

**Props.**
```python
glb_url: str
camera_preset: str
control_mode: ControlMode
callouts: list[CalloutTagProps]
compass: bool = True
vignette: bool = True
on_camera_change: Callable
```

States: `loading`, `ready`, `webgl-error → fallback`, `paused`.

CSS hook: `.c03-scene-viewport`.

Контракт с `assets/viewer3d.mjs`: тот же formatter, что в текущем
`scene3d.py`, плюс `signals.callouts` (см. `08_data_mapping.md`).

---

### D.4. `CalloutTag`  *(desktop/tablet)*

**Назначение.** Подпись на 3D-сцене с leader-line.

**Props.**
```python
class CalloutTagProps:
    callout_id: str                       # «filter-fine», «heater»
    title: str                            # «Фильтр F7»
    rows: list[CalloutRow]                # [{label, value, unit}]
    anchor_world: tuple[float,float,float]
    state: Literal["ok","warn","alarm"]
    side: Literal["top","bottom","left","right","auto"] = "auto"
```

States: `ok`, `warn`, `alarm`, `hover` (chevron expands), `selected`.

Mapping: HTML overlay 12-13px, leader-line — SVG. Позиционирование —
clientside через `viewer3d_bridge.js` (см. `07_interaction_design.md §5`).

CSS hook: `.c03-callout`, `.c03-callout--warn`, `.c03-callout--alarm`.

---

### D.5. `CalloutTagMobile`

Mobile-версия: 28-32 px pill, 1-2 строки только, без chevron.

**Props.** аналогичны `CalloutTagProps`, но `rows` ограничен 1-2.

CSS hook: `.c03-callout--mobile`.

---

### D.6. `CompassWidget`

**Props.**
```python
heading_deg: float = 0                    # rotation
size: Literal["sm","md"] = "md"           # 28 / 56
```

States: `static`.

Mapping: SVG крест 4 направления; на desktop — внутри 3D viewport
top-right.

CSS hook: `.c03-compass`.

---

### D.7. `CameraToolButton`

**Props.** `tool_id: str`, `icon: str`, `label_aria: str`,
`active: bool`, `on_click`.

Tool ids:
- `view-orbit` (orbit / drag),
- `view-fit`   (fit-to-bounds),
- `view-fullscreen`,
- `view-split` *(Defense Day Variant)* — split AHU + room view,
- `view-layers` *(Defense Day Variant)* — layer toggle.

States: `default`, `active`, `disabled`.

CSS hook: `.c03-camera-tool`.

---

### D.8. `LayersDropdown`  *(Defense Day Variant)*

**Props.**
```python
class LayersDropdownProps:
    options: list[LayerToggle]            # [{id, label, visible}]
    on_toggle: Callable
```

States: `closed`, `open`, `applied`.

Mapping: dropdown с чекбоксами.

CSS hook: `.c03-layers-dropdown`.

---

### D.9. `CanvasPaginationDots`

**Props.** `count: int`, `active: int`, `on_click: Callable`.

CSS hook: `.c03-canvas-dots`.

---

## E. Right rail

### E.1. `StatusBanner`

**Props.**
```python
class StatusBannerProps:
    state: Literal["normal","warning","alarm"]
    title: str                            # «НОРМАЛЬНАЯ РАБОТА»
    sub: str                              # «Критических отклонений нет»
    accent_icon: str = "shield-check"
    action_href: str | None = "?page=analytics&tab=alarms"
```

States: `normal`, `warning`, `alarm`.

CSS hook: `.c03-status-banner`, `.c03-status-banner--warn|alarm`.

Источники: правый rail tablet (большой banner), правый rail desktop
(eyebrow + green pill).

---

### E.2. `KpiRow`

**Назначение.** Строка KPI в правом rail (operator dashboard).

**Props.**
```python
class KpiRowProps:
    kpi_id: str                           # «kpi-row-airflow»
    icon: str                             # lucide
    label: str                            # «Производительность»
    value_text: str                       # «6 250»
    unit: str                             # «м³/ч»
    setpoint_text: str | None             # «Задание: 6 300»
    deviation_pct: float | None           # 99 → progress 99%
    state: Literal["normal","warning","alarm","unavailable"]
```

States: `normal`, `warning`, `alarm`, `unavailable` (text «Недоступно»).

Mapping: 3-row card (label, big value, progress bar).

CSS hook: `.c03-kpi-row`, `.c03-kpi-row--warn|alarm|unavailable`.

Источник: правый rail tablet.

---

### E.3. `KpiCard`  *(Defense Day Variant)*

**Назначение.** Карточка KPI с sparkline (правый rail desktop).

**Props.**
```python
class KpiCardProps(KpiRowProps):
    sparkline: list[float]                # последние N точек
    sparkline_color: Literal["ok","warn","alarm"] = "ok"
    delta_text: str | None                # «+1.0», «100 %»
```

States: `normal`, `warning`, `alarm`, `unavailable`.

Mapping: 4-row card (label / value+delta / sparkline / setpoint).

CSS hook: `.c03-kpi-card`.

Источник: правый rail desktop.

---

### E.4. `KpiTileMobile`

Mobile квадратная карточка 87×88. Уменьшенная версия `KpiCard` без
sparkline.

CSS hook: `.c03-kpi-tile`.

---

### E.5. `HealthTile`

**Props.**
```python
class HealthTileProps:
    health_id: Literal["equipment","automation","sensors","safety"]
    title: str
    sub: str                              # «Исправно» / «Сервис»
    icon: str
    state: Literal["normal","warning","alarm"]
```

States: 3 status-цвета. Side-stripe 4 px по статусу.

CSS hook: `.c03-health-tile`.

Источник: правый rail tablet (`ОБЩЕЕ СОСТОЯНИЕ` 2×2).

---

### E.6. `ComponentStatusList`  *(Defense Day Variant)*

**Назначение.** Аккордеон «СТАТУС КОМПОНЕНТОВ» в desktop правый rail.

**Props.**
```python
items: list[ComponentStatus]              # [{label, value, unit, state}]
expanded: bool = True
```

States: `expanded`, `collapsed`.

Mapping: header row + list-rows.

CSS hook: `.c03-component-status-list`.

---

### E.7. `AlarmsAccordion`  *(Defense Day Variant)*

**Назначение.** «АКТИВНЫЕ АЛАРМЫ» аккордеон с числом.

**Props.** `count: int`, `expanded: bool`, `items: list[AlarmEntry]`.

States: `count==0` → green pill «0»; `count>0` → orange/red pill.

CSS hook: `.c03-alarms-accordion`.

---

### E.8. `EventLogAccordion`  *(Defense Day Variant)*

Аккордеон с компактным журналом событий (5-7 строк) в правый rail
desktop.

CSS hook: `.c03-event-log-accordion`.

---

## F. Bottom strip

### F.1. `BottomPanel`

Базовый контейнер для каждой нижней панели.

**Props.**
```python
panel_id: str
title_uppercase: str
right_slot: ReactNode | None              # dropdown / link
children: ReactNode
```

States: `default`, `loading`, `error`.

CSS hook: `.c03-bottom-panel`.

---

### F.2. `ReadinessRingPanel`  *(operator dashboard)*

«Готовность к валидации 86%».

**Props.**
```python
overall_pct: int
sections: list[ReadinessSection]          # [{label, pct, state}]
status_text: str
status_state: Literal["normal","warning","alarm"]
```

States: производные от `DemoReadinessEvaluation`.

CSS hook: `.c03-readiness-ring`.

---

### F.3. `ReadinessChecksPanel`  *(Defense Day Variant)*

«ГОТОВНОСТЬ К ЗАЩИТЕ 96%» — donut + 4 yes/no checks.

**Props.**
```python
overall_pct: int
checks: list[ReadinessCheck]              # [{label, value_text, ok}]
cta_label: str = "Открыть чек-лист защиты"
cta_href: str = "?page=analytics&tab=defense-checklist"
```

CSS hook: `.c03-readiness-checks`.

---

### F.4. `ValidationSummaryPanel`  *(Defense Day Variant)*

«ВАЛИДАЦИЯ МОДЕЛИ» — список балансов и зелёная metka «МОДЕЛЬ
ВАЛИДИРОВАНА».

**Props.**
```python
items: list[ValidationItem]               # [{label, value_text, ok}]
overall_label: str = "МОДЕЛЬ ВАЛИДИРОВАНА"
overall_state: Literal["normal","warning","alarm"]
generated_at: datetime
```

CSS hook: `.c03-validation-summary`.

---

### F.5. `ComparisonChartPanel`

«СРАВНЕНИЕ: МОДЕЛЬ vs РЕАЛЬНОСТЬ» / «СРАВНЕНИЕ СЦЕНАРИЕВ».

**Props.**
```python
mode: Literal["model_vs_reality","scenario_vs_scenario"]
metric_label: str                         # «Температура приточного воздуха, °С»
series: list[Series]                      # [{label, points, dashed}]
right_slot: ReactNode | None              # dropdown сценариев
cta_label: str = "Детальный анализ"
cta_href: str = "?page=analytics&tab=comparison"
```

CSS hook: `.c03-comparison-panel`.

---

### F.6. `EventLogTable`

«ЖУРНАЛ СОБЫТИЙ» — компактная таблица последних N записей.

**Props.**
```python
entries: list[EventLogEntry]              # [{timestamp, level, message}]
right_slot: ReactNode | None              # dropdown «Все события»
cta_label: str = "Открыть журнал"
cta_href: str = "?page=analytics&tab=event-log"
```

States: `empty`, `loaded`.

CSS hook: `.c03-event-log-table`.

---

### F.7. `ReportsPanel`

«ОТЧЁТЫ И ЭКСПОРТ».

**Props.**
```python
rows: list[ReportRow]                     # [{title, format, on_click}]
cta_label: str = "Сформировать отчёт"
on_generate: Callable
```

CSS hook: `.c03-reports-panel`.

---

### F.8. `ReportRow`

**Props.** `title: str`, `format: Literal["PDF","XLSX","CSV","PNG"]`,
`on_click: Callable`.

States: `default`, `hover`, `loading`, `done`.

CSS hook: `.c03-report-row`.

---

### F.9. `ExportPackagePanel`  *(Defense Day Variant)*

«ЭКСПОРТНЫЙ ПАКЕТ ДЛЯ ЗАЩИТЫ» — список из 6 файлов + CTA «Сформировать
пакет» (использует существующий `DemoReadinessService.build_demo_package`).

**Props.**
```python
items: list[PackageItem]
on_build: Callable
last_build_at: datetime | None
```

CSS hook: `.c03-export-package`.

---

## G. Footer-nav (operator dashboard)

### G.1. `FooterNav`

**Props.**
```python
items: list[FooterNavItem]                # [{id, label, icon, href}]
active_id: str
right_slot: ReactNode | None              # version pill, secured-loop pill
```

CSS hook: `.c03-footer-nav`.

---

### G.2. `FooterNavItem`

**Props.** `id`, `label`, `icon`, `href`, `is_active`, `badge_count?`.

CSS hook: `.c03-footer-nav__item`.

---

### G.3. `SecuredLoopPill`

**Props.** `state: Literal["active","reduced","disabled"]`.

States: green / amber / muted.

CSS hook: `.c03-secured-loop-pill`.

Источник: footer в tablet.

---

### G.4. `AcademicFooter`  *(Defense Day Variant)*

**Назначение.** Replace footer-nav на desktop defense-вариант:

```
ВКР 2026  |  09.04.01 Информатика и ВТ  |  Профиль: ...  |  Кафедра: ...   Версия: 1.3.2  ✓ Сохранено
```

**Props.**
```python
class AcademicFooterProps:
    program: str = "ВКР 2026"
    speciality: str = "09.04.01 Информатика и вычислительная техника"
    profile: str = "Информационное и программное обеспечение..."
    department: str = "Информационные технологии и системы управления"
    version: str = "1.3.2"
    saved: bool = True
```

CSS hook: `.c03-academic-footer`.

Источник: footer в desktop макете.

---

## H. Mobile-специфичные

### H.1. `MobileHeroBar`

«Приточная вентиляционная установка П1 + В работе + 3D▾» (см. `05`).

CSS hook: `.c03-mobile-hero`.

---

### H.2. `ScenarioPickerCardMobile`

Карточка scenario picker с dropdown.

CSS hook: `.c03-scenario-picker-card`.

---

### H.3. `ReadinessSmallCardMobile`

«Готовность к защите 92%» — donut 72×72 + 4 чекбокс-строки.

CSS hook: `.c03-readiness-small`.

---

### H.4. `ComparisonTableMobile`

4×2 grid сравнения сценариев.

CSS hook: `.c03-comparison-table`.

---

### H.5. `MobileEventRow`

Строка журнала с цветной иконкой слева.

CSS hook: `.c03-mobile-event-row`.

---

### H.6. `ExportShortcutGrid`

Row из 4 кнопок (Отчёт / Протокол / Сравнительный / Экспорт CSV).

CSS hook: `.c03-export-shortcut-grid`.

---

### H.7. `MobileBottomNav`

5 пунктов sticky.

CSS hook: `.c03-mobile-bottom-nav`.

---

### H.8. `OffCanvasMenu`

Off-canvas справа 280 px (см. `05_layout_specification_mobile.md §10`).

CSS hook: `.c03-offcanvas`.

---

## I. Утилитарные

### I.1. `Icon`

Wrapper над lucide SVG sprite (`assets/concept03_icons.svg`).

```python
def Icon(name: str, *, size: int = 18, className: str = "") -> html.I: ...
```

---

### I.2. `Badge`

Для status pills, KPI percentage, alarm count.

**Props.** `text`, `state: ok|warn|alarm|info|muted`, `outlined: bool`.

CSS hook: `.c03-badge`.

---

### I.3. `ProgressBar`

Для KPI deviation и Readiness section progress.

**Props.** `value: float`, `max: float`, `state`, `variant: linear|circular`.

CSS hook: `.c03-progress`.

---

### I.4. `Sparkline`

Inline mini-chart (clientside, без Plotly — чистый SVG path) для
`KpiCard`.

**Props.** `points: list[float]`, `state`, `width`, `height`.

CSS hook: `.c03-sparkline`.

---

### I.5. `Donut` (ring chart)

Для Readiness ring (84×84 desktop, 72×72 mobile).

**Props.** `value_pct: int`, `state`, `size`, `stroke`.

CSS hook: `.c03-donut`.

---

### I.6. `Tooltip`

Hover-tooltip для callouts и KPI sparklines (clientside).

CSS hook: `.c03-tooltip`.

---

## J. Соответствие компонентов и регионов

| Регион | Компоненты |
|---|---|
| `#app-header` | `BrandLogoBlock` + `InstallationTitle` + (`HeaderActionToolbar` / `StatusPill`×N) + `HeaderMetaPills` + `DateTimeBlock` + `UserAvatar` (+ `HeaderIconLink`×3) |
| `#left-rail` | `SectionEyebrow` + `ScenarioCard`×5 + `CtaButton` + `ControlModeCard`×4 + `ConfigBriefCard` + `CtaButton` |
| `#central-canvas` | `CanvasSubStrip` + `CanvasTabBar` + `Scene3DViewport` + `CalloutTag`×N + `CompassWidget` + `CanvasPaginationDots` (+ `LayersDropdown`) |
| `#right-rail` | `StatusBanner` + `SectionEyebrow` + (`KpiRow`/`KpiCard`)×6 + `HealthTile`×4 / `ComponentStatusList` + `AlarmsAccordion` + `EventLogAccordion` |
| `#bottom-strip` | `ReadinessRingPanel` / `ReadinessChecksPanel`, `ValidationSummaryPanel`, `ComparisonChartPanel`, `EventLogTable`, `ReportsPanel` / `ExportPackagePanel` |
| `#app-footer-nav` | `FooterNav` (operator) или `AcademicFooter` (Defense Day) |
| `#mobile-bottom-nav` | `MobileBottomNav` |

## K. Покрытие тестами

Каждый компонент имеет unit-renderer-тест (см. `15_qa_checklist.md`):

- snapshot HTML + CSS class set;
- prop-vs-render тест для всех `state`-вариантов;
- accessibility: aria-labels на icon-buttons и pills.

Тесты живут в `tests/unit/ui/concept03/test_<component>.py`.

## L. Ссылки на концепт

- desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
- tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
- mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`
- Дизайн-система: `02_visual_design_system.md`
- Раскладки: `03_layout_specification_desktop.md`,
  `04_layout_specification_tablet.md`, `05_layout_specification_mobile.md`
- Поведение и анимация: `07_interaction_design.md`
- Связь с моделями данных: `08_data_mapping.md`
