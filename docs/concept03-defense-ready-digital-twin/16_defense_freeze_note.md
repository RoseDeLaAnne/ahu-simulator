# 16. Defense Freeze Note — concept-03

Снимок состояния интерфейса concept-03 «Defense-Ready Digital Twin» на момент
подготовки к защите ВКР. Документ фиксирует, что готово, как это проверено и
что остаётся открытым. Источник истины по фазам — `09_implementation_phases.md`.

> Скрин-эталоны: `artifacts/visual-concepts/concept-03-defense-ready-digital-twin{,-tablet,-mobile}.png`
> Фактические скриншоты сборки: `artifacts/playwright/concept03/phase7/`, `phase8/`

## 1. Статус по вариантам

| Вариант | URL | Состояние |
|---|---|---|
| Legacy | `/dashboard` | работает, не затронут |
| Operator dashboard | `/dashboard?theme=concept03` | Phase 0–6 готовы, регрессий нет |
| Defense Day Variant | `/dashboard?theme=concept03&defense=true` | Phase 7 рабочий инкремент + финализация фиделити |
| Mobile / tablet | `?theme=concept03` на ≤ 780 px | Phase 8 рабочий инкремент, без horizontal overflow |

## 2. Проверки (evidence)

- **Регрессия:** `python -m pytest` — **247 passed** (после CSS-финализации Phase 7).
- **Defense 1500×900:** реальный headless-скриншот, 0 console errors;
  header в один ряд, KPI одноколоночные (`phase7/defense-1500x900-final.png`,
  сравнение с `defense-1500x900-before.png`).
- **Operator 1500×900 / 1920×1080:** регрессионные скриншоты — вариант не сломан
  изменениями defense (`phase7/operator-*-regression.png`).
- **Mobile 375×812, 414×896, tablet 768×1024:** рендер без горизонтального
  overflow (`scrollWidth == clientWidth`), 0 console errors (`phase8/`).
- **Harness:** `tooling/visual-qa/` (Playwright headless Chromium) —
  воспроизводимый прогон, см. `17_changelog.md` и память проекта.

## 3. Готово к защите

- Шесть регионов defense-раскладки, header toolbar (Запустить/Пауза/Стоп/Сброс),
  4 KPI cards со sparkline, статус компонентов, алармы, журнал, 5 нижних панелей,
  balances tab, academic footer, 9 defense callouts, 3D PNG capture.
- Header и KPI-rail приведены к геометрии desktop-концепта на 1500 px.
- Demo-bundle и defense export package собираются существующими сервисами
  (`artifacts/demo-packages/`, `artifacts/exports/`).
- Mobile-раскладка целостна на телефоне и portrait-планшете.

## 4. Открытые пункты (осознанно не закрыты)

1. **Буквальный pixel-diff ≤ 2 % / ≤ 5 %** к AI-концептам недостижим по
   построению (фотореалистичный рендер, иные шрифты/данные). Достигнута
   структурно-стилевая фиделити; таргеты в `15 §N` трактуются как аспирационные.
2. **Дефолтное состояние = РИСК (amber), не НОРМА (green).** Рантайм-данные, не
   баг и не CSS. Подтверждено `GET /state`: `parameters.airflow_m3_h=2600`
   (номинал/задание), `actual_airflow_m3_h=1830`, `fan_speed_ratio=0.74`,
   `setpoint_gap_c=0.0`. Регулятор отрабатывает **уставку приточной температуры**
   (тепловая ошибка = 0) и держит вентилятор на 74 % — этого хватает зимней
   тепловой нагрузке; 74 % → 1830 м³/ч ≈ 70 % от номинала 2600, что строгая
   KPI-полоса расхода трактует как предупреждение. Даже при 100 % вентилятор дал
   бы ≈ 2472 < 2600. Это **корректное частично-нагрузочное поведение**. Решение
   (не подделывая данные): (а) сравнивать достигнутый расход с *требуемым по
   режиму*, а не с фиксированным номиналом; (б) показать сценарий полного расхода;
   (в) принять РИСК как честное поведение и объяснить на защите.
3. **Capacitor APK / iOS-Android smoke** — требует Android SDK/эмулятора в
   окружении сборки; не прогонялось.
4. **Полировка:** scene-control dropdowns поверх 3D в defense; легенда сцены на
   узком mobile (общая с legacy `viewer3d.mjs`).

## 5. Перед финальным sign-off (см. 15 §Q)

- [ ] Решить вопрос РИСК/НОРМА (пункт 4.2) — продуктовое решение.
- [ ] Capacitor smoke на устройстве/эмуляторе.
- [ ] Прогон `14_demo_script.md` целиком.
- [ ] Подпись настоящего freeze-note ответственным.
- [ ] Тег `v3.0.0-concept03-defense` (Phase 9 exit, после sign-off).

## 6. Подпись

| Роль | Имя | Дата | Подпись |
|---|---|---|---|
| Автор ВКР | | | |
| Научный руководитель | | | |

---

Связано: `09_implementation_phases.md`, `10_todo.md`, `11_acceptance_criteria.md`,
`14_demo_script.md`, `15_qa_checklist.md`, `17_changelog.md`.
