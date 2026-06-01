# Задача 3.2: Режим сравнения (Side-by-Side)

**Дата создания:** 2026-05-31  
**Статус:** В работе  
**Приоритет:** Средний  
**Сложность:** Высокая

---

## Цель

Реализовать режим визуального сравнения двух состояний 3D-модели ПВУ side-by-side с синхронизацией камер, загрузкой разных состояний симуляции и визуальным выделением различий.

---

## Требования

### Функциональные требования

1. **Разделение viewport**
   - Split-screen режим: вертикальное разделение 50/50
   - Опциональное горизонтальное разделение
   - Настраиваемое соотношение (30/70, 40/60, 50/50, 60/40, 70/30)
   - Возможность переключения между single и split режимами

2. **Синхронизация камер**
   - Синхронизация позиции камеры между левым и правым viewport
   - Синхронизация target (точка, на которую смотрит камера)
   - Синхронизация zoom
   - Опция включения/выключения синхронизации
   - Независимое управление камерами при выключенной синхронизации

3. **Загрузка состояний**
   - Загрузка "до" состояния в левый viewport
   - Загрузка "после" состояния в правый viewport
   - Интеграция с существующим comparison API
   - Поддержка источников: active run, archived runs, named snapshots
   - Автоматическое обновление при изменении данных

4. **Визуальное выделение различий**
   - Цветовое кодирование изменений:
     - Зелёный: улучшение (например, снижение температуры)
     - Красный: ухудшение (например, повышение температуры)
     - Жёлтый: незначительное изменение
     - Серый: без изменений
   - Режимы выделения:
     - По статусу узлов (normal → warning → alarm)
     - По температуре (тепловая карта дельт)
     - По мощности (энергопотребление)
     - По тревогам (появление/исчезновение)
   - Легенда с пояснениями

5. **Режим "до/после"**
   - Выбор пары для сравнения из UI
   - Dropdown с доступными источниками
   - Автоматический выбор default пары (named snapshots или последний архив + active)
   - Проверка совместимости (одинаковый шаг, горизонт, временная сетка)
   - Отображение метаданных источников (label, timestamp, scenario)

6. **Экспорт сравнительных отчётов**
   - Захват скриншота split-screen режима
   - Включение метаданных сравнения
   - Автоматическая генерация имени файла
   - Опциональное включение легенды различий

### Нефункциональные требования

1. **Производительность**
   - FPS не должен падать ниже 20 в split режиме
   - Overhead на второй renderer: < 50% CPU/GPU
   - Время переключения между режимами: < 500ms
   - Плавная синхронизация камер без рывков

2. **Совместимость**
   - Работа со всеми существующими display modes (studio, xray, schematic)
   - Совместимость с bloom, heatmap, clipping planes, LOD
   - Корректная работа с flow field visualization
   - Поддержка measurement tools в обоих viewport

3. **Удобство использования**
   - Интуитивный UI для выбора источников
   - Понятные индикаторы "до" и "после"
   - Быстрое переключение между single и split режимами
   - Сохранение настроек в session

---

## Архитектура

### Компоненты

#### 1. Dual Renderer System (viewer3d.mjs)

```javascript
// State variables
let comparisonMode = false;
let comparisonSplit = 0.5; // 50/50 split
let comparisonOrientation = "vertical"; // "vertical" | "horizontal"
let comparisonSyncCameras = true;

// Renderers and scenes
let leftRenderer = null;
let rightRenderer = null;
let leftScene = null;
let rightScene = null;
let leftCamera = null;
let rightCamera = null;
let leftControls = null;
let rightControls = null;

// Comparison data
let comparisonBeforeData = null;
let comparisonAfterData = null;
let comparisonDiffMode = "status"; // "status" | "temperature" | "power" | "alarms"
```

#### 2. Comparison Data Loader (viewer3d.mjs)

```javascript
async function loadComparisonData(beforeRefId, afterRefId) {
  // Fetch comparison from API
  const response = await fetch("/api/comparison/runs/build", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      before_reference_id: beforeRefId,
      after_reference_id: afterRefId
    })
  });
  
  const comparison = await response.json();
  
  // Store data
  comparisonBeforeData = comparison.before_source;
  comparisonAfterData = comparison.after_source;
  
  // Apply to scenes
  _applyComparisonState(leftScene, comparison.before_source);
  _applyComparisonState(rightScene, comparison.after_source);
  
  // Highlight differences
  _highlightDifferences(comparison);
}
```

#### 3. Camera Synchronization (viewer3d.mjs)

```javascript
function _syncCameras() {
  if (!comparisonSyncCameras || !leftCamera || !rightCamera) return;
  
  // Sync position
  rightCamera.position.copy(leftCamera.position);
  
  // Sync target (via controls)
  if (leftControls && rightControls) {
    rightControls.target.copy(leftControls.target);
    rightControls.update();
  }
  
  // Sync zoom
  rightCamera.zoom = leftCamera.zoom;
  rightCamera.updateProjectionMatrix();
}
```

