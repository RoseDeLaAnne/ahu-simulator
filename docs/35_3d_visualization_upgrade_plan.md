# План доведения 3D-визуализации до целевого уровня

Дата: 2026-05-02.

## Назначение

Этот документ фиксирует курс доведения текущего optional 3D-viewer до состояния
защитной инженерной 3D-визуализации: крупный читаемый цифровой двойник ПВУ,
понятные потоки воздуха, температурно-давленческие эффекты, интерактивные
датчики, устойчивый 2D fallback и проверяемое качество показа.

Подробный рабочий handoff сохранен в
`.omx/plans/3d_visualization_upgrade_plan.md`, To-Do - в
`.omx/plans/3d_visualization_upgrade_todo.md`, приемка - в
`.omx/plans/3d_visualization_acceptance_matrix.md`, визуальная карта курса - в
`docs/36_3d_visualization_course_map.md`, стартовый prompt и визуальный ориентир - в
`docs/37_3d_visualization_start_prompt.md` и
`docs/assets/3d_visualization_final_reference_ru.png`. Копия prompt для OMX-сессии
лежит в `.omx/plans/3d_visualization_new_session_prompt.md`.

## Северная звезда

3D-режим должен выглядеть не как декоративная модель, а как рабочее инженерное
окно:

- главный viewport занимает визуальный приоритет и сразу показывает ПВУ;
- модель читается по секциям: intake, filter, coil, fan, dampers, supply, room;
- пользователь видит причинно-следственную связь: параметры -> расчет ->
  статус -> цвет/эффект/подпись в сцене;
- 3D остается optional renderer поверх `VisualizationSignalMap`, а не вторым
  расчетным ядром;
- 2D SVG остается надежным fallback для защиты.

## Текущее основание

У проекта уже есть рабочая база, которую нужно не переписывать, а
последовательно усилить:

- 3D workspace и панель управления строятся в
  `src/app/ui/render_modes/scene3d.py`, включая `build_scene3d_workspace()` и
  developer transform controls.
- Browser-side renderer находится в `src/app/ui/assets/viewer3d.mjs`: lifecycle
  `init()`, `loadModel()`, `applySignals()`, `setDisplayMode()`,
  `setCameraPreset()`, `dispose()`.
- Dash bridge находится в `src/app/ui/assets/viewer3d_bridge.js`: переключение
  2D/3D, обновление viewer и синхронизация transform controls.
- Единый контракт сигналов строится в
  `src/app/ui/viewmodels/visualization.py` через `VisualizationSignalMap`.
- Scene metadata и валидация находятся в
  `data/visualization/scene3d.json` и `src/app/ui/scene/bindings.py`.
- Текущий визуальный результат уже подтверждает, что WebGL path работает, но
  нуждается в композиционной, семантической и UX-доводке.

## Использованные ориентиры

Сверка выполнена через Context7 и веб-поиск по официальным источникам:

- Context7 `/mrdoob/three.js`: GLTFLoader, OrbitControls, render loop,
  responsive renderer lifecycle и cleanup-подходы.
- Context7 `/websites/dash_plotly`: `clientside_callback`, `dcc.Store`,
  локальные JS assets и предсказуемое состояние callback-цепочек.
- Three.js GLTFLoader:
  https://threejs.org/docs/pages/GLTFLoader.html.
- Three.js cleanup:
  https://threejs.org/manual/en/cleanup.html.
- Three.js OrbitControls:
  https://threejs.org/docs/pages/OrbitControls.html.
- Dash clientside callbacks:
  https://dash.plotly.com/clientside-callbacks.

## Архитектурное решение

Решение: усиливать существующий 3D-viewer инкрементально, сохраняя текущую
архитектуру `simulation -> services -> VisualizationSignalMap -> 2D/3D
renderer`.

Не делаем:

- не добавляем новое расчетное ядро для CFD;
- не вводим npm/bundler, пока текущий локальный assets-путь работает;
- не делаем 3D единственным режимом показа;
- не смешиваем серверные расчеты и frame-by-frame анимации.

## Фазы реализации

### Phase 0. Target freeze и evidence harness

Цель: зафиксировать, что именно считается целевым видом, и подготовить
проверочную рамку до визуальных правок.

Работы:

- держать target-референс `docs/assets/3d_visualization_final_reference_ru.png`
  открытым при визуальных фазах;
- добавить baseline smoke checklist для desktop/mobile viewport;
- зафиксировать минимальный набор сценариев: межсезонье, зима, лето, пик,
  загрязненный фильтр;
- убедиться, что текущие тесты scene metadata и visual signal map проходят.

Критерий выхода:

- есть стартовый screenshot baseline;
- есть список приемочных кадров и сценариев;
- полный `python -m pytest` проходит или известный gap явно записан.

### Phase 1. Композиция dashboard и главный viewport

Цель: сделать 3D-сцену главным экранным объектом, а панели - вспомогательными.

Работы:

- переразложить `scene3d-stage-grid`: viewport шире, sidebar компактнее;
- убрать из 3D-режима лишнюю обучающую текстовую нагрузку;
- оставить короткую live-сводку, ключевые KPI и режимы;
- добавить устойчивые размеры canvas и stage, чтобы текст/controls не
  сдвигали модель;
- проверить desktop 1365x768, 1440x900 и mobile/touch-friendly viewport.

