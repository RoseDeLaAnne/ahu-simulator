# 07. Interaction Design

> Источник истины:
> - desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
> - tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
> - mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`

Этот документ описывает поведение, переходы и микро-анимации концепта-03.
Он расширяет статические раскладки (`03/04/05`) и каталог компонентов
(`06`) описанием **как именно UI отвечает на действия пользователя**.

## 1. Общие принципы

1. **Никаких мгновенных перерисовок без причины.** Любое изменение
   состояния, которое влияет на расчёт, проходит через backend и
   отражается с короткой transition-анимацией (200 ms).
2. **Clientside для view-only.** Переключение tab, camera-preset,
   hover-tooltip, layer-toggle, off-canvas — без обращения к backend.
3. **Status-first feedback.** Любая ошибка отображается в
   `StatusBanner` (правый rail) и в `EventLogTable` (нижняя лента).
   Тосты не используются (есть на уровне scaffolding, но в концепте
   они не предусмотрены).
4. **Keyboard-first для desktop.** Все ключевые действия имеют hotkey.
5. **Touch-first для tablet/mobile.** Минимум 44 px tap target.
6. **Сохранение состояния.** Tab, scenario, control mode и status
   persist между перезагрузками страницы (через `dcc.Store` +
   `localStorage` mirror).

## 2. Глобальная палитра состояний

| Action | Visual response | Source of truth |
|---|---|---|
| Click сценария | active glow + check-icon, scene callouts фейдят на 120 ms, KPI обновляются c 200 ms transition | `simulation-session-state` |
| Click режима работы | active dot pulse, controls в `Параметры` enabled/disabled | `control_mode` |
| Click tab | подчёркивание двигается, viewport fade-in 200 ms | `central-canvas-tab` |
| Hover callout | chevron expands, text reveal 120 ms ease-out | clientside |
| Click camera preset | scene smoothly интерполирует 400 ms | `viewer3d.mjs` |
| Click footer-nav | route смена через query, fade-in 200 ms | `dashboard-page` |
| Click `Запустить` | session enters `running`, KPI streaming | `SimulationService.start_session` |
| Click `Сформировать пакет` | progress на CTA → готовый zip | `DemoReadinessService.build_demo_package` |

## 3. Hotkey map (desktop / Defense Day Variant)

| Клавиша | Действие |
|---|---|
| `Space` | Запустить / Пауза (toggle) |
| `Esc` | Сброс (через подтверждающий dialog) |
| `1`–`5` | Tab переключение (3D / 2D / Графики / Таблицы / Балансы) |
| `Shift+1`–`Shift+6` | Footer-nav (Дашборд → Настройки) — **operator dashboard only** |
| `Q`/`E` | Поворот камеры (orbit) — `viewer3d` |
| `F` | Fit-to-bounds |
| `M` | Полноэкранный 3D viewport |
| `S` | Открыть scenario picker (focus left rail first card) |
| `R` | Открыть mode picker |
| `?` | Справка |

Все hotkeys регистрируются `concept03_overlay.js`. Когда `input/textarea`
имеет focus, клавиатурный обработчик не срабатывает.

## 4. Анимация переходов

### 4.1. Базовые transitions

```css
.c03-shell, .c03-scenario-card, .c03-mode-card, .c03-tab,
.c03-bottom-panel, .c03-callout, .c03-kpi-row, .c03-kpi-card {
  transition:
    background-color var(--c03-transition-base),
    border-color     var(--c03-transition-base),
    box-shadow       var(--c03-transition-base),
    opacity          var(--c03-transition-base),
    transform        var(--c03-transition-fast);
}
```

### 4.2. Hover/active

| Компонент | Hover | Active |
|---|---|---|
| `ScenarioCard` | bg lift на 1 step, border lighter | + glow `--c03-card-active-glow` + check icon (fade 120 ms) |
| `ControlModeCard` | bg lift | + dot pulse `2.4s ease-in-out infinite` |
| `KpiRow/Card` | нет hover (read-only) | при `state==alarm` — pulse border 600 ms × 3 |
| `BottomPanel CTA` | bg darken | scale(0.98) 80 ms |
| `FooterNavItem` | bg subtle | top-bar 2px slide-in 200 ms |

### 4.3. Tab fade

При click на tab текущий viewport `opacity: 0` за 120 ms, `display:none`,
новый viewport `opacity: 1` за 200 ms. Используется
`React-Transition-Group`-эквивалент через clientside callbacks.

### 4.4. Pulse-индикаторы

```
@keyframes c03-pulse {
  0%   { box-shadow: 0 0 0 0    rgba(63,203,120,0.55); }
  70%  { box-shadow: 0 0 0 10px rgba(63,203,120,0);    }
  100% { box-shadow: 0 0 0 0    rgba(63,203,120,0);    }
}
.c03-mode-card--active .c03-mode-card__dot { animation: c03-pulse 2.4s ease-in-out infinite; }
```

### 4.5. Donut ring fill

`Donut` компонент при mount анимирует `stroke-dashoffset` от `100%` до
целевого процента за 600 ms `cubic-bezier(0.2, 0.8, 0.2, 1)`. Повторно
анимируется при изменении value > 1%.

## 5. 3D-сцена и callouts

### 5.1. Mount sequence

```
1. AppShell mount
2. Scene3DViewport создаёт WebGL context
3. fetch /visualization/signals (server-side)
4. fetch /assets/pvu_installation.glb
5. callbacks-overlay позиционирует callouts
6. fade-in scene 320 ms
7. fade-in callouts 200 ms (после загрузки)
```

При `webgl-error` шаги 2-4 falling back на 2D mnemonic; tab `3D Модель`
помечается `disabled`.

### 5.2. Callout positioning

Callouts позиционируются через clientside:

```js
function projectAnchor(world, camera, viewport) { /* три. Vector3.project */ }
```

Алгоритм (на каждый animation frame):

1. Преобразование `anchor_world` в screen-space.
2. Если screen-space точка outside viewport → callout `display: none`.
3. Иначе позиционирование с учётом `side` (top/bottom/left/right) и
   collision-detection (callouts не перекрываются).
4. Leader-line — SVG с `M(anchorX, anchorY) L(calloutX, calloutY)`.

При orbit / pan камеры — callouts двигаются плавно (60 fps).

### 5.3. Hover callout

```
on hover:
  - chevron icon rotates 90°
  - tooltip-block expands вниз с rows[1..N] (200 ms)
  - leader-line становится 1.5 px (default 1 px)
