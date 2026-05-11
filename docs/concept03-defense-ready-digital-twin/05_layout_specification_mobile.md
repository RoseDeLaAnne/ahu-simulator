# 05. Спецификация раскладки — Mobile

> Источник истины:
> `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`
> Аналитическое разрешение макета — `~ 740×1530` (iPhone Pro / Galaxy S24+,
> с учётом safe-area).
> Целевая поддерживаемая размерность — от `360×640` до `430×932`
> (Capacitor mobile shell, см. `mobile/README.md`).

Mobile-вариант — **«полевой быстрый осмотр»**. Это не урезанная копия
desktop, а самостоятельный продукт со своим набором блоков. Ставка —
крупные тапаемые зоны, один длинный scroll, fixed bottom-nav с пятью
пунктами, отдельное переключение режима view (3D / 2D / Тренды) в
правом верхнем углу под заголовком.

## 1. Общая сетка

```
Width 375 px (CSS) — base:
  app-padding-x = 16
  card-radius   = 16
  region-gap    = 16

Heights (375×812, base):
  status-bar (system) = 44
  app-header          = 56
  hero block          = 360 (title + scene + callouts)
  KPI strip           = 88
  scenario+readiness  = 168
  comparison panel    = 156
  event log panel     = 168
  exports panel       = 110
  footer-nav          = 72
  safe-area bottom    = 12
  ─────────────────────────
  total scrollable    ≈ 1188
```

Scroll вертикальный, всегда; bottom-nav фиксирован в нижней части
viewport (`position: fixed`). Header не sticky на mobile (в концепте header
прокручивается вместе с контентом).

## 2. Region 1 — App header (`#app-header-mobile`, 375×56)

Двухстрочный header без status pills:

```
[ logo 32 ] ООО "НПО "Каскад-ГРУП"     [shield-mini]   [hamburger]
            Цифровой двойник
```

- logo — иконка «К» в прямоугольнике 32×32 с `--c03-accent-soft`
  заливкой;
- title `ООО "НПО "Каскад-ГРУП"` — Body 13px 600;
- sub `Цифровой двойник` — Body 11px muted;
- shield-mini — иконка `shield-check` 22 px + label под ней
  «Готов к защите» (Body 9-10px);
- hamburger — `menu` 22 px (открывает off-canvas со всеми пунктами
  navigation + about).

## 3. Region 2 — Hero (Title + Scene)

### 3.1. Title bar

```
┌──────────────────────────────────────────────┐
│ Приточная вентиляционная установка П1   [3D ▾] │
│ ● В работе                                    │
└──────────────────────────────────────────────┘
```

- title 16-17 px 700 «Приточная вентиляционная установка П1»;
- status row: dot `● --c03-status-ok` + label `В работе` (или `На паузе`,
  `Стоп`, `Авария`);
- view dropdown: `3D ▾` (`3D` / `2D Схема` / `Тренды` / `Параметры`);
- паттерн pill button 36 px height с иконкой `box` слева.

### 3.2. Scene block (375×320)

- 3D-сцена занимает почти всю ширину (с padding 16);
- vignette + 7 callouts (mobile-вариант):
  | Расположение | Подпись | Контент |
  |---|---|---|
  | top-left | Нар. воздух | -3.2 °C |
  | top-1 | Влажность | 68 % |
  | top-2 | Приток | 22.4 °C |
  | top-3 | Расход | 1 250 м³/ч |
  | bottom-1 | Клапан | 45 % |
  | bottom-2 | ΔP фильтра | 320 Па |
  | bottom-3 | В помещении | 22.1 °C |
- стиль callout: см. `06_components_catalog.md → CalloutTagMobile`;
  white pill 28-32 px height + small drop-shadow + leader-line к узлу.
- При замене view на `2D Схема` — отображается responsive SVG mnemonic;
- при `Тренды` — отображается одна Plotly диаграмма supply_temp; при
  `Параметры` — короткий список ключевых параметров с возможностью
  редактирования (только в `manual`).

