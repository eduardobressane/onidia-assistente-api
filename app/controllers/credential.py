from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from app.services.credential import CredentialService
from app.schemas.credential import (
    CredentialCreate, CredentialUpdate, CredentialOutList, CredentialOutDetail, CredentialOutInternal
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.security import require_permissions, get_current_user, validate_and_alter_contractor, validate_contractor_access
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted
from fastapi.encoders import jsonable_encoder

router = APIRouter(prefix="/credentials_types", tags=["Credentials"])


@router.get("/{credential_type_id}/credentials", response_model=HttpResponse[List[CredentialOutList]], dependencies=[Depends(require_permissions(["*", "hafiu7as5j"]))])
def get_all(credential_type_id: str, contractor_id: Optional[UUID] = Query(None), current_user: dict = Depends(get_current_user)):
    contractor_id = validate_and_alter_contractor(current_user, contractor_id)

    rows: List[CredentialOutList] = CredentialService.get_all(credential_type_id, contractor_id)
    payload = [CredentialOutList.from_raw(r) for r in rows]
    return ok(total=len(rows), data=jsonable_encoder(payload))


@router.get("/{credential_type_id}/credentials/{id}", response_model=CredentialOutDetail, dependencies=[Depends(require_permissions(["*", "hafiujfqz0"]))])
def get_by_id(credential_type_id: str, id: str, current_user: dict = Depends(get_current_user)):
    credencial: CredentialOutInternal = CredentialService.get_by_id(id)

    # Validating whether the logged-in user can access the contractor's data
    validate_contractor_access(current_user, credencial.contractor_id)

    if credencial is not None and credencial.credential_type_id != credential_type_id:
        raise NotFoundError("Credencial não encontrada")

    return CredentialOutDetail(**credencial.dict())


@router.post("/{credential_type_id}/credentials", response_model=HttpResponse[CredentialOutDetail], dependencies=[Depends(require_permissions(["*", "hafiuwl24h"]))])
def create(
    credential_type_id: str,
    payload: CredentialCreate,
    contractor_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    contractor_id = validate_and_alter_contractor(current_user, contractor_id)

    data: CredentialOutDetail = CredentialService.create(
        credential_type_id, contractor_id, payload
    )
    return created(data=data)


@router.put("/{credential_type_id}/credentials/{id}", response_model=HttpResponse[CredentialOutDetail], dependencies=[Depends(require_permissions(["*", "hafiv73qtg"]))])
def update(credential_type_id: str, id: str, payload: CredentialUpdate, current_user: dict = Depends(get_current_user)):
    credencial: CredentialInternal = CredentialService.get_by_id(id)

    # Validating whether the logged-in user can access the contractor's data
    validate_contractor_access(current_user, credencial.contractor_id)

    if credencial is not None and credencial.credential_type_id != credential_type_id:
        raise NotFoundError("Credencial não encontrada")

    data: CredentialOutDetail = CredentialService.update(id, payload)
    return updated(data=data)


@router.delete("/{credential_type_id}/credentials/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafivn408n"]))])
def delete(credential_type_id: str, id: str, current_user: dict = Depends(get_current_user)):
    credencial: CredentialInternal = CredentialService.get_by_id(id)

    # Validating whether the logged-in user can access the contractor's data
    validate_contractor_access(current_user, credencial.contractor_id)

    if credencial is not None and credencial.credential_type_id != credential_type_id:
        raise NotFoundError("Credencial não encontrada")

    CredentialService.remover(id)
    return deleted()
