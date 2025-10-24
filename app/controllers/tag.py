from typing import List, Literal
from fastapi import APIRouter, Depends

from app.services.tag import TagService
from app.schemas.tag import (
    TagCreate, TagUpdate, TagOutList, TagOutDetail
)
from app.core.security import require_permissions
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("", response_model=HttpResponse[List[TagOutList]], dependencies=[Depends(require_permissions(["*", "hc707575ma"]))])
def get_all(tag_type: Literal["agent"]):
    tags: List[TagOutList] = TagService.get_all(tag_type=tag_type)
    return ok(total=len(tags), data=tags)


@router.get("/{id}", response_model=TagOutDetail, dependencies=[Depends(require_permissions(["*", "hc707lmouj"]))])
def get_by_id(id: str):
    tag: TagOutDetail = TagService.get_by_id(id)
    return tag


@router.post("", response_model=HttpResponse[TagOutDetail], dependencies=[Depends(require_permissions(["*", "hc709o0fnh"]))])
def create(payload: TagCreate):
    data: TagOutDetail = TagService.create(payload)
    return created(data=data)


@router.put("/{id}", response_model=HttpResponse[TagOutDetail], dependencies=[Depends(require_permissions(["*", "hc70a7rjbr"]))])
def update(id: str, payload: TagUpdate):
    data: TagOutDetail = TagService.update(id, payload)
    return updated(data=data)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hc70al0q51"]))])
def delete(id: str):
    TagService.delete(id)
    return deleted()