## 4. Region 3 — Top KPI strip (375×88)

4 квадратные карточки 87×88 в горизонтальной row (gap 8):

| id | label | value | sub |
|---|---|---|---|
| `kpi-tile-temp` | Темп. притока | `22.4 °C` | Уставка `22.0 °C` |
| `kpi-tile-humidity` | Влажность | `36 %` | Уставка `40 %` |
| `kpi-tile-airflow` | Расход воздуха | `1 250 м³/ч` | Уставка `1 300` |
| `kpi-tile-power` | Потреб. мощность | `3.42 кВт` | Энергоэфф. `0.61` |

- иконка лева 16 px (thermometer / droplet / wind / zap);
- value 18px mono 700;
- unit 11px muted под value;
- sub 10-11px muted;
- card padding 10px, radius 12, фон `--c03-bg-panel`.

## 5. Region 4 — «Сценарий работы» + «Готовность к защите»

```
┌─ Сценарий работы ──────┐ ┌─ Готовность к защите ────┐
│ [snowflake] Зимний реж.▾│ │   ┌────┐ ✓ Модель веры. │
│ ✓ Уставки активны       │ │   │92 %│ ✓ Данные актуа.│
│ [Управление сценариями] │ │   │Гото│ ✓ Сценарии про.│
│                         │ │   └────┘ ✓ Отчёты сформ.│
│                         │ │   Детализация проверки →│
└─────────────────────────┘ └─────────────────────────┘
```

- card-row из 2 равных колонок, gap 12;
- слева: scenario picker (dropdown с иконкой и стрелкой),
  pill «Уставки активны», secondary button «Управление сценариями»;
- справа: donut 72×72 с center text «92 %» и sub «Готово»;
  4 чекбокс-строки с зелёной check-иконкой; ссылка
  «Детализация проверки →»;
- размер row: 168 px высота.

## 6. Region 5 — «Сравнение сценариев (ключевые показатели)»

```
┌── Сравнение сценариев  Все сценарии → ──┐
│ ─ Зимний режим                          │
│ ─ Летний режим                          │
│ ┌────────────┬───────────┬──────┬──────┐│
│ │ Темп.прит. │ Расх.возд │ Мощн.│ COP  ││
│ │  22.4 °C   │ 1 250 м³/ч│ 3.42 │ 2.61 ││
│ │  20.1 °C   │ 1 100 м³/ч│ 4.15 │ 2.05 ││
│ └────────────┴───────────┴──────┴──────┘│
└─────────────────────────────────────────┘
```

- 4 столбца показателей × 2 строки сценариев;
- legend: 2 pill-цвета (active green dash для активного, blue solid для
  comparison);
- right link «Все сценарии →» открывает full comparison page.

## 7. Region 6 — «Журнал событий»

- header row: «Журнал событий» + link «Все события →»;
- 3 строки последних событий (как в концепте):
  | Иконка | Time | Title | Sub |
  |---|---|---|---|
  | `check-circle` зелёный | `08:35` | Параметры в норме | Все системы работают штатно |
  | `info` blue | `08:21` | Сценарий переключён: Зимний режим | Оператор: Иванов И.И. |
  | `alert-triangle` amber | `08:05` | ΔP фильтра повышено | Текущее значение: 320 Па |
- каждая строка — 48 px height, chevron справа `>`.

## 8. Region 7 — «Экспорт и отчёты»

- header row: «Экспорт и отчёты»;
- 4 квадратные кнопки в 1 row (gap 8):
  - Отчёт по установке (icon `file-text`),
  - Протокол валидации (icon `clipboard-check`),
  - Сравнительный отчёт (icon `bar-chart-3`),
  - Экспорт данных (CSV) (icon `download`);
- кнопка 76×72 px, label 11px center.

## 9. Region 8 — Bottom nav (`#mobile-bottom-nav`, 375×72)

5 пунктов (на 1 меньше, чем tablet — «Библиотека» спрятана в hamburger):

