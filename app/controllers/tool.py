from typing import List
from fastapi import APIRouter, Depends

from app.services.tool import ToolService
from app.schemas.tool import (
    ToolCreate, ToolUpdate, ToolOutList, ToolOutDetail
)
from app.core.security import require_permissions
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("", response_model=HttpResponse[List[ToolOutList]], dependencies=[Depends(require_permissions(["*", "hafir5fmxh"]))])
async def listar():
    tools: List[ToolOutList] = await ToolService.listar()
    return ok(total=len(tools), data=tools)


@router.get("/{id}", response_model=ToolOutDetail, dependencies=[Depends(require_permissions(["*", "hafirf720i"]))])
async def obter(id: str):
    tool: ToolOutDetail = await ToolService.obter(id)
    return tool


@router.post("", response_model=HttpResponse[ToolOutDetail], dependencies=[Depends(require_permissions(["*", "hafirojaiq"]))])
async def criar(payload: ToolCreate):
    novo: ToolOutDetail = await ToolService.criar(payload)
    return created(data=novo)


@router.put("/{id}", response_model=HttpResponse[ToolOutDetail], dependencies=[Depends(require_permissions(["*", "hafis7dqeb"]))])
async def atualizar(id: str, payload: ToolUpdate):
    atualizado: ToolOutDetail = await ToolService.atualizar(id, payload)
    return updated(data=atualizado)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafisjuecf"]))])
async def remover(id: str):
    await ToolService.remover(id)
    return deleted()
