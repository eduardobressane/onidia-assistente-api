from typing import List, Literal
from fastapi import APIRouter, Depends

from app.services.category import CategoryService
from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryOutList, CategoryOutDetail
)
from app.core.security import require_permissions
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=HttpResponse[List[CategoryOutList]], dependencies=[Depends(require_permissions(["*", "hafir5fmxh"]))])
def get_all(category_type: Literal["agent"]):
    categories: List[CategoryOutList] = CategoryService.get_all(category_type=category_type)
    return ok(total=len(categories), data=categories)


@router.get("/{id}", response_model=CategoryOutDetail, dependencies=[Depends(require_permissions(["*", "hafirf720i"]))])
def get_by_id(id: str):
    category: CategoryOutDetail = CategoryService.get_by_id(id)
    return category


@router.post("", response_model=HttpResponse[CategoryOutDetail], dependencies=[Depends(require_permissions(["*", "hafirojaiq"]))])
def create(payload: CategoryCreate):
    data: CategoryOutDetail = CategoryService.create(payload)
    return created(data=data)


@router.put("/{id}", response_model=HttpResponse[CategoryOutDetail], dependencies=[Depends(require_permissions(["*", "hafis7dqeb"]))])
def update(id: str, payload: CategoryUpdate):
    data: CategoryOutDetail = CategoryService.update(id, payload)
    return updated(data=data)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafisjuecf"]))])
def delete(id: str):
    CategoryService.delete(id)
    return deleted()
