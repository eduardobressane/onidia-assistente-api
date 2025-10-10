from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from app.services.credencial_modelo_ai import CredencialModeloAiService
from app.schemas.credencial_modelo_ai import (
    CredencialModeloAiCreate, CredencialModeloAiUpdate, CredencialModeloAiOutList, CredencialModeloAiOutDetail, CredencialModeloAiInterna
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.security import require_permissions, get_current_user, validate_contratante_access
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted
from fastapi.encoders import jsonable_encoder

router = APIRouter(prefix="/modelos_ai", tags=["Modelos de AI"])


@router.get("/{id_modelo_ai}/credenciais", response_model=HttpResponse[List[CredencialModeloAiOutList]], dependencies=[Depends(require_permissions(["*", "hafiy9ighm"]))])
async def listar(id_modelo_ai: str, id_contratante: Optional[UUID] = Query(None), current_user: dict = Depends(get_current_user)):
    # Se id_contratante não for informado, usar o cid do usuário atual
    if id_contratante is None:
        id_contratante = current_user.get("cid")
    else:
        validate_contratante_access(current_user, id_contratante)

    rows: List[CredencialModeloAiOutList] = await CredencialModeloAiService.listar(id_modelo_ai, id_contratante)
    payload = [CredencialModeloAiOutList.from_raw(r) for r in rows]
    return ok(total=len(rows), data=jsonable_encoder(payload))


@router.get("/{id_modelo_ai}/credenciais/{id}", response_model=CredencialModeloAiOutDetail, dependencies=[Depends(require_permissions(["*", "hafiyegwye"]))])
async def obter(id_modelo_ai: str, id: str, current_user: dict = Depends(get_current_user)):
    credencial: CredencialModeloAiInterna = await CredencialModeloAiService.obter(id)

    # Validando se usuário logado pode acessar o dado da contratante
    validate_contratante_access(current_user, credencial.id_contratante)

    if credencial is not None and credencial.id_modelo_ai != id_modelo_ai:
        raise NotFoundError("Credencial não encontrada")

    return CredencialModeloAiOutDetail(**credencial.dict())


@router.post("/{id_modelo_ai}/credenciais", response_model=HttpResponse[CredencialModeloAiOutDetail], dependencies=[Depends(require_permissions(["*", "hafiyjo1ee"]))])
async def criar(
    id_modelo_ai: str,
    payload: CredencialModeloAiCreate,
    id_contratante: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    # Se id_contratante não for informado, usar o cid do usuário atual
    if id_contratante is None:
        id_contratante = current_user.get("cid")
    else:
        validate_contratante_access(current_user, id_contratante)

    novo: CredencialModeloAiOutDetail = await CredencialModeloAiService.criar(
        id_modelo_ai, id_contratante, payload
    )
    return created(data=novo)


@router.put("/{id_modelo_ai}/credenciais/{id}", response_model=HttpResponse[CredencialModeloAiOutDetail], dependencies=[Depends(require_permissions(["*", "hafiyoxwru"]))])
async def atualizar(id_modelo_ai: str, id: str, payload: CredencialModeloAiUpdate, current_user: dict = Depends(get_current_user)):
    credencial: CredencialModeloAiInterna = await CredencialModeloAiService.obter(id)

    # Validando se usuário logado pode acessar o dado da contratante
    validate_contratante_access(current_user, credencial.id_contratante)

    if credencial is not None and credencial.id_modelo_ai != id_modelo_ai:
        raise NotFoundError("Credencial não encontrada")

    atualizado: CredencialModeloAiOutDetail = await CredencialModeloAiService.atualizar(id, payload)
    return updated(data=atualizado)


@router.delete("/{id_modelo_ai}/credenciais/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafiyuf3du"]))])
async def remover(id_modelo_ai: str, id: str, current_user: dict = Depends(get_current_user)):
    credencial: CredencialModeloAiInterna = await CredencialModeloAiService.obter(id)

    # Validando se usuário logado pode acessar o dado da contratante
    validate_contratante_access(current_user, credencial.id_contratante)

    if credencial is not None and credencial.id_modelo_ai != id_modelo_ai:
        raise NotFoundError("Credencial não encontrada")

    await CredencialModeloAiService.remover(id)
    return deleted()
