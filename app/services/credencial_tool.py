from typing import List
import json
from uuid import UUID
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument

from app.dataprovider.mongo.models.credencial_tool import collection as credencial_tool_coll
from app.schemas.credencial_tool import (
    CredencialToolCreate, CredencialToolUpdate, CredencialToolOutList, CredencialToolOutDetail, CredencialToolInterna
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.utils.mongo import ensure_object_id


class CredencialToolService:

    @staticmethod
    async def listar(id_tool: str, id_contratante: UUID) -> List[CredencialToolOutList]:
        items: list[CredencialToolOutList] = []

        async for doc in credencial_tool_coll.find({
            "id_tool": id_tool,
            "id_contratante": str(id_contratante)
        }):
            items.append(CredencialToolOutList.from_raw(doc))

        return items

    @staticmethod
    async def obter(id: str) -> CredencialToolInterna:
        oid = ensure_object_id(id)
        doc = await credencial_tool_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Credencial não encontrada")

        return CredencialToolInterna.from_raw(doc)

    @staticmethod
    async def criar(id_tool: str, id_contratante: UUID, payload: CredencialToolCreate) -> CredencialToolOutDetail:
        try:
            to_insert = payload.model_dump()
            to_insert["id_tool"] = id_tool
            to_insert["id_contratante"] = str(id_contratante)

            result = await credencial_tool_coll.insert_one(to_insert)
            created = await credencial_tool_coll.find_one({"_id": result.inserted_id})

            return CredencialToolOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma credencial com esta descrição")

    @staticmethod
    async def atualizar(id: str, payload: CredencialToolUpdate) -> CredencialToolOutDetail:
        oid = ensure_object_id(id)
        doc = await credencial_tool_coll.find_one({"_id": oid})

        if (not doc):
            raise NotFoundError("Credencial não encontrada")

        data = payload.model_dump(exclude_none=True)

        updated = await credencial_tool_coll.find_one_and_update(
            {"_id": oid},
            {"$set": data},
            return_document=ReturnDocument.AFTER
        )

        return CredencialToolOutDetail.from_raw(updated)

    @staticmethod
    async def remover(id: str) -> bool:
        oid = ensure_object_id(id)
        doc = await credencial_tool_coll.find_one({"_id": oid})

        if (not doc):
            raise NotFoundError("Credencial não encontrada")

        result = await credencial_tool_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Credencial não encontrada")
            
        return True
