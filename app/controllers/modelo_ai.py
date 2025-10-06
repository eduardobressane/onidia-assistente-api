from typing import List
from fastapi import APIRouter, Depends

from app.services.modelo_ai import ModeloAiService
from app.schemas.modelo_ai import (
    ModeloAiCreate, 
    ModeloAiUpdate, 
    ModeloAiOutList, 
    ModeloAiOutDetail
)
from app.core.security import require_permissions
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted

router = APIRouter(prefix="/modelo_ai", tags=["ModeloAI"])


@router.get("", response_model=HttpResponse[List[ModeloAiOutList]], dependencies=[Depends(require_permissions(["*", "hafinjvq6t"]))])
async def listar():
    modelos: List[ModeloAiOutList] = await ModeloAiService.listar()
    return ok(total=len(modelos), data=modelos)


@router.get("/{id}", response_model=ModeloAiOutDetail, dependencies=[Depends(require_permissions(["*", "hafinyo101"]))])
async def obter(id: str):
    modelo: ModeloAiOutDetail = await ModeloAiService.obter(id)
    return modelo


@router.post("", response_model=HttpResponse[ModeloAiOutDetail], dependencies=[Depends(require_permissions(["*", "hafioitpkt"]))])
async def criar(payload: ModeloAiCreate):
    novo: ModeloAiOutDetail = await ModeloAiService.criar(payload)
    return created(data=novo)


@router.put("/{id}", response_model=HttpResponse[ModeloAiOutDetail], dependencies=[Depends(require_permissions(["*", "hafip1bfnc"]))])
async def atualizar(id: str, payload: ModeloAiUpdate):
    atualizado: ModeloAiOutDetail = await ModeloAiService.atualizar(id, payload)
    return updated(data=atualizado)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafipau25p"]))])
async def remover(id: str):
    await ModeloAiService.remover(id)
    return deleted()
