# Источники

Дата сверки внешних материалов: 2026-05-02.

## Локальная база

- `C:\My\Work\Diploma\modeling.md`
  - основной источник исходных решений по теме, стеку и функциональности;
  - использован для извлечения MVP-функций, ограничений и общего направления проекта.

## Context7

- `/fastapi/fastapi`
  - подтверждает рекомендуемый паттерн bigger application с `APIRouter`, `include_router()` и автоматической документацией `/docs`.
  - также использован для сверки `response_model` у endpoint'ов `GET /validation/matrix`, `GET /validation/agreement`, `GET /validation/basis`, `POST /validation/manual-check`, `GET /readiness/demo`, `GET /readiness/package`, `POST /readiness/package/build`, `GET /archive/scenarios`, `POST /archive/scenarios`, `GET /exports/result` и `POST /exports/result/build`.
  - дополнительно использован при добавлении `GET /project/baseline`, чтобы новый router оставался в той же модульной схеме bigger application.
- `/docker/docs`
  - использован для сверки актуального Compose-паттерна с `build`, `ports`, `volumes` и `healthcheck` при подготовке `deploy/docker-compose.yml`.
- `/plotly/dash/v3_2_0`
  - подтверждает паттерн `app.layout` + callbacks для реактивного аналитического интерфейса.
- `/websites/dash_plotly`
  - подтверждает использование `assets` и `clientside_callback` для локального JS-рендера SVG-сцены через `window.dash_clientside`.
  - также использован для сверки паттернов секционного dashboard-интерфейса, server callback по `html.Button(n_clicks)` и выбора встроенных блоков `Defense Pack`, `Validation Agreement`, `Validation Basis`, `Manual Check`, `Demo Readiness`, `Demo Bundle`, `Export Pack` и `Scenario Archive` без новых зависимостей.
  - дополнительно использован при встраивании нового dashboard-блока `P0 Baseline` на тех же `html.Table`/`html.Details` без новых UI-зависимостей.
  - дополнительно использован при добавлении `Verified Browser Profile`: live browser capability snapshot по-прежнему собирается через clientside callback в `dcc.Store`, а Python-слой только форматирует и сравнивает его с profile из `data/visualization/browser_capability_profile.json`.
- `/pydantic/pydantic`
  - подтверждает использование `Field(...)` и числовых ограничений для валидации параметров модели.
  - дополнительно использован для строгих nested-model схем с `ConfigDict(extra="forbid")` и `model_validate(...)` при загрузке `validation_agreement.json`.
- `/mrdoob/three.js`
  - использован для сверки следующего этапа optional 3D-viewer: загрузка `GLB/GLTF` через `GLTFLoader`, orbit-навигация через `OrbitControls`, picking через `Raycaster`, resize/render-loop и корректный lifecycle WebGL-renderer.
  - дополнительно использован при реализации P3 Optional 3D-viewer: three.js r170 загружен как локальные ES-модули (`three.module.min.mjs`, `GLTFLoader.mjs`, `OrbitControls.mjs`, `BufferGeometryUtils.js`) в `src/app/ui/assets/vendor/three/`, интеграция через `<script type="importmap">` в `index_string` без npm/bundler.
- запросы по Dash/Plotly для SVG-ассетов и `clientside callbacks` были выполнены;
  - итоговое решение принято по официальной документации Dash и подтверждено локальной проверкой через Playwright.

## Официальные веб-источники

- НПО «Каскад-ГРУП»: учебный стенд «Приточная вентиляция»
  - https://kaskad-asu.com/press-center/newsfeed/postavleny-uchebnye-stendy-dlya-obucheniya-studentov-elektrotehnicheskogo-fakulteta-chgu-im-ulyanova.html
  - использовано для подтверждения профиля предприятия, наличия SCADA/KLogic/OPC-направления и того, что стенд по приточной вентиляции уже оперирует уставками, внешними факторами, ПИД-регулятором, авариями и предысторией параметров.

- Python license
  - https://docs.python.org/3/license.html
  - использовано как источник по лицензии Python.

- NumPy
  - https://numpy.org/
  - использовано как базовый официальный источник по выбранной численной библиотеке.

