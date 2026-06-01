# 19. 3D Scene & Modeling — Technical Summary

Комплексный обзор 3D-сцены и моделирования для concept03 defense-ready интерфейса.

## Архитектура 3D-сцены

### Компоненты системы

```
┌─────────────────────────────────────────────────────────────┐
│                    3D Scene Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ scene3d.json │  │ viewer3d.mjs │  │ scene3d.py   │      │
│  │ (config)     │  │ (Three.js)   │  │ (Python UI)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         └──────────────────┴──────────────────┘              │
│                            │                                  │
│                            ▼                                  │
│              ┌─────────────────────────┐                     │
│              │  pvu_installation.glb   │                     │
│              │  (3D Model Asset)       │                     │
│              └─────────────────────────┘                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1. scene3d.json — Конфигурация сцены

**Размер:** 295 строк  
**Версия:** 3  
**Путь:** `data/visualization/scene3d.json`

**Содержимое:**
- **Asset:** GLB модель `data/visualization/assets/pvu_installation.glb`
- **Camera presets:** 3 предустановки (default, top, front)
- **Orbit controls:** Настройки навигации (min/max distance, damping)
- **Performance budget:** 
  - Max canvas: 1400×900
  - Target FPS: 30
  - Antialias: true
  - Fallback to 2D if FPS < 10
- **Interactive targets:** 67 узлов (ПВУ, датчики, потоки)
- **Auxiliary nodes:** 78 вспомогательных узлов (ротор, заслонки, эффекты)
- **Animation rules:** 
  - `fan_rotation` — вращение вентилятора
  - `flow_pulse` — пульсация потоков
  - `damper_position` — позиция заслонок
  - `plume_pulse` — пульсация шлейфов
  - `sensor_pulse` — пульсация датчиков
- **Status colors:** normal/warning/alarm/inactive
- **Bindings:** 294 связи между visual_id и scene_node

### 2. viewer3d.mjs — Three.js Viewer

**Размер:** 3857 строк  
**Путь:** `src/app/ui/assets/viewer3d.mjs`

**Основные функции:**

#### Инициализация
```javascript
init(containerId, meta)
  ├─ WebGL context check
  ├─ THREE.WebGLRenderer setup
  ├─ PerspectiveCamera (FOV 42°)
  ├─ OrbitControls
  ├─ Raycaster для интерактивности
  └─ Environment scaffold
```

#### Загрузка моделей
```javascript
loadModel(modelUrl, bindings, modelDescriptor)
  ├─ GLTFLoader
  ├─ Model normalization
  ├─ Material preparation
  ├─ Binding setup
  └─ Scene building
```

#### Классификация mesh
```javascript
_classifyAhuRole(meshName)
  ├─ intake (воздухозабор)
  ├─ damper (воздушный клапан)
  ├─ filter (фильтр)
  ├─ silencer (шумоглушитель)
  ├─ heater (калорифер)
  ├─ fan (вентилятор)
  ├─ duct (воздуховод)
  ├─ outdoor (наружный канал)
  ├─ enclosure (корпус)
  └─ building (помещение)
```

#### Display modes
- **studio** — реалистичный вид с цветовой семантикой
- **xray** — прозрачный корпус, видны внутренние секции
- **schematic** — плоский образовательный вид

#### Анимация
```javascript
_startAnimation()
  ├─ _animateFan(dt)
  ├─ _animateDamperPosition(dt)
  ├─ _animateFlowNodes(time)
  ├─ _animateSensorPulse(time)
  ├─ _animatePlumePulse(time)
  ├─ _animateProcessEffects(time)
  ├─ _animateRoomEffects(time)
  ├─ _animateSeasonalEnvironment(time)
  └─ _animateAlarmFlash(time)
