# 03. Спецификация раскладки — Desktop (Operator Dashboard)

> Источник истины (структура раскладки):
>   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
> Этот документ описывает desktop-вариант **Operator Dashboard** —
> расширение tablet-раскладки на 1500×900+. Это режим повседневной
> работы.
>
> Файл `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
> (1500×900 desktop) — это отдельный **Defense Day Variant** с другим
> набором панелей и control-toolbar в header. Он специфицирован в:
>
>   - `09_implementation_phases.md → Phase 7`,
>   - `06_components_catalog.md` (компоненты с пометкой *Defense Day Variant*),
>   - `15_qa_checklist.md → §B-D, §F.2`.
>
> Целевая поддерживаемая размерность Operator Dashboard — от `1366×768` до
> `1920×1080+` без ухудшения. Проектные значения для контрольной
> точки **`1500×900`** ниже.

## 1. Полная сетка

```
Width 1500 px:
  app-padding-x = 16
  region-gap   = 12
  cols (desktop main row): [16][LEFT 260][12][CENTER  ][12][RIGHT 320][16]  ← 1500
  → CENTER width = 1500 − 16 − 260 − 12 − 12 − 320 − 16 = 864

Heights (1500×900):
  header               =  56
  gap                  =  12
  main row             = 528  (между header и bottom strip)
  gap                  =  12
  bottom strip         = 220
  gap                  =  8
  footer nav           =  64
  ─────────────────────────────
  total                = 900
```

Ниже — спецификация регион-за-регионом.

## 2. Region 1 — App header (`#app-header`, 1500×56)

Один ряд из 5 групп слева направо:

```
[ logo  ][ title ][ flex spacer ][ pills ][ datetime ][ user avatar ]
```

### 2.1. Logo group (left)

- ширина: `auto`, max 220 px;
- состав: `<svg>` логотип «Каскад» + текстовый блок:
  - **К-АСКАД ГРУП** (Display 12px, uppercase, ls 0.18em, text);
  - **ООО «НПО «Каскад-ГРУП»** (Body 11px, color muted).
- паддинг: `0 16px`;
- разделитель справа: `1px solid var(--c03-line)`.

### 2.2. Title group (center-left)

- двухстрочный заголовок:
  - line 1 — «ЦИФРОВОЙ ДВОЙНИК ВЕНТИЛЯЦИОННОЙ УСТАНОВКИ П1»
    (Display 18px, uppercase, ls 0.06em, color text);
  - line 2 — «Моделирование работы приточной установки»
    (Body 12px, color muted).
- align-self: center;
- max-width: 560 px;
- truncate: `text-overflow: ellipsis` для line 1 при <1366.

### 2.3. Status pills (`#header-pill-readiness`, `#header-pill-sync`)

Два пилла справа от центра:

| pill | id | икона | title | sub | состояния |
|---|---|---|---|---|---|
| Готовность | `#header-pill-readiness` | `shield-check` | «РЕЖИМ» | «ГОТОВНОСТИ» | green / amber / red |
| Синхронизация | `#header-pill-sync` | `refresh-ccw` | «СИНХРОНИЗАЦИЯ» | «Активна» / «Стоит» | green / muted |

Размеры pill: высота 36 px, паддинги `0 12px`, радиус `--c03-radius-pill`,
border `1px solid` соответствующего status-цвета.

### 2.4. DateTime block

- два текстовых поля в колонку:
  - дата `22.05.2025` (Body 13px, mono, tabular-nums);
  - время `14:32:41` (Display 18px, mono, tabular-nums).
- right-align;
- ширина 96 px.

### 2.5. User avatar

- круг 36 px, border `1px solid var(--c03-line-strong)`,
  иконка `user` lucide 18px;
- onclick → меню профиля (`?page=settings`).

### 2.6. Header background

```css
#app-header {
  background: var(--c03-bg-base);
  border-bottom: 1px solid var(--c03-line);
}
```

## 3. Region 2 — Left rail (`#left-rail`, 260×528)

Колонка с тремя секциями + одной CTA-кнопкой.

### 3.1. Section «СЦЕНАРИИ» (`#sidebar-scenarios`)