- SciPy `solve_ivp`
  - https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html
  - использовано как официальный ориентир на случай динамического режима и ОДУ.

- FastAPI bigger applications
  - https://fastapi.tiangolo.com/tutorial/bigger-applications/
  - использовано для модульной структуры API и автоматической документации.

- Dash basic callbacks
  - https://dash.plotly.com/basic-callbacks
  - использовано для паттерна реактивного UI.

- Dash `html.Button`
  - https://dash.plotly.com/dash-html-components/button
  - использовано как reference для server callback по `n_clicks` в кнопках сборки `Demo Bundle`, `Export Pack` и сохранения `Scenario Archive`.

- Dash external resources
  - https://dash.plotly.com/external-resources
  - использовано для решения хранить SVG, CSS и JS-ассеты 2D-модели в `assets`.

- Dash clientside callbacks
  - https://dash.plotly.com/clientside-callbacks
  - использовано как основание для быстрых обновлений 2D-сцены без лишней серверной нагрузки.

- Dash performance
  - https://dash.plotly.com/performance
  - использовано как аргумент держать частые визуальные обновления и будущую 3D-логику изолированно от тяжелых Python-callback'ов.

- Dash `html.Table`
  - https://dash.plotly.com/dash-html-components/table
  - использовано как reference для табличного представления validation-matrix, `Validation Agreement`, `Validation Basis`, `Manual Check`, `Demo Readiness`, `Export Pack` и `Scenario Archive` прямо в dashboard без новых зависимостей.

- Plotly for Python
  - https://plotly.com/python/
  - использовано для выбора интерактивного графического слоя.

- Plotly 3D scatter plots
  - https://plotly.com/python/3d-scatter-plots/
  - использовано как официальный ориентир, что будущий 3D-viewer можно встраивать в тот же стек Plotly/Dash.

- three.js `GLTFLoader`
  - https://threejs.org/docs/#examples/en/loaders/GLTFLoader
  - использовано как reference для плана загрузки `GLB/GLTF`, работы с scene graph и optional animation data.

- three.js `OrbitControls`
  - https://threejs.org/docs/#examples/en/controls/OrbitControls
  - использовано как reference для безопасной camera-навигации в optional 3D-viewer.

- three.js `Raycaster`
  - https://threejs.org/docs/#api/en/core/Raycaster
  - использовано как reference для hover/click picking по 3D-узлам сцены.

- three.js `WebGLRenderer`
  - https://threejs.org/docs/#api/en/renderers/WebGLRenderer
  - использовано как reference для resize/render/dispose lifecycle внутри browser-side 3D-renderer.

- three.js r170 (local assets)
  - https://unpkg.com/three@0.170.0/
  - версия r170, загружена как ES-модули в `src/app/ui/assets/vendor/three/`.
  - включает: `three.module.min.mjs` (691 KB), `GLTFLoader.mjs` (110 KB), `OrbitControls.mjs` (32 KB), `BufferGeometryUtils.js` (32 KB).
  - обновление: скачать новую версию с unpkg, заменить файлы в `vendor/three/`, проверить совместимость importmap и viewer3d.mjs.

- Pydantic fields
  - https://docs.pydantic.dev/latest/concepts/fields/
  - использовано для задания диапазонов и ограничений полей.

- MDN SVG `viewBox`
  - https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/viewBox
  - использовано как основание для адаптивной 2D SVG-мнемосхемы без жесткой привязки к одному разрешению.

- MDN WebGL tutorial
  - https://developer.mozilla.org/docs/Web/API/WebGL_API/Tutorial
  - использовано как официальный ориентир по ограничениям будущего WebGL-режима: 3D должен оставаться необязательным для MVP, потому что он зависит от поддержки браузера и графического стека.

- MDN WebGL best practices
  - https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/WebGL_best_practices
  - использовано как reference для следующего 3D-этапа: ограничение device-pixel budget, resize-поведение, аккуратная работа с памятью GPU и обязательный graceful fallback.

- Khronos glTF 2.0 Specification
  - https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
  - использовано как reference для выбора `GLB/GLTF`, scene graph, узлов, камер, материалов и правил хранения scene metadata.

