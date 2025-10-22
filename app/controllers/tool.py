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
def get_all():
    tools: List[ToolOutList] = ToolService.get_all()
    return ok(total=len(tools), data=tools)


@router.get("/{id}", response_model=ToolOutDetail, dependencies=[Depends(require_permissions(["*", "hafirf720i"]))])
def get_by_id(id: str):
    tool: ToolOutDetail = ToolService.get_by_id(id)
    return tool


@router.post("", response_model=HttpResponse[ToolOutDetail], dependencies=[Depends(require_permissions(["*", "hafirojaiq"]))])
def create(payload: ToolCreate):
    data: ToolOutDetail = ToolService.create(payload)
    return created(data=data)


@router.put("/{id}", response_model=HttpResponse[ToolOutDetail], dependencies=[Depends(require_permissions(["*", "hafis7dqeb"]))])
def update(id: str, payload: ToolUpdate):
    data: ToolOutDetail = ToolService.update(id, payload)
    return updated(data=data)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafisjuecf"]))])
def delete(id: str):
    ToolService.delete(id)
    return deleted()
