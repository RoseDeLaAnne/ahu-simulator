# Визуальная карта курса 3D-визуализации

Дата: 2026-05-02.

## Финальный ориентир

![Финальный вид 3D-визуализации](assets/3d_visualization_final_reference_ru.png)

## Карта движения

```mermaid
flowchart LR
    A["Текущий 3D-прототип<br/>модель, room, сигналы, fallback"] --> B["Phase 0<br/>зафиксировать цель и baseline"]
    B --> C["Phase 1<br/>крупный viewport и спокойный dashboard"]
    C --> D["Phase 2<br/>секции ПВУ, cutaway, xray"]
    D --> E["Phase 3<br/>потоки, температура, давление"]
    E --> F["Phase 4<br/>датчики, подписи, interaction"]
    F --> G["Phase 5<br/>сценарный показ и UX-полировка"]
    G --> H["Phase 6<br/>performance, cleanup, fallback"]
    H --> I["Phase 7<br/>QA, screenshots, docs"]
    I --> J["Целевой результат<br/>инженерная 3D-сцена для защиты"]
```

## Целевой экран

```mermaid
flowchart TB
    subgraph Screen["3D Студия: первый экран"]
        Top["Верхняя строка: режим 2D/3D, модель, камера, сценарий"]
        subgraph Main["Главная зона"]
            Viewport["Большой 3D viewport<br/>cutaway ПВУ + потоки + датчики"]
            Side["Компактный пульт<br/>KPI, параметры, статус, легенда"]
        end
        Bottom["Нижняя полоса: live summary, выбранный узел, подсказка статуса"]
    end

    Top --> Viewport
    Top --> Side
    Viewport --> Bottom
    Side --> Bottom
```

## Смысловые слои сцены

```mermaid
flowchart TB
    Params["Входные параметры<br/>температура, расход, фильтр, уставка"] --> Core["Расчетное ядро<br/>SimulationResult"]
    Core --> Signals["VisualizationSignalMap<br/>nodes, sensors, flows, room_sensors"]
    Signals --> Scene["3D renderer<br/>viewer3d.mjs"]

    Scene --> Geometry["Геометрия<br/>секции ПВУ и помещение"]
    Scene --> Effects["Эффекты<br/>поток, температура, давление, вентилятор"]
    Scene --> Overlay["Overlay<br/>подписи, карточки, легенда"]
    Scene --> Fallback["Fallback<br/>2D SVG при ошибке WebGL"]
```

## Матрица визуального языка

| Слой | Что показывает | Источник данных | Визуальный прием |
| --- | --- | --- | --- |
| Узлы ПВУ | Intake, filter, coil, fan, dampers, supply | `nodes` | материал, подсветка, cutaway |
| Датчики | температура, давление, расход, room sensors | `sensors`, `room_sensors` | anchors, labels, click cards |
| Потоки | направление и интенсивность воздуха | `flows.*.intensity` | streamlines, скорость, прозрачность |
| Температура | холодный/нейтральный/теплый режим | state + parameters | blue -> neutral -> amber gradient |
| Давление фильтра | рост сопротивления | `filter_pressure_drop_pa` | violet/amber pressure cue |
| Статус | Норма / Риск / Авария | `OperationStatus` | зеленый / желтый / красный |

## Контрольные кадры

```mermaid
journey
    title Сценарный маршрут проверки 3D
    section Старт
      Открыть dashboard: 5: Пользователь
      Переключить 3D: 5: Пользователь
      Увидеть крупную ПВУ: 5: Пользователь
    section Инженерное объяснение
      Включить xray/cutaway: 5: Пользователь
      Кликнуть фильтр: 5: Пользователь
      Изменить загрязнение: 4: Пользователь
      Увидеть pressure cue: 5: Пользователь
    section Сценарии
      Выбрать зиму: 4: Пользователь
      Выбрать пик нагрузки: 4: Пользователь
      Проверить статусы: 5: Пользователь
    section Надежность
      Вернуться в 2D: 5: Пользователь
      Снова открыть 3D: 5: Пользователь
      Сохранить evidence: 5: Разработчик
```

## Правило курса

Каждая визуальная правка должна отвечать хотя бы на один вопрос:

- где находится физический узел установки;
- какой параметр сейчас влияет на этот узел;
- почему статус стал `Норма`, `Риск` или `Авария`;
- как пользователь может проверить это кликом, сценарием или скриншотом.
