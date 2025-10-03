from typing import List
from bson import ObjectId
from fastapi import HTTPException

from app.dataprovider.models.tool import collection as tool_coll
from app.schemas.tool import (
    ToolCreate, ToolUpdate, ToolOutList, ToolOutDetail
)
from app.core.exceptions.types import NotFoundError


def _ensure_object_id(id_str: str) -> ObjectId:
    if not ObjectId.is_valid(id_str):
        raise HTTPException(status_code=400, detail="ID inválido")
    return ObjectId(id_str)

class ToolService:

    @staticmethod
    async def listar() -> List[ToolOutList]:
        items: list[ToolOutList] = []
        async for doc in tool_coll.find():
            items.append(ToolOutList.from_mongo(doc))
        return items

    @staticmethod
    async def obter(id: str) -> ToolOutDetail:
        oid = _ensure_object_id(id)
        doc = await tool_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Tool não encontrada")

        return ToolOutDetail.from_mongo(doc)

    @staticmethod
    async def criar(payload: ToolCreate) -> ToolOutDetail:
        to_insert = payload.model_dump()
        result = await tool_coll.insert_one(to_insert)
        created = await tool_coll.find_one({"_id": result.inserted_id})
        return ToolOutDetail.from_mongo(created)

    @staticmethod
    async def atualizar(id: str, payload: ToolUpdate) -> ToolOutDetail:
        oid = _ensure_object_id(id)
        data = payload.model_dump(exclude_none=True)

        updated = await tool_coll.find_one_and_update(
            {"_id": oid},
            {"$set": data},
            return_document=True
        )

        if not updated:
            raise NotFoundError("Tool não encontrada")

        return ToolOutDetail.from_mongo(updated)

    @staticmethod
    async def remover(id: str) -> bool:
        oid = _ensure_object_id(id)
        result = await tool_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Tool não encontrada")

        return True