#### 4. Difference Highlighting (viewer3d.mjs)

```javascript
function _highlightDifferences(comparison) {
  if (!comparison.compatibility.is_compatible) {
    console.warn("Cannot highlight differences: incompatible comparison");
    return;
  }
  
  // Iterate through metric deltas
  for (const delta of comparison.metric_deltas) {
    const color = _getDeltaColor(delta);
    _applyDeltaColor(delta.metric_id, color);
  }
  
  // Highlight alarm changes
  _highlightAlarmChanges(
    comparison.before_source.alarm_count,
    comparison.after_source.alarm_count
  );
}

function _getDeltaColor(delta) {
  const direction = _getMetricDirection(delta.metric_id);
  const tolerance = Math.abs(delta.before_value) * 0.005;
  
  if (Math.abs(delta.delta_value) <= tolerance) {
    return 0x808080; // Gray: no change
  }
  
  if (direction === 0) {
    return 0xFFFF00; // Yellow: neutral change
  }
  
  if (delta.delta_value * direction > 0) {
    return 0x00FF00; // Green: improvement
  } else {
    return 0xFF0000; // Red: worsening
  }
}
```

#### 5. UI Controls (scene3d.py)

```python
def _scene3d_comparison_tools() -> html.Details:
    """Контролы для режима сравнения side-by-side."""
    return html.Details(
        className="scene3d-dev-controls",
        children=[
            html.Summary("⚖️ Режим сравнения"),
            html.Div([
                # Enable/disable comparison mode
                dcc.Checklist(
                    id="scene3d-comparison-enabled",
                    options=[{"label": " Включить сравнение", "value": "enabled"}],
                    value=[],
                ),
                
                # Before source selector
                html.Label("До:"),
                dcc.Dropdown(
                    id="scene3d-comparison-before-source",
                    options=[],  # Populated dynamically
                    value=None,
                    placeholder="Выберите источник 'до'",
                ),
                
                # After source selector
                html.Label("После:"),
                dcc.Dropdown(
                    id="scene3d-comparison-after-source",
                    options=[],  # Populated dynamically
                    value=None,
                    placeholder="Выберите источник 'после'",
                ),
                
                # Split ratio slider
                html.Label("Соотношение разделения:"),
                dcc.Slider(
                    id="scene3d-comparison-split",
                    min=0.3, max=0.7, step=0.1, value=0.5,
                    marks={0.3: "30/70", 0.5: "50/50", 0.7: "70/30"},
                ),
                
                # Orientation toggle
                dcc.RadioItems(
                    id="scene3d-comparison-orientation",
                    options=[
                        {"label": " Вертикальное", "value": "vertical"},
                        {"label": " Горизонтальное", "value": "horizontal"},
                    ],
                    value="vertical",
                ),
                
                # Camera sync toggle
                dcc.Checklist(
                    id="scene3d-comparison-sync-cameras",
                    options=[{"label": " Синхронизировать камеры", "value": "sync"}],
                    value=["sync"],
                ),
                
                # Difference mode selector
                html.Label("Режим выделения различий:"),
                dcc.Dropdown(
                    id="scene3d-comparison-diff-mode",
                    options=[
                        {"label": "По статусу", "value": "status"},
                        {"label": "По температуре", "value": "temperature"},
                        {"label": "По мощности", "value": "power"},
                        {"label": "По тревогам", "value": "alarms"},
                    ],
                    value="status",
                    clearable=False,
                ),
                
                # Compatibility status
                html.Div(
                    id="scene3d-comparison-compatibility",
                    children="Выберите источники для сравнения",
                ),
                
                # Statistics display
                html.Div(
                    id="scene3d-comparison-stats",
                    children="",
                ),
            ]),
        ],
    )
```

#### 6. Bridge Function (viewer3d_bridge.js)

```javascript
function syncComparisonMode(
  enabledCheckbox,
  beforeSource,
  afterSource,
  split,
  orientation,
  syncCamerasCheckbox,
  diffMode
) {
  var enabled = Array.isArray(enabledCheckbox) && enabledCheckbox.includes("enabled");
  var syncCameras = Array.isArray(syncCamerasCheckbox) && syncCamerasCheckbox.includes("sync");
  
  if (!enabled) {
    window.pvu3d.setComparisonMode("off");
    return [
      [],
      beforeSource,
      afterSource,
      split,
      orientation,
      ["sync"],
      diffMode,
      "Режим сравнения выключен",
      ""
    ];
  }
  
  if (!beforeSource || !afterSource) {
    return [
      ["enabled"],
      beforeSource,
      afterSource,
      split,
      orientation,
      syncCameras ? ["sync"] : [],
      diffMode,
      "Выберите оба источника для сравнения",
      ""
    ];
  }
  
  // Load comparison data
  window.pvu3d.loadComparisonData(beforeSource, afterSource).then(function() {
    window.pvu3d.setComparisonMode("split", {
      split: split,
      orientation: orientation,
      syncCameras: syncCameras,
      diffMode: diffMode
    });
  });
  
  var stats = window.pvu3d.getComparisonStats();
  var compatibilityText = _formatCompatibility(stats.compatibility);
  var statsText = _formatComparisonStats(stats);
  
  return [
    ["enabled"],
    beforeSource,
    afterSource,
    split,
    orientation,
    syncCameras ? ["sync"] : [],
    diffMode,
    compatibilityText,
    statsText
  ];
}
```

