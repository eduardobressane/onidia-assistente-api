from typing import List
from fastapi import APIRouter, Depends, UploadFile, File

from app.services.credential_type import CredentialTypeService
from app.schemas.credential_type import (
    CredentialTypeCreate, 
    CredentialTypeUpdate, 
    CredentialTypeOutList, 
    CredentialTypeOutDetail
)
from app.core.security import require_permissions
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted

router = APIRouter(prefix="/credentials_types", tags=["Credentials Types"])


@router.get("", response_model=HttpResponse[List[CredentialTypeOutList]], dependencies=[Depends(require_permissions(["*", "hafinjvq6t"]))])
def get_all():
    credentials_types: List[CredentialTypeOutList] = CredentialTypeService.get_all()
    return ok(total=len(credentials_types), data=credentials_types)


@router.get("/{id}", response_model=CredentialTypeOutDetail, dependencies=[Depends(require_permissions(["*", "hafinyo101"]))])
def get_by_id(id: str):
    credential_type: CredentialTypeOutDetail = CredentialTypeService.get_by_id(id)
    return credential_type


@router.post("", response_model=HttpResponse[CredentialTypeOutDetail], dependencies=[Depends(require_permissions(["*", "hafioitpkt"]))])
def create(payload: CredentialTypeCreate):
    data: CredentialTypeOutDetail = CredentialTypeService.create(payload)
    return created(data=data)


@router.put("/{id}", response_model=HttpResponse[CredentialTypeOutDetail], dependencies=[Depends(require_permissions(["*", "hafip1bfnc"]))])
def update(id: str, payload: CredentialTypeUpdate):
    data: CredentialTypeOutDetail = CredentialTypeService.update(id, payload)
    return updated(data=data)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafipau25p"]))])
def delete(id: str):
    CredentialTypeService.delete(id)
    return deleted()


@router.post("/{id}/upload", dependencies=[Depends(require_permissions(["*", "hafioitpkt", "hafip1bfnc"]))])
async def upload_image(id: str, file: UploadFile = File(...)):
    data = CredentialTypeService.upload_image(id, file)
    return created(message="Imagem criada ou atualizada com sucesso!", data=data)


@router.delete("/{id}/upload", dependencies=[Depends(require_permissions(["*", "hafioitpkt", "hafip1bfnc"]))])
async def delete_image(id: str):
    data = CredentialTypeService.delete_image(id)
    return deleted(message="Imagem excluída com sucesso!", data=data)
