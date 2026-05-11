# 04. Спецификация раскладки — Tablet

> Источник истины:
> `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
> Аналитическое разрешение макета — `1500×1024` (landscape, ~3:2).
> Целевая поддерживаемая размерность — от `1024×768` до `1366×1024` (iPad Pro,
> Surface Pro, Galaxy Tab S9+, Lenovo ThinkPad X12). Вертикальный (portrait)
> 768×1024 — отдельный sub-вариант, см. §9.

Tablet-вариант — **канонический «оператор-дашборд»** концепта-03. Именно его
структуру опираясь на этот же макет описывает `03_layout_specification_desktop.md`
(в качестве extended-tablet раскладки на 1500×900). Здесь зафиксированы
точные размеры под планшет, а также правила адаптивного даунгрейда от desktop.

## 1. Полная сетка

```
Width 1500 px:
  app-padding-x = 16
  region-gap   = 12
  cols (main row): [16][LEFT 240][12][CENTER  ][12][RIGHT 320][16]   ← 1500
  → CENTER width = 1500 − 16 − 240 − 12 − 12 − 320 − 16 = 884

Heights (1500×1024):
  header               =  72
  gap                  =  12
  main row             = 612   (между header и bottom strip)
  gap                  =  12
  bottom strip         = 220
  gap                  =  12
  footer nav           =  72
  bottom safe-area     =  12   (для iPadOS / Surface)
  ─────────────────────────────
  total                = 1024
```

Высоты на `1024 × 768` (Galaxy Tab S9, baseline в landscape):

```
header 56 + gap 8 + main 504 + gap 8 + bottom 168 + gap 8 + footer 64 + safe 4 = 820
                                                                         (нужно scroll)
```

Вертикальный scroll допускается ТОЛЬКО на 1024×768 и ниже; на 1180×820+
дашборд должен помещаться в один экран.

## 2. Region 1 — App header (`#app-header`, 1500×72)

```
[ logo ][ title block ][ flex spacer ][ pills ][ datetime ][ user avatar ]
```

Все элементы и id повторяют `03_layout_specification_desktop.md §2`,
но размеры:

| Элемент | Tablet 1500 | Tablet 1024 |
|---|---|---|
| logo block | 220 px | 200 px |
| title block | 560 px max | 440 px max, line 1 truncate |
| pills | 220 px (`shield-check` + `refresh-ccw`) | 200 px |
| datetime | 96 px | 84 px |
| user avatar | 36 px | 32 px |

Дополнения для tablet:

- `#app-header` теряет тонкий разделитель справа от user avatar, чтобы не
  спорить с status bar iPadOS;
- на `<1180` логотип заменяется на иконку без подписи `ООО «НПО ...»`;
- title line 2 «Моделирование работы приточной установки» прячется на
  `<1180` (в концепте видно только line 1).

## 3. Region 2 — Left rail (`#left-rail`, 240×612)

Колонка идентична desktop, но 240 px вместо 260 px и плотнее.

### 3.1. Section «СЦЕНАРИИ»

- 5 карточек, как в концепте tablet:
  1. **Номинальный режим** — Базовый сценарий (active, иконка `layout-grid`)
  2. **Зимний режим** — Низкие температуры (`snowflake`)
  3. **Летний режим** — Высокие температуры (`sun`)
  4. **Рециркуляция** — Частичная рециркуляция (`refresh-cw`)
  5. **Пожарная вентиляция** — Дымоудаление (`flame`)
- card height: 52 px (на 4 px тоньше desktop), padding `8px 12px`;
- активная карточка имеет правую галочку `check` 16 px и
  `--c03-card-active-glow`.

### 3.2. Кнопка «Управление сценариями»

- 100% × 32 px, secondary, label «Управление сценариями»;
- onclick → `?page=control`.

### 3.3. Section «РЕЖИМЫ РАБОТЫ»

- 4 карточки:
  1. **Автоматический** — Работает по заданному сценарию (active)
  2. **Полуавтоматический** — Операторский контроль
  3. **Ручной** — Ручное управление оборудованием
  4. **Тестовый** — Испытания и наладка
