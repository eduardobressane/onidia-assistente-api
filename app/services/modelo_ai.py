from typing import List
from bson import ObjectId
from fastapi import HTTPException
import json

from app.dataprovider.mongo.models.modelo_ai import collection as modelo_ai_coll
from app.schemas.modelo_ai import (
    ModeloAiCreate, ModeloAiUpdate,
    ModeloAiOutList, ModeloAiOutDetail
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.cache import (
    cache_get_json, cache_set_json,
    cache_delete
)
from app.core.utils.mongo import ensure_object_id
from pymongo.errors import DuplicateKeyError

class ModeloAiService:

    @staticmethod
    async def listar() -> List[ModeloAiOutList]:
        cache_key = "modelos_ai:all"

        cached = cache_get_json(cache_key)
        if cached:
            data = json.loads(cached)
            return [ModeloAiOutList(**item) for item in data]

        items: list[ModeloAiOutList] = []
        async for doc in modelo_ai_coll.find():
            items.append(ModeloAiOutList.from_mongo(doc))

        cache_set_json(cache_key, json.dumps([i.model_dump() for i in items]))
        return items

    @staticmethod
    async def obter(id: str) -> ModeloAiOutDetail:
        cache_key = f"modelos_ai:{id}"

        cached = cache_get_json(cache_key, ModeloAiOutDetail)
        if cached:
            return cached

        oid = ensure_object_id(id)
        doc = await modelo_ai_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Modelo não encontrado")

        modelo = ModeloAiOutDetail.from_mongo(doc)
        cache_set_json(cache_key, modelo.model_dump())
        return modelo

    @staticmethod
    async def criar(payload: ModeloAiCreate) -> ModeloAiOutDetail:
        try:
            to_insert = payload.model_dump()
            result = await modelo_ai_coll.insert_one(to_insert)
            created = await modelo_ai_coll.find_one({"_id": result.inserted_id})

            modelo = ModeloAiOutDetail.from_mongo(created)

            cache_delete("modelos_ai:all")
            return modelo
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um modelo com este nome")

    @staticmethod
    async def atualizar(id: str, payload: ModeloAiUpdate) -> ModeloAiOutDetail:
        oid = ensure_object_id(id)
        data = payload.model_dump(exclude_none=True)

        updated = await modelo_ai_coll.find_one_and_update(
            {"_id": oid},
            {"$set": data},
            return_document=True
        )

        if not updated:
            raise NotFoundError("Modelo não encontrado")

        modelo = ModeloAiOutDetail.from_mongo(updated)

        cache_delete("modelos_ai:all")
        cache_delete(f"modelos_ai:{id}")
        return modelo

    @staticmethod
    async def remover(id: str) -> bool:
        oid = ensure_object_id(id)
        result = await modelo_ai_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Modelo não encontrado")

        cache_delete("modelos_ai:all")
        cache_delete(f"modelos_ai:{id}")
        return True
