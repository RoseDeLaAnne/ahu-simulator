# 02. Дизайн-система концепта-03

> Источник истины:
> - desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
> - tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
> - mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`

Это **технический контракт** между макетом и кодом. Любой UI-блок, который
не использует токены из этого файла, считается несоответствующим концепту.

## 1. Палитра

Палитра холодная, технологическая, без тёплых амбер-акцентов. Все значения
берутся из визуального анализа `concept-03-defense-ready-digital-twin*.png`.

### 1.1. Базовые цвета

```css
/* Background и панели */
--c03-bg-deep: #0A1119;        /* самый дальний фон страницы */
--c03-bg-base: #0E1620;        /* фон контейнеров */
--c03-bg-panel: #131C28;       /* фон панелей и карточек */
--c03-bg-panel-strong: #182232;/* активные/выделенные карточки */
--c03-bg-overlay: #1B2535;     /* модалки, поповеры */

/* Линии и разделители */
--c03-line: #1F2C3D;
--c03-line-strong: #2A3A50;

/* Текст */
--c03-text: #E6EEF7;           /* primary */
--c03-text-muted: #94A4B8;     /* secondary */
--c03-text-faint: #6A7C92;     /* tertiary, captions */
--c03-text-inverse: #0A1119;   /* на ярких заливках */
```

### 1.2. Акценты

```css
/* Cyan/Blue — основной акцент (active sidebar, primary buttons, links) */
--c03-accent: #3DA9F0;
--c03-accent-strong: #4FC3F7;
--c03-accent-soft: rgba(61, 169, 240, 0.16);
--c03-accent-glow: 0 0 24px rgba(61, 169, 240, 0.35);

/* Teal — KPI vital signs, "Готов к защите" */
--c03-teal: #5CE0CD;
--c03-teal-soft: rgba(92, 224, 205, 0.16);

/* Status: Норма / Риск / Авария */
--c03-status-ok: #3FCB78;          /* Норма */
--c03-status-ok-soft: rgba(63, 203, 120, 0.16);
--c03-status-warn: #FFB547;        /* Риск */
--c03-status-warn-soft: rgba(255, 181, 71, 0.16);
--c03-status-alarm: #FF5A6E;       /* Авария */
--c03-status-alarm-soft: rgba(255, 90, 110, 0.16);
--c03-status-info: #5CB7F0;        /* Инфо */
```

### 1.3. Семантика статуса

| Статус (UI) | Технический enum | Цвет фона pill | Цвет текста pill | Цвет dot/иконки |
|---|---|---|---|---|
| Норма | `normal` | `--c03-status-ok-soft` | `--c03-status-ok` | `--c03-status-ok` |
| Риск | `warning` | `--c03-status-warn-soft` | `--c03-status-warn` | `--c03-status-warn` |
| Авария | `alarm` | `--c03-status-alarm-soft` | `--c03-status-alarm` | `--c03-status-alarm` |
| Инфо | `info` | rgba(92,183,240,0.16) | `--c03-status-info` | `--c03-status-info` |

`StatusService` уже фиксирует пользовательский язык и enum; concept-03 лишь
подменяет CSS-переменные классов.

### 1.4. Градиенты и эффекты

```css
/* Vignette на 3D-сцене */
--c03-scene-vignette: radial-gradient(
  ellipse at center,
  rgba(20, 30, 45, 0) 35%,
  rgba(8, 14, 22, 0.65) 100%
);

/* Glow вокруг активной карточки сценария */
--c03-card-active-glow: 0 0 0 1px var(--c03-accent),
                         0 18px 48px rgba(61, 169, 240, 0.18);

/* Top-bar progress / sync */
--c03-sync-pulse: 0 0 0 0 rgba(63, 203, 120, 0.6);
```

## 2. Типографика

```css
--c03-font-display: 'Bebas Neue', 'Oswald', 'Inter', sans-serif;
--c03-font-heading: 'Inter', 'Manrope', sans-serif;
--c03-font-body: 'Inter', 'Manrope', sans-serif;
--c03-font-mono: 'JetBrains Mono', 'IBM Plex Mono', ui-monospace, monospace;

/* Размеры */
--c03-fs-xxs: 10px;   /* eyebrow, badges */
--c03-fs-xs:  11px;   /* меток в KPI, captions */
--c03-fs-sm:  12px;   /* secondary text */
--c03-fs-base: 13px;  /* body */
--c03-fs-md:  14px;   /* нав. ссылки */
--c03-fs-lg:  16px;   /* заголовки карточек */
--c03-fs-xl:  20px;   /* KPI numbers */
--c03-fs-2xl: 28px;   /* "Цифровой двойник" subtitle */
--c03-fs-3xl: 36px;   /* "86% Готово" */

