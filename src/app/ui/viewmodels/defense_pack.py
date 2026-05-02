from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoFlowStep:
    minute_range: str
    title: str
    operator_action: str
    expected_outcome: str


@dataclass(frozen=True)
class TechnologyRow:
    technology: str
    purpose: str


@dataclass(frozen=True)
class FunctionModuleRow:
    function_name: str
    module_path: str


@dataclass(frozen=True)
class DefensePackView:
    demo_duration: str
    intro: str
    demo_flow: list[DemoFlowStep]
    visual_scenario: list[str]
    technology_rows: list[TechnologyRow]
    function_module_rows: list[FunctionModuleRow]
    model_limitations: list[str]
    ai_usage_notes: list[str]


def build_defense_pack_view() -> DefensePackView:
    return DefensePackView(
        demo_duration="5-7 минут",
        intro=(
            "Этот блок собирает в одном месте сценарий показа, архитектурные опоры и "
            "ограничения модели, чтобы защита проходила без переключения между внешними "
            "документами и без зависимости от интернета."
        ),
        demo_flow=[
            DemoFlowStep(
                minute_range="0:00-0:40",
                title="Открытие и цель проекта",
                operator_action=(
                    "Показать главный экран и коротко назвать задачу: локальная цифровая "
                    "модель приточной вентиляционной установки для учебной демонстрации."
                ),
                expected_outcome=(
                    "Комиссия сразу видит, что проект запускается локально и уже включает "
                    "параметры, 2D-схему, тревоги и тренды."
                ),
            ),
            DemoFlowStep(
                minute_range="0:40-1:40",
                title="Базовый устойчивый режим",
                operator_action=(
                    "Оставить сценарий `midseason`, показать входные параметры слева и "
                    "объяснить, как статус, метрики и сводка синхронно отражают нормальный режим."
                ),
                expected_outcome=(
                    "Подтверждается, что модель даёт воспроизводимое состояние без ручного "
                    "обновления страницы."
                ),
            ),
            DemoFlowStep(
                minute_range="1:40-2:50",
                title="Сценарий `winter`",
                operator_action=(
                    "Переключиться на зимний режим и обратить внимание на рост мощности нагрева, "
                    "изменение температуры притока и реакцию трендов."
                ),
                expected_outcome=(
                    "Показывается, что сценарии не декоративны: они меняют расчётное состояние "
                    "и визуализацию установки."
                ),
            ),
            DemoFlowStep(
                minute_range="2:50-4:10",
                title="Аварийный сценарий `dirty_filter`",
                operator_action=(
                    "Включить загрязнение фильтра и акцентировать красный узел `filter_bank`, "
                    "перепад давления, тревоги и текстовую сводку."
                ),
                expected_outcome=(
                    "Комиссия видит связку «физический параметр -> аварийный статус -> "
                    "объяснимое сообщение на экране»."
                ),
            ),
            DemoFlowStep(
                minute_range="4:10-5:20",
                title="Ручная корректировка параметров",
                operator_action=(
                    "Изменить расход воздуха или наружную температуру вручную и показать, "
                    "что дашборд пересчитывает состояние вне готовых пресетов, а блок "
                    "`Ручная инженерная сверка` пошагово объясняет формулы для активного режима; "
                    "при вопросе о достоверности открыть `Протокол согласия`, а затем "
                    "`Основания валидации`."
                ),
                expected_outcome=(
                    "Подтверждается, что это именно интерактивная модель, а не только набор "
                    "статичных сценариев; расчёт можно кратко защитить по шагам и по источникам "
                    "прямо на экране."
                ),
            ),
            DemoFlowStep(
                minute_range="5:20-6:10",
                title="Фундамент под 3D без риска для MVP",
                operator_action=(
                    "Открыть диагностику браузера и веб-графики и объяснить, что 2D SVG остаётся "
                    "основным режимом отображения, а 3D подключается позже поверх тех же "
                    "визуальных сигналов."
                ),
                expected_outcome=(
                    "Закрывается вопрос о развитии проекта: архитектура уже готова к 3D, "
                    "но защита не зависит от WebGL."
                ),
            ),
            DemoFlowStep(
                minute_range="6:10-6:40",
                title="Завершение",
                operator_action=(
                    "Коротко открыть `Готовность к демо`, показать `Демо-пакет`, затем упомянуть "
                    "справку API `/docs`, автотесты и модульную структуру проекта."
                ),
                expected_outcome=(
                    "Фиксируется инженерная зрелость решения: есть код, тесты, API, "
                    "преддемонстрационная проверка, воспроизводимая упаковка и документированный "
                    "путь дальнейшего развития."
                ),
            ),
        ],
        visual_scenario=[
            "Показ начинать в устойчивом режиме, чтобы 2D SVG-модель читалась как нормальный технологический тракт.",
            "Во время `winter` акцентировать цепочку «наружный воздух -> рекуперация -> нагреватель -> приток -> помещение».",
            "Во время `dirty_filter` держать внимание на узле фильтра, перепаде давления и списке предупреждений справа.",
            "После ручного изменения параметров показать, что сводка и тренды меняются вместе с SVG-мнемосхемой, `Ручной инженерной сверкой`, `Протоколом согласия` и `Основаниями валидации`.",
            "В финале использовать панель диагностики браузера как аргумент, почему 2D остаётся безопасной демонстрационной базой.",
            "Перед завершением открыть `Готовность к демо` и показать, что проект можно собрать в `Демо-пакет` для локального офлайн-показа с явным шагом проверки на целевом демо-ПК.",
        ],
        technology_rows=[
            TechnologyRow(
                technology="Python 3.12+",
                purpose="Основной язык проекта, объединяющий расчётную модель, API и локальный запуск.",
            ),
            TechnologyRow(
                technology="FastAPI",
                purpose="API-контракты, проверка доступности и модульная серверная обвязка приложения.",
            ),
            TechnologyRow(
                technology="Pydantic",
                purpose="Проверка диапазонов параметров и строгая схема обмена между слоями.",
            ),
            TechnologyRow(
                technology="Dash",
                purpose="Операторский экран с реактивной разметкой и обработчиками для локальной демонстрации.",
            ),
            TechnologyRow(
                technology="Plotly",
                purpose="Тренды температуры, расхода и мощности как пояснение поведения модели во времени.",
            ),
            TechnologyRow(
                technology="SVG + Dash assets",
                purpose="Адаптивная 2D-мнемосхема, пригодная для безопасного офлайн-показа на защите.",
            ),
            TechnologyRow(
                technology="Клиентский JS в assets",
                purpose="Быстрое обновление SVG-сцены и браузерная диагностика без перегрузки Python-обработчиков.",
            ),
            TechnologyRow(
                technology="pytest",
                purpose="Автоматическая проверка расчётного ядра, API и логики представлений.",
            ),
        ],
        function_module_rows=[
            FunctionModuleRow(
                function_name="Сборка приложения и подключение API/дашборда",
                module_path="src/app/main.py; src/app/ui/dashboard.py",
            ),
            FunctionModuleRow(
                function_name="Параметры модели и ограничения диапазонов",
                module_path="src/app/simulation/parameters.py",
            ),
            FunctionModuleRow(
                function_name="Базовая конфигурация P0 и зафиксированный контур первой версии",
                module_path=(
                    "config/p0_baseline.yaml; docs/19_p0_baseline.md; "
                    "src/app/services/project_baseline_service.py; src/app/api/routers/project.py; "
                    "src/app/ui/viewmodels/project_baseline.py"
                ),
            ),
            FunctionModuleRow(
                function_name="Расчёт физических зависимостей и состояний",
                module_path="src/app/simulation/equations.py; src/app/simulation/state.py",
            ),
            FunctionModuleRow(
                function_name="Сценарии и загрузка пресетов",
                module_path="src/app/simulation/scenarios.py; data/scenarios/presets.json",
            ),
            FunctionModuleRow(
                function_name="Оркестрация расчёта и формирование трендов",
                module_path="src/app/services/simulation_service.py; src/app/services/trend_service.py",
            ),
            FunctionModuleRow(
                function_name="HTTP-эндпоинты и внешние контракты",
                module_path="src/app/api/routers/*.py",
            ),
            FunctionModuleRow(
                function_name="Разметка дашборда и композиция UI-блоков",
                module_path="src/app/ui/layout.py",
            ),
            FunctionModuleRow(
                function_name="Пакет валидации, Протокол согласия, Основания валидации и ручная инженерная сверка",
                module_path=(
                    "src/app/services/validation_service.py; src/app/api/routers/validation.py; "
                    "src/app/ui/viewmodels/validation_matrix.py; src/app/ui/viewmodels/validation_agreement.py; "
                    "src/app/ui/viewmodels/validation_basis.py; "
                    "src/app/ui/viewmodels/manual_check.py"
                ),
            ),
            FunctionModuleRow(
                function_name="Реактивные обновления статуса, сводки и графиков",
                module_path="src/app/ui/callbacks.py",
            ),
            FunctionModuleRow(
                function_name="Единый словарь визуальных сигналов и привязок сцены",
                module_path="src/app/ui/viewmodels/visualization.py; src/app/ui/scene/bindings.py; data/visualization/scene3d.json",
            ),
            FunctionModuleRow(
                function_name="Диагностика браузера и веб-графики для будущего 3D-режима",
                module_path="src/app/ui/viewmodels/browser_diagnostics.py; src/app/ui/assets/browser_diagnostics.js",
            ),
            FunctionModuleRow(
                function_name="Преддемонстрационная проверка, Демо-пакет и офлайн-готовность",
                module_path=(
                    "src/app/services/demo_readiness_service.py; src/app/api/routers/readiness.py; "
                    "src/app/ui/viewmodels/demo_readiness.py; deploy/build-demo-package.ps1"
                ),
            ),
        ],
        model_limitations=[
            "Текущая версия является учебно-обобщённой моделью ПВУ, а не подтверждённой паспортной цифровой копией конкретного объекта.",
            "Валидация зафиксирована для учебно-обобщённой ПВУ через согласованные контрольные точки, допуски ручной сверки и автотесты; отдельной будущей задачей остаётся калибровка конкретной установки.",
            "Первая версия опирается на стационарный расчёт и упрощённую динамику помещения; PID-регулирование и расширенная автоматика вынесены за пределы MVP.",
            "Будущий 3D-визуализатор архитектурно подготовлен, но зависит от поддержки WebGL и не является обязательной частью защиты; базовый 2D SVG-режим остаётся основным.",
            "Проект не подключается к реальному оборудованию и не использует конфиденциальные данные предприятия.",
        ],
        ai_usage_notes=[
            "ИИ использовался как вспомогательный инструмент для структурирования задач, ускорения черновых правок и проверки ссылок на официальную документацию.",
            "Формулы, допустимые диапазоны, сценарии, инженерные допущения и финальные решения по архитектуре проверялись и принимались автором проекта.",
            "Интеграция правок, тестирование, запуск приложения и интерпретация результатов выполнялись в рабочем контуре проекта, а не делегировались внешнему сервису как источнику инженерной истины.",
            "В проекте используются только синтетические или обезличенные данные, поэтому ИИ не получает чувствительные производственные материалы.",
        ],
    )
