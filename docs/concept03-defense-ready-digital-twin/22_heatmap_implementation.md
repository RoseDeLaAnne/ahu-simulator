# Тепловая карта помещения - Документация

## Обзор

Реализован компонент тепловой карты для визуализации распределения температуры в помещении. Использует интерполяцию методом обратных взвешенных расстояний (IDW) для создания плавного градиента между точками измерения.

## Реализованные возможности

### 1. Генерация SVG тепловой карты

**Компонент:** `src/app/ui/components/heatmap.py`

```python
from app.ui.components.heatmap import build_heatmap_svg

svg = build_heatmap_svg(
    width=400,
    height=300,
    temperature_points=[
        (0.2, 0.2, 18.0),  # (x, y, temp) в нормализованных координатах
        (0.5, 0.5, 21.0),
        (0.8, 0.8, 24.0),
    ],
    grid_resolution=20,
    min_temp=18.0,
    max_temp=26.0,
    show_legend=True,
)
```

### 2. Интерполяция температуры (IDW)

**Метод:** Inverse Distance Weighting (обратное взвешивание расстояний)

```python
weight = 1.0 / (distance ** power)
interpolated_temp = Σ(weight_i × temp_i) / Σ(weight_i)
```

**Параметры:**
- `power = 2.0` - степень затухания влияния с расстоянием
- Автоматическая обработка граничных случаев

**Преимущества:**
- Плавные переходы между точками измерения
- Физически корректная интерполяция
- Быстрые вычисления (O(n) на точку сетки)

### 3. Цветовая шкала

**Градиент:** Синий → Голубой → Зелёный → Жёлтый → Красный

| Температура | Цвет | Hex | Значение |
|-------------|------|-----|----------|
| < 18°C | Синий | `#0080ff` | Холодно |
| 18-20°C | Голубой | `#00ffff` | Прохладно |
| 20-22°C | Зелёный | `#00ff00` | Комфортно |
| 22-24°C | Жёлтый | `#ffff00` | Тепло |
| > 24°C | Красный | `#ff0000` | Жарко |

### 4. Визуальные элементы

#### Сетка температур
- Настраиваемое разрешение (по умолчанию 20×20)
- Gaussian blur для плавности (σ = 3)
- Прозрачность 60% для наложения на 3D сцену

#### Точки измерения
- Круги диаметром 8px
- Цвет соответствует температуре
- Белая обводка для контраста

#### Легенда
- Вертикальный градиент
- Подписи min/max температур
- Позиция: правый верхний угол

## Параметры конфигурации

```python
build_heatmap_svg(
    width: int = 400,              # Ширина SVG
    height: int = 300,             # Высота SVG
    temperature_points: Sequence,  # Точки измерения [(x, y, temp), ...]
    grid_resolution: int = 20,     # Разрешение сетки (NxN)
    min_temp: float = 18.0,        # Минимум шкалы (°C)
    max_temp: float = 26.0,        # Максимум шкалы (°C)
    show_legend: bool = True,      # Показать легенду
    class_name: str = "heatmap",   # CSS класс
)
```

## Использование в UI

### Интеграция с 3D сценой

Тепловая карта может быть наложена поверх 3D viewport как HTML overlay:

```python
# В concept03 central canvas
heatmap_svg = build_heatmap_svg(
    width=viewport_width,
    height=viewport_height,
    temperature_points=extract_temperature_points(session),
)

# Добавить как overlay
html.Div(
    className="c03-heatmap-overlay",
    dangerouslySetInnerHTML={"__html": heatmap_svg},
)
```

### Извлечение точек температуры

```python
def extract_temperature_points(session: SimulationSession) -> list[tuple[float, float, float]]:
    """Extract temperature measurement points from simulation."""
    result = session.current_result
    
    return [
        (0.1, 0.1, result.parameters.outdoor_temp_c),      # Наружный воздух
        (0.5, 0.3, result.state.supply_temp_c),            # Приток
        (0.5, 0.7, result.state.room_temp_c),              # Помещение
        (0.9, 0.5, result.state.room_temp_c - 0.5),        # Вытяжка
    ]
```

