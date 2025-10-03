from typing import List
from bson import ObjectId
from fastapi import HTTPException

from app.dataprovider.models.modelo_ai import collection as modelo_ai_coll
from app.schemas.modelo_ai import (
    ModeloAiCreate, ModeloAiUpdate, ModeloAiOutList, ModeloAiOutDetail
)
from app.core.exceptions.types import NotFoundError


def _ensure_object_id(id_str: str) -> ObjectId:
    if not ObjectId.is_valid(id_str):
        raise HTTPException(status_code=400, detail="ID inválido")
    return ObjectId(id_str)

class ModeloAiService:

    @staticmethod
    async def listar() -> List[ModeloAiOutList]:
        items: list[ModeloAiOutList] = []
        async for doc in modelo_ai_coll.find():
            items.append(ModeloAiOutList.from_mongo(doc))
        return items

    @staticmethod
    async def obter(id: str) -> ModeloAiOutDetail:
        oid = _ensure_object_id(id)
        doc = await modelo_ai_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Modelo não encontrado")

        return ModeloAiOutDetail.from_mongo(doc)

    @staticmethod
    async def criar(payload: ModeloAiCreate) -> ModeloAiOutDetail:
        to_insert = payload.model_dump()
        result = await modelo_ai_coll.insert_one(to_insert)
        created = await modelo_ai_coll.find_one({"_id": result.inserted_id})
        return ModeloAiOutDetail.from_mongo(created)

    @staticmethod
    async def atualizar(id: str, payload: ModeloAiUpdate) -> ModeloAiOutDetail:
        oid = _ensure_object_id(id)
        data = payload.model_dump(exclude_none=True)

        updated = await modelo_ai_coll.find_one_and_update(
            {"_id": oid},
            {"$set": data},
            return_document=True
        )

        if not updated:
            raise NotFoundError("Modelo não encontrado")

        return ModeloAiOutDetail.from_mongo(updated)

    @staticmethod
    async def remover(id: str) -> bool:
        oid = _ensure_object_id(id)
        result = await modelo_ai_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Modelo não encontrado")

        return True
