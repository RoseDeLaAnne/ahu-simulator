# Задача 3.2: Режим сравнения (Side-by-Side) — Справочник API и руководство

**Статус:** Этап 10 (Testing & Documentation)
**Дата:** 2026-05-31

Этот документ описывает программный интерфейс режима сравнения 3D-двойника,
REST-эндпоинты, на которые он опирается, режимы выделения различий и
практические сценарии использования.

---

## 1. Архитектура

```
┌─────────────────────┐     clientside      ┌──────────────────────────┐
│  Dash UI контролы    │  syncComparisonMode  │  window.dash_clientside  │
│  (scene3d.py)        │ ───────────────────▶ │      .pvu3dBridge        │
│  scene3d-comparison-*│                      │  (viewer3d_bridge.js)    │
└─────────────────────┘                      └────────────┬─────────────┘
         ▲                                                  │ window.pvu3d.*
         │ options/value (серверный callback)              ▼
┌────────┴─────────────┐   POST /api/...   ┌──────────────────────────┐
│ populate_comparison_  │ ◀──────────────── │   3D-движок viewer3d.mjs │
│ sources (callbacks.py)│                   │   (2 сцены, split-screen)│
└──────────────────────┘                   └──────────────────────────┘
```

- **viewer3d.mjs** — движок THREE.js; держит основную сцену (`scene`, "до") и
  вторую сцену (`comparisonSceneAfter`, "после"), рендерит их side-by-side.
- **viewer3d_bridge.js** — мост между Dash clientside-callback и `window.pvu3d`.
- **scene3d.py** — UI-панель `_scene3d_comparison_tools()` (только при
  `developer_tools_enabled=True`).
- **callbacks.py** — clientside `syncComparisonMode` + серверный
  `populate_comparison_sources`.

---

## 2. Публичный JS API (`window.pvu3d`)

### `loadComparisonData(beforeRefId, afterRefId) → Promise<RunComparison>`

Загружает пару прогонов через REST и сохраняет их во внутреннем состоянии
движка. Возвращает объект `RunComparison` (см. §4).

| Параметр | Тип | Описание |
|----------|-----|----------|
| `beforeRefId` | `string` | reference_id источника "до" (`active-run`, `archive:*`, `snapshot:*`) |
| `afterRefId` | `string` | reference_id источника "после" |

```js
const comparison = await window.pvu3d.loadComparisonData(
  "snapshot:before",
  "active-run"
);
console.log(comparison.compatibility.is_compatible); // true / false
```

> Метод только загружает данные; он **не** включает split-screen. Сетку
> запускает `setComparisonMode("split", …)`.

---

### `setComparisonMode(mode, options?) → void`

Включает или выключает split-screen рендеринг.

| Параметр | Тип | Описание |
|----------|-----|----------|
| `mode` | `"off"` \| `"split"` | Режим отображения |
| `options.split` | `number` | Соотношение разделения, 0.3–0.7 (по умолчанию 0.5) |
| `options.orientation` | `"vertical"` \| `"horizontal"` | Ориентация (по умолчанию `"vertical"`) |
| `options.syncCameras` | `boolean` | Синхронизация камер (по умолчанию `true`) |
| `options.diffMode` | `string` | Режим выделения различий (по умолчанию `"status"`) |

Поведение:
- `"split"` требует, чтобы данные были предварительно загружены
  (`loadComparisonData`) **и** были совместимы. Иначе выводит warning и выходит.
- `"off"` уничтожает вторую сцену, восстанавливает полный viewport и удаляет
  CSS-оверлеи (разделитель и подписи).

```js
window.pvu3d.setComparisonMode("split", {
  split: 0.5,
  orientation: "vertical",
  syncCameras: true,
  diffMode: "temperature",
});
```

---

### `updateComparisonDiffMode(mode) → void`

Меняет режим выделения различий **без перезагрузки данных** (≈10× быстрее
полного цикла `loadComparisonData` + `setComparisonMode`). Сбрасывает прежнее
выделение, переприменяя сигналы к сцене "после", и накладывает новое.

| Параметр | Тип | Описание |
|----------|-----|----------|
| `mode` | `"status"` \| `"temperature"` \| `"power"` \| `"alarms"` \| `"none"` | Новый режим |

```js
window.pvu3d.updateComparisonDiffMode("power"); // мгновенное переключение
window.pvu3d.updateComparisonDiffMode("none");  // снять выделение
```

> Работает только при активном режиме сравнения; иначе выводит warning.

---

### `getComparisonStats() → object`

Возвращает снимок текущего состояния режима сравнения.

```js
{
  enabled: false,          // boolean — split-screen активен
  split: 0.5,              // number  — соотношение разделения
  orientation: "vertical", // string  — ориентация
  syncCameras: true,       // boolean — синхронизация камер
  diffMode: "status",      // string  — режим выделения
  beforeRefId: null,       // string|null — reference_id "до"
  afterRefId: null,        // string|null — reference_id "после"
  beforeLabel: null,       // string|null — человекочитаемая подпись "до"
  afterLabel: null,        // string|null — подпись "после"
  compatibility: null,     // object|null — результат проверки совместимости
  dataLoaded: false,       // boolean — обе стороны загружены
}
```