- MDN `Window.isSecureContext`
  - https://developer.mozilla.org/en-US/docs/Web/API/Window/isSecureContext
  - использовано как reference для отдельного требования secure context внутри `browser_capability_profile.json` и live browser/WebGL diagnostics.

- MDN `HTMLCanvasElement.getContext()`
  - https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/getContext
  - использовано для встроенной проверки `webgl` и `webgl2` через браузерный canvas-контекст.

- MDN `WEBGL_debug_renderer_info`
  - https://developer.mozilla.org/en-US/docs/Web/API/WEBGL_debug_renderer_info
  - использовано как reference для чтения `renderer`/`vendor` в browser diagnostics и фиксации verified GPU-environment внутри `browser_capability_profile.json`.

- MDN `WebGLRenderingContext.getParameter()`
  - https://developer.mozilla.org/en-US/docs/Web/API/WebGLRenderingContext/getParameter
  - использовано как reference для измерения `MAX_TEXTURE_SIZE` и `MAX_VIEWPORT_DIMS` как части verified browser/WebGL envelope.

- MDN `Navigator.userAgentData`
  - https://developer.mozilla.org/en-US/docs/Web/API/Navigator/userAgentData
  - использовано как ориентир для безопасного чтения client hints с fallback на `navigator.userAgent`, потому что API поддерживается не во всех браузерах.

- MDN `Navigator.hardwareConcurrency`
  - https://developer.mozilla.org/en-US/docs/Web/API/Navigator/hardwareConcurrency
  - использовано как ориентир для отображения запаса по CPU в панели browser/WebGL-диагностики.

- MDN `Navigator.deviceMemory`
  - https://developer.mozilla.org/en-US/docs/Web/API/Navigator/deviceMemory
  - использовано как ориентир для отображения reported device memory в панели browser/WebGL-диагностики с пониманием, что API поддерживается не везде.

- MDN `<details>`
  - https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details
  - использовано как ориентир для встраиваемых раскрывающихся секций `Defense Pack`, чтобы материалы к защите были доступны офлайн прямо в dashboard.

- pytest documentation
  - https://docs.pytest.org/en/stable/
  - использовано для подтверждения тестового стека.

- FastAPI response models
  - https://fastapi.tiangolo.com/tutorial/response-model/
  - использовано как reference для явного `response_model` в `GET /validation/matrix`, `GET /validation/agreement`, `GET /validation/basis`, `POST /validation/manual-check`, `GET /readiness/demo`, `GET /readiness/package`, `POST /readiness/package/build`, `GET /archive/scenarios`, `POST /archive/scenarios`, `GET /exports/result` и `POST /exports/result/build`.

- ECMA Open XML overview
  - https://dev.ecma-international.org/wp-content/uploads/OpenXML-White-Paper.pdf
  - использовано как внешний ориентир по структуре SpreadsheetML/Open XML-пакета при сборке минимального локального `XLSX` без дополнительной runtime-зависимости.

- MDN `Navigator.onLine`
  - https://developer.mozilla.org/en-US/docs/Web/API/Navigator/onLine
  - использовано как ориентир для offline/online hint в `Demo Readiness`, с пониманием ограничений и эвристического характера этого признака.

- MDN `Window.innerWidth`
  - https://developer.mozilla.org/en-US/docs/Web/API/Window/innerWidth
  - использовано как reference для viewport preflight в `Demo Readiness`, чтобы предупреждать о слишком узком окне перед показом.

- MDN `Screen.width`
  - https://developer.mozilla.org/en-US/docs/Web/API/Screen/width
  - использовано как reference для экранного preflight-check в `Demo Readiness` и оценки комфортного демонстрационного разрешения.

- DOE Energy Saver: Whole-House Ventilation
  - https://www.energy.gov/energysaver/whole-house-ventilation
  - использовано как внешний методический источник для роли balanced ventilation, HRV/ERV и recovery-логики в `Validation Basis` и `Validation Agreement`.