```

### 5.4. Click callout

Открывает full-screen `Callout Detail` overlay (modal, вмещает: title,
все rows, links to: `Параметры` tab, `Тренды` tab, KPI row).

В Defense Day Variant — клик callout автоматически переключает
`Layers` dropdown на видимость соответствующего узла.

### 5.5. Camera presets

5 точек pagination dots = 5 предустановленных камер:

| Preset | Камера | Описание |
|---|---|---|
| `overview` (default) | iso 30°, 0.7 zoom | весь AHU + helper room |
| `intake` | left side | фильтрация и наружный воздух |
| `recovery` | mid | рекуператор + нагреватель |
| `delivery` | right side | вентилятор + охладитель + supply |
| `room` | внутрь помещения | потоки в комнате (только Defense Day) |

Переключение presets — `tween 400 ms ease-out`. Сохраняется в
`localStorage.c03_camera_preset`.

## 6. Сценарии: переключение

### 6.1. Optimistic update + сервер-truth

```
user clicks ScenarioCard
  ↓
clientside callback:
  - оптимистично подсвечивает card
  - блокирует все ScenarioCards (pointer-events: none) 200 ms
  ↓
server callback:
  - POST /scenarios/{id}/run
  - получает SimulationResult
  - обновляет `simulation-session-state`
  ↓
clientside:
  - снимает блокировку
  - запускает 200 ms transition KPI и callouts
