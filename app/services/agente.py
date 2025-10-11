from typing import List
from bson import ObjectId
from fastapi import HTTPException
import json

from app.dataprovider.mongo.models.agente import collection as agente_coll
from app.dataprovider.mongo.models.agente import get_agente_detail
from app.schemas.agente import (
    AgenteCreate, AgenteUpdate, AgenteOutList, AgenteOutDetail
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError
from app.core.utils.mongo import ensure_object_id
from app.core.cache_decorators import cacheable, cache_evict
from pymongo.errors import DuplicateKeyError


class AgenteService:

    @staticmethod
    #@cacheable("agentes:all", ttl_seconds=0)
    def listar() -> List[AgenteOutList]:
        items: list[AgenteOutList] = []
        for doc in agente_coll.find():
            items.append(AgenteOutList.from_raw(doc))
        return items

    @staticmethod
    #@cacheable("tools", key_params=["id"], ttl_seconds=0)
    def obter(id: str) -> AgenteOutDetail:
        doc = get_agente_detail(id)

        if not doc:
            raise NotFoundError("Agente não encontrado")

        return AgenteOutDetail.from_raw(doc)

    @staticmethod
    #@cache_evict(["tools:all"])
    def criar(payload: AgenteCreate) -> AgenteOutDetail:
        try:
            to_insert = payload.model_dump()
            result = agente_coll.insert_one(to_insert)
            created = agente_coll.find_one({"_id": result.inserted_id})
            return AgenteOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um agente com este nome")

    @staticmethod
    #@cache_evict(["tools:all", "tools:id={id}"], key_params=["id"])
    def atualizar(id: str, payload: AgenteUpdate) -> AgenteOutDetail:
        oid = ensure_object_id(id)
        data = payload.model_dump(exclude_none=True)

        try:
            updated = tool_cagente_colloll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=True
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um agente com este nome")

        if not updated:
            raise NotFoundError("Agente não encontrado")

        return AgenteOutDetail.from_raw(updated)

    @staticmethod
    #@cache_evict(["tools:all", "tools:id={id}"], key_params=["id"])
    def remover(id: str) -> bool:
        oid = ensure_object_id(id)
        result = agente_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Agente não encontrado")

        return True
