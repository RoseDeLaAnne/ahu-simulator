# Концепт-03 «Defense-Ready Digital Twin» — индекс пакета

Этот каталог содержит полный пакет проектной документации для внедрения
концепта `concept-03-defense-ready-digital-twin` в проект «AHU Simulator»
(ВКР: «Моделирование работы приточной вентиляционной установки для
ООО «НПО «Каскад-ГРУП»»).

Источник дизайна — три синхронизированных макета:

- desktop (Defense Day Variant): `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
- tablet (Operator Dashboard): `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
- mobile (Field Quick View): `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`
- комментарий: `artifacts/visual-concepts/README.md`

## Что это и зачем

Текущая версия приложения — **техническая лаборатория**: длинный одностраничный
скролл, тёплая палитра amber на чёрном, MVP-фокус и набор post-MVP блоков
(`Defense Pack`, `Demo Readiness`, `Validation Pack`, `Manual Check`,
`Export Pack`, `Scenario Archive`, `Run Comparison`, `Event Log` и т. д.),
видимых одновременно. Это удобно для разработчика, но создаёт визуальный шум
для комиссии ВКР и заказчика.

Концепт-03 переводит продукт в формат **«цифрового двойника»**: один компактный
экран с явным центром внимания (3D-сцена с callout-метками), технологичной
холодно-синей палитрой, чёткими боковыми панелями (сценарии и режимы слева,
состояние и KPI справа) и нижней лентой защитных артефактов.

Под одним концептом-03 уживаются **три комплементарные раскладки**:

| Раскладка | Источник | Назначение | Ключевые отличия |
|---|---|---|---|
| **Operator Dashboard** | tablet макет (1500×1024) | Повседневный оператор-режим — ежедневный пульт | 6 вкладок canvas, 4 нижние панели, footer-nav 6 пунктов, маркер «Защищённый контур», 6 KPI rows |
| **Defense Day Variant** | desktop макет (1500×900) | Демонстрация ВКР: один экран без отвлечений | 5 вкладок canvas (`3D / 2D / Графики / Таблицы / Балансы`), action-toolbar в header (Запустить/Пауза/Стоп/Сброс), 5 нижних панелей включая «Экспортный пакет» и «Готовность к защите 96%», academic footer |
| **Field Quick View** | mobile макет (375×812) | Мобильный полевой осмотр | 7 callouts вокруг 3D, 4 KPI tile, scenario picker, donut «Готовность к защите 92%», 5-пунктовый bottom-nav, off-canvas «Библиотека» |

Подробное описание различий — в `09_implementation_phases.md` (фаза 7
«Defense Day Variant») и `12_migration_strategy.md` (стратегия toggle).

## Состав пакета

| № | Документ | Зачем нужен |
|---|---|---|
| 00 | [`00_vision_and_goals.md`](00_vision_and_goals.md) | Мотивация, целевая аудитория, бизнес-цели, что входит и не входит в scope. |
| 01 | [`01_information_architecture.md`](01_information_architecture.md) | IA, sitemap, нав-модель, page-зоны, переходы. |
| 02 | [`02_visual_design_system.md`](02_visual_design_system.md) | Цветовая палитра, типографика, иконография, токены. |
| 03 | [`03_layout_specification_desktop.md`](03_layout_specification_desktop.md) | Пиксель-точная спецификация desktop (extended-tablet operator dashboard). |
| 04 | [`04_layout_specification_tablet.md`](04_layout_specification_tablet.md) | Tablet-вариант operator dashboard (1500×1024). |
| 05 | [`05_layout_specification_mobile.md`](05_layout_specification_mobile.md) | Mobile field quick view (375×812). |
| 06 | [`06_components_catalog.md`](06_components_catalog.md) | Каталог UI-компонентов с props/состояниями (operator + Defense Day + mobile). |
| 07 | [`07_interaction_design.md`](07_interaction_design.md) | Анимации, переходы, callouts, hover/click, клавиатура, hotkeys. |
| 08 | [`08_data_mapping.md`](08_data_mapping.md) | Связь UI-блоков с services/API/domain текущего проекта; `ControlMode` extension; bindings v3. |
| 09 | [`09_implementation_phases.md`](09_implementation_phases.md) | Поэтапный roadmap (Phase 0–Phase 9), включая Phase 7 Defense Day Variant. |
| 10 | [`10_todo.md`](10_todo.md) | Детальный action-list по фазам с критериями завершения. |
| 11 | [`11_acceptance_criteria.md`](11_acceptance_criteria.md) | Критерии готовности UX/UI и функциональности (по фазам, визуально, perf, a11y, release). |
| 12 | [`12_migration_strategy.md`](12_migration_strategy.md) | Стратегия параллельной миграции с feature toggle (legacy ↔ concept03 ↔ defense). |
| 13 | [`13_risks_and_mitigations.md`](13_risks_and_mitigations.md) | 22 риска (technical / UX / operational / docs / dependencies / defense day) + митигации. |
| 14 | [`14_demo_script.md`](14_demo_script.md) | Сценарий 5/7/10-минутной защиты под концепт-03 (Defense Day Variant). |
| 15 | [`15_qa_checklist.md`](15_qa_checklist.md) | Чек-лист визуальной приёмки, регрессии, и финального sign-off. |

