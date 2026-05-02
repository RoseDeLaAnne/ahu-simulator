# tests

Тесты проекта уже разделены по уровням:

- `unit` — формулы, сервисные правила и локальная логика UI-колбэков;
- `integration` — API-слой, стартовое состояние приложения и валидация ошибок;
- `scenario` — типовые режимы установки и эталонная матрица контрольных точек.

Ключевые проверки текущей версии:

- расчёт температуры, расхода и влияния загрязнения фильтра;
- API-endpoint'ы `/health`, `/simulation/run`, `/state`, `/scenarios/{scenario_id}/run`;
- сценарии `winter`, `dirty_filter` и набор reference-point режимов из `data/validation/reference_points.json`.
- согласованный validation-contract из `data/validation/validation_agreement.json` проверяется через unit/integration-контур API и viewmodels.
