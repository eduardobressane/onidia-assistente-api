from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from uuid import UUID

from app.services.authenticator import AuthenticatorService
from app.schemas.authenticator import (
    AuthenticatorCreate,
    AuthenticatorUpdate,
    AuthenticatorOutList,
    AuthenticatorOutDetail,
)
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted
from app.core.security import require_permissions, get_current_user, validate_and_alter_contractor

router = APIRouter(prefix="/authenticators", tags=["Authenticators"])


@router.get(
    "",
    response_model=HttpResponse[List[AuthenticatorOutList]],
    dependencies=[Depends(require_permissions(["*", "hcdg62e8ho"]))],
)
def get_all(
    contractor_id: Optional[UUID] = Query(None),
    name: Optional[str] = Query(None, description="Filtro parcial por nome"),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Número da página (inicia em 1)"),
    rpp: int = Query(10, ge=1, le=100, description="Registros por página"),
):
    """
    Lista todos os Authenticators com paginação e filtro opcional por nome.
    """
    contractor_id = validate_and_alter_contractor(current_user, contractor_id)

    result = AuthenticatorService.get_all(contractor_id, name, page, rpp)
    return ok(total=result["total"], pages=result["pages"], data=result["items"])


@router.get(
    "/{id}",
    response_model=AuthenticatorOutDetail,
    dependencies=[Depends(require_permissions(["*", "hcdg6h72dy"]))],
)
def get_by_id(id: str):
    """
    Retorna os detalhes de um Authenticator pelo ID.
    """
    auth = AuthenticatorService.get_by_id(id)
    return auth


@router.post(
    "",
    response_model=HttpResponse[AuthenticatorOutDetail],
    dependencies=[Depends(require_permissions(["*", "hcdg7330ey"]))],
)
def create(
    payload: AuthenticatorCreate,
    contractor_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Cria um novo Authenticator.
    """
    contractor_id = validate_and_alter_contractor(current_user, contractor_id)
    data = AuthenticatorService.create(contractor_id, payload)
    return created(data=data)


@router.put(
    "/{id}",
    response_model=HttpResponse[AuthenticatorOutDetail],
    dependencies=[Depends(require_permissions(["*", "hcdg7dippn"]))],
)
def update(id: str, payload: AuthenticatorUpdate):
    """
    Atualiza um Authenticator existente.
    """
    data = AuthenticatorService.update(id, payload)
    return updated(data=data)


@router.delete(
    "/{id}",
    response_model=HttpResponse[None],
    dependencies=[Depends(require_permissions(["*", "hcdg6rqxzz"]))],
)
def delete(id: str):
    """
    Exclui um Authenticator pelo ID.
    """
    AuthenticatorService.delete(id)
    return deleted()

@router.post(
    "/{id}/execute",
    response_model=HttpResponse[dict],
    dependencies=[Depends(require_permissions(["*", "hcdg7execau"]))],
)
def execute(id: str):
    """
    Executa o Authenticator (realiza a requisição HTTP configurada) e retorna o resultado da execução.

    - Obtém os dados do authenticator cadastrado no banco.
    - Monta e executa a chamada HTTP (url, método, headers, body).
    - Retorna a resposta já processada conforme o response_map configurado.
    """
    result = AuthenticatorService.execute(id)
    return ok(data=result)
