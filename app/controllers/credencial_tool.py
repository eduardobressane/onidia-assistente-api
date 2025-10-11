from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from app.services.credencial_tool import CredencialToolService
from app.schemas.credencial_tool import (
    CredencialToolCreate, CredencialToolUpdate, CredencialToolOutList, CredencialToolOutDetail, CredencialToolInterna
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.security import require_permissions, get_current_user, validate_contratante_access
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, created, updated, deleted
from fastapi.encoders import jsonable_encoder

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("/{id_tool}/credenciais", response_model=HttpResponse[List[CredencialToolOutList]], dependencies=[Depends(require_permissions(["*", "hafiy9ighm"]))])
def listar(id_tool: str, id_contratante: Optional[UUID] = Query(None), current_user: dict = Depends(get_current_user)):
    # Se id_contratante não for informado, usar o cid do usuário atual
    if id_contratante is None:
        id_contratante = current_user.get("cid")
    else:
        validate_contratante_access(current_user, id_contratante)

    rows: List[CredencialToolOutList] = CredencialToolService.listar(id_tool, id_contratante)
    payload = [CredencialToolOutList.from_raw(r) for r in rows]
    return ok(total=len(rows), data=jsonable_encoder(payload))


@router.get("/{id_tool}/credenciais/{id}", response_model=CredencialToolOutDetail, dependencies=[Depends(require_permissions(["*", "hafiyegwye"]))])
def obter(id_tool: str, id: str, current_user: dict = Depends(get_current_user)):
    credencial: CredencialToolInterna = CredencialToolService.obter(id)

    # Validando se usuário logado pode acessar o dado da contratante
    validate_contratante_access(current_user, credencial.id_contratante)

    if credencial is not None and credencial.id_tool != id_tool:
        raise NotFoundError("Credencial não encontrada")

    return CredencialToolOutDetail(**credencial.dict())


@router.post("/{id_tool}/credenciais", response_model=HttpResponse[CredencialToolOutDetail], dependencies=[Depends(require_permissions(["*", "hafiyjo1ee"]))])
def criar(
    id_tool: str,
    payload: CredencialToolCreate,
    id_contratante: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    # Se id_contratante não for informado, usar o cid do usuário atual
    if id_contratante is None:
        id_contratante = current_user.get("cid")
    else:
        validate_contratante_access(current_user, id_contratante)

    novo: CredencialToolOutDetail = CredencialToolService.criar(
        id_tool, id_contratante, payload
    )
    return created(data=novo)


@router.put("/{id_tool}/credenciais/{id}", response_model=HttpResponse[CredencialToolOutDetail], dependencies=[Depends(require_permissions(["*", "hafiyoxwru"]))])
def atualizar(id_tool: str, id: str, payload: CredencialToolUpdate, current_user: dict = Depends(get_current_user)):
    credencial: CredencialToolInterna = CredencialToolService.obter(id)

    # Validando se usuário logado pode acessar o dado da contratante
    validate_contratante_access(current_user, credencial.id_contratante)

    if credencial is not None and credencial.id_tool != id_tool:
        raise NotFoundError("Credencial não encontrada")

    atualizado: CredencialToolOutDetail = CredencialToolService.atualizar(id, payload)
    return updated(data=atualizado)


@router.delete("/{id_tool}/credenciais/{id}", response_model=HttpResponse[None], dependencies=[Depends(require_permissions(["*", "hafiyuf3du"]))])
def remover(id_tool: str, id: str, current_user: dict = Depends(get_current_user)):
    credencial: CredencialToolInterna = CredencialToolService.obter(id)

    # Validando se usuário logado pode acessar o dado da contratante
    validate_contratante_access(current_user, credencial.id_contratante)

    if credencial is not None and credencial.id_tool != id_tool:
        raise NotFoundError("Credencial não encontrada")

    CredencialToolService.remover(id)
    return deleted()