- паттерн: иконка слева 22 px (mic / sliders / hand / beaker), title 13px
  600, sub 11px muted;
- активный режим — мигающий dot `--c03-status-ok` справа.

В tablet секции «Конфигурация установки» и CTA «Свойства установки»
**свёрнуты в нижний accordion** под режимами:

```
┌ КОНФИГУРАЦИЯ УСТАНОВКИ ▾  ┐
│ (раскрытие по клику)       │
└────────────────────────────┘
[ Свойства установки → ]
```

Это даёт +120 px высоты для `СЦЕНАРИИ` и `РЕЖИМЫ РАБОТЫ`, что важно на
1024×768.

## 4. Region 3 — Central canvas (`#central-canvas`, 884×612)

Структура:

```
[ Sub-strip   28 px ]
[ Tab bar     44 px ]
[ Viewport    516 px ]
[ Pagination  24 px ]
```

### 4.1. Sub-strip (28 px)

- Слева:
  - «Объект: Учебно-производственный корпус, помещ. 1.02»
    (Body 12px muted)
  - «Установка: П1 (Приточная)» (Body 12px text, 600)
- Справа:
  - 3 camera-кнопки (`move-3d`, `eye`, `maximize`), 24×24, gap 8;
  - compass mini-block 28×28 справа.

### 4.2. Tab bar (44 px) — `#central-canvas-tabs`

Tablet вариант имеет **6 вкладок** (одинаково с canonical operator
dashboard):

1. **3D Модель** — default active.
2. **Схема** — 2D mnemonic.
3. **Параметры** — таблица параметров.
4. **Тренды** — Plotly графики.
5. **Алармы** — список тревог.
6. **Документация** — методические основания.

Tabs: `text + 2px under-bar при active`; на ширине `≤1180` подписи
разрешено сокращать («Параметры» → «Парам.», «Документация» → «Док.»),
но иконки не добавляются (макет без иконок).

### 4.3. Viewport (#central-canvas-viewport, 516 px)

#### 4.3.1. 3D-режим (default)

Согласно tablet-макету:

- canvas three.js;
- vignette `--c03-scene-vignette`;
- callouts (8 штук, попарно сверху/снизу, см. список ниже):

| Узел | Позиция | Контент в концепте |
|---|---|---|
| Outdoor air | left side | -15.2 °C / 87% / 1.8 м/с |
| Фильтр грубой очистки | top-1 | ΔP: 128 Па |
| Водяной нагреватель | top-2 | Твх 70.0 °С / Твых 50.3 °С |
| Вентилятор | top-3 | Скорость 1420 об/мин / 2.35 кВт |
| Фильтр тонкой очистки | top-4 | ΔP: 152 Па |
| Водяной охладитель | bottom-2 | Твх 7.0 °С / Твых 12.1 °С |
| Шумоглушитель | bottom-3 | ΔP: 28 Па |
| Supply air | right side | 22.1 °С / 38% / 2.6 м/с |

- compass top-right inside scene: 56×56 (С/В/Ю/З + крест);
- pagination dots 5 шт (camera presets).

#### 4.3.2. Схема (2D fallback)

- использует существующий `assets/pvu_mnemonic.svg`;
- bindings из `app/ui/scene/bindings.py` без изменений;
- callouts отключены.

#### 4.3.3. Параметры

- table: 2 столбца «Входы оператора» / «Выходы расчёта»;
- editability по `ControlMode`;
- источник: текущий `SimulationParameters`.

#### 4.3.4. Тренды

- Plotly figure 100% × 100%;
- 4 серии: `supply_temp_c`, `room_temp_c`, `fan_power_kw`,
  `filter_pressure_drop_pa`;
- timeline по `SimulationSession.history`.

#### 4.3.5. Алармы

- список карточек code/level/message + timestamp;
- group по уровню (alarm > warning > info);
- empty: «Нет активных тревог. Все системы в норме.»

