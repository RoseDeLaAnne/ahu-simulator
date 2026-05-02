# Стратегия визуализации

## Цель

Для текущего этапа проекта визуализация должна решать две задачи одновременно:

- дать полноценную 2D-модель установки для MVP и защиты;
- не закрыть путь к следующему этапу, где будет подключаться 3D-представление.

Поэтому 2D считается обязательной частью реализации, а 3D сейчас рассматривается как следующий слой, под который уже на этапе MVP закладывается технический фундамент.

## Принятое решение

### Что делаем сейчас

- основное представление установки строится как 2D SVG-мнемосхема;
- 2D-модель живет в `ui/assets`, а не кодируется как случайный набор `html.Div`;
- визуальные состояния узлов не вычисляются внутри SVG и не смешиваются с расчетной моделью;
- поверх расчетного результата формируется отдельный view-model слой визуальных сигналов.

### Что готовим на следующий этап

- единые `visual_id` для узлов, датчиков и потоков;
- общий словарь визуальных сигналов для 2D и 3D;
- scene bindings, связывающие сигнал модели и элемент сцены;
- отдельную структуру каталогов для будущих 3D-ассетов и scene-конфигураций.

## Реализовано на 2026-04-04

- SVG-мнемосхема вынесена в `src/app/ui/assets/pvu_mnemonic.svg`.
- Clientside-рендер привязки сигналов реализован в `src/app/ui/assets/visualization.js`.
- Clientside browser/WebGL-диагностика реализована в `src/app/ui/assets/browser_diagnostics.js`.
- Зафиксированный browser/demo-PC profile хранится в `data/visualization/browser_capability_profile.json`.
- Преобразование `SimulationResult -> VisualizationSignalMap` вынесено в `src/app/ui/viewmodels/visualization.py`.
- Форматирование browser diagnostics для Dash вынесено в `src/app/ui/viewmodels/browser_diagnostics.py`.
- Сравнение live snapshot с verified browser profile вынесено в `src/app/services/browser_capability_service.py`.
- Scene bindings и их валидация вынесены в `src/app/ui/scene/bindings.py`.
- Базовый файл scene metadata подготовлен в `data/visualization/scene3d.json`.
- Ручные скриншоты Playwright перенесены в `artifacts/playwright/manual/YYYY-MM-DD/...`.

## Зафиксированные `visual_id`

### Узлы

- `outdoor_air`
- `filter_bank`
- `heater_coil`
- `supply_fan`
- `supply_duct`
- `room_zone`

### Датчики

- `sensor_outdoor_temp`
- `sensor_filter_pressure`
- `sensor_supply_temp`
- `sensor_airflow`
- `sensor_room_temp`

### Потоки

- `flow_outdoor_to_filter`
- `flow_filter_to_heater`
- `flow_heater_to_fan`
- `flow_fan_to_room`

## Принципы реализации 2D-модели

### Формат

- использовать SVG как основной формат схемы;
- использовать `viewBox`, чтобы схема адаптивно масштабировалась;
- не привязывать 2D-схему к одному разрешению экрана;
- слои SVG разделять по смыслу: оборудование, воздуховоды, датчики, подписи, overlays тревог.

### Привязка к модели

- каждый визуальный элемент получает стабильный `visual_id`;
- данные из `SimulationResult` преобразуются в `VisualizationSignalMap`;
- 2D использует только этот набор сигналов, а не прямой доступ к внутренним формулам;
- цвет, текст, иконка тревоги и анимация потока задаются правилами на уровне UI-адаптера.

### Обновление UI

- медленные и расчетные изменения остаются в Python-callbacks;
- частые косметические обновления допускается переводить в clientside callbacks;
- вся логика, критичная для модели, остается на стороне Python.

### Текущее разделение ответственности

- Python-callbacks считают модель, формируют alarms, summary, trend и наполняют `dcc.Store` визуальными сигналами.
- Clientside callback обновляет SVG: цвета узлов, подписи, тревожные бейджи и анимацию потоков без повторного серверного рендера.
- Отдельный clientside callback собирает browser/WebGL capability snapshot, а Python-слой форматирует его в безопасную текстовую панель для phase 7.

## Browser diagnostics и WebGL-ограничения

- будущий 3D-режим не должен подключаться вслепую: перед этим нужно понимать, доступен ли `webgl`, `webgl2`, secure context и какой графический renderer отдает браузер;
- для этого в UI добавлена встроенная панель Browser / WebGL, которая собирает capability snapshot на стороне клиента и не влияет на расчетный слой;
- поверх live snapshot проект теперь хранит `browser_capability_profile.json`, где зафиксированы verified environment, требования future WebGL-envelope и рекомендуемый viewport;
- `GET /visualization/browser-profile` и dashboard-блок `Verified Browser Profile` показывают, совпадает ли текущий браузер с уже подтверждённой средой;
- если WebGL недоступен или ограничен, основной renderer для защиты остаётся 2D SVG.