- header row (h: 32 px):
  - eyebrow «СЦЕНАРИИ» (Heading 11px, uppercase, ls 0.18em, color muted);
  - кнопка `+` (icon-button 28×28, иконка `plus`).
- список карточек: 5 штук.
- card (см. `06_components_catalog.md → ScenarioCard`):
  - h: 56 px;
  - паддинг: `10px 12px`;
  - icon 22×22 (snowflake, sun, refresh-cw, flame, layout-grid);
  - title 13px 600;
  - sub 11px muted;
  - состояния: default / hover / active.
- зазор между карточками: 4 px.
- divider после списка: `1px solid var(--c03-line)`.

### 3.2. Кнопка «Управление сценариями»

- button-secondary 100% × 36 px;
- стрелка → справа (lucide `arrow-right`);
- onclick → `?page=control`.

### 3.3. Section «РЕЖИМЫ РАБОТЫ» (`#sidebar-control-modes`)

- header row аналогично сценариям, без `+`;
- 4 карточки, аналогичный паттерн (icon + title + sub);
- активный mode: dot-индикатор справа (8 px) с pulse-анимацией
  (`--c03-status-ok` + `--c03-sync-pulse`).

### 3.4. Конфигурация установки (`#sidebar-config`)

- паттерн `dl`-список (key/value rows):
  - Тип установки → ПВУ-12500 / ПВУ-6300 (зависит от baseline);
  - Производительность → 6 250 м³/ч;
  - Напор (ном.) → 700 Па;
  - Класс фильтрации → F7 + F9;
  - Рекуператор → Пластинчатый;
  - Нагреватель → Водяной;
  - Охладитель → Водяной;
  - Секция увлажнения → Паровой.
- key 11px muted, value 12px text 600;
- паддинги ряда `4px 0`.

### 3.5. CTA «Свойства установки»

- button-tertiary 100% × 36 px;
- onclick → `?page=equipment`.

## 4. Region 3 — Central canvas (`#central-canvas`, 864×528)

Самый сложный регион. Состоит из трёх вертикальных подзон:

```
[ Sub-strip   24 px ]   ← objective + installation badge + camera tools
[ Tab bar     44 px ]
[ Viewport    432 px ]   ← 3D / 2D / параметры / тренды
[ Pagination  24 px ]   ← scene navigation dots
                          + bottom shadow vignette
```

### 4.1. Sub-strip (24 px)

```
Объект: Учебно-производственный корпус, помещ. 1.02   |   Установка: П1 (Приточная)
                                              [icon][icon][icon] camera tools  [compass]
```

- text 11-12px muted;
- разделитель `|` 1×16 px line muted;
- camera tools: 3 кнопки (orbit, fit, fullscreen);
- compass mini-block 28×28 справа.

### 4.2. Tab bar (44 px) — `#central-canvas-tabs`

- 6 вкладок:
  1. **3D Модель** (default active)
  2. **Схема**
  3. **Параметры**
  4. **Тренды**
  5. **Аларма**
  6. **Документация**
- паттерн: text + 2 px under-bar при active;
- активный bar — `--c03-accent` glow.

### 4.3. Viewport (#central-canvas-viewport, 432 px)

#### 4.3.1. 3D-режим (default)

- canvas от three.js;
- vignette `--c03-scene-vignette`;
- 7 callout-меток (ровно как в концепте):
  | Узел | Позиция | Контент |
  |---|---|---|
  | Outdoor air | top-left | -15.2 °C / 87% / 1.8 м/с (Heading 11px + values mono 13px) |
  | Фильтр грубой очистки | top-1 | ΔP: 128 Па |
  | Водяной нагреватель | top-2 | Твх 70.0 °С / Твых 50.3 °С |
  | Вентилятор | top-3 | Скорость 1420 об/мин / 2.35 кВт |
  | Фильтр тонкой очистки | top-4 | ΔP: 152 Па |
  | Водяной охладитель | bottom-2 | Твх 7.0 °С / Твых 12.1 °С |
  | Шумоглушитель | bottom-3 | ΔP: 28 Па |
  | Supply air | top-right | 22.1 °С / 38% / 2.6 м/с |
- callout style: см. `06_components_catalog.md → CalloutTag`.
- compass top-right inside scene: 56×56 (С/В/Ю/З + крест).