#### 4.3.6. Документация

- 3 карточки (Технологическая карта / Формулы / Источники).

### 4.4. Pagination dots (24 px)

- 5 точек по центру, активная — `--c03-accent`.

## 5. Region 4 — Right rail (`#right-rail`, 320×612)

### 5.1. Состояние установки (`#status-banner`)

- card 100% × 88 px;
- слева shield-icon 28 px в контейнере 36×36 со скруглением;
- title 14px 700 «НОРМАЛЬНАЯ РАБОТА» / «ВНИМАНИЕ» / «АВАРИЯ»;
- sub 12px muted («Критических отклонений нет»).

### 5.2. Ключевые показатели (`#kpi-list`)

- header eyebrow «КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ» 11px ls 0.18em muted;
- 6 строк KPI:
  1. Производительность (`kpi-row-airflow`) — value 18px mono, sub 11px muted, 99%;
  2. Статическое давление (`kpi-row-pressure`) — 520 Па, 104%;
  3. Температура притока (`kpi-row-supply-temp`) — 22.1 °С, 100%;
  4. Относительная влажность (`kpi-row-humidity`) — 38 %, 95%;
  5. Эффективность рекуперации (`kpi-row-recovery`) — «Недоступно»;
  6. Потребляемая мощность (`kpi-row-power`) — 2.35 кВт, 67%.
- паттерн строки см. `06_components_catalog.md → KpiRow`;
- зазор между строками: 6 px (на 2 px тоньше desktop);
- progress-bar 100% — fill cyan/teal при `normal`.

### 5.3. Общее состояние (`#health-grid`, 2×2)

- 4 tile-карточки:
  - Оборудование (icon `boxes`),
  - Автоматика (icon `cpu`),
  - Датчики (icon `radio`),
  - Безопасность (icon `shield`).
- размер tile: 152×64 (tablet);
- состав: icon 18px slot top-left, title 12px 600, sub 11px muted;
- side-stripe 4 px по статусу.

## 6. Region 5 — Bottom strip (`#bottom-strip`, 1500×220)

Четыре панели в одной строке (как desktop concept на tablet):

```
[#bp-readiness 28%][#bp-comparison 32%][#bp-event-log 24%][#bp-reports 16%]
```

### 6.1. Готовность к валидации (`#bp-readiness`)

- title row: «ГОТОВНОСТЬ К ВАЛИДАЦИИ»;
- слева donut-ring 84×84 + центр-число «86 %», sub «ГОТОВО»
  (Display 11px ls 0.16em);
- справа — 5 строк прогресса:
  - Структура модели — **100%** (`--c03-status-ok`);
  - Параметризация — **92%** (`--c03-status-ok`);
  - Верификация — **78%** (`--c03-status-warn`);
  - Валидация — **85%** (`--c03-status-ok`);
  - Документирование — **80%** (`--c03-status-ok`);
- footer status: «Статус: В процессе» (или «Завершено» / «Просрочено»).

### 6.2. Сравнение модель vs реальность (`#bp-comparison`)

- title row: «СРАВНЕНИЕ: МОДЕЛЬ vs РЕАЛЬНОСТЬ» + dropdown «Все события»;
- область графика: Plotly mini-line, padding 0;
- 2 серии:
  - Реальные данные (cyan dashed),
  - Модель (cyan solid);
- ось X: HH:MM (13:30 → 14:30 в концепте), ось Y: 10..30;
- footer:
  - sub-text «Показатель: Температура приточного воздуха, °С»;
  - кнопка «Детальный анализ» secondary right-align.

### 6.3. Журнал событий (`#bp-event-log`)

- title row: «ЖУРНАЛ СОБЫТИЙ» + dropdown «Все события»;
- таблица из 4 строк (как в концепте):
  - 14:31:08  `Инфо`  «Режим работы: Автоматический»
  - 14:30:55  `Инфо`  «Сценарий «Номинальный режим» активирован»
  - 14:28:12  `Предупр`  «ΔР фильтра грубой очистки выше нормы»
  - 14:25:47  `Инфо`  «Параметры синхронизированы»
  - 14:20:33  `Тревога`  «Температура обратной воды низкая»