---

## API Design

### Public API (viewer3d.mjs)

```javascript
// Enable/disable comparison mode
window.pvu3d.setComparisonMode(mode, options)
// mode: "off" | "split"
// options: {split, orientation, syncCameras, diffMode}

// Load comparison data from API
window.pvu3d.loadComparisonData(beforeRefId, afterRefId)
// Returns: Promise<ComparisonData>

// Get comparison statistics
window.pvu3d.getComparisonStats()
// Returns: {enabled, compatibility, beforeLabel, afterLabel, diffMode, ...}

// Capture split-screen screenshot
window.pvu3d.captureComparisonScreenshot(options)
// options: {scale, format, includeMetadata, includeLegend}
```

---

## Этапы реализации

### Этап 1: Dual Renderer Setup (4 часа)
- [ ] Создать второй renderer и scene
- [ ] Реализовать split viewport (вертикальное разделение)
- [ ] Настроить aspect ratio для обоих камер
- [ ] Интегрировать в render loop
- [ ] Тестирование базового split режима

### Этап 2: Camera Synchronization (2 часа)
- [ ] Реализовать синхронизацию позиции камеры
- [ ] Синхронизация target через controls
- [ ] Синхронизация zoom
- [ ] Добавить toggle для включения/выключения
- [ ] Тестирование плавности синхронизации

### Этап 3: Comparison Data Integration (3 часа)
- [ ] Создать функцию loadComparisonData()
- [ ] Интеграция с /api/comparison/runs/build
- [ ] Применение состояний к левой и правой сценам
- [ ] Обработка ошибок и несовместимости
- [ ] Тестирование загрузки данных

### Этап 4: Difference Highlighting (4 часа)
- [ ] Реализовать цветовое кодирование дельт
- [ ] Режим выделения по статусу
- [ ] Режим выделения по температуре
- [ ] Режим выделения по мощности
- [ ] Режим выделения по тревогам
- [ ] Создать легенду различий
- [ ] Тестирование визуализации

### Этап 5: UI Controls (2 часа)
- [ ] Создать UI панель в scene3d.py
- [ ] Добавить dropdowns для выбора источников
- [ ] Populate источников из comparison API
- [ ] Slider для split ratio
- [ ] Radio buttons для orientation
- [ ] Checkbox для camera sync
- [ ] Dropdown для diff mode
- [ ] Тестирование UI

### Этап 6: Bridge Integration (2 часа)
- [ ] Создать syncComparisonMode() в viewer3d_bridge.js
- [ ] Форматирование compatibility status
- [ ] Форматирование statistics
- [ ] Добавить clientside callback в callbacks.py
- [ ] Тестирование интеграции

### Этап 7: Screenshot Export (1 час)
- [ ] Расширить captureScreenshot() для split режима
- [ ] Добавить опцию includeLegend
- [ ] Включение comparison metadata
- [ ] Тестирование экспорта

### Этап 8: Testing & Documentation (2 часа)
- [ ] Тестирование всех режимов
- [ ] Проверка производительности
- [ ] Проверка совместимости с другими features
- [ ] Создание документации API
- [ ] Создание примеров использования

**Общее время:** ~20 часов

---

## Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Падение FPS в split режиме | Высокая | Высокое | LOD, упрощение эффектов, опциональный split |
| Сложность синхронизации камер | Средняя | Среднее | Использовать события controls, throttling |
| Проблемы с памятью (2 сцены) | Средняя | Высокое | Shared geometries, dispose при выключении |
| Несовместимость источников | Низкая | Среднее | Проверка compatibility, понятные сообщения |

---

## Метрики успеха

1. **Производительность:**
   - FPS в split режиме: ≥ 20
   - Overhead на второй renderer: < 50%
   - Время переключения режимов: < 500ms

2. **Функциональность:**
   - Корректная синхронизация камер
   - Точное выделение различий
   - Работа со всеми источниками comparison API

3. **Удобство:**
   - Интуитивный выбор источников
   - Понятная визуализация различий
   - Быстрое переключение режимов

---

## Следующие шаги

1. Начать с Этапа 1: Dual Renderer Setup
2. Создать базовый split viewport
3. Интегрировать в render loop
4. Тестировать производительность

**Дата начала:** 2026-05-31  
**Ожидаемое завершение:** 2026-06-01
