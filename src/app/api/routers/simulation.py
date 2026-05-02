from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from app.api.dependencies import get_event_log_service, get_simulation_service
from app.services.event_log_service import EventLogService
from app.services.simulation_service import (
    SimulationService,
    SimulationSessionTransitionError,
)
from app.simulation.parameters import SimulationParameters
from app.simulation.state import SimulationResult, SimulationSession, TrendSeries

router = APIRouter(prefix="/simulation", tags=["simulation"])


class SimulationPlaybackSpeedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    playback_speed: float


@router.post("/run", response_model=SimulationResult)
def run_simulation(
    parameters: SimulationParameters,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
    event_log_service: Annotated[EventLogService, Depends(get_event_log_service)],
) -> SimulationResult:
    previous_result = service.get_state()
    try:
        result = service.run(parameters)
    except SimulationSessionTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    event_log_service.record_simulation_event(
        result,
        previous_result=previous_result,
        trigger="simulation.run",
        source_type="api",
    )
    return result


@router.post("/preview", response_model=SimulationResult)
def preview_simulation(
    parameters: SimulationParameters,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationResult:
    return service.preview(parameters)


@router.get("/trends", response_model=TrendSeries)
def get_simulation_trends(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> TrendSeries:
    return service.get_trends()


@router.get("/session", response_model=SimulationSession)
def get_simulation_session(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationSession:
    return service.get_session()


@router.post("/session/start", response_model=SimulationSession)
def start_simulation_session(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
    event_log_service: Annotated[EventLogService, Depends(get_event_log_service)],
) -> SimulationSession:
    try:
        session = service.start()
    except SimulationSessionTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    event_log_service.record_session_event(
        session,
        trigger="simulation.session.start",
        source_type="api",
    )
    return session


@router.post("/session/pause", response_model=SimulationSession)
def pause_simulation_session(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
    event_log_service: Annotated[EventLogService, Depends(get_event_log_service)],
) -> SimulationSession:
    try:
        session = service.pause()
    except SimulationSessionTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    event_log_service.record_session_event(
        session,
        trigger="simulation.session.pause",
        source_type="api",
    )
    return session


@router.post("/session/speed", response_model=SimulationSession)
def set_simulation_session_speed(
    request: SimulationPlaybackSpeedRequest,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
    event_log_service: Annotated[EventLogService, Depends(get_event_log_service)],
) -> SimulationSession:
    try:
        session = service.set_playback_speed(request.playback_speed)
    except SimulationSessionTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    event_log_service.record_session_event(
        session,
        trigger="simulation.session.speed",
        source_type="api",
    )
    return session


@router.post("/session/reset", response_model=SimulationSession)
def reset_simulation_session(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
    event_log_service: Annotated[EventLogService, Depends(get_event_log_service)],
) -> SimulationSession:
    session = service.reset()
    event_log_service.record_session_event(
        session,
        trigger="simulation.session.reset",
        source_type="api",
    )
    return session


@router.post("/session/tick", response_model=SimulationSession)
def tick_simulation_session(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
    event_log_service: Annotated[EventLogService, Depends(get_event_log_service)],
) -> SimulationSession:
    try:
        session = service.tick()
    except SimulationSessionTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    event_log_service.record_session_event(
        session,
        trigger="simulation.session.tick",
        source_type="api",
    )
    return session
