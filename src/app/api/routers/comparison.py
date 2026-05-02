from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict

from app.api.dependencies import (
    get_comparison_service,
    get_simulation_service,
)
from app.api.downloads import build_download_filename, resolve_download_file
from app.services.comparison_service import (
    RunComparison,
    RunComparisonCompatibilityError,
    RunComparisonExportBuildResult,
    RunComparisonSnapshotSaveResult,
    RunComparisonService,
    RunComparisonSnapshot,
)
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/comparison", tags=["comparison"])


class RunComparisonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    before_reference_id: str
    after_reference_id: str


class RunComparisonSnapshotSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = None
    notes: str = ""


@router.get("/runs", response_model=RunComparisonSnapshot)
def get_run_comparison_snapshot(
    comparison_service: Annotated[RunComparisonService, Depends(get_comparison_service)],
    simulation_service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> RunComparisonSnapshot:
    session = simulation_service.get_session()
    return comparison_service.build_snapshot(session.current_result, session)


@router.post("/runs/before", response_model=RunComparisonSnapshotSaveResult)
def save_run_comparison_before(
    payload: RunComparisonSnapshotSaveRequest,
    comparison_service: Annotated[RunComparisonService, Depends(get_comparison_service)],
    simulation_service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> RunComparisonSnapshotSaveResult:
    session = simulation_service.get_session()
    return comparison_service.save_before(
        session.current_result,
        label=payload.label,
        notes=payload.notes,
    )


@router.post("/runs/after", response_model=RunComparisonSnapshotSaveResult)
def save_run_comparison_after(
    payload: RunComparisonSnapshotSaveRequest,
    comparison_service: Annotated[RunComparisonService, Depends(get_comparison_service)],
    simulation_service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> RunComparisonSnapshotSaveResult:
    session = simulation_service.get_session()
    return comparison_service.save_after(
        session.current_result,
        label=payload.label,
        notes=payload.notes,
    )


@router.post("/runs/build", response_model=RunComparison)
def build_run_comparison(
    payload: RunComparisonRequest,
    comparison_service: Annotated[RunComparisonService, Depends(get_comparison_service)],
    simulation_service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> RunComparison:
    session = simulation_service.get_session()
    try:
        return comparison_service.build_comparison_from_references(
            payload.before_reference_id,
            payload.after_reference_id,
            session.current_result,
            session,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/runs/export", response_model=RunComparisonExportBuildResult)
def export_run_comparison(
    payload: RunComparisonRequest,
    comparison_service: Annotated[RunComparisonService, Depends(get_comparison_service)],
    simulation_service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> RunComparisonExportBuildResult:
    session = simulation_service.get_session()
    try:
        comparison = comparison_service.build_comparison_from_references(
            payload.before_reference_id,
            payload.after_reference_id,
            session.current_result,
            session,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        return comparison_service.export_comparison(comparison)
    except RunComparisonCompatibilityError as exc:
        raise HTTPException(status_code=409, detail="; ".join(exc.issues)) from exc


@router.get("/runs/download", response_class=FileResponse)
def download_run_comparison_artifact(
    path: Annotated[str, Query(min_length=1)],
    service: Annotated[RunComparisonService, Depends(get_comparison_service)],
) -> FileResponse:
    target_file = resolve_download_file(
        service.path_resolver,
        path,
        allowed_prefixes=("artifacts/exports",),
    )
    return FileResponse(
        path=target_file,
        filename=build_download_filename(path, "comparison-artifact.bin"),
    )
