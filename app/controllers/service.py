from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from uuid import UUID

from app.services.service import ServiceService
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceOutList,
    ServiceOutDetail,
)
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted
from app.core.security import require_permissions, get_current_user, validate_and_alter_contractor

router = APIRouter(prefix="/services", tags=["Services"])


@router.get(
    "",
    response_model=HttpResponse[List[ServiceOutList]],
    dependencies=[Depends(require_permissions(["*", "hcdg62svc1"]))],
)
def get_all(
    contractor_id: Optional[UUID] = Query(None),
    name: Optional[str] = Query(None, description="Filtro parcial por nome"),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Número da página (inicia em 1)"),
    rpp: int = Query(10, ge=1, le=100, description="Registros por página"),
):
    """
    Lista todos os serviços com paginação e filtro opcional por nome.
    """
    contractor_id = validate_and_alter_contractor(current_user, contractor_id)

    result = ServiceService.get_all(contractor_id, name, page, rpp)
    return ok(total=result["total"], pages=result["pages"], data=result["items"])


@router.get(
    "/{id}",
    response_model=ServiceOutDetail,
    dependencies=[Depends(require_permissions(["*", "hcdg6svc2"]))],
)
def get_by_id(id: str):
    """
    Retorna os detalhes de um serviço pelo ID.
    """
    service = ServiceService.get_by_id(id)
    return service


@router.post(
    "",
    response_model=HttpResponse[ServiceOutDetail],
    dependencies=[Depends(require_permissions(["*", "hcdg7svc3"]))],
)
def create(
    payload: ServiceCreate,
    contractor_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Cria um novo serviço.
    """
    contractor_id = validate_and_alter_contractor(current_user, contractor_id)
    data = ServiceService.create(contractor_id, payload)
    return created(data=data)


@router.put(
    "/{id}",
    response_model=HttpResponse[ServiceOutDetail],
    dependencies=[Depends(require_permissions(["*", "hcdg7svc4"]))],
)
def update(id: str, payload: ServiceUpdate):
    """
    Atualiza um serviço existente.
    """
    data = ServiceService.update(id, payload)
    return updated(data=data)


@router.delete(
    "/{id}",
    response_model=HttpResponse[None],
    dependencies=[Depends(require_permissions(["*", "hcdg6svc5"]))],
)
def delete(id: str):
    """
    Exclui um serviço pelo ID.
    """
    ServiceService.delete(id)
    return deleted()

@router.post(
    "/{id}/execute",
    response_model=HttpResponse[dict],
    dependencies=[Depends(require_permissions(["*", "srv_execute"]))],
)
def execute(id: str):
    """
    Executa o Service configurado.
    - Se tiver authenticator_id, ele será executado antes e seus valores serão aplicados.
    - Caso contrário, o service será executado diretamente.
    """
    result = ServiceService.execute(id)
    return ok(data=result)