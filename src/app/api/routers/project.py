from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_project_baseline_service
from app.services.project_baseline_service import (
    ProjectBaselineService,
    ProjectBaselineSnapshot,
)

router = APIRouter(prefix="/project", tags=["project"])


@router.get("/baseline", response_model=ProjectBaselineSnapshot)
def get_project_baseline(
    service: Annotated[ProjectBaselineService, Depends(get_project_baseline_service)],
) -> ProjectBaselineSnapshot:
    return service.build_snapshot()
