from typing import List
from bson import ObjectId
from fastapi import HTTPException
import json

from app.dataprovider.mongo.models.tool import collection as tool_coll
from app.schemas.tool import (
    ToolCreate, ToolUpdate, ToolOutList, ToolOutDetail
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.utils.mongo import ensure_object_id
from app.core.cache_decorators import cacheable, cache_evict
from pymongo.errors import DuplicateKeyError


class ToolService:

    @staticmethod
    @cacheable("tools:all", ttl_seconds=0)
    async def listar() -> List[ToolOutList]:
        items: list[ToolOutList] = []
        async for doc in tool_coll.find():
            items.append(ToolOutList.from_raw(doc))
        return items

    @staticmethod
    @cacheable("tools", key_params=["id"], ttl_seconds=0)
    async def obter(id: str) -> ToolOutDetail:
        oid = ensure_object_id(id)
        doc = await tool_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Tool não encontrada")

        return ToolOutDetail.from_raw(doc)

    @staticmethod
    @cache_evict(["tools:all"])
    async def criar(payload: ToolCreate) -> ToolOutDetail:
        try:
            to_insert = payload.model_dump()
            result = await tool_coll.insert_one(to_insert)
            created = await tool_coll.find_one({"_id": result.inserted_id})
            return ToolOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma tool com este nome")

    @staticmethod
    @cache_evict(["tools:all", "tools:id={id}"], key_params=["id"])
    async def atualizar(id: str, payload: ToolUpdate) -> ToolOutDetail:
        oid = ensure_object_id(id)
        data = payload.model_dump(exclude_none=True)

        updated = await tool_coll.find_one_and_update(
            {"_id": oid},
            {"$set": data},
            return_document=True
        )

        if not updated:
            raise NotFoundError("Tool não encontrada")

        return ToolOutDetail.from_raw(updated)

    @staticmethod
    @cache_evict(["tools:all", "tools:id={id}"], key_params=["id"])
    async def remover(id: str) -> bool:
        oid = ensure_object_id(id)
        result = await tool_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Tool não encontrada")

        return True
