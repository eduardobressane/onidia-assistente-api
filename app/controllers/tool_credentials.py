from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from app.services.tool_credentials import ToolCredentialsService
from app.schemas.tool_credentials import (
    ToolCredentialsCreate, ToolCredentialsUpdate, ToolCredentialsOutList, ToolCredentialsOutDetail, ToolCredentialsInternal
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.security import require_permissions, get_current_user, validate_and_alter_contractor
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted
from fastapi.encoders import jsonable_encoder

router = APIRouter(prefix="/tools", tags=["Tools Credentials"])


@router.get("/{tool_id}/credentials", response_model=HttpResponse[List[ToolCredentialsOutList]], dependencies=[Depends(require_permissions(["*", "hafiy9ighm"]))])
def get_all(tool_id: str, contractor_id: Optional[UUID] = Query(None), current_user: dict = Depends(get_current_user)):
    if contractor_id is None:
        contractor_id = validate_and_alter_contractor(current_user, current_user.get("cid"))

    rows: List[ToolCredentialsOutList] = ToolCredentialsService.get_all(tool_id, contractor_id)
    payload = [ToolCredentialsOutList.from_raw(r) for r in rows]
    return ok(total=len(rows), data=jsonable_encoder(payload))


@router.get("/{tool_id}/credentials/{id}", response_model=ToolCredentialsOutDetail, dependencies=[Depends(require_permissions(["*", "hafiyegwye"]))])
def get_by_id(tool_id: str, id: str, current_user: dict = Depends(get_current_user)):
    credencial: ToolCredentialsInternal = ToolCredentialsService.get_by_id(id)

    # Validating whether the logged-in user can access the contractor's data
    validate_contractor_access(current_user, credencial.contractor_id)

    if credencial is not None and credencial.tool_id != tool_id:
        raise NotFoundError("Credencial não encontrada")

    return ToolCredentialsOutDetail(**credencial.dict())


@router.post("/{tool_id}/credentials", response_model=HttpResponse[ToolCredentialsOutDetail], dependencies=[Depends(require_permissions(["*", "hafiyjo1ee"]))])
def create(
    tool_id: str,
    payload: ToolCredentialsCreate,
    contractor_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    if contractor_id is None:
        contractor_id = validate_and_alter_contractor(current_user, current_user.get("cid"))

    data: ToolCredentialsOutDetail = ToolCredentialsService.create(
        tool_id, contractor_id, payload
    )
    return created(data=data)


@router.put("/{tool_id}/credentials/{id}", response_model=HttpResponse[ToolCredentialsOutDetail], dependencies=[Depends(require_permissions(["*", "hafiyoxwru"]))])
def update(tool_id: str, id: str, payload: ToolCredentialsUpdate, current_user: dict = Depends(get_current_user)):
    credencial: ToolCredentialsInternal = ToolCredentialsService.obter(id)

    # Validating whether the logged-in user can access the contractor's data
    validate_contractor_access(current_user, credencial.contractor_id)

    if credencial is not None and credencial.tool_id != tool_id:
        raise NotFoundError("Credencial não encontrada")

    data: ToolCredentialsOutDetail = ToolCredentialsService.update(id, payload)
    return updated(data=data)


@router.delete("/{tool_id}/credentials/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafiyuf3du"]))])
def delete(tool_id: str, id: str, current_user: dict = Depends(get_current_user)):
    credencial: ToolCredentialsInternal = ToolCredentialsService.obter(id)

    # Validating whether the logged-in user can access the contractor's data
    validate_contractor_access(current_user, credencial.contractor_id)

    if credencial is not None and credencial.tool_id != tool_id:
        raise NotFoundError("Credencial não encontrada")

    ToolCredentialsService.delete(id)
    return deleted()