## Фундамент под 3D

### Что обязательно подготовить

- таблицу соответствия `visual_id -> scene node`;
- формат scene metadata в `data/visualization`;
- единый словарь статусов и цветовых состояний для 2D и 3D;
- разделение слоев `simulation -> service -> visualization view-model -> renderer`.

### Принятый формат переключения `2D <-> 3D`

- расчетный слой и API отдают единый `VisualizationSignalMap`;
- 2D использует SVG renderer, 3D будет использовать scene renderer;
- выбор renderer выполняется только на уровне UI-адаптера и не затрагивает `simulation` и `services`.

### Что не делаем в MVP

- детальную геометрию установки;
- полноценную камеру и навигацию по сцене;
- обязательную WebGL-зависимость для основного показа;
- попытку смешать 2D и 3D в одном неуправляемом callback-слое.

## Следующий этап: реализация optional 3D-viewer

### Цель следующего этапа

- подключить реальную 3D-сцену без изменений `simulation`, `services` и `GET /visualization/state`;
- сохранить 2D SVG как гарантированный fallback-path;
- перевести 3D в режим отдельного renderer/adaptor с собственным lifecycle и cleanup.

### Технический scope

- `three.js` подключается как browser-side renderer в текущий Dash-стек через локальные assets;
- основным форматом сцены считается `GLB/GLTF`, потому что он сохраняет scene graph, материалы, камеры и возможные анимации;
- текущий `scene3d.json` расширяется от простого bindings-файла до scene metadata контракта между моделью, UI и ассетом.

### Что нужно добавить в данные

- реальный `GLB/GLTF`-файл установки и связанные текстуры в `data/visualization/assets`;
- стабильные имена узлов в 3D-модели, совпадающие с `scene_node` в `data/visualization/scene3d.json`;
- metadata по стартовой камере, допустимым interaction-targets, точкам привязки подписей и правилам animation/highlight;
- metadata по performance budget: ожидаемый размер canvas, допустимый quality-level и условия принудительного fallback в 2D.

### Что нужно добавить в UI

- selector режима `2D / 3D` в dashboard;
- отдельный контейнер `scene-3d-container` рядом с существующей SVG-мнемосхемой;
- новый clientside renderer-asset, который:
  - создаёт `scene`, `camera`, `renderer` и `controls`;
  - загружает `GLB/GLTF` через `GLTFLoader`;
  - реагирует на resize контейнера;
  - освобождает GPU-ресурсы и DOM/listener state при teardown.

### Что нужно добавить в runtime

- слой применения `VisualizationSignalMap` к 3D-узлам: `visible`, `material.color`, `emissive`, label text и flow intensity;
- picking через `Raycaster` для hover/click по узлам сцены;
- camera-controls через `OrbitControls` с ограничениями, чтобы пользователь не терял сцену;
- optional animation-layer для потока воздуха, тревог и вращения вентилятора, который не зависит от перерасчёта Python-ядра на каждый кадр.

### Ограничения и guardrails

- 3D не должен становиться единственным renderer, пока проект опирается на browser/WebGL envelope конкретного demo-PC;
- все отказные состояния `loading`, `asset error`, `webgl unavailable`, `context lost` должны мягко возвращать пользователя к 2D-режиму;
- обновление visual signals должно оставаться совместимым с существующим SVG-renderer;
- если verified browser profile меняется, сначала обновляются `browser_capability_profile.json` и evidence, а уже потом включается новый 3D-scope.

### Критерии готовности следующего этапа

- одна и та же симуляция обновляет и 2D, и 3D через единый `VisualizationSignalMap`;
- переключение между renderer-режимами не требует рестарта приложения и не ломает dashboard-state;
- пользователь может вращать сцену, приближать её и выбирать узлы кликом;
- при сбое WebGL или загрузки ассета интерфейс автоматически остаётся работоспособным в 2D;
- у проекта есть отдельный checklist по 3D smoke-test и обновлённые Playwright-артефакты для verified browser/demo-PC.

## Рекомендуемая структура

```text
src/app/ui/
  dashboard.py
  layout.py
  callbacks.py
  viewmodels/
    browser_diagnostics.py
    visualization.py
  scene/
    bindings.py
  assets/
    browser_diagnostics.js
    dashboard.css
    pvu_mnemonic.svg
    visualization.js

data/visualization/
  browser_capability_profile.json
  scene3d.json

artifacts/playwright/
  README.md
  manual/
    YYYY-MM-DD/
      dashboard/
```

