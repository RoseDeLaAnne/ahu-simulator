from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_simulation_service
from app.services.simulation_service import SimulationService
from app.simulation.state import SimulationResult, TrendSeries

router = APIRouter(tags=["state"])


@router.get("/state", response_model=SimulationResult)
def get_state(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationResult:
    return service.get_state()


@router.get("/trends", response_model=TrendSeries)
def get_trends(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> TrendSeries:
    return service.get_trends()