- NREL / DOE: Research and Development of a Ventilation-Integrated Comfort System
  - https://www.nrel.gov/docs/fy21osti/78352.pdf
  - использовано как основной внешний источник по sensible heat, airflow-density-cp-ΔT и effectiveness formulas для `Manual Check`, `Validation Basis` и `Validation Agreement`.

- Better Buildings Better Plants: Fan System Info Card
  - https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/BP_Fan%20Systems_Info%20Card_Final_0.pdf
  - использовано как внешний источник по fan affinity laws и связи расхода, скорости вентилятора и мощности в `Validation Basis` и `Validation Agreement`.

- DOE FEMP: Operations & Maintenance Best Practices Guide: Release 3.0
  - https://www1.eere.energy.gov/femp/pdfs/om_9.pdf
  - использовано как внешний источник по pressure-drop контролю фильтров и сервисной логике в `Validation Basis` и `Validation Agreement`.

- NIST: A Summary of Industrial Verification, Validation, and Uncertainty Quantification Procedures in Computational Fluid Dynamics
  - https://www.nist.gov/publications/summary-industrial-verification-validation-and-uncertainty-quantification-procedures
  - использовано как внешний методический ориентир, что credibility модели строится на явных V&V-процедурах и что validation format должен быть зафиксирован отдельно от кода и от ad-hoc заметок.

- U.S. DOE: Guide to Operating and Maintaining EnergySmart Schools
  - https://www1.eere.energy.gov/buildings/publications/pdfs/energysmartschools/ess_o-and-m-guide.pdf
  - использовано как внешний ориентир по набору practically checked HVAC-метрик: airflow, temperatures, electrical demand и pressure-drop across filter, что поддержало фиксированный список обязательных выходов baseline и scope agreed control points.

- Docker Compose
  - https://docs.docker.com/compose/
  - использовано как источник для воспроизводимого локального запуска.
- Docker Compose reference
  - https://docs.docker.com/reference/compose-file/
  - использовано как дополнительный reference для структуры `docker-compose.yml`, `healthcheck` и bind-mounts.

- OpenModelica
  - https://openmodelica.org/
  - использовано как официальный ориентир для опционального инженерного усиления.
- OpenModelica User's Guide
  - https://openmodelica.org/doc/OpenModelicaUsersGuide/OpenModelicaUsersGuide-latest.pdf
  - использовано для оценки наличия scripting-подхода и Python-интерфейса `OMPython` при решении по post-MVP адаптеру.

## Как использовать этот список дальше

- Для раздела ВКР о выборе средств реализации брать в первую очередь источники по стеку.
- Для раздела о практической значимости и связи с предприятием брать официальный материал НПО «Каскад-ГРУП».
- При bootstrap проекта дополнительно проверить актуальные версии библиотек и закрепить их в зависимостях.

## Дополнительные источники для пакета M10-M14 (сверка 2026-04-18)

### Context7

- `/websites/dash_plotly`
  - использован для подтверждения паттернов `dcc.Interval` (периодические обновления), `dcc.Store` (разделяемое состояние) и callback-оркестрации для live-симуляции и режима сравнения.
- `/websites/pandas_pydata`
  - использован для сверки параметров `DataFrame.to_csv(...)` при проектировании стабильного CSV-экспорта сценариев и сравнений.
- `/websites/reportlab`
  - использован как reference по `SimpleDocTemplate`, `Paragraph`, `Table` и построению структурированного PDF-отчета.

### Веб-поиск / официальные страницы

- Pandas `DataFrame.to_csv`
  - https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html
  - использовано для фиксации параметров экспорта (`index`, `encoding`, `compression`, `float_format`) и требований к файловому буферу.
- ReportLab User Guide, Chapter 5 (PLATYPUS)
  - https://docs.reportlab.com/reportlab/userguide/ch5_platypus/
  - использовано как основание для структурного шаблона PDF-отчета (doc template + flowables).
- Dash `dcc.Interval`
  - https://dash.plotly.com/dash-core-components/interval
  - использовано как reference для live-обновления интерфейса; подробные примеры взяты через Context7 из-за ограничений парсинга страницы в fetch-инструменте.
