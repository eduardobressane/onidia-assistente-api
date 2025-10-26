from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from uuid import UUID

from app.services.ocpm import OCPMService
from app.schemas.ocpm import (
    OCPMCreate,
    OCPMUpdate,
    OCPMOutList,
    OCPMOutDetail,
)
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted
from app.core.security import require_permissions, get_current_user, validate_and_alter_contractor

router = APIRouter(prefix="/ocp-m", tags=["OCP-M"])


@router.get(
    "",
    response_model=HttpResponse[List[OCPMOutList]],
    dependencies=[Depends(require_permissions(["*", "hcopm62e8ho"]))],
)
def get_all(
    contractor_id: Optional[UUID] = Query(None),
    name: Optional[str] = Query(None, description="Filtro parcial por nome"),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Número da página (inicia em 1)"),
    rpp: int = Query(10, ge=1, le=100, description="Registros por página"),
):
    """
    Lista todos os OCP-Ms com paginação e filtro opcional por nome.
    """
    contractor_id = validate_and_alter_contractor(current_user, contractor_id)

    result = OCPMService.get_all(contractor_id, name, page, rpp)
    return ok(total=result["total"], pages=result["pages"], data=result["items"])


@router.get(
    "/{id}",
    response_model=OCPMOutDetail,
    dependencies=[Depends(require_permissions(["*", "hcopm6h72dy"]))],
)
def get_by_id(id: str):
    """
    Retorna os detalhes de um OCP-M pelo ID.
    """
    ocpm = OCPMService.get_by_id(id)
    return ocpm


@router.post(
    "",
    response_model=HttpResponse[OCPMOutDetail],
    dependencies=[Depends(require_permissions(["*", "hcopm7330ey"]))],
)
def create(
    payload: OCPMCreate,
    contractor_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Cria um novo OCP-M.
    """
    contractor_id = validate_and_alter_contractor(current_user, contractor_id)
    data = OCPMService.create(contractor_id, payload)
    return created(data=data)


@router.put(
    "/{id}",
    response_model=HttpResponse[OCPMOutDetail],
    dependencies=[Depends(require_permissions(["*", "hcopm7dippn"]))],
)
def update(id: str, payload: OCPMUpdate):
    """
    Atualiza um OCP-M existente.
    """
    data = OCPMService.update(id, payload)
    return updated(data=data)


@router.delete(
    "/{id}",
    response_model=HttpResponse[None],
    dependencies=[Depends(require_permissions(["*", "hcopm6rqxzz"]))],
)
def delete(id: str):
    """
    Exclui um OCP-M pelo ID.
    """
    OCPMService.delete(id)
    return deleted()
