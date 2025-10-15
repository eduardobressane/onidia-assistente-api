from typing import List
from bson import ObjectId
from fastapi import HTTPException
import json

from app.dataprovider.mongo.models.tool import collection as tool_coll
from app.dataprovider.mongo.models.credencial_tool import collection as credencial_tool_coll
from app.dataprovider.mongo.models.agente import collection as agente_coll
from app.schemas.tool import (
    ToolCreate, ToolUpdate, ToolOutList, ToolOutDetail
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError
from app.core.utils.mongo import ensure_object_id
from app.core.cache_decorators import cacheable, cache_evict
from pymongo.errors import DuplicateKeyError


class ToolService:

    @staticmethod
    @cacheable("tools:all", ttl_seconds=0)
    def listar() -> List[ToolOutList]:
        items: list[ToolOutList] = []
        for doc in tool_coll.find():
            items.append(ToolOutList.from_raw(doc))
        return items

    @staticmethod
    @cacheable("tools", key_params=["id"], ttl_seconds=0)
    def obter(id: str) -> ToolOutDetail:
        oid = ensure_object_id(id)
        doc = tool_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Tool não encontrada")

        return ToolOutDetail.from_raw(doc)

    @staticmethod
    @cache_evict(["tools:all"])
    def criar(payload: ToolCreate) -> ToolOutDetail:
        try:
            to_insert = payload.model_dump()
            result = tool_coll.insert_one(to_insert)
            created = tool_coll.find_one({"_id": result.inserted_id})
            return ToolOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma tool com este nome")

    @staticmethod
    @cache_evict(["tools:all", "tools:id={id}"], key_params=["id"])
    def atualizar(id: str, payload: ToolUpdate) -> ToolOutDetail:
        oid = ensure_object_id(id)
        data = payload.model_dump(exclude_none=True)

        try:
            updated = tool_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=True
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma tool com este nome")

        if not updated:
            raise NotFoundError("Tool não encontrada")

        return ToolOutDetail.from_raw(updated)

    @staticmethod
    @cache_evict(["tools:all", "tools:id={id}"], key_params=["id"])
    def remover(id: str) -> bool:
        # Verifica se existem credenciais cadatradas para esta tool
        credencial_existente = credencial_tool_coll.find_one({"id_tool": id})
        if credencial_existente:
            raise BusinessDomainError("Existem credenciais cadastradas para esta tool. Exclua-as primeiro.")

        # Verifica se existem agentes com esta tool vinculada
        credencial_vinculada = agente_coll.find_one({"tools.tool.id": id})
        if credencial_vinculada:
            raise BusinessDomainError("Existe um ou mais agente utilizando esta credencial")

        oid = ensure_object_id(id)
        result = tool_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Tool não encontrada")

        return True