/* Высоты строк */
--c03-lh-tight: 1.1;
--c03-lh-normal: 1.4;
--c03-lh-relaxed: 1.6;

/* Letter-spacing */
--c03-ls-uppercase: 0.12em;   /* для caps секций "СЦЕНАРИИ", "РЕЖИМЫ РАБОТЫ" */
--c03-ls-tight: -0.01em;
```

### 2.1. Стилевые правила текста

| Назначение | Шрифт | Размер | Стиль | Применение |
|---|---|---|---|---|
| Заголовок установки | Display | 16-18px | uppercase, letter-spacing 0.05em | header center |
| Подзаголовок «Моделирование...» | Body | 12px | regular, color muted | header center sub |
| Section eyebrow («СЦЕНАРИИ», «РЕЖИМЫ РАБОТЫ»...) | Heading | 11px | uppercase 700, letter-spacing 0.18em, color muted | sidebar, right rail |
| Section title в карточке («Готовность к валидации») | Heading | 13px | uppercase 600, letter-spacing 0.14em | bottom strip |
| Card title (Сценарий) | Heading | 13-14px | 600 | scenario card |
| Card sub | Body | 11-12px | regular, color faint | scenario card sub |
| KPI number | Mono | 20-22px | 600, tabular-nums | right rail |
| KPI label | Body | 11-12px | regular, color muted | right rail |
| Большое 86% | Display | 36-40px | 700, tabular-nums | readiness ring |
| Tab label | Heading | 12-13px | 500-600, uppercase, ls 0.1em | central canvas tab-bar |
| Footer-nav label | Body | 11px | 500, ls 0.06em | global footer |

## 3. Spacing и радиусы

```css
/* spacing scale (8-base) */
--c03-space-0: 0;
--c03-space-1: 4px;
--c03-space-2: 8px;
--c03-space-3: 12px;
--c03-space-4: 16px;
--c03-space-5: 20px;
--c03-space-6: 24px;
--c03-space-7: 32px;
--c03-space-8: 40px;

