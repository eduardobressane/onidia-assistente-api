from typing import List
from fastapi import APIRouter

from app.services.modelo_ai import ModeloAiService
from app.schemas.modelo_ai import (
    ModeloAiCreate, 
    ModeloAiUpdate, 
    ModeloAiOutList, 
    ModeloAiOutDetail
)
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted

router = APIRouter(prefix="/modelo_ai", tags=["ModeloAI"])


@router.get("", response_model=HttpResponse[List[ModeloAiOutList]])
async def listar():
    modelos: List[ModeloAiOutList] = await ModeloAiService.listar()
    return ok(total=len(modelos), data=modelos)


@router.get("/{id}", response_model=HttpResponse[ModeloAiOutDetail])
async def obter(id: str):
    modelo: ModeloAiOutDetail = await ModeloAiService.obter(id)
    return ok(data=modelo)


@router.post("", response_model=HttpResponse[ModeloAiOutDetail], status_code=201)
async def criar(payload: ModeloAiCreate):
    novo: ModeloAiOutDetail = await ModeloAiService.criar(payload)
    return created(data=novo)


@router.put("/{id}", response_model=HttpResponse[ModeloAiOutDetail])
async def atualizar(id: str, payload: ModeloAiUpdate):
    atualizado: ModeloAiOutDetail = await ModeloAiService.atualizar(id, payload)
    return updated(data=atualizado)


@router.delete("/{id}", response_model=HttpResponse[None], status_code=200)
async def remover(id: str):
    await ModeloAiService.remover(id)
    return deleted()