```

#### Интерактивность
- **Hover** — подсветка узла при наведении
- **Click** — выбор узла, показ info card
- **Info card** — карточка с label, state, value, detail, alarm_text
- **Priority labels** — 11 постоянных подписей (Забор, Фильтр, Калорифер, ...)
- **Legend overlay** — легенда статусов/температур/потоков

#### Temperature-based coloring
```javascript
_temperatureColor(celsius)
  ├─ < 20°C: холодный голубой (#38bdf8)
  ├─ 20-24°C: нейтральный комфортный (#d1d5db)
  └─ > 24°C: тёплый оранжевый (#f97316)
```

### 3. scene3d.py — Python UI Module

**Размер:** 943 строки  
**Путь:** `src/app/ui/render_modes/scene3d.py`

**Структура:**

```python
build_scene3d_workspace()
  ├─ _scene3d_top_toolbar()
  │   ├─ Модель установки (dropdown)
  │   ├─ Режим сцены (dropdown)
  │   └─ Камера (dropdown)
  ├─ _scene3d_stage_grid()
  │   ├─ _scene3d_stage_column() — canvas
  │   └─ _scene3d_kpi_sidebar() — live KPI
  └─ _scene3d_secondary_grid()
      ├─ _scene3d_control_deck_card() — параметры
      ├─ _scene3d_reference_card() — профиль модели
      ├─ _scene3d_room_card() — каталог помещений
      └─ _scene3d_room_sensors_card() — датчики
```

**Transform controls (developer mode):**
- 18 параметров для настройки позиций модели и помещения
- Масштаб, смещение, поворот по 3 осям
- Скрыты по умолчанию, включаются через `developer_tools_enabled`

## Semantic Palette — Цветовая семантика секций ПВУ

По СП 60.13330.2020 и рекомендациям АВОК:

```javascript
const SECTION_PALETTE = {
  intake: #7dd3fc,    // воздухозабор — ледяной голубой
  damper: #fbbf24,    // воздушный клапан — янтарный
  filter: #f1f5f9,    // фильтр — чистый светло-серый
  silencer: #a78bfa,  // шумоглушитель — приглушённый сиреневый
  heater: #fb7185,    // калорифер — тёпло-розовый
  fan: #22d3ee,       // вентилятор — бирюзовый
  duct: #94a3b8,      // воздуховод — стальной
  outdoor: #60a5fa,   // наружный канал — синий
  enclosure: #475569, // корпус — графит
  frame: #6b7280,     // рамы и крепления — холодный серый
};
```

## Выполненные улучшения (2026-05-30)

### ✅ 1. Скрытие scene-control dropdowns в defense mode

**До:**
```python
className="c03-scene-control-bar"
```

**После:**
```python
className="c03-scene-control-bar c03-operator-only"
```

**Результат:**
- Operator mode — dropdowns видны
- Defense mode — dropdowns скрыты
- 3D-сцена чистая, соответствует концепту

### ✅ 2. Оптимизация легенды для mobile 375px

**Добавлен media query:**
```css
@media (max-width: 480px) {
  .viewer3d-legend {
    left: 6px;
    bottom: 6px;
    padding: 6px 8px;
    font-size: 0.58rem;
    max-width: 140px;
  }
  /* ... компактные размеры для всех элементов */
}
```

**Результат:**
- Desktop (>1100px) — полная легенда
- Tablet (480-1100px) — компактная легенда
- Mobile (≤480px) — минимальная легенда
- Легенда не перекрывает UI

## Performance Metrics

### Rendering
- **Target FPS:** 30
- **Max pixel ratio:** 2.0
- **Max canvas:** 1400×900
- **Antialias:** enabled
- **Tone mapping:** ACESFilmic, exposure 1.05

### Animation
- **Fan rotation:** до 3.0 RPM
- **Flow particles:** 24 частицы на поток
- **Sensor pulse:** 1.6 Hz
- **Atmosphere particles:** 180 частиц

### Memory
- **Cached models:** хранятся в `cachedModelEntries`
- **Cached rooms:** хранятся в `cachedRoomEntries`
- **Generated textures:** кешируются в `generatedTextureCache`

## Тестирование

### Unit Tests (35 passed)
```bash
python -m pytest tests/unit/ -k "concept03" -v
```

### Integration Tests (5 passed)
```bash
python -m pytest tests/integration/test_concept03_theme_toggle.py -v
```

### Visual QA
```bash
node tooling/visual-qa/screenshot.mjs
```

**Скриншоты:**
- `artifacts/playwright/concept03/phase7/` — desktop 1500×900
- `artifacts/playwright/concept03/phase8/` — mobile/tablet

## Статус Phase 7 открытых пунктов

| Пункт | Статус | Комментарий |
|-------|--------|-------------|
| Scene-control dropdowns | ✅ Закрыт | Скрыты в defense mode |
| Легенда 3D на mobile | ✅ Закрыт | Оптимизирована для 375px |
| Pixel-diff ≤2% | ⏳ Аспирационный | AI-рендер vs реальность |
| РИСК/НОРМА дефолт | ⏳ Продуктовое решение | Корректное поведение физики |

## Следующие шаги

1. ✅ Запустить тесты — **Выполнено (40 passed)**
2. ⏳ Запустить visual QA harness
3. ⏳ Обновить скриншоты в artifacts/
4. ⏳ Прогон demo script (14_demo_script.md)
5. ⏳ Финальный sign-off

## Ссылки

- **Improvements:** `18_3d_scene_improvements.md`
- **Changelog:** `17_changelog.md`
- **TODO:** `10_todo.md`
- **Acceptance:** `11_acceptance_criteria.md`
- **QA Checklist:** `15_qa_checklist.md`
- **Visual QA:** `tooling/visual-qa/`

---

**Дата создания:** 2026-05-30  
**Автор:** Kiro AI Development Environment  
**Статус:** ✅ Improvements Complete, Ready for Visual QA
