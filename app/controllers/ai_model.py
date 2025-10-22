from typing import List
from fastapi import APIRouter, Depends, UploadFile, File

from app.services.ai_model import AiModelService
from app.schemas.ai_model import (
    AiModelCreate, 
    AiModelUpdate, 
    AiModelOutList, 
    AiModelOutDetail
)
from app.core.security import require_permissions
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted

router = APIRouter(prefix="/ai_models", tags=["AI Models"])


@router.get("", response_model=HttpResponse[List[AiModelOutList]], dependencies=[Depends(require_permissions(["*", "hafinjvq6t"]))])
def get_all():
    modelos: List[AiModelOutList] = AiModelService.get_all()
    return ok(total=len(modelos), data=modelos)


@router.get("/{id}", response_model=AiModelOutDetail, dependencies=[Depends(require_permissions(["*", "hafinyo101"]))])
def get_by_id(id: str):
    modelo: AiModelOutDetail = AiModelService.get_by_id(id)
    return modelo


@router.post("", response_model=HttpResponse[AiModelOutDetail], dependencies=[Depends(require_permissions(["*", "hafioitpkt"]))])
def create(payload: AiModelCreate):
    data: AiModelOutDetail = AiModelService.create(payload)
    return created(data=data)


@router.put("/{id}", response_model=HttpResponse[AiModelOutDetail], dependencies=[Depends(require_permissions(["*", "hafip1bfnc"]))])
def update(id: str, payload: AiModelUpdate):
    data: AiModelOutDetail = AiModelService.update(id, payload)
    return updated(data=data)


@router.delete("/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafipau25p"]))])
def delete(id: str):
    AiModelService.delete(id)
    return deleted()


@router.post("/{id}/upload", dependencies=[Depends(require_permissions(["*", "hafioitpkt", "hafip1bfnc"]))])
async def upload_image(id: str, file: UploadFile = File(...)):
    data = AiModelService.upload_image(id, file)
    return created(message="Imagem criada ou atualizada com sucesso!", data=data)


@router.delete("/{id}/upload", dependencies=[Depends(require_permissions(["*", "hafioitpkt", "hafip1bfnc"]))])
async def delete_image(id: str):
    data = AiModelService.delete_image(id)
    return deleted(message="Imagem excluída com sucesso!", data=data)
