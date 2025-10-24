from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from uuid import UUID

from app.services.ocp import OCPService
from app.schemas.ocp import (
    OCPCreate, OCPUpdate, OCPOutList, OCPOutDetail
)
from app.core.security import require_permissions
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted
from app.core.security import require_permissions, get_current_user, validate_and_alter_contractor

router = APIRouter(prefix="/ocps", tags=["OCPs"])


@router.get("", response_model=HttpResponse[List[OCPOutList]], dependencies=[Depends(require_permissions(["*", "hc9v6zj3sc"]))])
def get_all(
    contractor_id: Optional[UUID] = Query(None), 
    nome: Optional[str] = Query(None), current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Número da página (inicia em 1)"),
    rpp: int = Query(10, ge=1, le=100, description="Registros por página"),
    ):
    contractor_id = validate_and_alter_contractor(current_user, contractor_id)

    agents: List[OCPOutList] = OCPService.get_all(contractor_id, nome, page, rpp)
    return ok(total=agents["total"], pages=agents["pages"], data=agents["items"])


@router.get("/{id}", response_model=OCPOutDetail, dependencies=[Depends(require_permissions(["*", "hc9v7gteo5"]))])
def get_by_id(id: str):
    ocp: OCPOutDetail = OCPService.get_by_id(id)
    return ocp


@router.post("", response_model=HttpResponse[OCPOutDetail], dependencies=[Depends(require_permissions(["*", "hc9v7texzy"]))])
def create(
    payload: OCPCreate,
    contractor_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_user),
    ):
    contractor_id = validate_and_alter_contractor(current_user, contractor_id)
    
    data: OCPOutDetail = OCPService.create(contractor_id, payload)
    return created(data=data)


@router.put("/{id}", response_model=HttpResponse[OCPOutDetail], dependencies=[Depends(require_permissions(["*", "hc9v84px7e"]))])
def update(id: str, payload: OCPUpdate):
    data: OCPOutDetail = OCPService.update(id, payload)
    return updated(data=data)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hc9v8hgdkz"]))])
def delete(id: str):
    OCPService.delete(id)
    return deleted()
