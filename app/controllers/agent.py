from fastapi import APIRouter, Depends, Query, UploadFile, File
from typing import List, Optional
from uuid import UUID

from app.services.agent import AgentService
from app.schemas.agent import (
    AgentCreate, AgentUpdate, AgentOutList, AgentOutDetail, AgentOutInternal
)
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted
from app.core.security import require_permissions, get_current_user, validate_and_alter_contractor, validate_contractor_access

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=HttpResponse[List[AgentOutList]], dependencies=[Depends(require_permissions(["*", "hafj03vwv4"]))])
def get_all(
    contractor_id: Optional[UUID] = Query(None), 
    nome: Optional[str] = Query(None), current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Número da página (inicia em 1)"),
    rpp: int = Query(10, ge=1, le=100, description="Registros por página"),
    ):
    contractor_id = validate_and_alter_contractor(current_user, contractor_id)

    agents: List[AgentOutList] = AgentService.get_all(contractor_id, nome, page, rpp)
    return ok(total=agents["total"], pages=agents["pages"], data=agents["items"])


@router.get("/{id}", response_model=AgentOutDetail, dependencies=[Depends(require_permissions(["*", "hafj0kaclm"]))])
def get_by_id(id: str):
    agent: AgentOutInternal = AgentService.get_by_id(id)

    return AgentOutDetail(**agent.dict())


@router.post("", response_model=HttpResponse[AgentOutDetail], dependencies=[Depends(require_permissions(["*", "hafj0qu4kb"]))])
def create(payload: AgentCreate, contractor_id: Optional[UUID] = Query(None), current_user: dict = Depends(get_current_user)):
    contractor_id = validate_and_alter_contractor(current_user, contractor_id)
    
    data: AgentOutDetail = AgentService.create(contractor_id, payload)
    return created(data=data)


@router.put("/{id}", response_model=HttpResponse[AgentOutDetail], dependencies=[Depends(require_permissions(["*", "hafj0vsur6"]))])
def update(id: str, payload: AgentUpdate, current_user: dict = Depends(get_current_user)):
    agent: AgentOutInternal = AgentService.get_by_id(id)

    # Validating whether the logged-in user can access the contractor's data
    validate_contractor_access(current_user, agent.contractor_id)
    
    data: AgentOutDetail = AgentService.update(id, payload)
    return updated(data=data)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafj0zvbsy"]))])
def delete(id: str, current_user: dict = Depends(get_current_user)):
    agent: AgentOutInternal = AgentService.get_by_id(id)

    # Validating whether the logged-in user can access the contractor's data
    validate_contractor_access(current_user, agent.contractor_id)

    AgentService.delete(id)
    return deleted()

@router.post("/{id}/upload", dependencies=[Depends(require_permissions(["*", "hafj0qu4kb", "hafj0vsur6"]))])
async def upload_image(id: str, file: UploadFile = File(...)):
    data = AgentService.upload_image(id, file)
    return created(message="Upload realizado com sucesso!", data=data)


@router.delete("/{id}/upload", dependencies=[Depends(require_permissions(["*", "hafj0zvbsy"]))])
async def delete_image(id: str):
    data = AgentService.delete_image(id)
    return deleted(message="Imagem excluída com sucesso!", data=data)
