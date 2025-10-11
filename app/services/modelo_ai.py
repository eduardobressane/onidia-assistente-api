from typing import List
from bson import ObjectId
from fastapi import HTTPException

from app.dataprovider.mongo.models.modelo_ai import collection as modelo_ai_coll
from app.dataprovider.mongo.models.credencial_modelo_ai import collection as credencial_modelo_ai_coll
from app.schemas.modelo_ai import (
    ModeloAiCreate, ModeloAiUpdate,
    ModeloAiOutList, ModeloAiOutDetail
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError
from app.core.utils.mongo import ensure_object_id
from app.core.cache_decorators import cacheable, cache_evict
from pymongo.errors import DuplicateKeyError


class ModeloAiService:

    @staticmethod
    @cacheable("modelos_ai:all", ttl_seconds=0)
    def listar() -> List[ModeloAiOutList]:
        items: list[ModeloAiOutList] = []
        for doc in modelo_ai_coll.find():
            items.append(ModeloAiOutList.from_raw(doc))
        return items

    @staticmethod
    @cacheable("modelos_ai", key_params=["id"], ttl_seconds=0)
    def obter(id: str) -> ModeloAiOutDetail:
        oid = ensure_object_id(id)
        doc = modelo_ai_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Modelo não encontrado")

        return ModeloAiOutDetail.from_raw(doc)

    @staticmethod
    @cache_evict(["modelos_ai:all"])
    def criar(payload: ModeloAiCreate) -> ModeloAiOutDetail:
        try:
            to_insert = payload.model_dump()
            result = modelo_ai_coll.insert_one(to_insert)
            created = modelo_ai_coll.find_one({"_id": result.inserted_id})
            return ModeloAiOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um modelo com este nome")

    @staticmethod
    @cache_evict(["modelos_ai:all", "modelos_ai:id={id}"], key_params=["id"])
    def atualizar(id: str, payload: ModeloAiUpdate) -> ModeloAiOutDetail:
        oid = ensure_object_id(id)
        data = payload.model_dump(exclude_none=True)

        try:
            updated = modelo_ai_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=True
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um modelo com este nome")

        if not updated:
            raise NotFoundError("Modelo não encontrado")

        return ModeloAiOutDetail.from_raw(updated)

    @staticmethod
    @cache_evict(["modelos_ai:all", "modelos_ai:id={id}"], key_params=["id"])
    def remover(id: str) -> bool:
        # Verifica se existem credenciais vinculadas
        credencial_existente = credencial_modelo_ai_coll.find_one({"id_tool": id})
        if credencial_existente:
            raise BusinessDomainError("Existem credenciais cadastradas para este modelo. Exclua-as primeiro.")

        oid = ensure_object_id(id)
        result = modelo_ai_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Modelo não encontrado")

        return True