- col 1: timestamp `HH:MM:SS` mono 11px muted;
- col 2: pill-status badge цветной;
- col 3: message body 12px text;
- footer button: «Открыть журнал».

### 6.4. Отчёты и экспорт (`#bp-reports`)

- title row: «ОТЧЁТЫ И ЭКСПОРТ»;
- 4 list-rows (см. `06_components_catalog.md → ReportRow`):
  - Отчёт по сценарию  (PDF),
  - Протокол валидации  (PDF),
  - Сравнительный отчёт  (PDF),
  - Данные моделирования  (CSV).
- footer button-primary: «Сформировать отчёт».

## 7. Region 6 — Footer nav (`#app-footer-nav`, 1500×72)

В tablet — 6 пунктов с иконками (lucide):

| id | label | icon |
|---|---|---|
| `footer-nav-dashboard` | Дашборд | `layout-grid` |
| `footer-nav-equipment` | Оборудование | `boxes` |
| `footer-nav-control` | Управление | `sliders-horizontal` |
| `footer-nav-analytics` | Аналитика | `bar-chart-3` |
| `footer-nav-library` | Библиотека | `book-marked` |
| `footer-nav-settings` | Настройки | `settings` |

- активный — подсветка cyan + bar 2px сверху;
- gap между пунктами: равномерно `flex: 1 1 0`;
- справа footer-strip:
  - версия `Версия: 2.4.1 (build 2025.05.20)` (mono 11px muted);
  - status-pill «ЗАЩИЩЁННЫЙ КОНТУР» зелёный.

## 8. Адаптивные правила tablet

| Breakpoint | Что меняется |
|---|---|
| `≥1366` | proportions как в §1 |
| `1180–1365` | left rail 220, right rail 296, KPI value 17px, tab bar shrink labels |
| `1024–1179` | center canvas минимум 720; bottom strip wraps в 2×2 grid; footer nav остаётся 6 пунктов |
| `≤1023` | переход на mobile-вариант (см. `05_layout_specification_mobile.md`) |

## 9. Portrait-вариант (768×1024)

Рекомендация: при portrait автоматически применять mobile layout
(см. `05_layout_specification_mobile.md`), потому что в концепте есть
только landscape tablet. Для системных требований ВКР это допустимо
(`config/defaults.mobile.yaml.ui.tablet_portrait_strategy = "mobile"`).

## 10. Соответствие tablet-концепту

Контрольные сверки (см. `15_qa_checklist.md`):

- [ ] header высота 56–72 px (макет: ~64 при экспорте);
- [ ] left rail 240 px на 1500;
- [ ] right rail 320 px;
- [ ] 3D viewport 60% height центральной зоны;
- [ ] 8 callouts на 3D-сцене + compass;
- [ ] нижняя лента из 4 панелей, без переноса на 1180+;
- [ ] footer-nav 6 пунктов sticky без horizontal scroll;
- [ ] readiness 86% + 5 строк прогресса;
- [ ] event log 5 записей с цветными pill-бейджами;
- [ ] статус «Защищённый контур» в footer.

## 11. Файлы и id

Все стабильные id такие же, как в `03_layout_specification_desktop.md §9`,
плюс:

- `tablet-config-accordion` — accordion «Конфигурация установки»;
- `tablet-portrait-strategy` — runtime-флаг переключения на mobile при
  portrait orientation.

## 12. Ссылки на концепт

- Tablet макет: `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
- Desktop вариант (Defense Day Variant): `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
- Mobile: `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`
- Структурное описание: `01_information_architecture.md`
- Дизайн-система: `02_visual_design_system.md`
- Полный desktop-spec (operator dashboard, extended): `03_layout_specification_desktop.md`
- Mobile-spec: `05_layout_specification_mobile.md`
- Defense Day Variant (academic single-screen): см. `09_implementation_phases.md → Phase 7`.
