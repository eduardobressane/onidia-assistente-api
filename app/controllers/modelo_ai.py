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

router = APIRouter(prefix="/modelos_ai", tags=["Modelos de AI"])


@router.get("", response_model=HttpResponse[List[ModeloAiOutList]], dependencies=[Depends(require_permissions(["*", "hafinjvq6t"]))])
def listar():
    modelos: List[ModeloAiOutList] = ModeloAiService.listar()
    return ok(total=len(modelos), data=modelos)


@router.get("/{id}", response_model=ModeloAiOutDetail, dependencies=[Depends(require_permissions(["*", "hafinyo101"]))])
def obter(id: str):
    modelo: ModeloAiOutDetail = ModeloAiService.obter(id)
    return modelo


@router.post("", response_model=HttpResponse[ModeloAiOutDetail], dependencies=[Depends(require_permissions(["*", "hafioitpkt"]))])
def criar(payload: ModeloAiCreate):
    novo: ModeloAiOutDetail = ModeloAiService.criar(payload)
    return created(data=novo)


@router.put("/{id}", response_model=HttpResponse[ModeloAiOutDetail], dependencies=[Depends(require_permissions(["*", "hafip1bfnc"]))])
def atualizar(id: str, payload: ModeloAiUpdate):
    atualizado: ModeloAiOutDetail = ModeloAiService.atualizar(id, payload)
    return updated(data=atualizado)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafipau25p"]))])
def remover(id: str):
    ModeloAiService.remover(id)
    return deleted()