#### 4.3.2. Схема (2D fallback)

- использует существующий `assets/pvu_mnemonic.svg`;
- bindings из `app/ui/scene/bindings.py`;
- callouts отключены (показ только подписей SVG-схемы).

#### 4.3.3. Параметры

- 2 колоночная таблица: левая «Входы оператора», правая «Выходы расчёта»;
- редактируемость зависит от `ControlMode`:
  - `auto` → выходы вычисляются, входы read-only кроме сценария;
  - `manual` → входы поднимают inputs (slider + numeric);
- источник — текущий `SimulationParameters`.

#### 4.3.4. Тренды

- Plotly figure 100% × 100%;
- 4 серии: `supply_temp_c`, `room_temp_c`, `fan_power_kw`,
  `filter_pressure_drop_pa`;
- timeline по `SimulationSession.history`.

#### 4.3.5. Аларма

- список карточек с code/level/message + timestamp;
- group по `level: alarm > warning > info`;
- empty-state: «Нет активных тревог. Все системы в норме.»

#### 4.3.6. Документация

- 3 карточки:
  - Технологическая карта (ссылка на `docs/02_functionality.md`);
  - Формулы (`docs/03_architecture.md`);
  - Источники (`docs/10_sources.md`).
- offline-режим — open in new tab.

### 4.4. Pagination dots (24 px)

- 5 точек по центру;
- активная — заливка `--c03-accent`, остальные — `--c03-bg-panel-strong`;
- onclick → camera presets (см. `07_interaction_design.md`).

## 5. Region 4 — Right rail (`#right-rail`, 320×528)

Колонка из трёх секций.

### 5.1. Состояние установки (`#status-banner`)

- card 100% × 96 px;
- слева dot 8 px + status-bar 4 px высоты слева,
  заливка зависит от статуса;
- title 14px 700 «НОРМАЛЬНАЯ РАБОТА» / «ВНИМАНИЕ» / «АВАРИЯ»;
- sub 12px muted («Критических отклонений нет»);
- hover не предусмотрен;
- click → `?page=analytics&tab=alarms`.

### 5.2. Ключевые показатели (`#kpi-list`)

- header eyebrow «КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ» 11px ls 0.18em muted;
- 6 строк KPI:
  1. Производительность (`kpi-row-airflow`);
  2. Статическое давление (`kpi-row-pressure`);
  3. Температура притока (`kpi-row-supply-temp`);
  4. Относительная влажность (`kpi-row-humidity`);
  5. Эффективность рекуперации (`kpi-row-recovery`);
  6. Потребляемая мощность (`kpi-row-power`).
- паттерн строки (см. `06_components_catalog.md → KpiRow`):
  ```
  ┌──────────────────────────────────────────────────────┐
  │ [icon] LABEL UPPERCASE 11px        Задание: 6 300    │
  │ VALUE 22px mono              UNIT 12px muted   99%   │
  │ progress-bar 4px (по deviation)                       │
  └──────────────────────────────────────────────────────┘
  ```
- зазор между строками: 8 px;
- progress-bar 100% — fill cyan/teal при `normal`, amber при `warning`,
  red при `alarm`.

### 5.3. Общее состояние (`#health-grid`, 2×2)

- 4 tile-карточки:
  - Оборудование (icon `boxes`),
  - Автоматика (icon `cpu`),
  - Датчики (icon `radio`),
  - Безопасность (icon `shield`).
- размер tile: 152×72;
- состав: icon 18px slot top-left, title 12px 600,
  sub 11px muted («Исправно» / «Неисправно» и т. д.),
  side-stripe 4 px по статусу.

## 6. Region 5 — Bottom strip (`#bottom-strip`, 1500×220)

Четыре панели в одной строке:

```
[#bp-readiness 28%][#bp-comparison 32%][#bp-event-log 24%][#bp-reports 16%]
```

(28+32+24+16=100; в концепте панели разной ширины — точные пропорции
повторяют макет.)

Все панели — `c03-card` с padding 16 px и radius 12 px.

### 6.1. Готовность к валидации (`#bp-readiness`, 420×220)

- title row: «ГОТОВНОСТЬ К ВАЛИДАЦИИ»;
- слева donut-ring 84×84 + центр-число (mono 28px, «86 %»),
  под ним sub «ГОТОВО» (Display 11px ls 0.16em);
