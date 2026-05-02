from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict

from app.api.dependencies import (
    get_event_log_service,
    get_export_service,
    get_simulation_service,
)
from app.api.downloads import build_download_filename, resolve_download_file
from app.services.event_log_service import EventLogService
from app.services.export_service import (
    ExportService,
    ResultExportBatchBuildResult,
    ResultExportBuildResult,
    ResultExportPreview,
    ResultExportSnapshot,
)
from app.services.simulation_service import SimulationService
from app.simulation.parameters import SimulationParameters
from app.simulation.state import SimulationResult

router = APIRouter(prefix="/exports", tags=["exports"])


class ResultExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_scenario_id: str | None = None
    parameters: SimulationParameters


class ResultExportBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_scenario_ids: list[str]


@router.get("/result", response_model=ResultExportSnapshot)
def get_result_export_snapshot(
    service: Annotated[ExportService, Depends(get_export_service)],
) -> ResultExportSnapshot:
    return service.build_snapshot()


@router.post("/result/preview", response_model=ResultExportPreview)
def preview_result_export(
    payload: ResultExportRequest,
    simulation_service: Annotated[SimulationService, Depends(get_simulation_service)],
    export_service: Annotated[ExportService, Depends(get_export_service)],
) -> ResultExportPreview:
    result = _resolve_export_result(simulation_service, payload)
    return export_service.preview_result(
        result,
        _resolve_export_session(simulation_service, result),
    )


@router.post("/result/build", response_model=ResultExportBuildResult)
def build_result_export(
    payload: ResultExportRequest,
    simulation_service: Annotated[SimulationService, Depends(get_simulation_service)],
    export_service: Annotated[ExportService, Depends(get_export_service)],
    event_log_service: Annotated[EventLogService, Depends(get_event_log_service)],
) -> ResultExportBuildResult:
    result = _resolve_export_result(simulation_service, payload)
    build_result = export_service.export_result(
        result,
        _resolve_export_session(simulation_service, result),
    )
    event_log_service.record_export_event(
        result,
        manifest_path=build_result.entry.manifest_path,
        source_type="api",
    )
    return build_result


@router.post("/result/batch", response_model=ResultExportBatchBuildResult)
def build_result_export_batch(
    payload: ResultExportBatchRequest,
    simulation_service: Annotated[SimulationService, Depends(get_simulation_service)],
    export_service: Annotated[ExportService, Depends(get_export_service)],
    event_log_service: Annotated[EventLogService, Depends(get_event_log_service)],
) -> ResultExportBatchBuildResult:
    if not payload.selected_scenario_ids:
        raise HTTPException(status_code=422, detail="selected_scenario_ids must not be empty")

    items: list[tuple[SimulationResult, None]] = []
    for scenario_id in payload.selected_scenario_ids:
        try:
            result = simulation_service.preview_scenario(scenario_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        items.append((result, None))

    batch_result = export_service.export_results(items)
    for entry, (result, _session) in zip(batch_result.entries, items, strict=True):
        event_log_service.record_export_event(
            result,
            manifest_path=entry.manifest_path,
            source_type="api-batch",
        )
    return batch_result


@router.get("/result/download", response_class=FileResponse)
def download_result_export_artifact(
    path: Annotated[str, Query(min_length=1)],
    service: Annotated[ExportService, Depends(get_export_service)],
) -> FileResponse:
    target_file = resolve_download_file(
        service.path_resolver,
        path,
        allowed_prefixes=("artifacts/exports",),
    )
    return FileResponse(
        path=target_file,
        filename=build_download_filename(path, "export-artifact.bin"),
    )


def _resolve_export_result(
    simulation_service: SimulationService,
    payload: ResultExportRequest,
) -> SimulationResult:
    if payload.selected_scenario_id is None:
        return simulation_service.preview(payload.parameters)

    try:
        scenario = simulation_service.get_scenario(payload.selected_scenario_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if payload.parameters.model_dump() == scenario.parameters.model_dump():
        return simulation_service.preview_scenario(payload.selected_scenario_id)
    return simulation_service.preview(payload.parameters)


def _resolve_export_session(
    simulation_service: SimulationService,
    result: SimulationResult,
):
    session = simulation_service.get_session()
    if session.current_result.parameters.model_dump(mode="json") != result.parameters.model_dump(
        mode="json"
    ):
        return None
    if session.current_result.scenario_id != result.scenario_id:
        return None
    return session
