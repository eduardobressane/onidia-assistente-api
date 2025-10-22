from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from uuid import UUID

from app.services.assistant import AssistantService
from app.schemas.assistant import (
    AssistantCreate, 
    AssistantUpdate, 
    AssistantOutList, 
    AssistantOutDetail, 
    AssistantOutInternal
)
from app.core.security import require_permissions
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted
from app.core.security import require_permissions, get_current_user, validate_and_alter_contractor

router = APIRouter(prefix="/assistants", tags=["Assistants"])


@router.get("", response_model=HttpResponse[List[AssistantOutList]], dependencies=[Depends(require_permissions(["*", "hafj2bx4a5"]))])
def get_all(
    contractor_id: Optional[UUID] = Query(None), 
    nome: Optional[str] = Query(None), current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Número da página (inicia em 1)"),
    rpp: int = Query(10, ge=1, le=100, description="Registros por página"),
    ):
    if contractor_id is None:
        contractor_id = validate_and_alter_contractor(current_user, current_user.get("cid"))

    assistants: List[AssistantOutList] = AssistantService.get_all(contractor_id, nome, page, rpp)
    return ok(total=assistants["total"], pages=assistants["pages"], data=assistants["items"])


@router.get("/{id}", response_model=AssistantOutDetail, dependencies=[Depends(require_permissions(["*", "hafj2g174r"]))])
def get_by_id(id: str):
    assistant: AssistantOutInternal = AssistantService.get_by_id(id)

    return AssistantOutDetail(**assistant.dict())


@router.post("", response_model=HttpResponse[AssistantOutDetail], dependencies=[Depends(require_permissions(["*", "hafj2l5jy1"]))])
def create(payload: AssistantCreate, contractor_id: Optional[UUID] = Query(None), current_user: dict = Depends(get_current_user)):
    if contractor_id is None:
        contractor_id = validate_and_alter_contractor(current_user, current_user.get("cid"))
    
    data: AssistantOutDetail = AssistantService.create(contractor_id, payload)
    return created(data=data)


@router.put("/{id}", response_model=HttpResponse[AssistantOutDetail], dependencies=[Depends(require_permissions(["*", "hafj2q9evc"]))])
def update(id: str, payload: AssistantUpdate, current_user: dict = Depends(get_current_user)):
    assistant: AssistantOutInternal = AssistantService.obter(id)

    # Validating whether the logged-in user can access the contractor's data
    validate_contractor_access(current_user, agente.contractor_id)
    
    data: AssistantOutDetail = AssistantService.update(id, payload)
    return updated(data=data)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafj2v3e45"]))])
def delete(id: str, current_user: dict = Depends(get_current_user)):
    assistant: AssistantOutInternal = AssistantService.obter(id)

    # Validating whether the logged-in user can access the contractor's data
    validate_contractor_access(current_user, agente.contractor_id)

    AssistantService.delete(id)
    return deleted()