## Этапы реализации

1. Описать состав узлов 2D-модели и зафиксировать `visual_id`.
2. Подготовить SVG-каркас установки с адаптивным `viewBox`.
3. Вынести преобразование `SimulationResult -> visualization signals` в отдельный модуль.
4. Привязать цвета, подписи, тревоги и поток к SVG-элементам.
5. Зафиксировать scene bindings и зарезервировать формат 3D-конфигурации.
6. Подтвердить browser/demo-PC envelope и сохранить verified profile вместе с Playwright-evidence.

## Критерий успеха

2D-визуализация должна быть уже достаточно выразительной для защиты, а включение будущего 3D-слоя должно требовать добавления нового renderer, а не пересборки расчетного ядра, API и сценарной логики.

## Реализовано: Optional 3D-viewer (P3)

### Дата реализации

2026-04-04.

### Что сделано

- three.js r170 загружен как локальные ES-модули в `src/app/ui/assets/vendor/three/` (без npm/bundler).
- Интеграция выполнена через `<script type="importmap">` в `app.index_string`, что обеспечивает корректное разрешение bare specifier `"three"` до загрузки модулей.
- Процедурная GLB-модель установки сгенерирована в `data/visualization/assets/pvu_installation.glb` (24 KB) с именами узлов, совпадающими с `scene_node` из `scene3d.json`.
- `scene3d.json` расширен до версии 2: camera presets (default/top/front), orbit controls, performance budget, interactive targets, animation rules (fan rotation, flow pulse), status colors, emissive highlight, export rules.
- Pydantic-валидация в `bindings.py` расширена 10+ моделями для полной валидации scene3d.json v2.
- В dashboard добавлен переключатель `2D / 3D` с отдельными контейнерами `scene-2d-wrapper` и `scene-3d-wrapper`.
- Создан `viewer3d.mjs` (~500 строк): init → loadModel → animate → applySignals → dispose, с полным lifecycle WebGL-renderer.
- Реализован маппинг `VisualizationSignalMap → scene nodes`: цвет, видимость, emissive/alarm, интенсивность потока.
- Hover/click picking через `Raycaster` с выводом информационной карточки элемента.
- Animation layer: вращение вентилятора, пульсация потока, alarm flash — без зависимости от Python-ядра.
- Обработка отказных состояний: loading overlay, WebGL unavailable, context lost → автоматический возврат в 2D.
- Полная очистка ресурсов при `dispose()`: geometries, materials, textures, event listeners.
- `viewer3d_bridge.js` — Dash clientside callback bridge для `switchRenderMode` и `updateViewer3d`.
- CSS-стили для 3D-контейнера, toggle, overlay, info card (~130 строк).
- Все 67 тестов проходят.
- Playwright-верификация: 3D-сцена рендерится корректно, переключение 2D↔3D работает, fallback сохраняется.

### Добавленные файлы

```text
src/app/ui/assets/
  vendor/three/
    three.module.min.mjs          # three.js r170 core (691 KB)
    addons/loaders/GLTFLoader.mjs # GLTF loader (110 KB)
    addons/controls/OrbitControls.mjs # camera controls (32 KB)
    addons/utils/BufferGeometryUtils.js # geometry utils (32 KB)
  viewer3d.mjs                    # 3D viewer ES module
  viewer3d_bridge.js              # Dash clientside callback bridge
  pvu_installation.glb            # procedural GLB model (24 KB)
src/app/ui/scene/
  generate_glb.py                 # GLB generator script
data/visualization/assets/
  pvu_installation.glb            # source GLB model
```

### Изменённые файлы

```text
src/app/ui/dashboard.py           # index_string с importmap, assets_ignore=r"\.mjs$"
src/app/ui/layout.py              # dcc.Store, 2D/3D toggle, 3D container
src/app/ui/callbacks.py           # 2 clientside callbacks для 3D mode
src/app/ui/scene/bindings.py      # 10+ Pydantic-моделей для scene3d v2
src/app/ui/assets/dashboard.css   # CSS для 3D viewer (~130 строк)
data/visualization/scene3d.json   # v1 → v2, полный scene metadata
```

### Критерии готовности (проверены)

- [x] Одна и та же симуляция обновляет и 2D, и 3D через единый `VisualizationSignalMap`.
- [x] Переключение между renderer-режимами не требует рестарта приложения.
- [x] Пользователь может вращать сцену, приближать её и кликать на узлы.
- [x] При сбое WebGL интерфейс автоматически остаётся работоспособным в 2D.
- [x] Playwright-верификация пройдена.
