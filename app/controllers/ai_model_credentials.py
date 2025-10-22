from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from app.services.ai_model_credentials import AiModelCredentialsService
from app.schemas.ai_model_credentials import (
    AiModelCredentialsCreate, AiModelCredentialsUpdate, AiModelCredentialsOutList, AiModelCredentialsOutDetail, AiModelCredentialsOutInternal
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.security import require_permissions, get_current_user, validate_and_alter_contractor
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted
from fastapi.encoders import jsonable_encoder

router = APIRouter(prefix="/ai_models", tags=["AI Models Credentials"])


@router.get("/{ai_model_id}/credentials", response_model=HttpResponse[List[AiModelCredentialsOutList]], dependencies=[Depends(require_permissions(["*", "hafiu7as5j"]))])
def get_all(ai_model_id: str, contractor_id: Optional[UUID] = Query(None), current_user: dict = Depends(get_current_user)):
    if contractor_id is None:
        contractor_id = validate_and_alter_contractor(current_user, current_user.get("cid"))

    rows: List[AiModelCredentialsOutList] = AiModelCredentialsService.get_all(ai_model_id, contractor_id)
    payload = [AiModelCredentialsOutList.from_raw(r) for r in rows]
    return ok(total=len(rows), data=jsonable_encoder(payload))


@router.get("/{ai_model_id}/credentials/{id}", response_model=AiModelCredentialsOutDetail, dependencies=[Depends(require_permissions(["*", "hafiujfqz0"]))])
def get_by_id(ai_model_id: str, id: str, current_user: dict = Depends(get_current_user)):
    credencial: AiModelCredentialsInternal = AiModelCredentialsService.get_by_id(id)

    # Validating whether the logged-in user can access the contractor's data
    validate_contractor_access(current_user, credencial.contractor_id)

    if credencial is not None and credencial.ai_model_id != ai_model_id:
        raise NotFoundError("Credencial não encontrada")

    return AiModelCredentialsOutDetail(**credencial.dict())


@router.post("/{ai_model_id}/credentials", response_model=HttpResponse[AiModelCredentialsOutDetail], dependencies=[Depends(require_permissions(["*", "hafiuwl24h"]))])
def create(
    ai_model_id: str,
    payload: AiModelCredentialsCreate,
    contractor_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    if contractor_id is None:
        contractor_id = validate_and_alter_contractor(current_user, current_user.get("cid"))

    data: AiModelCredentialsOutDetail = AiModelCredentialsService.create(
        ai_model_id, contractor_id, payload
    )
    return created(data=data)


@router.put("/{ai_model_id}/credentials/{id}", response_model=HttpResponse[AiModelCredentialsOutDetail], dependencies=[Depends(require_permissions(["*", "hafiv73qtg"]))])
def update(ai_model_id: str, id: str, payload: AiModelCredentialsUpdate, current_user: dict = Depends(get_current_user)):
    credencial: AiModelCredentialsInternal = AiModelCredentialsService.get_by_id(id)

    # Validating whether the logged-in user can access the contractor's data
    validate_contractor_access(current_user, credencial.contractor_id)

    if credencial is not None and credencial.ai_model_id != ai_model_id:
        raise NotFoundError("Credencial não encontrada")

    data: AiModelCredentialsOutDetail = AiModelCredentialsService.update(id, payload)
    return updated(data=data)


@router.delete("/{ai_model_id}/credentials/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafivn408n"]))])
def delete(ai_model_id: str, id: str, current_user: dict = Depends(get_current_user)):
    credencial: AiModelCredentialsInternal = AiModelCredentialsService.get_by_id(id)

    # Validating whether the logged-in user can access the contractor's data
    validate_contractor_access(current_user, credencial.contractor_id)

    if credencial is not None and credencial.ai_model_id != ai_model_id:
        raise NotFoundError("Credencial não encontrada")

    AiModelCredentialsService.remover(id)
    return deleted()
