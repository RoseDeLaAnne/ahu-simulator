# 20. 3D Models Inventory & Verification

Полная инвентаризация и проверка 3D моделей в проекте.

## Дата: 2026-05-30

---

## 📦 Инвентаризация 3D моделей

### AHU Models (Модели установок)

#### Master Models (Основные модели)
| Файл | Размер | Статус | Описание |
|------|--------|--------|----------|
| `models/ahu/master/pvu_installation.glb` | 1.1M | ✅ Используется | Учебная ПВУ (СП 60.13330.2020) |
| `models/ahu/master/modular_ahu_pbr.glb` | 15M | ✅ В каталоге | Флагманская ПВУ (PBR) |
| `models/ahu/master/modular_ahu_shaded.glb` | 11M | ✅ В каталоге | Флагманская ПВУ (Shaded) |

#### Variant Models (Варианты)
| Файл | Размер | Статус | Описание |
|------|--------|--------|----------|
| `models/ahu/variants/base_classic.glb` | 7.5M | ✅ В каталоге | Базовый классический |
| `models/ahu/variants/base_variant_b.glb` | 6.7M | ✅ В каталоге | Базовый вариант Б |
| `models/ahu/variants/base_variant_c_pbr.glb` | 16M | ✅ В каталоге | Базовый вариант C (PBR) |
| `models/ahu/variants/base_variant_c_shaded.glb` | 8.8M | ✅ В каталоге | Базовый вариант C (Shaded) |
| `models/ahu/variants/industrial_hvac_unit.glb` | 29M | ✅ В каталоге | Промышленная ПВУ |
| `models/ahu/variants/industrial_machinery_unit.glb` | 29M | ✅ В каталоге | Промышленный агрегат |

**Всего AHU моделей:** 9 файлов, ~124M

### Room Models (Модели помещений)

| Файл | Размер | Статус | Описание |
|------|--------|--------|----------|
| `models/rooms/office_suite.glb` | 14M | ✅ В каталоге | Офис open-space |
| `models/rooms/classroom_wing.glb` | 16M | ✅ В каталоге | Учебная аудитория |
| `models/rooms/lab_cluster.glb` | 16M | ✅ В каталоге | Лабораторный блок |

**Всего Room моделей:** 3 файла, ~46M

### Additional Models (Дополнительные)

| Файл | Размер | Статус | Описание |
|------|--------|--------|----------|
| `3d-references/Meshy_AI_Industrial_supply_air_*.glb` | ? | ⚠️ Референс | AI-сгенерированная модель |
| `data/visualization/assets/pvu_installation.glb` | 1.1M | ✅ Активная | Копия основной модели |

---

## ✅ Проверка интеграции

### 1. Model Catalog (AHU Models)

**Файл:** `src/app/ui/scene/model_catalog.py`

**Статус:** ✅ **Все модели зарегистрированы**

**Зарегистрированные модели:**
```python
_MODEL_META = {
    "ahu/master/pvu_installation.glb": {...},      # ✅
    "ahu/master/modular_ahu_pbr.glb": {...},       # ✅
    "ahu/master/modular_ahu_shaded.glb": {...},    # ✅
    "ahu/variants/base_variant_c_pbr.glb": {...},  # ✅
    "ahu/variants/base_variant_c_shaded.glb": {...}, # ✅
    "ahu/variants/industrial_hvac_unit.glb": {...}, # ✅
    "ahu/variants/industrial_machinery_unit.glb": {...}, # ✅
    "ahu/variants/base_classic.glb": {...},        # ✅
    "ahu/variants/base_variant_b.glb": {...},      # ✅
}
```

**Приоритетные группы:**
```python
_PREFERRED_SCENE_MODEL_PATH_GROUPS = (
    ("ahu/master/pvu_installation.glb",),  # Группа 1: Учебная модель
    ("ahu/master/modular_ahu_pbr.glb", "ahu/master/modular_ahu_shaded.glb"),  # Группа 2: Флагманская
    ("ahu/variants/base_variant_c_pbr.glb", "ahu/variants/base_variant_c_shaded.glb"),  # Группа 3: Вариант C
)
```

### 2. Room Catalog (Room Models)

**Файл:** `src/app/ui/scene/room_catalog.py`

**Статус:** ✅ **Все модели зарегистрированы**

