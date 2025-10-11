from typing import List
import json
from uuid import UUID
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument

from app.dataprovider.mongo.models.credencial_modelo_ai import collection as credencial_modelo_ai_coll
from app.schemas.credencial_modelo_ai import (
    CredencialModeloAiCreate, CredencialModeloAiUpdate, CredencialModeloAiOutList, CredencialModeloAiOutDetail, CredencialModeloAiInterna
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.utils.mongo import ensure_object_id


class CredencialModeloAiService:

    @staticmethod
    def listar(id_modelo_ai: str, id_contratante: UUID) -> List[CredencialModeloAiOutList]:
        items: list[CredencialModeloAiOutList] = []

        for doc in credencial_modelo_ai_coll.find({
            "id_modelo_ai": id_modelo_ai,
            "id_contratante": str(id_contratante)
        }):
            items.append(CredencialModeloAiOutList.from_raw(doc))

        return items

    @staticmethod
    def obter(id: str) -> CredencialModeloAiInterna:
        oid = ensure_object_id(id)
        doc = credencial_modelo_ai_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Credencial não encontrada")

        return CredencialModeloAiInterna.from_raw(doc)

    @staticmethod
    def criar(id_modelo_ai: str, id_contratante: UUID, payload: CredencialModeloAiCreate) -> CredencialModeloAiOutDetail:
        try:
            to_insert = payload.model_dump()
            to_insert["id_modelo_ai"] = id_modelo_ai
            to_insert["id_contratante"] = str(id_contratante)

            result = credencial_modelo_ai_coll.insert_one(to_insert)
            created = credencial_modelo_ai_coll.find_one({"_id": result.inserted_id})

            return CredencialModeloAiOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma credencial com esta descrição")

    @staticmethod
    def atualizar(id: str, payload: CredencialModeloAiUpdate) -> CredencialModeloAiOutDetail:
        oid = ensure_object_id(id)
        doc = credencial_modelo_ai_coll.find_one({"_id": oid})

        if (not doc):
            raise NotFoundError("Credencial não encontrada")

        data = payload.model_dump(exclude_none=True)

        try:
            updated = credencial_modelo_ai_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=ReturnDocument.AFTER
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma credencial com esta descrição")

        return CredencialModeloAiOutDetail.from_raw(updated)

    @staticmethod
    def remover(id: str) -> bool:
        oid = ensure_object_id(id)
        doc = credencial_modelo_ai_coll.find_one({"_id": oid})

        if (not doc):
            raise NotFoundError("Credencial não encontrada")

        result = credencial_modelo_ai_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Credencial não encontrada")
            
        return True
