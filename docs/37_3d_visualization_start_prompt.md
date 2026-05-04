# Стартовый prompt для реализации 3D-визуализации

Дата: 2026-05-02.

Этот файл нужен для старта новой Codex-сессии без потери курса. Перед началом реализации открой визуальный ориентир:

![Финальный ориентир 3D-визуализации](assets/3d_visualization_final_reference_ru.png)

## Prompt

```text
Ты работаешь в репозитории C:\My\Work\Diploma\ahu-simulator.

Цель: довести текущую optional 3D-визуализацию AHU/PVU до защитного инженерного уровня, ориентируясь на финальный русскоязычный кадр:
- docs/assets/3d_visualization_final_reference_ru.png

Перед изменениями прочитай:
- docs/35_3d_visualization_upgrade_plan.md
- docs/36_3d_visualization_course_map.md
- docs/37_3d_visualization_start_prompt.md
- docs/38_3d_visualization_ru_source_prompt.md
- .omx/plans/3d_visualization_upgrade_plan.md
- .omx/plans/3d_visualization_upgrade_todo.md
- .omx/plans/3d_visualization_acceptance_matrix.md

Главный визуальный принцип:
- первый экран должен восприниматься как инженерная 3D-студия;
- крупный canvas с ПВУ в разрезе является главным объектом;
- справа находится компактный пульт KPI/статуса/легенды;
- снизу находится короткая live summary полоса;
- русские подписи объясняют физические узлы, параметры и статус без маркетингового текста.

Обязательные правила:
- Не переписывай расчетное ядро и API ради 3D.
- Сохраняй архитектуру: SimulationResult -> VisualizationSignalMap -> 2D/3D renderer.
- 2D SVG остается fallback, 3D не становится обязательным режимом.
- Не добавляй новые зависимости без явного запроса.
- Не заявляй CFD/физически точные объемные потоки; эффекты являются инженерной визуализацией текущей упрощенной модели.
- Сохраняй существующие component IDs, если нет сильной причины менять их.
- Не трогай unrelated dirty files.

Стартовые файлы:
- src/app/ui/render_modes/scene3d.py
- src/app/ui/assets/viewer3d.mjs
- src/app/ui/assets/viewer3d_bridge.js
- src/app/ui/assets/dashboard.css
- src/app/ui/viewmodels/visualization.py
- src/app/ui/scene/bindings.py
- data/visualization/scene3d.json
- tests/unit/test_scene3d_developer_controls.py
- tests/unit/test_visualization_viewmodel.py
- tests/unit/test_scene_model_catalog.py

Начни с Phase 0/Phase 1:
1. Зафиксируй baseline: git status, текущие screenshots, релевантные unit tests по 3D/viewmodel.
2. Улучши layout 3D-режима так, чтобы главный canvas стал визуальным центром первого экрана.
3. Сожми control deck до компактного инженерного пульта.
4. Добавь или уточни русские подписи для режима, камеры, разреза, X-Ray, потока, температуры, давления, статуса и 2D fallback.
5. Проверь desktop layout через browser smoke и сохрани screenshots/evidence.
6. Отметь выполненные пункты в .omx/plans/3d_visualization_upgrade_todo.md.
7. Добавь evidence в .omx/plans/3d_visualization_acceptance_matrix.md.

После каждой фазы:
- запускай релевантные unit tests;
- для визуальных фаз делай browser smoke и screenshots;
- обновляй To-Do и acceptance matrix;
- фиксируй оставшиеся риски честно, без заявлений сверх модели.

Финальный DoD:
- python -m pytest проходит или задокументирован конкретный внешний блокер;
- есть свежие browser screenshots;
- 3D показывает крупную ПВУ, cutaway/xray, направленные потоки, датчики, русскую легенду и стабильный fallback;
- docs/13_visualization_strategy.md и demo docs обновлены фактическим состоянием;
- итоговый экран визуально следует docs/assets/3d_visualization_final_reference_ru.png, но не копирует его слепо, если реальные ограничения текущего UI требуют аккуратной адаптации.
```

## Контрольные визуальные требования

| Зона | Требование |
| --- | --- |
| Главный viewport | ПВУ крупная, читаемая, с прозрачным корпусом и видимыми секциями |
| Секции | Забор воздуха, фильтр, нагреватель, вентилятор, подача |
| Потоки | Направление воздуха видно без перегруза сцены |
| Пульт | Статус, расход, перепад давления, температура подачи, fallback |
| Подписи | Русские, короткие, без наложений на важные элементы |
| Fallback | 2D режим остается доступным и понятным |
