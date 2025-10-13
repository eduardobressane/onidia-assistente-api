from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from uuid import UUID

from app.services.agente import AgenteService
from app.schemas.agente import (
    AgenteCreate, AgenteUpdate, AgenteOutList, AgenteOutDetail
)
from app.core.security import require_permissions
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted
from app.core.security import require_permissions, get_current_user, validate_contratante_access

router = APIRouter(prefix="/agentes", tags=["Agentes"])


@router.get("", response_model=HttpResponse[List[AgenteOutList]], dependencies=[Depends(require_permissions(["*", "hafj03vwv4"]))])
def listar(id_contratante: Optional[UUID] = Query(None), nome: Optional[str] = Query(None), current_user: dict = Depends(get_current_user)):
    # Se id_contratante não for informado, usar o cid do usuário atual
    if id_contratante is None:
        id_contratante = current_user.get("cid")
    else:
        validate_contratante_access(current_user, id_contratante)

    agentes: List[AgenteOutList] = AgenteService.listar(id_contratante, nome)
    return ok(total=len(agentes), data=agentes)


@router.get("/{id}", response_model=AgenteOutDetail, dependencies=[Depends(require_permissions(["*", "hafj0kaclm"]))])
def obter(id: str):
    agente: AgenteOutDetail = AgenteService.obter(id)
    return agente


@router.post("", response_model=HttpResponse[AgenteOutDetail], dependencies=[Depends(require_permissions(["*", "hafj0qu4kb"]))])
def criar(payload: AgenteCreate, id_contratante: Optional[UUID] = Query(None)):
    # Se id_contratante não for informado, usar o cid do usuário atual
    if id_contratante is None:
        id_contratante = current_user.get("cid")
    else:
        validate_contratante_access(current_user, id_contratante)

    novo: AgenteOutDetail = AgenteService.criar(id_contratante, payload)
    return created(data=novo)


@router.put("/{id}", response_model=HttpResponse[AgenteOutDetail], dependencies=[Depends(require_permissions(["*", "hafj0vsur6"]))])
def atualizar(id: str, payload: AgenteUpdate):
    agente: AgenteOutDetail = AgenteService.obter(id)

    # Validando se usuário logado pode acessar o dado da contratante
    validate_contratante_access(current_user, agente.id_contratante)

    if agente is not None:
        raise NotFoundError("Agente não encontrado")

    atualizado: AgenteOutDetail = AgenteService.atualizar(id, payload)
    return updated(data=atualizado)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafj0zvbsy"]))])
def remover(id: str):
    agente: AgenteOutDetail = AgenteService.obter(id)

    # Validando se usuário logado pode acessar o dado da contratante
    validate_contratante_access(current_user, agente.id_contratante)

    if agente is not None:
        raise NotFoundError("Agente não encontrado")

    AgenteService.remover(id)
    return deleted()
