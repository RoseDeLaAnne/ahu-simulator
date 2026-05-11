# 13. Risks and Mitigations

> Источник истины:
> - desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
> - tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
> - mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`

Этот документ — реестр рисков, которые могут помешать внедрению
концепта-03. Каждый риск имеет:

- **R-id** — уникальный идентификатор;
- **Probability** — оценка (Low / Medium / High);
- **Impact** — оценка (Low / Medium / High / Critical);
- **Mitigation** — план снижения / устранения;
- **Trigger** — что говорит «риск материализовался»;
- **Owner** — кто следит за риском.

В рамках ВКР `Owner` — это сам выпускник. На больших проектах эту
графу можно расширять.

## 1. Технические риски

### R-1. Dash-фреймворк не справляется с complexity концепта

- **Probability.** Medium.
- **Impact.** High.
- **Trigger.** Перформанс падает ниже 30 fps на 1366×768; visible
  flicker при tab switch; callbacks duplicate-call.
- **Mitigation.**
  - Использовать clientside callbacks для view-only переключений
    (см. `07 §1`).
  - Минимизировать `Output[]` per callback — один callback не
    обновляет более 6 outputs.
  - Применять `dcc.Store` как cache между callback-ами.
  - При phase 5 — заранее провести pilot 3D-сцены с 8 callouts на
    target machine (1366×768).
  - При непреодолимых проблемах — миграция на React/Next.js
    рассматривается ТОЛЬКО после ВКР (см. `12 §13.1`).

### R-2. WebGL не работает на target machine защиты

- **Probability.** Low–Medium (зависит от target laptop комиссии).
- **Impact.** High.
- **Trigger.** `webgl-error` в DevTools; сцена не рендерится.
- **Mitigation.**
  - Tab `2D Схема` — обязательный fallback (см. `01 §3`,
    `04 §4.3.2`).
  - Auto-fallback при `webgl-error`: переключение на 2D с
    notification «3D недоступно».
  - Перед защитой — проверка WebGL на target машине
    (`?theme=concept03&debug=webgl`).
  - В Defense Day Variant — заранее подготовить «Тур по 3D разрезам»
    PNG bundle (`viewer3d.captureViews(...)`), показываемый при
    отказе WebGL.
- **Owner.** Пользователь (студент) перед демонстрацией.

### R-3. Callouts overlap на маленьком экране

- **Probability.** Medium.
- **Impact.** Medium.
- **Trigger.** На 1366×768 callouts перекрывают друг друга / границу
  viewport.
- **Mitigation.**
  - Collision-detection алгоритм в `concept03_overlay.js`
    (см. `07 §5.2`).
  - При недостатке места — chevron-collapse режим: только title +
    значок без значений; полные данные — при hover.
  - Acceptance criteria `A5-4` тестирует это на minimum width.

### R-4. Capacitor mobile build ломается

- **Probability.** Low–Medium.
- **Impact.** Medium (mobile — не критичный для защиты).
- **Trigger.** `npm run build:debug` падает с ошибкой плагина / build
  config.
- **Mitigation.**
  - Перед Phase 8 — pin Capacitor versions в `mobile/package.json`.
  - Хранить рабочий APK от Phase 6 (operator dashboard) как
    safety-net.
  - На защите mobile shell — опционально, не required.
- **Owner.** Студент.

### R-5. PyInstaller frozen build не подхватывает concept-03 ассеты

- **Probability.** Low.
- **Impact.** High (если EXE — основной артефакт защиты).
- **Trigger.** Frozen exe падает с `FileNotFoundError: concept03_tokens.css`.
- **Mitigation.**
  - В `deploy/ahu-simulator-desktop.spec` — явное добавление
    `('src/app/ui/assets/concept03_*', 'app/ui/assets')`.
  - В `dashboard.py` — graceful degradation если css не найден
    (warn в log, fallback на `legacy`).
  - Обязательная `deploy/build-windows-exe.ps1 -Clean` перед защитой.

### R-6. Расширение `ControlMode` enum ломает existing code

- **Probability.** Low.
- **Impact.** Medium.
- **Trigger.** Test failures в `tests/unit/test_parameters.py` или
  unexpected behavior в `equations.py`.
- **Mitigation.**
  - Все новые case-ветки в `equations.py` — fallback на `AUTO`
    или `MANUAL` поведение, без новой физики до Phase 7.
  - `python -m pytest tests/unit` обязательно зелёный после
    расширения enum.
  - В Phase 3 — отдельный коммит «extend ControlMode enum» с
    чек-поинтом по тестам.

## 2. UX-риски

### R-7. Интерфейс выглядит «слишком цифровым» для комиссии

- **Probability.** Low.
- **Impact.** Medium.
- **Trigger.** Comments комиссии: «непонятно», «слишком много элементов».
- **Mitigation.**
  - Demo-script `14_demo_script.md` фокусируется на 3-4 ключевых
    сценариях, не показывает всё одновременно.
  - 5-7 минут проигранного демо предотвращают «overload» комиссии.
  - В offcanvas (mobile) и в `?page=...` разделах — пояснительные
    блоки.

### R-8. Цветовая палитра не воспроизводится корректно на проекторе

- **Probability.** Medium.
- **Impact.** Medium.
- **Trigger.** На демо-проекторе тёмная палитра выглядит «грязно»;
  cyan акценты сливаются.
- **Mitigation.**
  - Перед защитой — тест на target проекторе минимум за неделю.
  - Если проектор плохой — fallback на `?theme=legacy` (известно,
    как выглядит).
  - При необходимости — увеличить контраст cyan-акцентов через
    `--c03-accent` override в `defaults.yaml`.
- **Owner.** Студент перед защитой.

### R-9. Нет фокуса на 3D-сцене (комиссия видит весь экран как «шум»)

- **Probability.** Low.
- **Impact.** Medium.
- **Trigger.** Reviewers говорят «слишком много панелей».
- **Mitigation.**
  - 3D viewport занимает ≥ 45% площади (см. `00 §4`).
  - Demo flow начинается с 3D-сцены и сценариев.
  - В Defense Day Variant — controls в header привлекают внимание к
    запуску.

## 3. Операционные риски

### R-10. Не хватает времени на все 9 фаз до защиты

- **Probability.** High.
- **Impact.** Critical (концепт не готов).
- **Trigger.** К дате защиты Phase 7 не закрыта.
- **Mitigation.**
  - **Минимальный жизнеспособный продукт** для защиты =
    Phase 0–6 (operator dashboard).
  - Phase 7 (Defense Day Variant) — желательно, но не обязательно.
    Если не успеваем — операторский dashboard на 1500×900 с
    «Защищённым контуром» в footer тоже выглядит как defense-ready.
  - Phase 8 (mobile) — необязателен для защиты.
  - Eisenhower priority: Phase 0/1/2/5 — must, Phase 3/4/6 — should,
    Phase 7/8/9 — could.

### R-11. Конфликт с существующим backlog проекта

- **Probability.** Low.
- **Impact.** Medium.
- **Trigger.** Существующие задачи `docs/07_backlog.md` пересекаются
  с concept-03.
- **Mitigation.**
  - В Phase 0 — review `docs/07_backlog.md` и пометка пересечений.
  - Concept-03 НЕ дополняет backlog «backlog» а заменяет его в роли
    P5 (Phase 5 in roadmap).
  - Любая новая задача из backlog проверяется на совместимость с
    concept-03 toggle.

### R-12. Защита переносится / меняется аудитория

- **Probability.** Low.
- **Impact.** High.
- **Trigger.** Объявление о переносе.
- **Mitigation.**
  - Operator dashboard работает в любой ситуации.
  - Defense Day Variant можно отключить за 30 секунд (`?defense=false`).
  - Demo flow гибкий: 5/7/10 минут вариант (см. `14_demo_script.md`).

### R-13. Потеря данных artefacts во время разработки

- **Probability.** Low.
- **Impact.** High.
- **Trigger.** `artifacts/scenario-archive` или
  `artifacts/comparison-snapshots` повреждены / потеряны.
- **Mitigation.**
  - `git ignore` уже настроен на не-коммит больших файлов; концепт
    не меняет этот контракт.
  - Перед началом каждой фазы — `xcopy /E /I artifacts artifacts.bak`.
  - В CI — readiness package сборка тестируется.

## 4. Документационные риски

### R-14. Документация рассогласовывается с реализацией

- **Probability.** Medium.
- **Impact.** Medium.
- **Trigger.** Specifications в `03/04/05` отличаются от реального
  layout; компонент в `06` не соответствует коду.
- **Mitigation.**
  - На каждой фазе — sync документации:
    - `09_implementation_phases.md` помечается как «Phase X done»;
    - `10_todo.md` чекбоксы обновляются;
    - `11_acceptance_criteria.md` обновляется.
  - Snapshot Playwright в `artifacts/playwright/concept03/phaseN/`
    привязан к доку.
  - Перед merge — документ-author читает diff кода и согласует.

### R-15. Документация чрезмерно детальна / устаревает

- **Probability.** Low (документы написаны компактно).
- **Impact.** Low.
- **Mitigation.**
  - Документы 03-05 имеют пиксельные значения, но они привязаны к
    изображениям, которые не меняются.
  - При изменении концепт-png — обновляется ВСЁ дерево документов
    единым PR.

### R-16. Защитная комиссия не имеет доступа к документации

- **Probability.** Low.
- **Impact.** Low.
- **Trigger.** Комиссия запросила документацию, не нашла её.
- **Mitigation.**
  - В `docs/14_defense_pack.md` — single-page summary с прямыми
    ссылками на этот пакет.
  - В demo bundle (`build-demo-bundle --concept03`) включаем PDF
    rendered копию пакета.
  - Defense rehearsal проигрывается с PDF-зеркалом.

## 5. Риски сторонних зависимостей

### R-17. Lucide Icons / Inter font не доступен offline

- **Probability.** Low.
- **Impact.** Medium.
- **Trigger.** «Защищённый контур» = offline; шрифт / icon-pack не
  загружается с CDN.
- **Mitigation.**
  - Все Lucide иконки — в SVG sprite, локально (`concept03_icons.svg`).
  - Inter / Bebas Neue / JetBrains Mono — bundled в
    `src/app/ui/assets/_vendor/fonts/` (если ещё нет).
  - Перед Phase 0 — verified offline run.

### R-18. Three.js / WebGL обновление ломает существующий viewer3d

- **Probability.** Low.
- **Impact.** High.
- **Trigger.** Browser update / library update меняет API.
- **Mitigation.**
  - Three.js — pinned version в
    `src/app/ui/assets/_vendor/three/`.
  - Перед каждой фазой 5/7 — smoke test сцены на target
    Chrome/Edge/Firefox.

### R-19. Plotly не масштабируется в bottom strip

- **Probability.** Low.
- **Impact.** Medium.
- **Trigger.** Plotly mini-line внутри 220 px высоты выглядит
  обрезанным.
- **Mitigation.**
  - Кастомизация Plotly layout (`margin: {l:24,r:8,t:8,b:24}`,
    `xaxis.fixedrange=true`).
  - Альтернатива — заменить на vanilla-SVG sparkline (для cooler
    look, см. `06 §I.4`).

## 6. Защитные риски (Defense Day specific)

### R-20. Запуск симуляции на демонстрации сбоит

- **Probability.** Low–Medium.
- **Impact.** Critical.
- **Trigger.** Click `Запустить` на защите → ошибка.
- **Mitigation.**
  - Перед защитой — отрепетировать demo flow (см. `14_demo_script.md`).
  - В artifacts — pre-recorded session, который можно загрузить
    через `Сценарий → Архив → Загрузить пресет`.
  - Запасная стратегия: «У нас уже есть готовый прогон, давайте
    рассмотрим его...»

### R-21. Сетевая проблема в Defense Day

- **Probability.** Low (offline-loop).
- **Impact.** Low.
- **Trigger.** Нет сети / медленная сеть.
- **Mitigation.**
  - Всё локально (`localhost`).
  - WebSocket / network endpoints — none required.
  - SecuredLoopPill стабильно green.

### R-22. Студент не может объяснить элементы UI

- **Probability.** Low.
- **Impact.** Medium.
- **Trigger.** Вопрос комиссии «Что значит этот блок?».
- **Mitigation.**
  - `14_demo_script.md` содержит подсказки и подсветку каждого блока.
  - `docs/31_defense_qna.md` готовит ответы на 25+ возможных
    вопросов.

## 7. Risk register summary

| R-id | Title | Prob | Impact | Mitigation status |
|---|---|---|---|---|
| R-1 | Dash performance | Medium | High | Active (clientside callbacks) |
| R-2 | WebGL fail | Low–Med | High | Active (2D fallback) |
| R-3 | Callouts overlap | Medium | Medium | Active (collision-detect) |
| R-4 | Capacitor build break | Low–Med | Medium | Pinned versions |
| R-5 | PyInstaller frozen | Low | High | Explicit asset list |
| R-6 | ControlMode enum | Low | Medium | Fallback в equations |
| R-7 | UI «too digital» | Low | Medium | Demo-script focuses |
| R-8 | Projector palette | Medium | Medium | Pre-test target projector |
| R-9 | No focus on 3D | Low | Medium | 45%+ area, demo intro |
| R-10 | Time before defense | High | Critical | Phase 0–6 = MVP |
| R-11 | Backlog conflict | Low | Medium | Review at Phase 0 |
| R-12 | Defense reschedule | Low | High | Toggle на лету |
| R-13 | Artifacts loss | Low | High | Backup перед фазой |
| R-14 | Doc-code drift | Medium | Medium | Sync per phase |
| R-15 | Doc obsolescence | Low | Low | Bound to images |
| R-16 | Doc unavailable | Low | Low | PDF в demo bundle |
| R-17 | Offline assets | Low | Medium | Bundled fonts/sprite |
| R-18 | Three.js break | Low | High | Pinned vendor |
| R-19 | Plotly scale | Low | Medium | Custom layout / SVG |
| R-20 | Live sim fails | Low–Med | Critical | Pre-recorded backup |
| R-21 | Network during defense | Low | Low | Offline-only |
| R-22 | Q&A unanswered | Low | Medium | Q&A doc |

## 8. Триггеры эскалации

- **Critical risk материализовался** → немедленно switch на
  `?theme=legacy` или `?defense=false`.
- **Phase deadline missed** → re-prioritize по Eisenhower; Phase 7+
  откладываются.
- **Visual mismatch > 10%** → созыв design review session;
  пересмотр layout-spec.
- **Test regression** → revert текущий PR + investigate.

## 9. Ссылки

- desktop:  `artifacts/visual-concepts/concept-03-defense-ready-digital-twin.png`
- tablet:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-tablet.png`
- mobile:   `artifacts/visual-concepts/concept-03-defense-ready-digital-twin-mobile.png`
- Migration: `12_migration_strategy.md`
- Phases: `09_implementation_phases.md`
- Demo: `14_demo_script.md`
- Q&A: `docs/31_defense_qna.md`
- Existing risks: `docs/08_risks_and_assumptions.md`
- Existing freeze note: `docs/28_defense_freeze_note.md`
