from __future__ import annotations

from dash import html

from app.ui.viewmodels.browser_diagnostics import BrowserProfileView


def build_scene2d_workspace(browser_profile_view: BrowserProfileView) -> html.Div:
    return html.Div(
        id="scene-2d-wrapper",
        className="scene2d-workspace",
        children=[
            html.Div(
                className="scene2d-overview",
                children=[
                    html.Div(
                        className="render-focus-card",
                        children=[
                            html.Div(
                                className="browser-panel-header",
                                children=[html.H3("2D-мониторинг")],
                            ),
                            html.P(
                                "Базовый режим контроля. Использует те же сигналы, что и 3D-сцена.",
                                className="validation-intro",
                            ),
                        ],
                    ),
                ],
            ),
            html.ObjectEl(
                id="mnemonic-svg-object",
                data="assets/pvu_mnemonic.svg",
                type="image/svg+xml",
                className="mnemonic-object",
            ),
            html.Details(
                className="browser-diagnostics-details",
                children=[
                    html.Summary(
                        className="browser-diagnostics-details__summary",
                        children=[
                            html.Span("Техдиагностика отображения"),
                            html.Span("по запросу", className="detail-tag"),
                        ],
                    ),
                    html.Div(
                        className="browser-panel",
                        children=[
                            html.Div(
                                className="browser-panel-header",
                                children=[
                                    html.H3("Браузер / веб-графика"),
                                    html.Button(
                                        "Повторить проверку",
                                        id="browser-capability-refresh",
                                        n_clicks=0,
                                        type="button",
                                        className="ghost-button",
                                    ),
                                ],
                            ),
                            html.Div(
                                "Проверка",
                                id="browser-capability-status",
                                className="status-pill status-warning",
                            ),
                            html.Div(
                                id="browser-capability-list",
                                className="capability-list",
                            ),
                            html.P(
                                id="browser-capability-note",
                                className="mnemonic-note",
                                children=(
                                    "SVG остаётся базовым контуром отображения, пока снимок браузера не собран."
                                ),
                            ),
                            html.Div(
                                className="readiness-browser-card",
                                children=[
                                    html.Div(
                                        className="browser-panel-header",
                                        children=[
                                            html.H3("Подтверждённый профиль браузера"),
                                            html.Div(
                                                id="browser-profile-status",
                                                className=browser_profile_view.status_class_name,
                                                children=browser_profile_view.status_text,
                                            ),
                                        ],
                                    ),
                                    html.P(
                                        id="browser-profile-summary",
                                        className="validation-intro",
                                        children=browser_profile_view.summary_text,
                                    ),
                                    html.Div(
                                        id="browser-profile-list",
                                        className="capability-list",
                                        children=[
                                            html.Div(
                                                item,
                                                className="capability-item",
                                            )
                                            for item in browser_profile_view.items
                                        ],
                                    ),
                                    html.P(
                                        id="browser-profile-note",
                                        className="mnemonic-note",
                                        children=browser_profile_view.note,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