Критерий выхода:

- первый экран 3D-режима сразу показывает модель и основные live-сигналы;
- управление не перекрывает canvas;
- не возникает горизонтального скролла и скачков layout.

### Phase 2. Семантика модели: секции, cutaway, xray

Цель: превратить модель из "объекта в комнате" в понятную инженерную ПВУ.

Работы:

- усилить профили `studio`, `xray`, `schematic`;
- добавить/уточнить scene nodes для intake, filter, coil, fan, dampers, supply;
- сделать cutaway/xray-режим с прозрачными стенками и читаемыми внутренними
  узлами;
- вынести правила материалов в небольшие helper-функции, чтобы не раздувать
  `viewer3d.mjs` хаотично;
- при необходимости обновить `generate_glb.py` или Blender build script, но
  сохранить стабильные `scene_node`.

Критерий выхода:

- пользователь без подсказки понимает, где фильтр, нагреватель, вентилятор,
  заслонки и помещение;
- xray/schematic режимы реально отличаются по смыслу, а не только цветом;
- bindings остаются валидными.

### Phase 3. Потоки, температура и давление

Цель: показать причинность расчета через анимированные инженерные эффекты.

Работы:

- заменить случайные вертикальные частицы на направленные airflow streamlines;
- привязать скорость/плотность потока к `flows.*.intensity`;
- добавить цветовой температурный градиент: cold/neutral/warm;
- добавить pressure-drop cue на фильтре и тревожный overlay при росте
  загрязнения;
- добавить fan rotation/damper state как локальные анимации, не требующие
  Python-tick на каждый кадр.

Критерий выхода:

- при изменении расхода, температуры и загрязнения фильтра видимо меняются
  поток, цвет, pressure cue и статус;
- эффекты читаются на скриншоте, а не только в движении;
- рендер держится в performance budget из `scene3d.json`.

### Phase 4. Overlays, датчики и interaction

Цель: сделать сцену объясняющей: кликнул узел - получил значение и смысл.

Работы:

- добавить 2D overlay labels поверх canvas для основных узлов и датчиков;
- стабилизировать project-to-screen anchors, чтобы подписи не прыгали;
- улучшить hover/click карточку: значение, статус, причина, связанный сценарий;
- добавить легенду `Норма / Риск / Авария`, температура, давление, поток;
- сделать mobile/touch fallback для click-only interaction.

Критерий выхода:

- все основные visual_id доступны через hover/click;
- подписи не закрывают модель и не перекрывают друг друга в базовых камерах;
- легенда объясняет цвета без чтения документации.

### Phase 5. UX-полировка режимов и сценарного показа

Цель: подготовить 3D как демонстрационный маршрут для защиты.

Работы:

- добавить camera presets: общий план, сервисный разрез, фильтр, вентилятор,
  помещение;
- добавить guided sequence для сценариев: "Зима", "Лето", "Пик",
  "Грязный фильтр";
- сделать control deck компактнее и ближе к инженерному пульту;
- синхронизировать live summary, статусные карточки и scene labels;
- обновить demo-script для 3D path.

Критерий выхода:

- за 60-90 секунд можно показать 3D-сцену, изменить параметры и объяснить
  результат без ручной подготовки;
- 2D fallback остается доступен одной кнопкой;
- словарь интерфейса остается русским и единым.

### Phase 6. Надежность, performance и cleanup

Цель: не потерять устойчивость ради красоты.

Работы:

- проверить `dispose()` по материалам, геометрии, texture maps, event listeners;
- добавить debug counters или lightweight diagnostics по renderer memory/calls;
- ограничить particle/label budget на слабом GPU;
- проверить context lost, asset error и WebGL unavailable;
- сохранить graceful fallback в 2D.

Критерий выхода:

- многократное переключение 2D/3D не копит canvas/listeners;
- ошибка ассета не ломает dashboard;
- renderer не выходит за выбранный canvas/pixel budget.

### Phase 7. QA, evidence и документация

Цель: зафиксировать результат как воспроизводимый, а не случайно красивый.

Работы:

- обновить `.omx/plans/3d_visualization_acceptance_matrix.md`;
- выполнить `python -m pytest`;
- провести browser smoke через Playwright или in-app browser;
- сохранить screenshots в `artifacts/...`;
- обновить `docs/13_visualization_strategy.md`, `docs/15_demo_readiness.md`,
  `docs/30_defense_presenter_script.md` при фактической реализации.

Критерий выхода:

- acceptance matrix заполнена evidence;
- есть свежие скриншоты desktop/mobile;
- известные риски описаны честно.

## Definition of Done

- 3D-режим визуально ближе к целевому образу: крупная ПВУ, cutaway/xray,
  направленные потоки, датчики, легенда, инженерная панель.
- Все основные состояния симуляции отражаются через один
  `VisualizationSignalMap`.
- 2D fallback работает после ошибок 3D и ручного переключения.
- Full regression проходит: `python -m pytest`.
- Browser smoke подтверждает canvas render, переключение режимов, interaction,
  несколько сценариев и отсутствие грубых layout overlap.

## Остаточные риски

- Реалистичность потоков остается визуальной аппроксимацией, а не CFD.
- Точная красота зависит от качества GLB и материалов; процедурный asset может
  потребовать нескольких итераций.
- Browser smoke нужно повторить на целевом демо-ПК перед защитой.