**Зарегистрированные модели:**
```python
_ROOM_META = {
    "office_suite.glb": {
        "id": "office_suite",
        "label": "Офис open-space",
        "volume_m3": 250.0,
        "design_occupancy_people": 18,
        "presets": [3 пресета],  # ✅
    },
    "classroom_wing.glb": {
        "id": "classroom_wing",
        "label": "Учебная аудитория",
        "volume_m3": 420.0,
        "design_occupancy_people": 32,
        "presets": [3 пресета],  # ✅
    },
    "lab_cluster.glb": {
        "id": "lab_cluster",
        "label": "Лабораторный блок",
        "volume_m3": 320.0,
        "design_occupancy_people": 14,
        "presets": [3 пресета],  # ✅
    },
}
```

### 3. Scene Configuration

**Файл:** `data/visualization/scene3d.json`

**Статус:** ✅ **Правильно настроен**

```json
{
  "version": 3,
  "asset": {
    "model_path": "data/visualization/assets/pvu_installation.glb",  // ✅ Существует
    "format": "glb",
    "generator": "tooling/scene/build_blender_pvu.py",
    "units": "meters",
    "up_axis": "Y",
    "forward_axis": "X"
  }
}
```

---

## 📊 Детальная информация по моделям

### AHU Master Models

#### 1. pvu_installation.glb (Учебная ПВУ)
- **Размер:** 1.1M
- **Тип:** Процедурная модель
- **Accent:** #22d3ee (бирюзовый)
- **Tone:** studio
- **Featured:** ✅ Да
- **Использование:** Основная модель для defense interface
- **Особенности:**
  - Явная разбивка по секциям (воздухозабор, клапан, фильтр, шумоглушитель, калорифер, вентилятор, воздуховод)
  - Сохраняет иерархию узлов для режимов «Рентген» и «Схема»
  - Соответствует СП 60.13330.2020

#### 2. modular_ahu_pbr.glb (Флагманская ПВУ PBR)
- **Размер:** 15M
- **Тип:** Детализированная модель с PBR материалами
- **Accent:** #38bdf8 (светло-голубой)
- **Tone:** precision
- **Featured:** ✅ Да
- **Использование:** Флагманская демонстрация
- **Особенности:**
  - Физически корректные материалы (PBR)
  - Высокая детализация
  - Подходит для презентаций

#### 3. modular_ahu_shaded.glb (Флагманская ПВУ Shaded)
- **Размер:** 11M
- **Тип:** Детализированная модель с простыми материалами
- **Accent:** #38bdf8 (светло-голубой)
- **Tone:** precision
- **Featured:** ✅ Да
- **Использование:** Альтернатива PBR для производительности

### AHU Variant Models

#### 4. base_classic.glb (Базовый классический)
- **Размер:** 7.5M
- **Accent:** #22c55e (зеленый)
- **Tone:** clean
- **Описание:** Базовый удлинённый корпус для чистой визуализации приточного тракта

#### 5. base_variant_b.glb (Базовый вариант Б)
- **Размер:** 6.7M
- **Accent:** #eab308 (желтый)
- **Tone:** clean
- **Описание:** Высокий вариант для демонстрации узлов по вертикали

#### 6. base_variant_c_pbr.glb (Базовый вариант C PBR)
- **Размер:** 16M
- **Accent:** #06b6d4 (циан)
- **Tone:** clean
- **Описание:** Новый вариант базового корпуса с PBR материалами

#### 7. base_variant_c_shaded.glb (Базовый вариант C Shaded)
- **Размер:** 8.8M
- **Accent:** #06b6d4 (циан)
- **Tone:** clean
- **Описание:** Альтернатива PBR для производительности

#### 8. industrial_hvac_unit.glb (Промышленная ПВУ)
- **Размер:** 29M
- **Accent:** #14b8a6 (бирюзовый)
- **Tone:** studio
- **Описание:** Компактная индустриальная ПВУ для акцентной студийной сцены

#### 9. industrial_machinery_unit.glb (Промышленный агрегат)
- **Размер:** 29M
- **Accent:** #f97316 (оранжевый)
- **Tone:** xray
- **Описание:** Вытянутый агрегат для режима рентген-визуализации

### Room Models

#### 1. office_suite.glb (Офис open-space)
- **Размер:** 14M
- **Accent:** #38bdf8 (светло-голубой)
- **Tone:** office
- **Объем:** 250 м³
- **Проектная загрузка:** 18 человек
- **Пресеты:**
  1. `office_focus` — Тихий рабочий день (7 человек)
  2. `office_meeting_rush` — Совещание на весь блок (18 человек)
  3. `office_overtime` — Вечерний минимум (2 человека)

