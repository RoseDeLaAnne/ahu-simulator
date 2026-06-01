# Sparklines в KPI Cards - Документация

## Обзор

Добавлена функциональность отображения мини-графиков (sparklines) в KPI cards интерфейса concept03 для визуализации исторических трендов ключевых показателей.

## Реализованные компоненты

### 1. Компонент Sparkline (`src/app/ui/components/sparkline.py`)

SVG-генератор для создания inline sparklines:

```python
from app.ui.components.sparkline import build_sparkline_svg

svg = build_sparkline_svg(
    values=[10, 20, 15, 25, 30],
    width=60,
    height=20,
    stroke_color="#22c55e",
    fill_color="#22c55e",
)
```

**Возможности:**
- Автоматическая нормализация значений
- Поддержка заливки области под кривой
- Опциональные точки данных
- Обработка пустых/плоских данных
- Настраиваемые цвета и размеры

### 2. Интеграция с KPI Viewmodel

**Обновлен `Concept03KpiRowView`:**
- Добавлено поле `sparkline_values: tuple[float, ...] | None`
- Автоматическое извлечение последних 12 точек из истории симуляции

**Функция `_extract_sparkline_data()`:**
- Извлекает данные для sparklines из `SimulationHistory`
- Ограничивает до 12 последних точек
- Поддерживает метрики: airflow, pressure, supply_temp, power

### 3. Рендеринг в UI

**Обновлен `_build_kpi_row()` в `right_rail.py`:**
- Автоматическое добавление sparkline при наличии данных
- Цветовое кодирование по статусу (normal/warning/alarm)
- Адаптивное отображение

### 4. CSS Стили

Добавлены стили в `concept03_dashboard.css`:
```css
.c03-kpi-row__sparkline-container {
  margin-left: auto;
  padding-left: 8px;
  opacity: 0.85;
  transition: opacity 0.2s ease;
}

.c03-kpi-row:hover .c03-kpi-row__sparkline-container {
  opacity: 1;
}
```

## Использование

### В Layout

```python
from app.ui.viewmodels.concept03_kpi import build_concept03_kpi_view

kpi_view = build_concept03_kpi_view(
    result=current_result,
    history=current_session.history  # Передать историю для sparklines
)
```

### В Callbacks

```python
kpis = build_concept03_kpi_view(
    result,
    status_service,
    history=session.history if session else None
)
```

## Тестирование

**Созданы тесты:**
- `tests/unit/test_sparkline.py` - 11 тестов компонента sparkline
- `tests/unit/test_concept03_kpi_sparklines.py` - 6 тестов интеграции

**Запуск тестов:**
```bash
python -m pytest tests/unit/test_sparkline.py -v
python -m pytest tests/unit/test_concept03_kpi_sparklines.py -v
```

## Визуальные характеристики

- **Размер:** 60×20 пикселей (компактный)
- **Позиция:** Справа в строке значения KPI
- **Цвет:** Соответствует статусу метрики
  - Normal: `#22c55e` (зеленый)
  - Warning: `#facc15` (желтый)
  - Alarm: `#ef4444` (красный)
  - Unavailable: `#94a3b8` (серый)
- **Эффекты:** Плавное появление при hover, заливка области

## Производительность

- Генерация SVG на сервере (без JavaScript)
- Минимальный размер разметки (~200-300 байт на sparkline)
- Нет дополнительных HTTP-запросов
- Кэширование через Dash callbacks

## Совместимость

- ✅ Desktop (1500×900)
- ✅ Mobile (375×812)
- ✅ Defense mode
- ✅ Operator mode
- ✅ Все браузеры с поддержкой SVG

## Ограничения

- Максимум 12 точек данных (последние)
- Требуется `SimulationHistory` с минимум 2 точками
- Не отображается для метрики "Влажность" (unavailable)

## Следующие шаги

1. ✅ **Sparklines в KPI cards** - ЗАВЕРШЕНО
2. ⏳ Улучшение анимации вентилятора
3. ⏳ Тепловая карта помещения
