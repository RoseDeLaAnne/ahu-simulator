# Задача 3.2: Режим сравнения — Примеры использования

Практические сценарии работы с режимом сравнения side-by-side. Справочник
по API — в [`TASK_3.2_API_REFERENCE.md`](TASK_3.2_API_REFERENCE.md).

---

## Сценарий A. Сравнение через UI (основной путь)

1. Включите developer-инструменты 3D-сцены (панель «⚖️ Режим сравнения»
   появляется только при `developer_tools_enabled=True`).
2. Откройте 3D-режим. При обновлении `visualization-signals` серверный callback
   `populate_comparison_sources` автоматически заполнит оба выпадающих списка
   доступными источниками и подставит дефолтную пару.
3. Поставьте галочку **«Включить сравнение»**.
4. Выберите **Источник 'До'** и **Источник 'После'** (например, снимок «До» и
   текущий прогон).
5. Настройте при необходимости:
   - **Соотношение разделения** (30/70 … 70/30);
   - **Ориентацию** (вертикальное лево/право или горизонтальное верх/низ);
   - **Синхронизацию камер** (по умолчанию включена);
   - **Режим выделения различий** (по статусу / температуре / мощности / тревогам).
6. Под контролами появятся строка совместимости («✓ Совместимо…» либо
   «⚠️ Несовместимо…») и статистика пары.

> Если выбрать один и тот же источник в обоих списках — режим не запустится и
> покажет «⚠️ Выберите разные источники для сравнения».

---

## Сценарий B. Программный запуск из консоли браузера

```js
// 1. Загрузить пару прогонов.
const comparison = await window.pvu3d.loadComparisonData(
  "snapshot:before",   // источник "до"
  "active-run"         // источник "после"
);

// 2. Проверить совместимость перед запуском.
if (!comparison.compatibility.is_compatible) {
  console.warn("Несовместимо:", comparison.compatibility.summary);
} else {
  // 3. Включить split-screen.
  window.pvu3d.setComparisonMode("split", {
    split: 0.5,
    orientation: "vertical",
    syncCameras: true,
    diffMode: "status",
  });
}
```

---

## Сценарий C. Быстрое переключение режима выделения

После того как сравнение уже запущено, меняйте подсветку без перезагрузки
данных — это примерно в 10 раз быстрее полного цикла:

```js
window.pvu3d.updateComparisonDiffMode("temperature"); // дельта температур
window.pvu3d.updateComparisonDiffMode("power");        // энергопотребление
window.pvu3d.updateComparisonDiffMode("alarms");       // тревоги
window.pvu3d.updateComparisonDiffMode("none");         // снять подсветку
```

---

## Сценарий D. Горизонтальное сравнение с акцентом на «после»

```js
await window.pvu3d.loadComparisonData("archive:pvu-run-20260418-115000", "active-run");
window.pvu3d.setComparisonMode("split", {
  split: 0.4,              // 40% сверху ("до"), 60% снизу ("после")
  orientation: "horizontal",
  syncCameras: true,
  diffMode: "power",
});
```

---

## Сценарий E. Проверка состояния и выключение

```js
// Узнать текущее состояние.
const stats = window.pvu3d.getComparisonStats();
console.log(stats.enabled, stats.diffMode, stats.beforeLabel, stats.afterLabel);

// Корректно выйти из режима (уничтожает вторую сцену и убирает оверлеи).
window.pvu3d.setComparisonMode("off");
```

---

## Сценарий F. Построение сравнения через REST напрямую

```bash
curl -X POST http://localhost:8000/api/comparison/runs/build \
  -H "Content-Type: application/json" \
  -d '{"before_reference_id": "snapshot:before", "after_reference_id": "active-run"}'
```

Ответ содержит `compatibility`, `interpretation`, `metric_deltas` и
`trend_deltas` — те же данные, что использует `loadComparisonData`.

---

## Типичные проблемы

| Симптом | Причина | Решение |
|---------|---------|---------|
| «Режим сравнения недоступен» | `window.pvu3d` ещё не инициализирован | Дождитесь загрузки 3D-сцены |
| Split не включается, warning в консоли | Источники несовместимы | Выберите прогоны с одинаковым шагом/горизонтом/сеткой |
| Пустые выпадающие списки | Нет доступных источников или callback не отработал | Сохраните снимок/архивный прогон; обновите `visualization-signals` |
| Подсветка не меняется | Режим сравнения не активен | Сначала включите split, затем `updateComparisonDiffMode` |
| Скриншот в split не работает | Не поддерживается (известное ограничение) | Используйте обычный режим для захвата |