```

При server error — card возвращается в default, появляется toast «Не
удалось применить сценарий» в `StatusBanner` (sub-text).

### 6.2. Создание user preset (`+`)

Кнопка `+` в `СЦЕНАРИИ` секции открывает `Modal: Создать пресет` с:
- title input;
- description textarea;
- copy-from select (текущий или один из системных);
- save button.

При save — POST `/scenarios/users` (через `ScenarioPresetService.create`),
preset сразу появляется в списке с тегом `Custom`.

### 6.3. Удаление user preset

Нажатие `delete` icon на user preset card открывает confirm-modal:

> Удалить пресет «Пользовательский_05»?
> Это действие нельзя отменить.

После подтверждения — DELETE `/scenarios/users/{id}`, card исчезает
(fade-out 200 ms).

## 7. Режимы работы

| Mode | Что меняется в UI |
|---|---|
| `auto` (Автоматический / АВТО) | `Параметры` tab — все inputs read-only кроме сценария. Header pill «Режим: АВТО» glow green. |
| `semi_auto` (Полуавтоматический) | inputs частично enabled (только основные уставки), pill amber. |
| `manual` (Ручной / РУЧНОЙ) | inputs полностью enabled, controls highlighted. KPI rows показывают пометку «Ручной режим» рядом с `Задание:`. |
| `test` (Тестовый / ТЕСТОВЫЙ) | в правый rail добавляется `TestPanel` с harness, инициированным `SimulationService.run_test_suite`. |
| `schedule` (Расписание) — **Defense Day Variant only** | header показывает «Шаг: 60 с» c link «Изменить расписание». |
| `service` (Сервис) — **Defense Day Variant only** | вход в diagnostic state, в правый rail переключаемся на `Diagnostics` panel (`?page=settings&tab=diagnostics`). |

Маппинг между mode-кнопками макета и `ControlMode`-enum-ами текущего
кода — в `08_data_mapping.md §3`.

## 8. Симуляция: запуск, пауза, остановка

### 8.1. Состояния

| `SimulationSessionStatus` | Что делать в UI |
|---|---|
| `idle` | Header pills: `Готовности`, `Синхронизация — Стоит`. Кнопка `Запустить` enabled. |
| `running` | Pulse green dot в header, KPI streaming (interval 1-2 c). Кнопка `Пауза` enabled. |
| `paused` | Pause icon overlay на 3D scene (40% opacity). KPI replays last frame. Кнопки `Запустить` (resume) и `Сброс` enabled. |
| `completed` | KPI замораживаются. Появляется banner «Симуляция завершена. Сохранить отчёт?» (CTA «Сохранить» / «Сбросить»). |

### 8.2. Defense Day Variant: header toolbar

Кнопки `Запустить / Пауза / Стоп / Сброс` дублируют API-вызовы
SimulationService и используют те же hotkeys (см. §3).

### 8.3. Speed control

В session есть `playback_speed` (`0.25 / 0.5 / 1 / 2 / 4`). На concept-03
он размещается:
- desktop: `Шаг модели: 60 с` в header — клик открывает popover с
  speed slider;
- tablet: в `?page=control` (для не-перегрузки header);
- mobile: hamburger → `Скорость моделирования`.

## 9. Sync indicator

`HeaderPillSync` (tablet) и `Сохранено` badge (desktop) показывают
состояние persistence:

| State | Visual |
|---|---|
| `synced` | green check + label «Сохранено» |
| `syncing` | spinner + «Сохраняем...» |
| `error` | red dot + «Ошибка сохранения» (click → retry) |

Источник — `event-log-snapshot` + `simulation-session-state.last_command`.

## 10. Bottom strip: интерактивы

### 10.1. ReadinessRingPanel hover

При hover на section row — выводится tooltip со ссылкой на soответствующий
documents:

| Section | Tooltip text | Link |
|---|---|---|
| Структура модели | «См. docs/03_architecture.md» | `?page=library&tab=docs` |
| Параметризация | «См. config/p0_baseline.yaml» | `?page=library&tab=baseline` |
| Верификация | «См. validation matrix» | `?page=analytics&tab=validation` |
| Валидация | «См. manual check» | `?page=analytics&tab=validation` |
| Документирование | «См. docs/14_defense_pack.md» | `?page=library&tab=defense` |

### 10.2. ComparisonChartPanel

При изменении dropdown сценариев → `ComparisonService.compare(scenario_a, scenario_b)`:

```
loading state: skeleton с pulse 1.2s
ready state: chart fade-in 200 ms
```

### 10.3. EventLogTable

- Click на запись → highlight 200 ms + scroll to detail panel в
  `?page=analytics&tab=event-log`.
- Dropdown «Все события» фильтрует по `level`.

### 10.4. ReportsPanel

Click на report row → `POST /exports/result/build` + button показывает
spinner (max 30 s timeout). После build — download автоматически
запускается; в `EventLogService` пишется entry.

## 11. Footer-nav (operator) и AcademicFooter (Defense Day)

### 11.1. Footer-nav

- Click footer-item → меняет `?page=...` query, fade-in main row 200 ms.
- Hover footer-item → bg subtle, label colour shifts cyan.
- При unsaved-changes (например, активная test session) — confirm
  dialog: «Прервать тест и перейти?»

### 11.2. SecuredLoopPill

Click на pill → opens popover:

```
ЗАЩИЩЁННЫЙ КОНТУР
Состояние: Активен
Внешние зависимости: 0 / 0
Локальные сервисы: 8 / 8
[ Показать диагностику → ]
```

### 11.3. AcademicFooter

- `Сохранено` badge при click — opens `?page=settings&tab=storage`
  с перечнем сохранённых файлов.
- Версия (`1.3.2`) при click — opens `Modal: О приложении` (содержит
  changelog summary).

## 12. Mobile-специфика

### 12.1. Off-canvas

Open: `right-slide 280 px` 320 ms ease-out.
Close: backdrop tap или swipe right.

### 12.2. View dropdown («3D ▾»)

При выборе нового view:
- 3D scene → 2D mnemonic: replace-mount, fade 200 ms;
- 2D mnemonic → Тренды: replace-mount, fade 200 ms;
- Тренды → Параметры: replace-mount.

### 12.3. KpiTile tap

Tap на KPI tile → opens `Modal: KPI Detail` с full sparkline и историей.

### 12.4. Bottom-nav

Active item — всегда «Главная» при первом запуске. Переход в `Модель`
(второй пункт) показывает full-screen 3D viewport без правой панели.

## 13. Accessibility (a11y)

- `aria-label` на всех icon-only buttons (camera tools, hamburger,
  hotkey indicators).
- Контраст текста: ≥ 4.5:1 (проверка по `02_visual_design_system §11`).
- Focus ring: 2px outline `--c03-accent`, `outline-offset: 2px`.
- Keyboard nav: tab по: ScenarioCards → ControlModeCards →
  CTA → CanvasTabBar → KpiList → BottomPanels → FooterNav → UserAvatar.
- Screen reader: status pills читаются как «Статус: <NAME>, <SUB>».
- Reduce motion: `prefers-reduced-motion` отключает pulse, donut fill,
  callout chevron rotate, оставляет fade.

## 14. Loading и empty states

| Component | Loading | Empty |
|---|---|---|
| `Scene3DViewport` | dim overlay + spinner + label «Загрузка модели...» | error overlay + CTA «Перейти в 2D» |
| `KpiList` | skeleton bars 6× | «Нет данных» (если session не запущена) |
| `EventLogTable` | shimmer 4 строки | «Нет событий» иллюстрация |
| `ComparisonChartPanel` | skeleton chart | «Выберите сценарий для сравнения» |
| `ReportsPanel` | spinner на CTA | «Нет доступных отчётов» |

## 15. Error handling

- Unrecoverable backend error → `ErrorBoundary` отображает full-screen
  «Что-то пошло не так» с кнопкой «Перезапустить контур».
- Recoverable error (HTTP 4xx/5xx на одном callback) → inline error
  state на компоненте + entry в `EventLogTable` с уровнем `Тревога`.
- Network offline → footer-pill `ЗАЩИЩЁННЫЙ КОНТУР` остаётся зелёным
  (мы локальные!), но WebSocket-индикатор синхронизации становится
  amber.

## 16. Connection с текущим кодом

| Backend service | UI hook |
|---|---|
| `SimulationService` | `simulation-session-state`, `KpiList`, `Scene3DViewport`, `HeaderActionToolbar` |
| `StatusService` | `StatusBanner`, `HeaderPillReadiness`, `KpiRow.state` |
| `DemoReadinessService` | `ReadinessRingPanel`, `ReadinessChecksPanel`, `ExportPackagePanel` |
| `ScenarioPresetService` | `ScenarioCard`, `+` modal |
| `ComparisonService` | `ComparisonChartPanel` |
| `EventLogService` | `EventLogTable`, `EventLogAccordion` |
| `ExportService` | `ReportsPanel` |
| `ValidationService` | `ValidationSummaryPanel`, `ReadinessRingPanel` |

## 17. Ссылки

- desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
- tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
- mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`
- `02_visual_design_system.md` (motion tokens)
- `06_components_catalog.md` (props/states каждого компонента)
- `08_data_mapping.md` (источники данных)
- `09_implementation_phases.md` (фазы внедрения)