| id | label | icon |
|---|---|---|
| `mobile-nav-home` | Главная | `home` (active) |
| `mobile-nav-model` | Модель | `box` |
| `mobile-nav-scenarios` | Сценарии | `layers` |
| `mobile-nav-analytics` | Аналитика | `bar-chart-3` |
| `mobile-nav-settings` | Настройки | `settings` |

- активный: cyan label + 2px under-bar;
- неактивный: muted label;
- glow на active home: `0 0 12px var(--c03-accent-soft)`;
- background — `rgba(14,22,32,0.92)` + backdrop-blur 16 px.

## 10. Off-canvas (hamburger menu)

Открывается справа, ширина 280 px.

```
[ ‐ ] Закрыть
─────────────
КАСКАД ГРУП
ООО «НПО «Каскад-ГРУП»»

ВКР: Моделирование работы ПВУ
Защищённый контур: Активен
Версия: 2.4.1 (build 2025.05.20)

────── Разделы ──────
Главная (active)
Модель
Сценарии
Аналитика
Библиотека
Настройки

────── Защита ──────
Готовность к защите
Чек-лист защиты
Открыть журнал событий
```

## 11. Адаптивные правила

| Breakpoint | Что меняется |
|---|---|
| `≥430` | KPI strip 4 quadrats остаются 4-в-ряд (увеличенные размеры) |
| `360–429` | KPI strip 4-в-ряд, но font 16/10, padding 8 |
| `<360` | KPI strip 2×2 grid; comparison table показывает 2 столбца, остальные swipe-able |
| portrait tablet (768×1024) | использует mobile-вариант полностью (см. `04_layout_specification_tablet.md §9`) |

## 12. Соответствие mobile-концепту

Контрольные сверки (см. `15_qa_checklist.md`):

- [ ] header: logo + ООО «НПО Каскад-ГРУП» + «Цифровой двойник» (одной
      строкой каждый);
- [ ] view dropdown работает (3D / 2D / Тренды / Параметры);
- [ ] 3D scene с 7 callouts при ширине 375;
- [ ] KPI strip 4 квадрата, mono numbers;
- [ ] двухколоночный row «Сценарий работы» + «Готовность к защите 92%»;
- [ ] comparison table 4×2 показателей;
- [ ] 3 строки журнала событий с цветными иконками;
- [ ] 4 кнопки экспорта в одну строку;
- [ ] bottom-nav 5 пунктов, sticky, без horizontal scroll;
- [ ] hamburger открывает off-canvas с пунктом «Библиотека».

## 13. Связь с Capacitor mobile shell

`mobile/` содержит Capacitor-конфигурацию + manifest. Mobile-концепт-03
требует:

- backend HTTPS (`deploy/run-mobile-backend.ps1`) — без изменений;
- настройка `splashscreen` и `safe-area` в `mobile/src/styles/`
  (концепт-цвета `--c03-bg-deep` и `--c03-accent`);
- Capacitor plugin status-bar: тёмная тема, `--c03-bg-deep`;
- back-button: на разделе «Главная» — выход через диалог «Выйти из
  приложения?», на других — переход на «Главную».

## 14. Файлы и id

```
src/app/ui/concept03/
├── mobile_layout.py        # build_mobile_layout()
├── mobile_components.py    # KpiTile, MobileEventRow, ScenarioPicker
└── assets/
    └── concept03_mobile.css
```

Стабильные id:

- `app-header-mobile`, `mobile-hero`, `mobile-scene`, `mobile-kpi-strip`,
- `mobile-scenario-card`, `mobile-readiness-card`,
- `mobile-comparison`, `mobile-event-log`, `mobile-exports`,
- `mobile-bottom-nav`, `mobile-offcanvas`.

## 15. Ссылки на концепт

- Mobile макет: `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`
- Tablet: `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
- Desktop: `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
- IA: `01_information_architecture.md`
- Дизайн-система: `02_visual_design_system.md`
- Tablet-spec: `04_layout_specification_tablet.md`
- Capacitor shell: `mobile/README.md`,
  `docs/24_windows_android_delivery_plan.md`.