/* радиусы */
--c03-radius-xs: 4px;     /* tags, dots */
--c03-radius-sm: 6px;     /* small buttons */
--c03-radius-md: 8px;     /* card */
--c03-radius-lg: 12px;    /* big card */
--c03-radius-xl: 16px;    /* modal */
--c03-radius-pill: 999px; /* status pill, чип */
```

### 3.1. Контейнеры

```css
--c03-container-max: 1600px;       /* desktop max */
--c03-app-padding-x: 16px;          /* base */
--c03-region-gap: 12px;             /* зазор между regions */
--c03-card-padding: 16px;
--c03-card-padding-tight: 12px;
```

### 3.2. Размеры регионов (desktop, ≥1440px)

| Регион | Ширина / Высота |
|---|---|
| App header | 56px |
| Left rail | 260px |
| Right rail | 320px |
| Bottom strip | 220–240px |
| App footer nav | 64px |
| Central canvas | оставшееся пространство |

Точные пиксельные значения с breakpoints — в `03_layout_specification_desktop.md`.

## 4. Иконография

Используется одна семья — **Lucide Icons** (`lucide-react`/SVG-набор):
неперегруженные техно-линии 1.5px, согласованы с Inter.

| Иконка | Lucide id | Где |
|---|---|---|
| Snowflake | `snowflake` | Сценарий «Зимний режим» |
| Sun | `sun` | Сценарий «Летний режим» |
| Refresh-cw | `refresh-cw` | Сценарий «Рециркуляция» |
| Flame | `flame` | Сценарий «Пожарная вентиляция» |
| Layout-grid | `layout-grid` | Сценарий «Номинальный режим» |
| Mic | `mic` | Режим «Автоматический» |
| Sliders | `sliders` | Режим «Полуавтоматический» |
| Hand | `hand` | Режим «Ручной» |
| Beaker | `beaker` | Режим «Тестовый» |
| Shield-check | `shield-check` | header «Режим готовности», footer «Защищённый контур» |
| Refresh | `refresh-ccw` | header «Синхронизация» |
| Compass | `compass` | header (сегодняшнее время мобильного варианта) |
| Camera | `camera` | tools над сценой |
| Maximize | `maximize` | tools (полный экран) |
| Move-3d | `move-3d` | tools (orbit) |
| Eye | `eye` | tools (видимость) |
| FileText | `file-text` | reports panel |
| File-spreadsheet | `file-spreadsheet` | reports panel CSV |
| Clipboard-check | `clipboard-check` | reports panel протокол валидации |
| Bar-chart | `bar-chart-3` | reports panel сравнительный отчёт |
| Bell | `bell` | event log Тревога |
| Info | `info` | event log Инфо |
| Alert-triangle | `alert-triangle` | event log Предупр |

Импорт/раскладка иконок — клиентский SVG-sprite в
`src/app/ui/assets/concept03_icons.svg` либо inline-SVG в layout.

## 5. Тени и слои

```css
--c03-shadow-elevated: 0 16px 32px rgba(0, 0, 0, 0.45);
--c03-shadow-card: 0 6px 18px rgba(0, 0, 0, 0.3);
--c03-shadow-inset-line: inset 0 -1px 0 rgba(255, 255, 255, 0.04);
--c03-z-app-shell: 1;
--c03-z-sticky-header: 50;
--c03-z-callouts: 80;
--c03-z-overlay: 100;
--c03-z-toast: 200;
```

## 6. Состояния компонентов

Цветовая дисциплина для интерактивных элементов:

| Состояние | Граница | Фон | Текст |
|---|---|---|---|
| default (карточка) | `--c03-line` | `--c03-bg-panel` | `--c03-text` |
| hover | `--c03-line-strong` | `--c03-bg-panel-strong` | `--c03-text` |
| active (sidebar item) | `--c03-accent` | `--c03-bg-panel-strong` + `--c03-accent-soft` overlay | `--c03-text` |
| focus | `--c03-accent` (2px) | unchanged | unchanged |
| disabled | `--c03-line` | `--c03-bg-panel` (0.6 opacity) | `--c03-text-faint` |
| error | `--c03-status-alarm` | `--c03-status-alarm-soft` | `--c03-text` |

## 7. Анимация и motion

```css
--c03-transition-fast: 120ms cubic-bezier(0.2, 0.8, 0.2, 1);
--c03-transition-base: 200ms cubic-bezier(0.2, 0.8, 0.2, 1);
--c03-transition-slow: 320ms cubic-bezier(0.2, 0.8, 0.2, 1);
```

- Hover/active на карточках/кнопках: `--c03-transition-base` для bg/border.
- Появление панели или модалки: `--c03-transition-slow` + opacity 0→1.
- Pulse-индикатор активного режима: `2.4s ease-in-out infinite`.
- 3D camera-preset transition: `400ms ease-out` (через viewer3d).

## 8. Файловая раскладка токенов

В коде токены живут в:

```
src/app/ui/assets/concept03_tokens.css     # все CSS variables
src/app/ui/assets/concept03_dashboard.css  # компоненты concept-03
src/app/ui/assets/concept03_icons.svg      # SVG-sprite
src/app/ui/assets/concept03_overlay.js     # callouts, compass, camera tools (clientside)
```

Текущие `dashboard.css` и `z_dashboard_mvp.css` **не удаляются** до завершения
Phase 6 миграции (см. `12_migration_strategy.md`); они остаются как baseline и
fallback при сбое concept-03 ассетов.

## 9. Светлая тема

Светлая тема в scope не входит. Если нужно — отдельный документ позднее;
концепт-03 спроектирован под dark-only.

## 10. Совместимость с существующими стилями

- `dashboard.css` — содержит legacy-токены (`--bg`, `--accent`,
  `--text-muted`). Не переименовываются. Concept-03 живёт в собственном
  пространстве переменных `--c03-*`, чтобы можно было держать оба слоя.
- При активации concept-03 на странице добавляется класс
  `body.theme-concept03` (заодно перекрывает legacy через каскад).
- Активация переключается переменной окружения / settings:
  `settings.ui.theme = "concept03" | "legacy"`.

## 11. Acceptance toolkit

- **Цветовое отклонение**: ≤ 4 ΔE по Lab между токеном и пикселем макета
  на референсных позициях (header pill, KPI value, scenario active card).
- **Типографические размеры**: точные значения по шкале
  `--c03-fs-*` без произвольных px.
- **Iconography**: нет иконок вне Lucide (либо строго документированные
  кастомные SVG, прописанные в `06_components_catalog.md`).
- **Тени**: ровно три уровня (`elevated/card/inset-line`); никаких
  кастомных box-shadow.
