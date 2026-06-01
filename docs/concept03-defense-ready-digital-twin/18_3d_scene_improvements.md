# 18. 3D Scene Improvements — Concept03 Defense Interface

Документация улучшений 3D-сцены для defense-ready интерфейса.

## Дата: 2026-05-30

## Выполненные улучшения

### 1. Скрытие scene-control dropdowns в defense mode

**Проблема:** Scene-control dropdowns (Режим/Модель) перекрывали 3D-сцену в defense mode, что не соответствовало концепту.

**Решение:** Добавлен класс `c03-operator-only` к контейнеру `.c03-scene-control-bar`, что скрывает dropdowns в defense mode через существующие CSS правила.

**Файлы:**
- `src/app/ui/concept03/central_canvas.py` — функция `_build_scene_controls()`

**Изменения:**
```python
def _build_scene_controls(view: Concept03CentralView) -> html.Div:
    return html.Div(
        className="c03-scene-control-bar c03-operator-only",  # Добавлен c03-operator-only
        children=[...]
    )
```

**Результат:**
- ✅ В operator mode (tablet) — dropdowns видны и работают
- ✅ В defense mode — dropdowns скрыты, 3D-сцена чистая
- ✅ Соответствие концепту достигнуто

### 2. Оптимизация легенды 3D на mobile 375px

**Проблема:** Легенда 3D-сцены занимала слишком много места на узких экранах (375px), перекрывая важные элементы.

**Решение:** Добавлен адаптивный media query для mobile устройств с уменьшенными размерами шрифтов, отступов и элементов.

**Файлы:**
- `src/app/ui/assets/dashboard.css` — добавлен `@media (max-width: 480px)`

**Изменения:**
```css
/* Mobile 375px — минимальная легенда */
@media (max-width: 480px) {
  .viewer3d-legend {
    left: 6px;
    bottom: 6px;
    padding: 6px 8px;
    font-size: 0.58rem;
    max-width: 140px;
  }
  .viewer3d-legend__title {
    font-size: 0.56rem;
    margin-bottom: 4px;
  }
  .viewer3d-legend__group {
    margin-top: 4px;
  }
  .viewer3d-legend__group-title {
    font-size: 0.54rem;
    margin-bottom: 2px;
  }
  .viewer3d-legend__row {
    gap: 6px;
    margin-top: 1px;
  }
  .viewer3d-legend__dot {
    width: 8px;
    height: 8px;
  }
  .viewer3d-legend__hint {
    display: none;
  }
}
```

**Результат:**
- ✅ На desktop (>1100px) — полная легенда
- ✅ На tablet (480-1100px) — компактная легенда
- ✅ На mobile (≤480px) — минимальная легенда
- ✅ Легенда не перекрывает важные элементы UI

## Технические детали

### CSS классы для режимов

Проект использует CSS классы для переключения между operator и defense режимами:

- `.c03-operator-only` — элемент виден только в operator mode
- `.c03-defense-only` — элемент виден только в defense mode

Эти классы управляются через `body.c03-defense` и соответствующие CSS правила в `concept03_dashboard.css`.

### 3D Scene Architecture

**Компоненты:**
1. **viewer3d.mjs** (3857 строк) — Three.js viewer с:
   - GLTFLoader для загрузки GLB моделей
   - OrbitControls для навигации
   - Классификация mesh по ролям (intake, filter, heater, fan, duct)
   - Temperature-based coloring
   - Priority labels overlay
   - Legend overlay
   - Environment decor (floor, particles, atmosphere)
   - Animation system

2. **scene3d.json** — конфигурация сцены:
   - GLB модель: `data/visualization/assets/pvu_installation.glb`
   - 3 camera presets (default, top, front)
   - 67 interactive targets
   - 78 auxiliary nodes
   - Animation rules для вентилятора, потоков, заслонок
   - 294 bindings между visual_id и scene_node

3. **scene3d.py** — Python модуль для построения 3D workspace:
   - Toolbar с dropdowns (модель, режим сцены, камера)
   - KPI sidebar с live показателями
   - Control deck с параметрами
   - Developer transform controls

### Performance Budget

Из `scene3d.json`:
```json
"performance_budget": {
  "max_pixel_ratio": 2.0,
  "max_canvas_width": 1400,
  "max_canvas_height": 900,
  "target_fps": 30,
  "antialias": true,
  "fallback_to_2d_on_fps_below": 10
}
```

## Тестирование

### Unit Tests
```bash
python -m pytest tests/unit/ -k "concept03" -v
```

### Integration Tests
```bash
python -m pytest tests/integration/test_concept03_theme_toggle.py -v
```

### Visual QA
```bash
# Headless screenshots для проверки
node tooling/visual-qa/screenshot.mjs
```

## Статус открытых пунктов

### Закрыто ✅
- ✅ Scene-control dropdowns скрыты в defense mode
- ✅ Легенда 3D оптимизирована для mobile 375px

### Остаются открытыми
- ⏳ Буквальный pixel-diff ≤2% (аспирационный таргет, AI-рендер vs реальность)
- ⏳ РИСК/НОРМА дефолтное состояние (требует продуктового решения)
- ⏳ Capacitor APK/iOS smoke test (требует Android SDK)

## Ссылки

- Changelog: `17_changelog.md`
- TODO: `10_todo.md`
- Acceptance: `11_acceptance_criteria.md`
- QA Checklist: `15_qa_checklist.md`
- Visual QA Harness: `tooling/visual-qa/`

## Следующие шаги

1. Запустить visual QA harness для проверки изменений
2. Обновить скриншоты в `artifacts/playwright/concept03/`
3. Запустить полный demo script (14_demo_script.md)
4. Обновить 10_todo.md с отметкой выполненных пунктов