- Dash shared state (`dcc.Store`)
  - https://dash.plotly.com/sharing-data-between-callbacks
  - использовано как reference для передачи промежуточного состояния между callback-цепочками; детальные фрагменты сверены через Context7.
- Dash Advanced Callbacks
  - https://dash.plotly.com/advanced-callbacks
  - использовано для сверки `running=[...]` у callback при временной блокировке кнопки сборки сценарного отчета.
- Dash `dcc.Store`
  - https://dash.plotly.com/dash-core-components/store
  - использовано как официальный reference для хранения snapshot состояния сессии и связанного export/report-потока.
- FastAPI Response Model
  - https://fastapi.tiangolo.com/tutorial/response-model/
  - использовано для проверки контрактов `GET /exports/result` и `POST /exports/result/build`, включая вложенный `report` в ответе сборки.
- Python `csv` module
  - https://docs.python.org/3/library/csv.html
  - использовано как reference для секционного CSV-отчета через `csv.writer(...)`.
- `/websites/fastapi_tiangolo`
  - использован через Context7 для сверки схем `response_model` и body-model у новых endpoint-ов `GET/POST /comparison/runs*`.
- Dash `dcc.Dropdown`
  - https://dash.plotly.com/dash-core-components/dropdown
  - использовано как официальный reference для выбора пары прогонов `before/after` из `active run` и `Scenario Archive`.
- `/websites/dash_plotly`
  - использован через Context7 для сверки `dcc.Graph`, HTML-компонентов и `running=[...]` в callback при добавлении legend/status-band и блокировки действий во время длительных UI-операций.
- `/websites/fastapi_tiangolo`
  - использован через Context7 как reference по `response_model` и enum-полям при сохранении совместимых API-контрактов после расширения status/export DTO.
- Plotly Shapes in Python
  - https://plotly.com/python/shapes/
  - использовано как официальный reference для status-band на trend-графике через вертикальные прямоугольники.
- Dash `dcc.Graph`
  - https://dash.plotly.com/dash-core-components/graph
  - использовано как reference по встроенному Plotly figure в dashboard.
- Dash HTML Components
  - https://dash.plotly.com/dash-html-components
  - использовано как reference для legend/status-блока из `html.Div`/`html.P`/`html.Span`.

## Release-readiness сверка M10-M14 (2026-05-02)

- Dash `dcc.Interval`
  - https://dash.plotly.com/dash-core-components/interval
  - подтверждает выбранный механизм auto tick в Simulation Session v2 и привязку частоты к `playback_speed`.
- Dash `dcc.Store`
  - https://dash.plotly.com/dash-core-components/store
  - подтверждает локальный UI-state pattern для preview/build/download потоков, выбора источников comparison и обновления preset metadata.
- Dash `dcc.Dropdown`
  - https://dash.plotly.com/dash-core-components/dropdown
  - подтверждает dashboard-паттерн выбора system/user presets и before/after comparison sources.
- FastAPI `FileResponse`
  - https://fastapi.tiangolo.com/advanced/custom-response/
  - подтверждает безопасную отдачу CSV/PDF/manifest artifacts через `/exports/result/download` и comparison downloads.
- FastAPI response models
  - https://fastapi.tiangolo.com/tutorial/response-model/
  - подтверждает сохранение явных API-контрактов при расширении session/report/comparison/preset DTO.
- ReportLab PLATYPUS
  - https://docs.reportlab.com/reportlab/userguide/ch5_platypus/
  - подтверждает выбранный renderer для структурированного PDF с таблицами, секциями и trend chart без новой зависимости.
- Python `csv`
  - https://docs.python.org/3/library/csv.html
  - подтверждает стандартный парсинг секционного CSV в `scenario-report.v2`.
- pytest
  - https://docs.pytest.org/en/stable/
  - подтверждает единый regression gate для unit, integration и scenario evidence по M10-M14.

Эта сверка не добавляет новых зависимостей. Она фиксирует, что финальные
контракты `scenario-report.v2`, `run-comparison.v2`, `scenario-preset.v2`,
Simulation Session v2 и статусный словарь `Норма` / `Риск` / `Авария`
реализованы на уже выбранном стеке FastAPI + Dash + ReportLab + pytest.