---

## 3. Bridge (`window.dash_clientside.pvu3dBridge.syncComparisonMode`)

Clientside-функция, связанная в `callbacks.py`. Принимает 7 входов и возвращает
9 выходов (echo-нормализация контролов + текст совместимости + текст
статистики).

**Входы (Inputs):** `enabled`, `before-source`, `after-source`, `split`,
`orientation`, `sync-cameras`, `diff-mode`.

**Выходы (Outputs):** те же 7 значений (нормализованные) +
`comparison-compatibility.children` + `comparison-stats.children`.

Логика:
1. Нет `window.pvu3d` → "Режим сравнения недоступен".
2. Чекбокс выключен → `setComparisonMode("off")`.
3. Не выбраны оба источника → подсказка выбрать оба.
4. Источники совпадают → "⚠️ Выберите разные источники".
5. Изменился только `diffMode` при активном режиме → `updateComparisonDiffMode`
   (быстрый путь, без перезагрузки).
6. Иначе → `loadComparisonData(...).then(setComparisonMode("split", …))`.

---

## 4. REST-эндпоинты (`/api/comparison/*`)

| Метод | Путь | Назначение |
|-------|------|------------|
| `GET`  | `/api/comparison/runs` | Снимок: доступные источники + дефолтная пара |
| `POST` | `/api/comparison/runs/before` | Сохранить именованный снимок "до" |
| `POST` | `/api/comparison/runs/after` | Сохранить именованный снимок "после" |
| `POST` | `/api/comparison/runs/build` | Построить `RunComparison` по двум reference_id |

**Тело `POST /runs/build`:**
```json
{ "before_reference_id": "snapshot:before", "after_reference_id": "active-run" }
```

**Ключевые поля ответа `RunComparison`:**
- `before_source` / `after_source` — `RunComparisonSource` (`reference_id`,
  `display_label`, `status`, `alarm_count`, `step_minutes`, `horizon_minutes`,
  `point_count`, …).
- `compatibility` — `{ is_compatible, status, summary, issues[], validated_rules[] }`.
- `interpretation` — `{ status, summary, improved_metrics[], worsened_metrics[],
  unchanged_metrics[], top_deltas[] }`.
- `metric_deltas[]`, `trend_deltas[]`.

### Типы источников (reference_id)

| Префикс | Тип | Описание |
|---------|-----|----------|
| `active-run` | active | Текущий активный прогон |
| `archive:<id>` | archive | Прогон из архива сценариев |
| `snapshot:<role>` | snapshot | Именованный снимок (`before` / `after`) |

### Правила совместимости

Сравнение разрешено только если совпадают: шаг времени, горизонт тренда,
число точек, временная сетка тренда и набор KPI-полей состояния. Источники
также должны различаться. Все дельты считаются как **после − до**.

---

## 5. Режимы выделения различий

Выделение применяется **только к сцене "после"**. Порог значимости —
`DIFF_THRESHOLD = 0.05` (5%).

### Цветовая палитра

| Тип | Цвет | Hex | Значение |
|-----|------|-----|----------|
| improved | 🟢 зелёный | `0x10b981` | Метрика улучшилась |
| worsened | 🔴 красный | `0xef4444` | Метрика ухудшилась |
| unchanged | ⚪ серый | `0x6b7280` | Без значимых изменений |
| new | 🔵 синий | `0x3b82f6` | Элемент появился в "после" |
| removed | 🟣 фиолетовый | `0x8b5cf6` | Элемент удалён в "после" |

### Режимы (`diffMode`)

| Режим | Что сравнивает | Логика дельты |
|-------|----------------|---------------|
| `status` | Статусы узлов | green=1, amber=0, red=−1, inactive=−0.5 |
| `temperature` | Температуру | нормализация дельты по 10 °C |
| `power` | Энергопотребление | дельта/средняя; ниже = лучше |
| `alarms` | Тревоги | меньше тревог = улучшение (±0.5) |
| `none` | — | Выделение снято |

Для узлов и сенсоров применяется `material.emissive` (intensity 0.3); для
потоков — `material.color`.

---

## 6. Камеры

При `syncCameras: true` камера сцены "после" копирует каждый кадр
`position`, `rotation`, `quaternion`, `zoom`, `fov`, `near`, `far` основной
камеры (`_syncCameras()` в render loop). `aspect` не копируется — он задаётся
индивидуально для каждого viewport. Overhead ≈0.1 мс/кадр.

---

## 7. Визуальные элементы (CSS-оверлеи)

- `#pvu3d-comparison-divider` — разделительная линия между viewport.
- `#pvu3d-comparison-label-before` / `-after` — подписи; берут текст из
  `display_label` источников (fallback «До» / «После»).

Оверлеи создаются при включении split-режима и удаляются при `setComparisonMode("off")`.

---

## 8. Ограничения

- ⚠️ Захват скриншота в split-режиме пока не поддерживается.

---

См. также: [`TASK_3.2_USAGE_EXAMPLES.md`](TASK_3.2_USAGE_EXAMPLES.md) —
пошаговые сценарии использования.
