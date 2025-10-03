from typing import List
from fastapi import APIRouter

from app.services.tool import ToolService
from app.schemas.tool import (
    ToolCreate, ToolUpdate, ToolOutList, ToolOutDetail
)
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("", response_model=HttpResponse[List[ToolOutList]])
async def listar():
    tools: List[ToolOutList] = await ToolService.listar()
    return ok(total=len(tools), data=tools)


@router.get("/{id}", response_model=HttpResponse[ToolOutDetail])
async def obter(id: str):
    tool: ToolOutDetail = await ToolService.obter(id)
    return ok(data=tool)


@router.post("", response_model=HttpResponse[ToolOutDetail], status_code=201)
async def criar(payload: ToolCreate):
    novo: ToolOutDetail = await ToolService.criar(payload)
    return created(data=novo)


@router.put("/{id}", response_model=HttpResponse[ToolOutDetail])
async def atualizar(id: str, payload: ToolUpdate):
    atualizado: ToolOutDetail = await ToolService.atualizar(id, payload)
    return updated(data=atualizado)


@router.delete("/{id}", response_model=HttpResponse[None], status_code=200)
async def remover(id: str):
    await ToolService.remover(id)
    return deleted()
