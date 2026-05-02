from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse

from app.api.dependencies import get_event_log_service
from app.api.downloads import build_download_filename, resolve_download_file
from app.services.event_log_service import EventLogService, EventLogSnapshot

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/log", response_model=EventLogSnapshot)
def get_event_log(
    service: Annotated[EventLogService, Depends(get_event_log_service)],
) -> EventLogSnapshot:
    return service.build_snapshot()


@router.get("/log/download", response_class=FileResponse)
def download_event_log_file(
    path: Annotated[str, Query(min_length=1)],
    service: Annotated[EventLogService, Depends(get_event_log_service)],
) -> FileResponse:
    target_file = resolve_download_file(
        service.path_resolver,
        path,
        allowed_prefixes=(
            "artifacts/event-log",
            "artifacts/exports",
            "artifacts/scenario-archive",
        ),
    )
    return FileResponse(
        path=target_file,
        filename=build_download_filename(path, "event-log.json"),
    )