- справа — 5 строк прогресса:
  - Структура модели — 100% (cyan);
  - Параметризация — 92% (cyan);
  - Верификация — 78% (amber);
  - Валидация — 85% (cyan);
  - Документирование — 80% (cyan).
- footer status: «Статус: В процессе» (или «Завершено» / «Просрочено»),
  цвет по `DemoReadinessEvaluation.overall_status`.

### 6.2. Сравнение модель vs реальность (`#bp-comparison`, 480×220)

- title row: «СРАВНЕНИЕ: МОДЕЛЬ vs РЕАЛЬНОСТЬ» + dropdown «Все события»;
- область графика: Plotly mini-line, padding 0;
- 2 серии:
  - **Реальные данные** (cyan dashed),
  - **Модель** (cyan solid);
- ось X: HH:MM, ось Y: 10..30 (зависит от `metric`);
- footer:
  - sub-text «Показатель: Температура приточного воздуха, °С»;
  - кнопка «Детальный анализ» secondary right-align.

### 6.3. Журнал событий (`#bp-event-log`, 360×220)

- title row: «ЖУРНАЛ СОБЫТИЙ» + dropdown «Все события»;
- таблица из 5 строк:
  - col 1: timestamp `HH:MM:SS` mono 11px muted;
  - col 2: pill-status badge (`Инфо` / `Предупр` / `Тревога`);
  - col 3: message body 12px text;
- footer button: «Открыть журнал».

### 6.4. Отчёты и экспорт (`#bp-reports`, 240×220)

- title row: «ОТЧЁТЫ И ЭКСПОРТ»;
- 4 list-rows (см. `06_components_catalog.md → ReportRow`):
  - Отчёт по сценарию (PDF);
  - Протокол валидации (PDF);
  - Сравнительный отчёт (PDF);
  - Данные моделирования (CSV).
- footer button-primary: «Сформировать отчёт».

## 7. Region 6 — Footer nav (`#app-footer-nav`, 1500×64)

- 6 пунктов: Дашборд, Оборудование, Управление, Аналитика, Библиотека,
  Настройки.
- паттерн пункта:
  - icon 18 px (top),
  - label 11px (bottom),
  - active item: top-bar 2px `--c03-accent` + цвет text;
- зазор между пунктами: равномерный (`flex: 1 1 0`);
- справа:
  - версия `2.4.1 (build 2025.05.20)` (mono 11px muted),
  - status-pill «ЗАЩИЩЁННЫЙ КОНТУР» зелёный / amber.

## 8. Брейкпойнты desktop

| Breakpoint | Что меняется |
|---|---|
| `≥1700` | left rail 280, right rail 340, padding 24, central canvas растягивается |
| `1500` (baseline) | значения как выше |
| `1366` | left rail 240, right rail 296, padding 12, KPI value 20px |
| `<1366` | переход к табличному варианту: bottom strip wraps в 2×2 grid |
| `<1280` | переход на tablet-вариант (см. `04_layout_specification_tablet.md`) |

## 9. Соответствие концепту

Контрольные сверки (см. `15_qa_checklist.md`):

- [ ] header высота 56–60 px (макет: ~64 при экспорте, +4 ради кросс-DPI);
- [ ] left rail точно 260 px на 1500;
- [ ] right rail точно 320 px;
- [ ] 3D viewport занимает ≥ 60% height центральной зоны;
- [ ] callouts всегда видны на 1366×768 (используют overflow-aware
      позиционирование);
- [ ] нижняя лента из 4 панелей, без переноса на 1366+;
- [ ] footer-nav 6 пунктов sticky, без horizontal scroll.

## 10. Ссылки на концепт

- desktop (Defense Day Variant — отдельная спецификация в `09 → Phase 7`):
  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
- tablet (operator dashboard, основа этой спецификации):
  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
- mobile (см. `05_layout_specification_mobile.md`):
  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`
- IA: `01_information_architecture.md`
- Дизайн-система: `02_visual_design_system.md`
- Tablet-spec: `04_layout_specification_tablet.md`
- Mobile-spec: `05_layout_specification_mobile.md`
- Каталог компонентов: `06_components_catalog.md`
