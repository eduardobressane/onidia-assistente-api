from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from uuid import UUID

from app.services.assistente import AssistenteService
from app.schemas.assistente import (
    AssistenteCreate, 
    AssistenteUpdate, 
    AssistenteOutList, 
    AssistenteOutDetail, 
    AssistenteOutInterno
)
from app.core.security import require_permissions
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted
from app.core.security import require_permissions, get_current_user, validate_contratante_access

router = APIRouter(prefix="/assistentes", tags=["Assistentes"])


@router.get("", response_model=HttpResponse[List[AssistenteOutList]], dependencies=[Depends(require_permissions(["*", "hafj2bx4a5"]))])
def listar(
    id_contratante: Optional[UUID] = Query(None), 
    nome: Optional[str] = Query(None), current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Número da página (inicia em 1)"),
    rpp: int = Query(10, ge=1, le=100, description="Registros por página"),
    ):
    # Se id_contratante não for informado, usar o cid do usuário atual
    if id_contratante is None:
        id_contratante = current_user.get("cid")
    else:
        validate_contratante_access(current_user, id_contratante)

    assistentes: List[AssistenteOutList] = AssistenteService.listar(id_contratante, nome, page, rpp)
    return ok(total=assistentes["total"], pages=assistentes["pages"], data=assistentes["items"])


@router.get("/{id}", response_model=AssistenteOutDetail, dependencies=[Depends(require_permissions(["*", "hafj2g174r"]))])
def obter(id: str):
    assistente: AssistenteOutInterno = AssistenteService.obter(id)

    return AssistenteOutDetail(**assistente.dict())


@router.post("", response_model=HttpResponse[AssistenteOutDetail], dependencies=[Depends(require_permissions(["*", "hafj2l5jy1"]))])
def criar(payload: AssistenteCreate, id_contratante: Optional[UUID] = Query(None), current_user: dict = Depends(get_current_user)):
    # Se id_contratante não for informado, usar o cid do usuário atual
    if id_contratante is None:
        id_contratante = current_user.get("cid")
    else:
        validate_contratante_access(current_user, id_contratante)
    
    novo: AssistenteOutDetail = AssistenteService.criar(id_contratante, payload)
    return created(data=novo)


@router.put("/{id}", response_model=HttpResponse[AssistenteOutDetail], dependencies=[Depends(require_permissions(["*", "hafj2q9evc"]))])
def atualizar(id: str, payload: AssistenteUpdate, current_user: dict = Depends(get_current_user)):
    assistente: AssistenteOutInterno = AssistenteService.obter(id)

    # Validando se usuário logado pode acessar o dado da contratante
    validate_contratante_access(current_user, agente.id_contratante)
    
    atualizado: AssistenteOutDetail = AssistenteService.atualizar(id, payload)
    return updated(data=atualizado)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafj2v3e45"]))])
def remover(id: str, current_user: dict = Depends(get_current_user)):
    assistente: AssistenteOutInterno = AssistenteService.obter(id)

    # Validando se usuário logado pode acessar o dado da contratante
    validate_contratante_access(current_user, agente.id_contratante)

    AssistenteService.remover(id)
    return deleted()
