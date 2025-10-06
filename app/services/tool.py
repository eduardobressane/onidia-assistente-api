from typing import List
from bson import ObjectId
from fastapi import HTTPException
import json

from app.dataprovider.mongo.models.tool import collection as tool_coll
from app.schemas.tool import (
    ToolCreate, ToolUpdate, ToolOutList, ToolOutDetail
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.cache import (
    cache_get_json, cache_set_json,
    cache_delete
)
from app.core.utils.mongo import ensure_object_id
from pymongo.errors import DuplicateKeyError

class ToolService:

    @staticmethod
    async def listar() -> List[ToolOutList]:
        cache_key = "tools:all"

        cached = cache_get_json(cache_key)
        if cached:
            data = json.loads(cached)
            return [ToolOutList(**item) for item in data]

        items: list[ToolOutList] = []
        async for doc in tool_coll.find():
            items.append(ToolOutList.from_mongo(doc))

        cache_set_json(cache_key, json.dumps([i.model_dump() for i in items]))
        return items

    @staticmethod
    async def obter(id: str) -> ToolOutDetail:
        cache_key = f"tools:{id}"

        cached = cache_get_json(cache_key, ToolOutDetail)
        if cached:
            return cached

        oid = ensure_object_id(id)
        doc = await tool_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Tool não encontrada")

        tool = ToolOutDetail.from_mongo(doc)
        cache_set_json(cache_key, tool.model_dump())
        return tool

    @staticmethod
    async def criar(payload: ToolCreate) -> ToolOutDetail:
        try:
            to_insert = payload.model_dump()
            result = await tool_coll.insert_one(to_insert)
            created = await tool_coll.find_one({"_id": result.inserted_id})

            tool = ToolOutDetail.from_mongo(created)

            cache_delete("tools:all")
            return tool
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma tool com este nome")

    @staticmethod
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

        tool = ToolOutDetail.from_mongo(updated)

        cache_delete("tools:all")
        cache_delete(f"tools:{id}")
        return tool

    @staticmethod
    async def remover(id: str) -> bool:
        oid = ensure_object_id(id)
        result = await tool_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Tool não encontrada")

        cache_delete("tools:all")
        cache_delete(f"tools:{id}")
        return True
