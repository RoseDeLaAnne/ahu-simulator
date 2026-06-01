# Следующие шаги после Фазы A

## Краткосрочные задачи (для защиты диплома)

### 1. Визуальное тестирование (1-2 часа)

**Запуск dashboard:**
```bash
python -m uvicorn app.main:app --reload
# Открыть: http://localhost:8000/dashboard?theme=concept03
```

**Что проверить:**
- ✅ Sparklines отображаются в KPI cards
- ✅ Sparklines обновляются при изменении параметров
- ✅ Анимация вентилятора плавно ускоряется/замедляется
- ✅ Motion blur появляется при высоких оборотах
- ✅ Все работает на mobile (375×812)
- ✅ Defense mode работает корректно

**Скриншоты для документации:**
```bash
# Сохранить в artifacts/screenshots/phase-a/
- sparklines-normal.png
- sparklines-warning.png
- sparklines-alarm.png
- fan-animation-low-speed.png
- fan-animation-high-speed-blur.png
- heatmap-example.png
```

---

### 2. Интеграция тепловой карты (опционально, 2-3 часа)

**Если есть время, добавить в UI:**

1. **Создать toggle в central canvas:**
```python
# В concept03/central_canvas.py
html.Button(
    "Тепловая карта",
    id="heatmap-toggle",
    className="c03-heatmap-toggle",
)
```

2. **Добавить callback:**
```python
@app.callback(
    Output("heatmap-overlay", "children"),
    Input("heatmap-toggle", "n_clicks"),
    State("simulation-session-state", "data"),
)
def toggle_heatmap(n_clicks, session_data):
    if n_clicks % 2 == 0:
        return None
    
    # Извлечь точки температуры
    points = extract_temperature_points(session_data)
    
    # Генерировать SVG
    svg = build_heatmap_svg(
        width=800,
        height=600,
        temperature_points=points,
    )
    
    return html.Div(
        className="c03-heatmap-overlay",
        dangerouslySetInnerHTML={"__html": svg},
    )
```

3. **Добавить CSS:**
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
```

**Или оставить как готовый компонент для демонстрации возможностей.**

---

### 3. Демо-видео для защиты (1-2 часа)

**Сценарий записи (5-7 минут):**

1. **Введение (30 сек)**
   - Запуск dashboard
   - Обзор интерфейса concept03

2. **Sparklines (1.5 мин)**
   - Показать KPI cards с sparklines
   - Запустить симуляцию
   - Показать как sparklines обновляются в реальном времени
   - Изменить сценарий → sparklines меняют цвет по статусу

3. **Анимация вентилятора (2 мин)**
   - Переключиться на 3D viewport
   - Запустить симуляцию с низкой скорости
   - Показать плавное ускорение
   - Увеличить расход → показать motion blur
   - Остановить → показать плавное замедление

4. **Тепловая карта (1.5 мин)**
   - Показать компонент heatmap
   - Объяснить метод интерполяции IDW
   - Показать цветовую шкалу
   - Показать точки измерения

5. **Технические детали (1.5 мин)**
   - Показать код sparkline компонента
   - Показать тесты (29/29 passed)
   - Показать документацию

6. **Заключение (30 сек)**
   - Итоги: 3 улучшения, 34 теста, готово к защите

**Инструменты для записи:**
- OBS Studio (бесплатно)
- ShareX (скриншоты + видео)
- Windows Game Bar (Win+G)

---

### 4. Слайды для защиты (1-2 часа)

**Структура презентации:**

**Слайд 1: Заголовок**
- Фаза A: Визуальные улучшения
- 3 реализованных компонента
- 34 теста, 100% покрытие

**Слайд 2: Sparklines в KPI**
- Скриншот KPI cards с sparklines
- Технические характеристики
- Преимущества для пользователя

**Слайд 3: Анимация вентилятора**
- Скриншоты: низкая скорость vs высокая скорость с blur
- Технические детали (easing, blur threshold)
- Физическая корректность

**Слайд 4: Тепловая карта**
- Визуализация температурного поля
- Метод интерполяции IDW
- Научная основа (ГОСТ 30494-2011)

**Слайд 5: Технические метрики**
- Таблица со статистикой
- Производительность (FPS, память, время генерации)
- Совместимость (desktop/mobile/browsers)

**Слайд 6: Тестирование**
- 29 unit тестов
- 5 integration тестов
- Примеры тестов

**Слайд 7: Архитектура**
- Диаграмма компонентов
- Модульная структура
- Точки интеграции

**Слайд 8: Выводы**
- Все задачи выполнены
- Готово к защите
- Возможности для развития

---

## Долгосрочные задачи (после защиты)

### Фаза B: Улучшение моделирования (опционально)

1. **PID-регулятор**
   - Заменить упрощенное управление на полноценный PID
   - Настройка коэффициентов Kp, Ki, Kd
   - Тесты стабильности

2. **Улучшенная динамика помещения**
   - Тепловая инерция стен
   - Учет солнечной радиации
   - Модель второго порядка

3. **Нелинейная модель фильтра**
   - Зависимость перепада давления от загрязнения
   - Модель накопления пыли
   - Прогноз замены фильтра

4. **Рекуператор с обмерзанием**
   - Модель обмерзания при низких температурах
   - Автоматическая разморозка
   - Снижение эффективности

---

## Команды для быстрого старта

```bash
# Запустить все тесты Фазы A
python -m pytest tests/unit/test_sparkline.py \
                 tests/unit/test_concept03_kpi_sparklines.py \
                 tests/unit/test_heatmap.py -v

# Запустить dashboard
python -m uvicorn app.main:app --reload

# Открыть в браузере
# Desktop: http://localhost:8000/dashboard?theme=concept03
# Defense: http://localhost:8000/dashboard?theme=concept03&defense=true

# Запустить полный набор тестов
python -m pytest

# Создать скриншоты (если настроен Playwright)
cd tooling/visual-qa
python capture_screenshots.py
```

---

## Контрольный список перед защитой

- [ ] Все тесты проходят (34/34)
- [ ] Dashboard запускается без ошибок
- [ ] Sparklines отображаются корректно
- [ ] Анимация вентилятора работает плавно
- [ ] Тепловая карта генерируется без ошибок
- [ ] Документация актуальна
- [ ] Демо-видео записано
- [ ] Слайды подготовлены
- [ ] Код закоммичен в git
- [ ] README обновлен

---

## Полезные ссылки

**Документация:**
- `docs/concept03-defense-ready-digital-twin/20_sparklines_implementation.md`
- `docs/concept03-defense-ready-digital-twin/21_fan_animation_improvements.md`
- `docs/concept03-defense-ready-digital-twin/22_heatmap_implementation.md`
- `docs/concept03-defense-ready-digital-twin/23_phase_a_final_summary.md`

**Прогресс:**
- `.omx/plans/phase_a_progress.md`

**Тесты:**
- `tests/unit/test_sparkline.py`
- `tests/unit/test_concept03_kpi_sparklines.py`
- `tests/unit/test_heatmap.py`

---

**Удачи на защите! 🎓🎉**
