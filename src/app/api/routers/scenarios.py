from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import get_event_log_service, get_simulation_service
from app.services.event_log_service import EventLogService
from app.services.scenario_preset_service import ScenarioPresetMutationError
from app.services.simulation_service import (
    SimulationService,
    SimulationSessionTransitionError,
)
from app.simulation.parameters import SimulationParameters
from app.simulation.scenarios import ScenarioDefinition
from app.simulation.state import SimulationResult

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class UserPresetCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    title: str = Field(min_length=1)
    description: str | None = None
    purpose: str | None = None
    expected_effect: str | None = None
    parameters: SimulationParameters


class UserPresetUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parameters: SimulationParameters


class UserPresetRenameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)


class UserPresetImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preset: dict[str, Any]


@router.get("", response_model=list[ScenarioDefinition])
def list_scenarios(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> list[ScenarioDefinition]:
    return service.list_scenarios()


@router.post("/user", response_model=ScenarioDefinition)
def create_user_preset(
    request: UserPresetCreateRequest,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> ScenarioDefinition:
    try:
        return service.create_user_preset(
            title=request.title,
            parameters=request.parameters,
            preset_id=request.id,
            description=request.description,
            purpose=request.purpose,
            expected_effect=request.expected_effect,
        )
    except ScenarioPresetMutationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.put("/user/{preset_id}", response_model=ScenarioDefinition)
def update_user_preset(
    preset_id: str,
    request: UserPresetUpdateRequest,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> ScenarioDefinition:
    try:
        return service.update_user_preset(preset_id, request.parameters)
    except ScenarioPresetMutationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/user/{preset_id}/rename", response_model=ScenarioDefinition)
def rename_user_preset(
    preset_id: str,
    request: UserPresetRenameRequest,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> ScenarioDefinition:
    try:
        return service.rename_user_preset(preset_id, title=request.title)
    except ScenarioPresetMutationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.delete("/user/{preset_id}", response_model=ScenarioDefinition)
def delete_user_preset(
    preset_id: str,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> ScenarioDefinition:
    try:
        return service.delete_user_preset(preset_id)
    except ScenarioPresetMutationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/user/import", response_model=ScenarioDefinition)
def import_user_preset(
    request: UserPresetImportRequest,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> ScenarioDefinition:
    try:
        return service.import_user_preset(request.preset)
    except ScenarioPresetMutationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/user/{preset_id}/export")
def export_user_preset(
    preset_id: str,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> dict[str, object]:
    try:
        return service.export_user_preset(preset_id)
    except ScenarioPresetMutationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{scenario_id}/run", response_model=SimulationResult)
def run_scenario(
    scenario_id: str,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
    event_log_service: Annotated[EventLogService, Depends(get_event_log_service)],
) -> SimulationResult:
    previous_result = service.get_state()
    try:
        result = service.run_scenario(scenario_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except SimulationSessionTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    event_log_service.record_simulation_event(
        result,
        previous_result=previous_result,
        trigger=f"scenarios.run:{scenario_id}",
        source_type="api",
    )
    return result
