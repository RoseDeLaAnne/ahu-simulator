from __future__ import annotations

from app.services.status_service import StatusService
from app.simulation.state import OperationStatus

_STATUS_SERVICE = StatusService()


def status_text(status: OperationStatus) -> str:
    return _STATUS_SERVICE.status_label(status)


def status_class_name(status: OperationStatus) -> str:
    return _STATUS_SERVICE.status_class_name(status)


def status_color(status: OperationStatus) -> str:
    return _STATUS_SERVICE.status_color(status)


def status_summary(status: OperationStatus) -> str:
    return _STATUS_SERVICE.status_summary(status)
