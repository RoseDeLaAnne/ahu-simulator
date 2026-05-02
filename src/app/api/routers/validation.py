from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_validation_service
from app.services.validation_service import (
    ValidationBasisEvaluation,
    ManualCheckEvaluation,
    ValidationAgreementEvaluation,
    ValidationMatrixEvaluation,
    ValidationService,
)
from app.simulation.parameters import SimulationParameters

router = APIRouter(prefix="/validation", tags=["validation"])


@router.get("/matrix", response_model=ValidationMatrixEvaluation)
def get_validation_matrix(
    service: Annotated[ValidationService, Depends(get_validation_service)],
) -> ValidationMatrixEvaluation:
    return service.build_matrix()


@router.get("/basis", response_model=ValidationBasisEvaluation)
def get_validation_basis(
    service: Annotated[ValidationService, Depends(get_validation_service)],
) -> ValidationBasisEvaluation:
    return service.build_basis()


@router.get("/agreement", response_model=ValidationAgreementEvaluation)
def get_validation_agreement(
    service: Annotated[ValidationService, Depends(get_validation_service)],
) -> ValidationAgreementEvaluation:
    return service.build_agreement()


@router.post("/manual-check", response_model=ManualCheckEvaluation)
def get_manual_check(
    parameters: SimulationParameters,
    service: Annotated[ValidationService, Depends(get_validation_service)],
) -> ManualCheckEvaluation:
    return service.build_manual_check(parameters)
