# Demo Readiness

Дата актуализации: 2026-05-02.

## Где это доступно

- В dashboard добавлен отдельный блок `Demo Readiness`.
- Он доступен по якорю `#demo-readiness`.
- API-снимок той же проверки доступен через `GET /readiness/demo`.

## Что входит в блок

- summary по преддемонстрационной готовности проекта;
- checklist по runtime-стеку, launch-скрипту, конфигам, validation-данным, документации и структуре Playwright-артефактов;
- launch-команды для локального показа;
- snapshot версий ключевых runtime-компонентов;
- список маршрутов, которые полезны перед защитой;
- встроенный `Demo Bundle` со status snapshot, zip/manifest сборкой и целевой директорией артефактов;
- ссылка на `Export Pack`, если нужно быстро собрать переносимый `CSV/XLSX/PDF` по текущему прогону;
- ссылка на `Scenario Archive`, если нужно сохранить и зафиксировать показанный режим до упаковки;
- блок Simulation Session v2 для показа `Старт`, `Пауза`, ручного шага, скорости, progress по горизонту и completed badge;
- preview/build/download поток `scenario-report.v2` для CSV/PDF/manifest;
- before/after comparison flow: зафиксировать `До`, изменить режим, зафиксировать `После`, посмотреть interpretation/top deltas и экспортировать `run-comparison.v2`;
- управление user presets: сохранить текущие параметры как пользовательский пресет, применить, переименовать, экспортировать/импортировать и удалить без изменения системных preset-файлов;
- зафиксированный `Browser Profile`, который опирается на `data/visualization/browser_capability_profile.json` и сверяет текущий браузер с verified WebGL-envelope;
- browser brief, который использует clientside-диагностику и предупреждает о слишком маленьком viewport даже в тех случаях, когда 2D-показ остаётся допустимым.

## Как использовать перед защитой

1. Поднять приложение через `.\deploy\run-local.ps1` или запасной `uvicorn`-запуск.
2. Проверить `GET /health` и открыть `/dashboard`.
3. В блоке `Demo Readiness` убедиться, что проектный preflight закрыт и `Browser/WebGL profile демо-ПК` отмечен как готовый.
4. Нажать `Повторить проверку` в `Browser / WebGL`, затем сверить browser brief внутри `Demo Readiness`.
5. Если viewport слишком мал, развернуть браузер на большую область экрана и повторить проверку.
6. В session-блоке выполнить `Старт -> Пауза -> Шаг -> смена скорости -> Сброс`; убедиться, что progress/interval/status обновляются без потери истории.
7. Собрать preview и артефакты отчета, затем проверить доступность CSV/PDF/manifest downloads.
8. Зафиксировать `До`, изменить параметры или применить другой preset, зафиксировать `После`, проверить compatibility/interpretation/top deltas и доступность export только для совместимой пары.
9. Создать временный пользовательский preset из текущих параметров, применить его и удалить; системные `winter`, `summer`, `peak_load` должны оставаться read-only.
10. При необходимости собрать `Demo Bundle` и проверить появление zip/manifest в `artifacts/demo-packages/<дата>/`.
11. Перед финальным показом использовать уже зафиксированный browser profile как baseline и при необходимости обновить snapshot/скриншоты под новую дату.

## Текущее состояние на 2026-05-02

- проектный preflight сейчас выдаёт `6 из 6 пунктов готовы`;
- packaging-контур закрыт технически: `Demo Bundle` собирает архив и manifest прямо из UI или через `.\deploy\build-demo-package.ps1`;
- browser/demo-PC envelope зафиксирован в `data/visualization/browser_capability_profile.json` и подтверждён Playwright-артефактами;
- M10-M14 доведен до release-ready контрактов: Simulation Session v2,
  `scenario-report.v2`, `run-comparison.v2`, `scenario-preset.v2`, единый
  статусный язык `Норма` / `Риск` / `Авария`;
- автоматическая приемка закреплена в `.omx/plans/m10_m14_acceptance_matrix.md`;
- свежий локальный browser walkthrough выполнен 2026-05-02 на
  `http://127.0.0.1:8765/dashboard`; evidence сохранён в
  `artifacts/release-readiness/2026-05-02/`;
- перед защитой walkthrough нужно повторить на целевом демо-окружении, потому
  что итог зависит от реально запущенного dashboard, viewport и браузера;
- dashboard различает как минимум два сценария браузерной пригодности:
  - verified profile match: `Показ допустим`;
  - полноэкранный режим: `Показ допустим`;
  - узкий viewport: `Нужно больше окно`.

## Phase G: защита demo-flow

Финальный защитный слой вынесен в `docs/14_defense_pack.md`: там
зафиксированы demo-flow на 8-10 минут, чеклист за 15 минут и за 2 минуты до
показа, а также план восстановления для типовых сбоев. Этот документ остается
операционным preflight-описанием, а `docs/14_defense_pack.md` является
сценарием выступления.

Свежий Phase G evidence хранится в
`artifacts/release-readiness/2026-05-02/m10-m14-phase-g-evidence.md`.
Минимальный успешный набор перед защитой:

1. `python -m pytest` проходит полностью.
2. `GET /health` отвечает `status=ok`.
3. `/dashboard` открывается в демонстрационном viewport.
4. В dashboard вручную проверены Simulation Session v2, Export Pack,
   Before/After Comparison и User Presets.
5. Серверный процесс после smoke-проверки не оставлен лишним фоновым процессом.

## Phase H: финальный freeze

Финальный локальный freeze выполнен 2026-05-02 на
`http://127.0.0.1:8767/dashboard`. Evidence сохранён в
`artifacts/release-readiness/2026-05-02/m10-m14-phase-h-final-demo-pc-evidence.md`,
а короткая памятка для запуска и показа вынесена в
`docs/28_defense_freeze_note.md`.

Свежий результат проверки:

1. `python -m pytest` прошёл полностью: `198 passed in 17.01s`.
2. `/health` вернул `status=ok`.
3. `/dashboard` вернул HTTP `200` и был открыт через in-app browser.
4. Через UI проверены Simulation Session v2, Export Pack, Before/After
   Comparison v2 и User Presets v2.
5. Через API собран Demo Bundle, потому что click automation для этой кнопки
   в in-app browser попала в ограничение координатного слоя.
6. Временный пользовательский preset удалён, системный
   `data/scenarios/presets.json` не изменялся.

Если защита проходит на другой машине, перед выступлением нужно повторить
короткую проверку viewport/browser profile и один click-pass по 5-7 шагам из
`docs/28_defense_freeze_note.md`.

## Phase I: handoff package

Финальный архивный слой Phase I добавлен как короткий пакет передачи:

- открыть первым: `docs/29_defense_handoff.md`;
- индекс артефактов:
  `artifacts/release-readiness/2026-05-02/m10-m14-defense-handoff-index.md`;
- дальнейшие действия после Phase I - только ручной повтор короткого
  click-pass на фактическом демо-ПК, если он отличается от текущей машины, или
  новые scope-задачи после защиты.

## Зачем это добавлено

- чтобы фаза 8 опиралась не только на материалы защиты, но и на явный launch/preflight-контур;
- чтобы не держать критичные шаги запуска «в голове» перед показом;
- чтобы browser/WebGL-диагностика была связана с практическим verdict по локальной демонстрации, а не только с будущим 3D-слоем;
- чтобы verified browser/demo-PC envelope можно было показать как отдельный артефакт, а не пересказывать устно.
