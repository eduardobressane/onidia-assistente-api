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
async def listar():
    agentes: List[AgenteOutList] = await AgenteService.listar()
    return ok(total=len(agentes), data=agentes)


@router.get("/{id}", response_model=AgenteOutDetail, dependencies=[Depends(require_permissions(["*", "hafirf720i"]))])
async def obter(id: str):
    agente: AgenteOutDetail = await AgenteService.obter(id)
    return agente


@router.post("", response_model=HttpResponse[AgenteOutDetail], dependencies=[Depends(require_permissions(["*", "hafirojaiq"]))])
async def criar(payload: AgenteCreate):
    novo: AgenteOutDetail = await AgenteService.criar(payload)
    return created(data=novo)


@router.put("/{id}", response_model=HttpResponse[AgenteOutDetail], dependencies=[Depends(require_permissions(["*", "hafis7dqeb"]))])
async def atualizar(id: str, payload: AgenteUpdate):
    atualizado: AgenteOutDetail = await AgenteService.atualizar(id, payload)
    return updated(data=atualizado)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafisjuecf"]))])
async def remover(id: str):
    await AgenteService.remover(id)
    return deleted()
