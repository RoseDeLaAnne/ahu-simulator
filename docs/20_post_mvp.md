# P2 После MVP

Дата обновления: 2026-04-04.

## Что закрыто в рамках P2

- `Event Log` добавлен как отдельный локальный артефактный контур:
  - API: `GET /events/log`;
  - dashboard: блок `Event Log`;
  - storage: `artifacts/event-log/YYYY-MM-DD/pvu-event-*.json`.
- `Control Modes` выведены в отдельный live-блок dashboard:
  - `auto` показывает, удерживается ли уставка и хватает ли доступной мощности;
  - `manual` явно трактуется как `operator override` и фиксируется в журнале событий.
- `Docker Compose` подготовлен:
  - `deploy/Dockerfile`;
  - `deploy/docker-compose.yml`;
  - запуск: `docker compose -f deploy/docker-compose.yml up --build`.
- OpenModelica-адаптер оценён как допустимый, но отложенный.

## OpenModelica: решение по целесообразности

### Что подтверждено по внешним источникам

- Docker и Compose официально поддерживают декларативный запуск Python-сервисов через `compose.yaml`/`docker-compose.yml`, `build`, `ports`, `volumes` и `healthcheck`.
- OpenModelica предоставляет scripting-подход и Python-интерфейс `OMPython`, то есть технически отдельный адаптер действительно реализуем.

### Почему адаптер не внедрён прямо сейчас

- текущий Python-core уже валидирован на уровне учебно-обобщённой ПВУ, API, dashboard и сценариев защиты;
- подключение Modelica добавляет второй расчётный runtime, второй контур отладки и отдельную задачу упаковки для офлайн-показа;
- для текущего scope важнее воспроизводимый локальный запуск, журнал событий, export/archive и прозрачность `auto/manual`, чем второй solver;
- полноценная ценность OpenModelica появится только вместе с более сложной динамикой, FMU/Modelica-моделью конкретной установки или field calibration.

### Итоговое решение

- оставить Python-ядро основным и единственным runtime для текущей версии;
- считать OpenModelica следующим инженерным enhancement, а не обязательной частью post-MVP;
- если адаптер понадобится позже, подключать его как отдельный сервисный слой поверх существующих `simulation/services/api`, не переписывая dashboard и не ломая текущие контракты.

## Что это даёт проекту

- P2 теперь закрывает не только артефакты результата (`Scenario Archive`, `Export Pack`), но и traceability самих действий пользователя;
- ручной и автоматический режимы стали видимы и объяснимы в UI/API;
- локальный запуск можно воспроизводить не только через PowerShell, но и через containerized entrypoint;
- решение по OpenModelica зафиксировано документально и не висит как неопределённый scope-risk.