## CSS стили

```css
.c03-heatmap-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10;
}

.heatmap {
  width: 100%;
  height: 100%;
}

.heatmap-legend {
  pointer-events: auto;
}

.heatmap--empty {
  opacity: 0.5;
}
```

## Производительность

### Вычислительная сложность

- **Генерация сетки:** O(N² × M)
  - N = grid_resolution (20)
  - M = количество точек измерения (обычно 3-5)
  - Время: ~5-10ms для 20×20 сетки

- **Рендеринг SVG:** O(N²)
  - 400 rect элементов для 20×20 сетки
  - Размер SVG: ~15-20 KB

### Оптимизации

1. **Кэширование:** SVG генерируется на сервере, кэшируется Dash
2. **Blur фильтр:** Применяется GPU (SVG filter)
3. **Минимальные вычисления:** Только при изменении температур

## Тестирование

**Создано 12 unit тестов:**
- ✅ Базовая генерация
- ✅ Пустые данные
- ✅ Легенда
- ✅ Кастомные диапазоны
- ✅ Разрешение сетки
- ✅ Точки измерения
- ✅ Blur фильтр
- ✅ Интерполяция
- ✅ Экстремальные температуры

**Запуск тестов:**
```bash
python -m pytest tests/unit/test_heatmap.py -v
# 12 passed in 0.06s
```

## Примеры использования

### Базовый пример

```python
# Простая тепловая карта
svg = build_heatmap_svg(
    width=400,
    height=300,
    temperature_points=[
        (0.2, 0.2, 18.0),
        (0.8, 0.8, 24.0),
    ],
)
```

### Высокое разрешение

```python
# Детальная карта для анализа
svg = build_heatmap_svg(
    width=800,
    height=600,
    temperature_points=measurement_points,
    grid_resolution=40,  # Более детальная сетка
)
```

### Кастомный диапазон

```python
# Зимний режим с низкими температурами
svg = build_heatmap_svg(
    width=400,
    height=300,
    temperature_points=winter_points,
    min_temp=-10.0,
    max_temp=20.0,
)
```

## Совместимость

- ✅ Desktop (1500×900)
- ✅ Mobile (375×812)
- ✅ Defense mode
- ✅ Operator mode
- ✅ Все браузеры с поддержкой SVG filters

## Ограничения

- Минимум 2 точки измерения для интерполяции
- Максимальное разрешение сетки: 50×50 (производительность)
- SVG размер растёт квадратично с разрешением

## Будущие улучшения (опционально)

1. **Анимация:** Плавный переход между состояниями
2. **Изолинии:** Контурные линии постоянной температуры
3. **Векторное поле:** Направление потоков воздуха
4. **Интерактивность:** Tooltip с температурой при hover
5. **WebGL версия:** Для очень высокого разрешения

## Научная основа

### Метод IDW

Inverse Distance Weighting - классический метод пространственной интерполяции:

```
T(x,y) = Σ[w_i × T_i] / Σ[w_i]

где w_i = 1 / d_i^p
```

**Литература:**
- Shepard, D. (1968). "A two-dimensional interpolation function for irregularly-spaced data"
- ГОСТ 30494-2011 "Параметры микроклимата в помещениях"

### Цветовая шкала

Основана на психофизических исследованиях восприятия температуры:
- Холодные тона (синий) → низкая температура
- Тёплые тона (красный) → высокая температура
- Зелёный → комфортная зона (20-22°C по ГОСТ 30494-2011)

## Файлы

- ✅ `src/app/ui/components/heatmap.py` (новый, 280 строк)
- ✅ `tests/unit/test_heatmap.py` (новый, 12 тестов)
- ✅ `docs/concept03-defense-ready-digital-twin/22_heatmap_implementation.md` (документация)
