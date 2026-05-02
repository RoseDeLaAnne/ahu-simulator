from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_demo_readiness_service
from app.services.demo_readiness_service import (
    DemoPackageBuildResult,
    DemoPackageSnapshot,
    DemoReadinessEvaluation,
    DemoReadinessService,
)

router = APIRouter(prefix="/readiness", tags=["readiness"])


@router.get("/demo", response_model=DemoReadinessEvaluation)
def get_demo_readiness(
    service: Annotated[DemoReadinessService, Depends(get_demo_readiness_service)],
) -> DemoReadinessEvaluation:
    return service.build_readiness()


@router.get("/package", response_model=DemoPackageSnapshot)
def get_demo_package_snapshot(
    service: Annotated[DemoReadinessService, Depends(get_demo_readiness_service)],
) -> DemoPackageSnapshot:
    return service.build_package_snapshot()


@router.post("/package/build", response_model=DemoPackageBuildResult)
def build_demo_package(
    service: Annotated[DemoReadinessService, Depends(get_demo_readiness_service)],
) -> DemoPackageBuildResult:
    try:
        return service.build_demo_package()
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
