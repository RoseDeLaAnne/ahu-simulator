# config

Здесь будут лежать конфигурационные файлы проекта:

- значения по умолчанию;
- baseline-фиксация P0 и рабочего scope первой версии;
- пресеты режима запуска;
- параметры логирования;
- локальные настройки демонстрации.

Текущие файлы:

- `defaults.yaml` — runtime-настройки приложения;
- `defaults.mobile.yaml` — профиль mobile deployment (HTTPS/CORS/trusted hosts);
- `p0_baseline.yaml` — машиночитаемая фиксация типа модели, обязательных входов/выходов, сценариев защиты и формата валидации первой версии.

Дополнительно:

- `defaults.yaml` используется и при локальном запуске, и внутри контейнерного запуска через `deploy/docker-compose.yml`;
- `defaults.mobile.yaml` подключается через `AHU_SIMULATOR_SETTINGS_FILE` и рассчитан на запуск за reverse-proxy в мобильном контуре;
- в `defaults.yaml` теперь зафиксированы и `status_thresholds` для единого слоя `Норма/Риск/Авария` по KPI, alerts, мнемосхеме, трендам и export;
- post-MVP функции `Event Log`, `Scenario Archive` и `Export Pack` не требуют новых runtime-настроек и пишут артефакты в `artifacts/...` по конвенции проекта.
