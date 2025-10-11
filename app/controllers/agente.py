from typing import List
from fastapi import APIRouter, Depends

from app.services.agente import AgenteService
from app.schemas.agente import (
    AgenteCreate, AgenteUpdate, AgenteOutList, AgenteOutDetail
)
from app.core.security import require_permissions
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted

router = APIRouter(prefix="/agentes", tags=["Agentes"])


@router.get("", response_model=HttpResponse[List[AgenteOutList]], dependencies=[Depends(require_permissions(["*", "hafir5fmxh"]))])
def listar():
    agentes: List[AgenteOutList] = AgenteService.listar()
    return ok(total=len(agentes), data=agentes)


@router.get("/{id}", response_model=AgenteOutDetail, dependencies=[Depends(require_permissions(["*", "hafirf720i"]))])
def obter(id: str):
    agente: AgenteOutDetail = AgenteService.obter(id)
    return agente


@router.post("", response_model=HttpResponse[AgenteOutDetail], dependencies=[Depends(require_permissions(["*", "hafirojaiq"]))])
def criar(payload: AgenteCreate):
    novo: AgenteOutDetail = AgenteService.criar(payload)
    return created(data=novo)


@router.put("/{id}", response_model=HttpResponse[AgenteOutDetail], dependencies=[Depends(require_permissions(["*", "hafis7dqeb"]))])
def atualizar(id: str, payload: AgenteUpdate):
    atualizado: AgenteOutDetail = AgenteService.atualizar(id, payload)
    return updated(data=atualizado)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafisjuecf"]))])
def remover(id: str):
    AgenteService.remover(id)
    return deleted()
