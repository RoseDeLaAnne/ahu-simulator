from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict

from app.api.dependencies import (
    get_event_log_service,
    get_scenario_archive_service,
    get_simulation_service,
)
from app.api.downloads import build_download_filename, resolve_download_file
from app.services.event_log_service import EventLogService
from app.services.scenario_archive_service import (
    ScenarioArchiveSaveResult,
    ScenarioArchiveService,
    ScenarioArchiveSnapshot,
)
from app.services.simulation_service import SimulationService
from app.simulation.parameters import SimulationParameters

router = APIRouter(prefix="/archive", tags=["archive"])


class ScenarioArchiveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_scenario_id: str | None = None
    parameters: SimulationParameters


@router.get("/scenarios", response_model=ScenarioArchiveSnapshot)
def get_scenario_archive(
    service: Annotated[ScenarioArchiveService, Depends(get_scenario_archive_service)],
) -> ScenarioArchiveSnapshot:
    return service.build_snapshot()


@router.post("/scenarios", response_model=ScenarioArchiveSaveResult)
def save_scenario_archive(
    payload: ScenarioArchiveRequest,
    simulation_service: Annotated[SimulationService, Depends(get_simulation_service)],
    archive_service: Annotated[
        ScenarioArchiveService,
        Depends(get_scenario_archive_service),
    ],
    event_log_service: Annotated[EventLogService, Depends(get_event_log_service)],
) -> ScenarioArchiveSaveResult:
    result = _resolve_archive_result(simulation_service, payload)
    save_result = archive_service.save_result(result)
    event_log_service.record_archive_event(
        result,
        archive_path=save_result.entry.file_path,
        source_type="api",
    )
    return save_result


@router.get("/scenarios/download", response_class=FileResponse)
def download_scenario_archive_file(
    path: Annotated[str, Query(min_length=1)],
    service: Annotated[ScenarioArchiveService, Depends(get_scenario_archive_service)],
) -> FileResponse:
    target_file = resolve_download_file(
        service.path_resolver,
        path,
        allowed_prefixes=("artifacts/scenario-archive",),
    )
    return FileResponse(
        path=target_file,
        filename=build_download_filename(path, "scenario-archive.json"),
    )


def _resolve_archive_result(
    simulation_service: SimulationService,
    payload: ScenarioArchiveRequest,
):
    if payload.selected_scenario_id is None:
        return simulation_service.preview(payload.parameters)

    try:
        scenario = simulation_service.get_scenario(payload.selected_scenario_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if payload.parameters.model_dump() == scenario.parameters.model_dump():
        return simulation_service.preview_scenario(payload.selected_scenario_id)
    return simulation_service.preview(payload.parameters)