#### 2. classroom_wing.glb (Учебная аудитория)
- **Размер:** 16M
- **Accent:** #22c55e (зеленый)
- **Tone:** classroom
- **Объем:** 420 м³
- **Проектная загрузка:** 32 человека
- **Пресеты:**
  1. `classroom_before_lesson` — Перед занятием (5 человек)
  2. `classroom_full_lesson` — Полная аудитория (32 человека)
  3. `classroom_recovery_flush` — Проветривание после пары (8 человек)

#### 3. lab_cluster.glb (Лабораторный блок)
- **Размер:** 16M
- **Accent:** #f97316 (оранжевый)
- **Tone:** lab
- **Объем:** 320 м³
- **Проектная загрузка:** 14 человек
- **Пресеты:**
  1. `lab_calibrated` — Калиброванный режим (6 человек)
  2. `lab_equipment_peak` — Пик оборудования (12 человек)
  3. `lab_purge_after_shift` — Продувка после смены (1 человек)

---

## 🔍 Проверка файлов

### Существующие файлы
```bash
✅ data/visualization/assets/pvu_installation.glb (1.1M)
✅ models/ahu/master/pvu_installation.glb (1.1M)
✅ models/ahu/master/modular_ahu_pbr.glb (15M)
✅ models/ahu/master/modular_ahu_shaded.glb (11M)
✅ models/ahu/variants/base_classic.glb (7.5M)
✅ models/ahu/variants/base_variant_b.glb (6.7M)
✅ models/ahu/variants/base_variant_c_pbr.glb (16M)
✅ models/ahu/variants/base_variant_c_shaded.glb (8.8M)
✅ models/ahu/variants/industrial_hvac_unit.glb (29M)
✅ models/ahu/variants/industrial_machinery_unit.glb (29M)
✅ models/rooms/office_suite.glb (14M)
✅ models/rooms/classroom_wing.glb (16M)
✅ models/rooms/lab_cluster.glb (16M)
```

**Всего:** 13 файлов, ~170M

### Дубликаты
```
⚠️ pvu_installation.glb существует в двух местах:
   - data/visualization/assets/pvu_installation.glb (активная)
   - models/ahu/master/pvu_installation.glb (каталог)
   
Статус: Это нормально, одна копия используется активно, другая в каталоге.
```

---

## 📈 Статистика использования

### По размеру
- **Маленькие (<10M):** 5 моделей (pvu_installation, modular_ahu_shaded, base_classic, base_variant_b, base_variant_c_shaded)
- **Средние (10-20M):** 5 моделей (modular_ahu_pbr, base_variant_c_pbr, office_suite, classroom_wing, lab_cluster)
- **Большие (>20M):** 2 модели (industrial_hvac_unit, industrial_machinery_unit)

### По типу
- **AHU Models:** 9 моделей (~124M)
- **Room Models:** 3 модели (~46M)
- **Total:** 12 уникальных моделей (~170M)

### По статусу
- **Активно используется:** 1 модель (pvu_installation.glb)
- **В каталоге (доступны):** 11 моделей
- **Featured (приоритетные):** 3 модели

---

## ✅ Выводы

### Статус интеграции
1. ✅ **Все модели найдены** — 13 файлов на диске
2. ✅ **Все модели зарегистрированы** — в model_catalog.py и room_catalog.py
3. ✅ **Конфигурация корректна** — scene3d.json указывает на существующий файл
4. ✅ **Каталоги работают** — build_scene_model_catalog() и build_room_catalog()

### Рекомендации

#### Для защиты диплома
1. ✅ **Основная модель готова** — pvu_installation.glb (1.1M) используется
2. ✅ **Есть альтернативы** — 8 дополнительных AHU моделей
3. ✅ **Есть room models** — 3 модели помещений с пресетами
4. ✅ **Документация полная** — все модели описаны

#### Для улучшения
1. ⚠️ **Оптимизация размера** — 2 модели >20M (можно сжать)
2. 💡 **Добавить превью** — не все модели имеют preview_path
3. 💡 **Тестирование** — проверить загрузку всех моделей в браузере

---

## 🚀 Следующие шаги

1. ⏳ Проверить загрузку всех моделей через UI
2. ⏳ Создать превью для моделей без preview_path
3. ⏳ Оптимизировать большие модели (>20M)
4. ⏳ Добавить unit тесты для model_catalog и room_catalog

---

**Дата создания:** 2026-05-30  
**Статус:** ✅ Все модели найдены и зарегистрированы  
**Всего моделей:** 12 уникальных (13 файлов с дубликатом)  
**Общий размер:** ~170M
