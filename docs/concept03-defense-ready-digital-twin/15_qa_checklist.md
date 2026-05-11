# 15. QA Checklist

> Источник истины:
> - desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
> - tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
> - mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`

Чеклист используется на трёх контрольных точках:

1. **После каждой фазы** (см. `09_implementation_phases.md`) — для
   подтверждения exit-criteria.
2. **Перед merge в `main`** — для регрессии.
3. **Перед защитой** — для финального sign-off (см.
   `14_demo_script.md`, `docs/28_defense_freeze_note.md`).

В каждом разделе чекбоксы. При сбое — открыть багу или вернуть фазу
в работу.

---

## A. Глобальная регрессия

- [ ] **A-1.** `python -m pytest` зелёный (включая unit / integration / scenario).
- [ ] **A-2.** `python -m pytest tests/scenario` зелёный — численные
      значения сценариев не изменились (acceptance в
      `tests/scenario/test_*.py`).
- [ ] **A-3.** `start.bat` запускает приложение, `/dashboard`
      доступен.
- [ ] **A-4.** `?theme=legacy` рендерит старый layout без ошибок.
- [ ] **A-5.** `?theme=concept03` рендерит новый layout без ошибок.
- [ ] **A-6.** `?theme=concept03&defense=true` рендерит Defense Day
      Variant без ошибок.
- [ ] **A-7.** Console (DevTools): 0 errors, 0 warnings (кроме
      ожидаемых deprecations).
- [ ] **A-8.** Network: 0 failed requests при normal flow.

---

## B. Header (operator dashboard, tablet/desktop)

> Источник: `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`

- [ ] **B-1.** Лого «КАСКАД ГРУП» (К-блок + текст) виден слева.
- [ ] **B-2.** Подпись «ООО «НПО «Каскад-ГРУП»» под лого.
- [ ] **B-3.** Title: «ЦИФРОВОЙ ДВОЙНИК ВЕНТИЛЯЦИОННОЙ УСТАНОВКИ П1»
      uppercase.
- [ ] **B-4.** Sub: «Моделирование работы приточной установки» (на
      ширине ≥ 1180 px).
- [ ] **B-5.** Pill «РЕЖИМ ГОТОВНОСТИ» (`shield-check` + 2-line label) green.
- [ ] **B-6.** Pill «СИНХРОНИЗАЦИЯ Активна» green.
- [ ] **B-7.** Datetime «22.05.2025 14:32:41» обновляется.
- [ ] **B-8.** User avatar круг 36 px.
- [ ] **B-9.** Header высота 64-72 px.
- [ ] **B-10.** На 1024 px sub скрывается; pills остаются видимыми.

## B-D. Header (Defense Day Variant)

> Источник: `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`

- [ ] **B-D-1.** Лого «КАСКАД» + ООО «НПО «КАСКАД-ГРУП».
- [ ] **B-D-2.** Title: «МОДЕЛИРОВАНИЕ РАБОТЫ ПРИТОЧНОЙ
      ВЕНТИЛЯЦИОННОЙ УСТАНОВКИ» uppercase.
- [ ] **B-D-3.** Action toolbar: 4 кнопки `Запустить / Пауза / Стоп /
      Сброс` с правильными иконками.
- [ ] **B-D-4.** «Запустить» — primary (cyan), остальные secondary.
- [ ] **B-D-5.** Header meta: «Режим: АВТО», «Шаг модели: 60 с»,
      datetime «08.05.2026 14:35:22».
- [ ] **B-D-6.** Action icons (Экспорт/Отчёт/Справка) видимы справа.
- [ ] **B-D-7.** User avatar круг 36 px (с initials или иконкой).

---

## C. Left Rail

- [ ] **C-1.** Section eyebrow «СЦЕНАРИИ» uppercase letter-spacing.
- [ ] **C-2.** 5 ScenarioCard с правильными иконками и titles.
- [ ] **C-3.** Active card имеет cyan glow + check icon.
- [ ] **C-4.** Click ScenarioCard → KPI правого rail обновляются.
- [ ] **C-5.** Кнопка `+` рядом с eyebrow открывает create-modal.
- [ ] **C-6.** «Управление сценариями» (secondary CTA) → `?page=control`.
- [ ] **C-7.** Section eyebrow «РЕЖИМЫ РАБОТЫ» / «РЕЖИМ РАБОТЫ»
      (Defense Day).
- [ ] **C-8.** 4 ControlModeCard с правильными иконками и titles.
- [ ] **C-9.** Active mode card имеет green pulse dot.
- [ ] **C-10.** Section eyebrow «КОНФИГУРАЦИЯ УСТАНОВКИ» (под
      modes).
- [ ] **C-11.** 8 строк key/value соответствуют
      `equipment_brief` snapshot.
- [ ] **C-12.** «Свойства установки» CTA (tertiary) → `?page=equipment`.
- [ ] **C-13.** Левый rail точно 240-260 px (operator) / 280 px
      (Defense Day) на ширине 1500 px.

---

## D. Central canvas

### D.1. Sub-strip

- [ ] **D-1.** «Объект: Учебно-производственный корпус, помещ. 1.02».
- [ ] **D-2.** «Установка: П1 (Приточная)».
- [ ] **D-3.** Camera tools: 3 (operator) или 7 (Defense Day) icon
      buttons.
- [ ] **D-4.** Compass mini-block 28×28 (operator) или внутри
      viewport (Defense Day).

### D.2. Tab bar

- [ ] **D-5.** 6 tabs (operator) или 5 tabs (Defense Day) с
      правильными labels.
- [ ] **D-6.** Default active = `3D Модель`.
- [ ] **D-7.** Под активным tab — bar 2px cyan.

### D.3. 3D Viewport

- [ ] **D-8.** Сцена рендерится; orbit камера работает.
- [ ] **D-9.** 8 callouts (operator) или 9 callouts (Defense Day)
      позиционируются корректно.
- [ ] **D-10.** Hover на callout раскрывает chevron + дополнительные
      строки.
- [ ] **D-11.** Compass top-right показывает реальное направление.
- [ ] **D-12.** Pagination dots 5 шт; click переключает camera
      preset с transition 400 ms.
- [ ] **D-13.** При WebGL fail — automatic fallback на 2D Схему.

### D.4. 2D Схема

- [ ] **D-14.** SVG mnemonic из `assets/pvu_mnemonic.svg`
      рендерится.
- [ ] **D-15.** Bindings обновляются согласно `simulation-session-state`.

### D.5. Параметры (operator) / Таблицы (Defense Day)

- [ ] **D-16.** Двухколоночная таблица: входы / выходы.
- [ ] **D-17.** Editability по `ControlMode` (только в `manual`/
      `semi_auto` входы редактируемые).

### D.6. Тренды (operator) / Графики (Defense Day)

- [ ] **D-18.** Plotly figure рендерится с 4 сериями.
- [ ] **D-19.** Timeline соответствует `SimulationSession.history`.

### D.7. Алармы (operator)

- [ ] **D-20.** Список карточек code/level/message + timestamp.
- [ ] **D-21.** Empty state при отсутствии тревог.

### D.8. Документация (operator)

- [ ] **D-22.** 3 карточки (Технологическая карта / Формулы /
      Источники).

### D.9. Балансы (Defense Day only)

- [ ] **D-23.** Plotly + table балансов расходов и энергий.

---

## E. Right rail

### E.1. Status banner

- [ ] **E-1.** Banner с цветом по statusу: NORMAL=green, WARNING=amber,
      ALARM=red.
- [ ] **E-2.** Title (operator) «НОРМАЛЬНАЯ РАБОТА» / sub
      «Критических отклонений нет».
- [ ] **E-3.** Defense Day: eyebrow «ТЕКУЩЕЕ СОСТОЯНИЕ» + green pill
      «НОРМА».

### E.2. KPI list (operator)

- [ ] **E-4.** Eyebrow «КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ».
- [ ] **E-5.** 6 KPI rows:
      - [ ] Производительность,
      - [ ] Статическое давление,
      - [ ] Температура притока,
      - [ ] Относительная влажность,
      - [ ] Эффективность рекуперации,
      - [ ] Потребляемая мощность.
- [ ] **E-6.** Каждая row: label uppercase, value mono large, sub
      muted, progress bar 4 px.
- [ ] **E-7.** Цвет progress bar по state.
- [ ] **E-8.** «Недоступно» state корректно показан для
      humidity / recovery.

### E.3. Health grid (operator)

- [ ] **E-9.** Eyebrow «ОБЩЕЕ СОСТОЯНИЕ».
- [ ] **E-10.** 4 health tiles 2×2 (Оборудование / Автоматика /
      Датчики / Безопасность).
- [ ] **E-11.** Side-stripe 4 px цвет по state.

### E.4. KPI cards (Defense Day)

- [ ] **E-D-1.** 4 KPI cards (Производительность, Температура
      притока, Влажность притока, Потребляемая мощность).
- [ ] **E-D-2.** Каждая card имеет sparkline и delta text.
- [ ] **E-D-3.** Sparkline отображает последние N точек, цвет по
      state.

### E.5. Component status list (Defense Day)

- [ ] **E-D-4.** Accordion «СТАТУС КОМПОНЕНТОВ».
- [ ] **E-D-5.** 7 строк: Фильтр F7, Рекуператор, Нагреватель,
      Вентилятор П1, Увлажнитель, Охладитель, Вентилятор П2.
- [ ] **E-D-6.** Каждая строка имеет value + status icon (✓/⚠/✕).

### E.6. Alarms accordion (Defense Day)

- [ ] **E-D-7.** Header «АКТИВНЫЕ АЛАРМЫ» + count badge.
- [ ] **E-D-8.** Count = 0 → green «0».

### E.7. Event log accordion (Defense Day)

- [ ] **E-D-9.** Header «ЖУРНАЛ СОБЫТИЙ» + collapse icon.
- [ ] **E-D-10.** При expand — 5-7 строк журнала.

---

## F. Bottom strip

### F.1. Operator dashboard (4 panels)

- [ ] **F-1.** Panel «ГОТОВНОСТЬ К ВАЛИДАЦИИ»:
      - [ ] donut 86%,
      - [ ] 5 строк прогресса с правильными %,
      - [ ] статус «В процессе» / «Завершено» / «Просрочено».
- [ ] **F-2.** Panel «СРАВНЕНИЕ: МОДЕЛЬ vs РЕАЛЬНОСТЬ»:
      - [ ] dropdown «Все события»,
      - [ ] mini-line с двумя сериями (Реальные данные / Модель),
      - [ ] sub-text «Показатель: ...»,
      - [ ] CTA «Детальный анализ».
- [ ] **F-3.** Panel «ЖУРНАЛ СОБЫТИЙ»:
      - [ ] dropdown «Все события»,
      - [ ] таблица 5 строк (timestamp / pill / message),
      - [ ] правильные pill-цвета,
      - [ ] CTA «Открыть журнал».
- [ ] **F-4.** Panel «ОТЧЁТЫ И ЭКСПОРТ»:
      - [ ] 4 list-rows (Отчёт / Протокол / Сравнительный / Данные),
      - [ ] CTA «Сформировать отчёт».

### F.2. Defense Day Variant (5 panels)

- [ ] **F-D-1.** Panel «ВАЛИДАЦИЯ МОДЕЛИ»:
      - [ ] 4 строки балансов с галочками,
      - [ ] метка «МОДЕЛЬ ВАЛИДИРОВАНА» green,
      - [ ] дата.
- [ ] **F-D-2.** Panel «ЭКСПОРТНЫЙ ПАКЕТ ДЛЯ ЗАЩИТЫ»:
      - [ ] 6 file rows (Паспорт / Описание / Результаты / Графики /
            2D / 3D),
      - [ ] CTA «Сформировать пакет».
- [ ] **F-D-3.** Panel «СРАВНЕНИЕ СЦЕНАРИЕВ»:
      - [ ] dropdown сценариев,
      - [ ] 4 строки сравнения,
      - [ ] CTA «Открыть детальное сравнение».
- [ ] **F-D-4.** Panel «ЖУРНАЛ СОБЫТИЙ» (большой, 7 строк).
- [ ] **F-D-5.** Panel «ГОТОВНОСТЬ К ЗАЩИТЕ»:
      - [ ] donut 96%,
      - [ ] 4 чекбокс-строки,
      - [ ] CTA «Открыть чек-лист защиты».

---

## G. Footer

### G.1. Operator dashboard

- [ ] **G-1.** Footer-nav 6 пунктов (Дашборд / Оборудование /
      Управление / Аналитика / Библиотека / Настройки).
- [ ] **G-2.** Active = «Дашборд» с top-bar 2px cyan.
- [ ] **G-3.** Версия `Версия: 2.4.1 (build 2025.05.20)` mono.
- [ ] **G-4.** «ЗАЩИЩЁННЫЙ КОНТУР» green pill с shield-check.
- [ ] **G-5.** Click pill открывает popover с диагностикой.
- [ ] **G-6.** Footer высота 64-72 px.

### G.2. Defense Day Variant

- [ ] **G-D-1.** «ВКР 2026» (mono).
- [ ] **G-D-2.** «09.04.01 Информатика и вычислительная техника».
- [ ] **G-D-3.** «Профиль: Информационное и программное обеспечение
      вычислительной техники и автоматизированных систем».
- [ ] **G-D-4.** «Кафедра: Информационные технологии и системы
      управления».
- [ ] **G-D-5.** «Версия модели: 1.3.2».
- [ ] **G-D-6.** Green «Сохранено» badge с check-icon.

---

## H. Сценарии

- [ ] **H-1.** 5 системных сценариев присутствуют:
      - [ ] Номинальный режим / Базовый офис (зима),
      - [ ] Зимний режим / Лето. Экономичный,
      - [ ] Летний режим / Ночь. Минимум воздуха,
      - [ ] Рециркуляция / Защита от замерзания,
      - [ ] Пожарная вентиляция / Проверка 100% расхода.
- [ ] **H-2.** Click scenario меняет активную карточку и обновляет
      KPI.
- [ ] **H-3.** Add scenario через `+` button работает.
- [ ] **H-4.** Edit user preset работает.
- [ ] **H-5.** Delete user preset с confirmation works.
- [ ] **H-6.** Localized titles переключаются по `?breakpoint=...`
      (если включено).

---

## I. Режимы работы

- [ ] **I-1.** Active mode card имеет green dot.
- [ ] **I-2.** Click сменяет mode в `parameters.control_mode`.
- [ ] **I-3.** В режиме `auto` — все inputs read-only кроме сценария.
- [ ] **I-4.** В режиме `manual` — inputs enabled.
- [ ] **I-5.** В режиме `semi_auto` — частичная enabled.
- [ ] **I-6.** В режиме `test` — `TestPanel` появляется в правом rail.

---

## J. Симуляция

- [ ] **J-1.** Click `Запустить` (или Space) запускает session.
- [ ] **J-2.** Pause / Resume / Stop / Reset работают.
- [ ] **J-3.** В running-режиме pulse-индикатор сине-зелёного цвета.
- [ ] **J-4.** Speed control работает (`0.25 / 0.5 / 1 / 2 / 4`).
- [ ] **J-5.** Hotkeys (Space, Esc, 1-5, Q/E, F, M, S) работают.

---

## K. Производительность

- [ ] **K-1.** First Meaningful Paint ≤ 2.5 s на baseline machine.
- [ ] **K-2.** Largest Contentful Paint ≤ 3.5 s.
- [ ] **K-3.** Time-to-Interactive ≤ 4.0 s.
- [ ] **K-4.** WebGL: 60 fps стабильно при orbit на 1366×768.
- [ ] **K-5.** Memory ≤ 200 MB peak.
- [ ] **K-6.** No layout thrashing (DevTools Performance).

---

## L. Доступность

- [ ] **L-1.** axe-core: 0 critical violations.
- [ ] **L-2.** Все icon-buttons имеют `aria-label`.
- [ ] **L-3.** Контраст текста ≥ 4.5:1 (≥ 3:1 для large).
- [ ] **L-4.** Focus ring видим на всех интерактивах.
- [ ] **L-5.** Keyboard tab order логичный (header → left → center →
      right → bottom → footer).
- [ ] **L-6.** Screen reader корректно читает status pills, KPI
      values, callouts.
- [ ] **L-7.** `prefers-reduced-motion` отключает pulse, donut fill,
      chevron rotate.

---

## M. Mobile

> Источник: `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`

- [ ] **M-1.** Header: logo + ООО «НПО Каскад-ГРУП» + «Цифровой
      двойник» + shield-mini + hamburger.
- [ ] **M-2.** Hero: title + status-dot + view dropdown.
- [ ] **M-3.** 3D scene с 7 callouts (mobile-вариант).
- [ ] **M-4.** KPI strip 4 квадрата (Темп. притока, Влажность,
      Расход, Мощность).
- [ ] **M-5.** Row «Сценарий работы» + «Готовность к защите 92%»
      donut.
- [ ] **M-6.** Comparison table 4×2.
- [ ] **M-7.** Журнал событий 3 строки.
- [ ] **M-8.** Экспорт 4 кнопки (Отчёт / Протокол / Сравнительный /
      Экспорт).
- [ ] **M-9.** Bottom-nav 5 пунктов (Главная / Модель / Сценарии /
      Аналитика / Настройки).
- [ ] **M-10.** Active = «Главная» с top-bar cyan.
- [ ] **M-11.** Hamburger открывает off-canvas с пунктом
      «Библиотека».
- [ ] **M-12.** Off-canvas закрывается swipe или backdrop tap.
- [ ] **M-13.** На orientation portrait tablet (768×1024) — mobile
      layout автоматически.
- [ ] **M-14.** Capacitor APK: splash + status-bar тёмные с cyan.
- [ ] **M-15.** Tap target ≥ 44 px на bottom-nav и KPI tiles.

---

## N. Snapshot-сверка

> Эталонные снапшоты: `artifacts/playwright/concept03/`

- [ ] **N-1.** Operator dashboard 1500×900 совпадает с tablet
      концептом ≤ 5% pixel diff.
- [ ] **N-2.** Operator dashboard 1366×768 совпадает (allow more
      transformations).
- [ ] **N-3.** Operator dashboard 1920×1080 совпадает.
- [ ] **N-4.** Defense Day Variant 1500×900 совпадает с desktop
      концептом ≤ 2% pixel diff.
- [ ] **N-5.** Mobile 375×812 совпадает с mobile концептом ≤ 5%
      pixel diff.
- [ ] **N-6.** Mobile 414×896 совпадает.
- [ ] **N-7.** Tablet portrait 768×1024 — applicable mobile layout.

---

## O. Связь с существующим кодом

- [ ] **O-1.** `src/app/simulation/` не модифицирован сверх
      `08_data_mapping.md §3`.
- [ ] **O-2.** `src/app/services/*` модифицированы только аддитивно
      (новые методы / поля с дефолтами).
- [ ] **O-3.** `src/app/api/routers/*` модифицированы только
      аддитивно (новые query params, новые endpoints).
- [ ] **O-4.** Тесты `tests/scenario/*` зелёные без изменений.
- [ ] **O-5.** `pyproject.toml` version обновлён до
      `3.0.0-concept03-defense` в Phase 9.

---

## P. Документация

- [ ] **P-1.** `docs/concept03-defense-ready-digital-twin/README.md`
      обновлён.
- [ ] **P-2.** Все 16 документов `00...15` присутствуют и
      синхронизированы.
- [ ] **P-3.** Каждый документ содержит ссылку на 3 концепт-png.
- [ ] **P-4.** `docs/14_defense_pack.md`, `docs/15_demo_readiness.md`,
      `docs/30_defense_presenter_script.md`,
      `docs/28_defense_freeze_note.md` обновлены.
- [ ] **P-5.** `docs/04_roadmap.md` упоминает блок `P5. Concept-03`.

---

## Q. Финальный sign-off

- [ ] **Q-1.** Все §A–§P пройдены.
- [ ] **Q-2.** Demo flow `14_demo_script.md` проигран без замечаний.
- [ ] **Q-3.** `11_acceptance_criteria.md` §14 (release) пройден.
- [ ] **Q-4.** Tag `git tag v3.0.0-concept03-defense` создан.
- [ ] **Q-5.** `docs/28_defense_freeze_note.md` подписан.
- [ ] **Q-6.** Demo bundle собран и сохранён.

---

## Метод выполнения чеклиста

### Per-phase (фазовая регрессия)

После каждой фазы:

```powershell
.venv\Scripts\Activate.ps1
python -m pytest                              # A-1
python -m pytest tests/playwright/concept03   # N-1..N-7 для текущей фазы
# ручная сверка ключевых пунктов фазы из 11_acceptance_criteria.md
```

### Per-PR (перед merge)

```powershell
python -m pytest
# Чеклист §A полностью
# Чеклист по затронутым областям (B, C, D, E, F, G, H, I, J)
```

### Pre-defense (полный)

```powershell
python -m pytest
.\deploy\build-windows-exe.ps1 -Clean
.\dist\AhuSimulator\AhuSimulator.exe
# Полный чеклист §A–§Q
# 14_demo_script.md прогон полностью
# 28_defense_freeze_note.md подпись
```

## Ссылки

- desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
- tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
- mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`
- Acceptance criteria: `11_acceptance_criteria.md`
- Phases: `09_implementation_phases.md`
- Risks: `13_risks_and_mitigations.md`
- Demo: `14_demo_script.md`
- Freeze note: `docs/28_defense_freeze_note.md`
