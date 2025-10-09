from typing import List
import json
from uuid import UUID
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument

from app.dataprovider.mongo.models.credencial_tool import collection as credencial_tool_coll
from app.schemas.credencial_tool import (
    CredencialToolCreate, CredencialToolUpdate, CredencialToolOut
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.utils.mongo import ensure_object_id
from app.core.cache_decorators import cacheable, cache_evict


class CredencialToolService:

    @staticmethod
    @cacheable("credenciais_tools:all", key_params=["id_tool", "id_contratante"], ttl_seconds=0)
    async def listar(id_tool: str, id_contratante: UUID) -> List[CredencialToolOut]:
        items: list[CredencialToolOut] = []

        async for doc in credencial_tool_coll.find({
            "id_tool": id_tool,
            "id_contratante": str(id_contratante)
        }):
            items.append(CredencialToolOut.from_raw(doc))

        return items

    @staticmethod
    @cacheable("credenciais_tools", key_params=["id"], ttl_seconds=0)
    async def obter(id_tool: str, id: str) -> CredencialToolOut:
        oid = ensure_object_id(id)
        doc = await credencial_tool_coll.find_one({
            "_id": oid,
            "id_tool": id_tool
        })

        if not doc:
            raise NotFoundError("Credencial não encontrada")

        return CredencialToolOut.from_raw(doc)

    @staticmethod
    @cache_evict(["credenciais_tools:all:id_tool={id_tool}:id_contratante={id_contratante}"])
    async def criar(id_tool: str, id_contratante: UUID, payload: CredencialToolCreate) -> CredencialToolOut:
        try:
            to_insert = payload.model_dump()
            to_insert["id_tool"] = id_tool
            to_insert["id_contratante"] = str(id_contratante)

            result = await credencial_tool_coll.insert_one(to_insert)
            created = await credencial_tool_coll.find_one({"_id": result.inserted_id})

            return CredencialToolOut.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma credencial com esta descrição")

    @staticmethod
    @cache_evict(["credenciais_tools:all:id_tool={id_tool}:id_contratante={id_contratante}", "credenciais_tools:id={id}"], key_params=["id"])
    async def atualizar(id_tool: str, id_contratante: UUID, id: str, payload: CredencialToolUpdate) -> CredencialToolOut:
        oid = ensure_object_id(id)
        doc = await credencial_tool_coll.find_one({"_id": oid})

        if (
            not doc
            or doc.get("id_tool") != id_tool
            or str(doc.get("id_contratante")) != str(id_contratante)
        ):
            raise NotFoundError("Credencial não encontrada")

        data = payload.model_dump(exclude_none=True)

        updated = await credencial_tool_coll.find_one_and_update(
            {"_id": oid},
            {"$set": data},
            return_document=ReturnDocument.AFTER
        )

        return ToolOutDetail.from_raw(updated)

    @staticmethod
    @cache_evict(["credenciais_tools:all:id_tool={id_tool}:id_contratante={id_contratante}", "credenciais_tools:id={id}"], key_params=["id"])
    async def remover(id_tool: str, id_contratante: UUID, id: str) -> bool:
        oid = ensure_object_id(id)
        doc = await credencial_tool_coll.find_one({"_id": oid})

        if (
            not doc
            or doc.get("id_tool") != id_tool
            or str(doc.get("id_contratante")) != str(id_contratante)
        ):
            raise NotFoundError("Credencial não encontrada")

        result = await credencial_tool_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Credencial não encontrada")
            
        return True
