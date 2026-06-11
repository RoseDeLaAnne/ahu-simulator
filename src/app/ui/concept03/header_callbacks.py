from __future__ import annotations

from dash import Dash, Input, Output


def register_header_callbacks(app: Dash) -> None:
    app.clientside_callback(
        """
        function(_) {
            var now = new Date();
            var pad = function(value) { return String(value).padStart(2, "0"); };
            var dateText = [
                pad(now.getDate()),
                pad(now.getMonth() + 1),
                now.getFullYear()
            ].join(".");
            var timeText = [
                pad(now.getHours()),
                pad(now.getMinutes()),
                pad(now.getSeconds())
            ].join(":");
            return [dateText, timeText];
        }
        """,
        Output("concept03-clock-date", "children"),
        Output("concept03-clock-time", "children"),
        Input("concept03-header-clock", "n_intervals"),
    )

    @app.callback(
        Output("concept03-sync-pill", "className"),
        Output("concept03-sync-pill-sub", "children"),
        Output("concept03-alarm-strip", "className"),
        Output("concept03-alarm-strip-text", "children"),
        Input("concept03-header-state", "data"),
    )
    def sync_header_status(payload):
        status = str((payload or {}).get("operation_status") or "normal")
        label = str((payload or {}).get("operation_label") or "Активна")
        alarm_count = str((payload or {}).get("alarm_count") or "0")
        highest_alarm = str((payload or {}).get("highest_alarm_level") or "normal")
        state = {
            "normal": "ok",
            "warning": "warn",
            "alarm": "alarm",
        }.get(status, "muted")
        alarm_strip_class = "c03-alarm-strip"
        if highest_alarm == "critical":
            alarm_strip_class += " c03-alarm-strip--alarm"
        elif highest_alarm == "warning":
            alarm_strip_class += " c03-alarm-strip--warn"
        alarm_text = f"Активные тревоги: {alarm_count}"
        return (
            f"c03-status-pill c03-status-pill--{state}",
            label,
            alarm_strip_class,
            alarm_text,
        )
