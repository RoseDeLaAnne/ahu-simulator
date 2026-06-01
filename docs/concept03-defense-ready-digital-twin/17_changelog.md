# 17. Changelog — concept-03 Defense-Ready Digital Twin

Хронология внедрения концепции concept-03 относительно базового
`legacy`-интерфейса. Источник истины по фазам — `09_implementation_phases.md`,
рабочий чек-лист — `10_todo.md`, контракт — `11_acceptance_criteria.md`.

Формат: каждая запись описывает завершённый инкремент фазы и оставшиеся
открытые пункты. Аддитивность (см. `11 §A`, `15 §O`) соблюдалась —
`legacy`-интерфейс и расчётное ядро не переписывались.

## Phase 0–6 — operator dashboard (ранее)

- **Phase 0 Foundations.** Feature flags (`ui.theme`, `ui.concept03_enabled`,
  `ui.defense_day_variant`), CSS-токены, dashboard mount, SVG-sprite.
- **Phase 1 Shell.** Шесть стабильных регионов на `/dashboard?theme=concept03`,
  tab-order, `?page=` router.
- **Phase 2 Header.** Brand / title / status pills / live-clock / avatar.
- **Phase 3 Left rail.** 5 scenario cards, 4 mode cards, config brief,
  click-bridge к scenario/mode inputs; `ControlMode.SEMI_AUTO`, `TEST`.
- **Phase 4 Right rail.** Status banner, 6 KPI rows, 4 health tiles, live-update.
- **Phase 5 Central canvas.** Tab-bar, 3D viewport на `viewer3d.mjs`, callout
  overlay, 2D fallback, visual bindings v3.
- **Phase 6 Bottom strip + footer.** 4 нижние панели, footer-nav 6 пунктов,
  secured-loop pill, comparison metric/pair selectors, report-build bridge.

## Phase 7 — Defense Day Variant

Готов рабочий desktop-инкремент: header toolbar (Запустить/Пауза/Стоп/Сброс),
4 KPI cards со sparkline, component-status / alarms / event-log аккордеоны,
5 нижних панелей, balances tab, academic footer, 9 defense callouts,
3D PNG capture, defense export manifest.

### Финализация фиделити (текущий инкремент)

Источник истины: `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
(desktop, 1672×941). Сверка — реальными headless-скриншотами 1500×900
(harness `tooling/visual-qa/`, см. `artifacts/playwright/concept03/phase7/`).

- **Header (defense)** доведён до одного ряда на 1500 px:
  - title `МОДЕЛИРОВАНИЕ РАБОТЫ ПРИТОЧНОЙ ВЕНТИЛЯЦИОННОЙ УСТАНОВКИ`
    рендерится в одну строку (nowrap, размер подобран по замеру ширины);
  - meta переведены в inline-формат `Режим: АВТО` (зелёный) / `Шаг модели: 60 с`
    вместо боксов — как на концепте;
  - datetime в одну строку;
  - бренд/тулбар/иконки уплотнены, чтобы освободить место под заголовок.
- **Right rail KPI (defense)** перестроены из сетки 2×2 в одноколоночный
  стек карточек на всю ширину — соответствует геометрии концепта.
- Все изменения CSS строго в области `body.c03-defense` / defense-only классов;
  operator-вариант (tablet) и `legacy` не затронуты (подтверждено
  регрессионными скриншотами 1500×900 и 1920×1080 + `pytest` 247 passed).

### Открытые пункты Phase 7

- Буквальный pixel-diff ≤ 2 % к desktop-концепту недостижим по построению:
  концепт — фотореалистичный AI-рендер (иной 3D, шрифты, идеализированные
  данные). Достигнута структурно-стилевая фиделити; см. `15 §N` (аспирационный
  таргет).
- Дефолтное состояние открывается как **РИСК** (amber), а не зелёная **НОРМА**:
  это рантайм-данные, не CSS. Сценарий `baseline_office_winter` фактически
  моделирует расход ≈ 70 % от задания (1 830 / 2 600 м³/ч), что строгие
  KPI-полосы помечают как предупреждение. Требуется продуктовое решение
  (тюнинг пресета или приведение KPI-задания к достигнутому расходу) —
  данные не подделывались.
- Scene-control dropdowns (Режим/Модель) перекрывают 3D-сцену в defense —
  на концепте их нет; вынесено в полировку (trade-off функция/фиделити).

## Phase 8 — Mobile / responsive

- Mobile header controls, 5-пунктовый bottom-nav, off-canvas, responsive CSS.
- **Проверено реальными скриншотами:** `mobile 375×812`, `mobile 414×896`,
  `portrait tablet 768×1024` рендерятся без горизонтального overflow
  (`scrollWidth == clientWidth` на всех трёх), 0 console errors
  (`artifacts/playwright/concept03/phase8/`).

### Открытые пункты Phase 8

- Capacitor APK / iOS-Android emulation smoke — требует Android SDK / эмулятора
  в окружении сборки; не выполнялось в текущем окружении.
- Легенда 3D-сцены (`viewer3d.mjs`) занимает много места на 375 px — полировка
  отложена, т.к. легенда общая с `legacy` 3D-студией.

## Phase 9 — Closeout

- Добавлены `16_defense_freeze_note.md` и этот changelog.
- Demo-bundle и defense export package уже существуют как сервисы
  (`DemoReadinessService.build_package_snapshot()` →
  `artifacts/demo-packages/<дата>/...zip` + manifest;
  `ExportService.build_defense_export_package(...)`), запускаются из UI.
- Обновлены чекбоксы `10_todo.md` / `11_acceptance_criteria.md`.

## Ссылки

- Фазы: `09_implementation_phases.md`
- To-do: `10_todo.md`
- Acceptance: `11_acceptance_criteria.md`
- QA: `15_qa_checklist.md`
- Freeze note: `16_defense_freeze_note.md`
- Harness: `tooling/visual-qa/`