## Принципы пакета

1. **UI/UX-fidelity первый**. Любая правка кода проверяется по
   `concept-03-defense-ready-digital-twin*.png`, а не по «общему ощущению».
2. **Не ломать MVP-ядро**. Расчётный модуль (`src/app/simulation`),
   API-контракты и тесты остаются стабильными; меняется UI-слой и тонкая
   часть viewmodels.
3. **Единый источник статусов**. `StatusService` остаётся единственным
   источником пользовательских формулировок «Норма / Риск / Авария».
4. **2D как fallback**. SVG-мнемосхема и её bindings продолжают работать
   как страховочный путь при отказе WebGL.
5. **Документация — рабочий инструмент**. Эти файлы — не «для отчёта», а
   рабочая база для каждой задачи в пакете concept-03.

## Связь с существующими документами

- `docs/02_functionality.md`, `docs/03_architecture.md` — не переписываются,
  расширяются ссылкой на concept-03-пакет.
- `docs/04_roadmap.md`, `docs/05_execution_phases.md`, `docs/06_todo.md` —
  получают новый блок «P5. Concept-03 Defense-Ready Digital Twin».
- `docs/13_visualization_strategy.md`, `docs/35_3d_visualization_upgrade_plan.md` —
  пересекаются по 3D-сцене; concept-03 наследует наработки и добавляет
  callout-overlay, compass и режимный tab-bar.
- `docs/14_defense_pack.md`, `docs/15_demo_readiness.md` — обновляются
  под новый внешний вид и под demo-скрипт `14_demo_script.md`.

## Быстрый старт по пакету

### Маршруты для разных ролей

**Студент / разработчик** (внедряет концепт):
1. Прочитать `00_vision_and_goals.md` и `01_information_architecture.md`.
2. Открыть `03_layout_specification_desktop.md` (operator dashboard) и
   `04_layout_specification_tablet.md` рядом с tablet-png.
3. Сверить `02_visual_design_system.md` с проектной палитрой и зафиксировать
   токены (CSS variables) в `src/app/ui/assets/concept03_tokens.css`.
4. Изучить `06_components_catalog.md` и `08_data_mapping.md` —
   карта между UI и существующим backend.
5. Идти по фазам из `09_implementation_phases.md` и отмечать чекбоксы в
   `10_todo.md`. Каждая фаза имеет фиксированные acceptance из
   `11_acceptance_criteria.md`.
6. Перед защитой: `14_demo_script.md` + `15_qa_checklist.md`.

**Научный руководитель / комиссия** (просматривает результат):
1. Прочитать `00_vision_and_goals.md` (что и зачем).
2. Прочитать `09_implementation_phases.md` (как поэтапно вводилось).
3. Открыть `14_demo_script.md` и одну из `concept-03-defense-ready-digital-twin*.png`.

**QA / тестировщик**:
1. `11_acceptance_criteria.md` для готовности.
2. `15_qa_checklist.md` для регрессии и финального sign-off.

### Концепт-изображения в одной точке

| Layout | PNG | Документ-спецификация |
|---|---|---|
| desktop / Defense Day Variant | `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png` | `03_layout_specification_desktop.md` (с заметками по Defense Day Variant) и `09_implementation_phases.md → Phase 7` |
| tablet / Operator Dashboard | `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png` | `04_layout_specification_tablet.md` |
| mobile / Field Quick View | `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png` | `05_layout_specification_mobile.md` |

### Toggle на лету (для разработки)

```
http://127.0.0.1:<port>/dashboard?theme=legacy                # старый layout
http://127.0.0.1:<port>/dashboard?theme=concept03             # operator dashboard
http://127.0.0.1:<port>/dashboard?theme=concept03&defense=true # Defense Day Variant
```

Стратегия toggle и rollback описана в `12_migration_strategy.md`.
