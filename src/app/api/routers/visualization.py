from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_browser_capability_service,
    get_simulation_service,
    get_status_service,
)
from app.services.browser_capability_service import (
    BrowserCapabilityProfile,
    BrowserCapabilityService,
)
from app.services.simulation_service import SimulationService
from app.services.status_service import StatusService
from app.ui.scene.bindings import load_scene_bindings
from app.ui.viewmodels.visualization import (
    VisualizationSignalMap,
    build_visualization_signal_map,
)

router = APIRouter(prefix="/visualization", tags=["visualization"])


@router.get("/state", response_model=VisualizationSignalMap)
def get_visualization_state(
    service: Annotated[SimulationService, Depends(get_simulation_service)],
    status_service: Annotated[StatusService, Depends(get_status_service)],
) -> VisualizationSignalMap:
    return build_visualization_signal_map(
        service.get_state(),
        bindings_version=load_scene_bindings().version,
        status_service=status_service,
    )


@router.get("/browser-profile", response_model=BrowserCapabilityProfile)
def get_browser_profile(
    service: Annotated[
        BrowserCapabilityService, Depends(get_browser_capability_service)
    ],
) -> BrowserCapabilityProfile:
    return service.build_profile()
