from typing import List
from bson import ObjectId
from fastapi import HTTPException
import json
from uuid import UUID

from app.dataprovider.mongo.models.agente import collection as agente_coll
from app.dataprovider.mongo.models.agente import get_agente_detail
from app.schemas.agente import (
    AgenteCreate, AgenteUpdate, AgenteOutList, AgenteOutDetail
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError
from app.core.utils.mongo import ensure_object_id
from pymongo.errors import DuplicateKeyError


class AgenteService:

    @staticmethod
    def listar(id_contratante: UUID, nome: str) -> List[AgenteOutList]:
        filtro = {"id_contratante": id_contratante}

        if nome is not None and str(nome).strip() != "":
            filtro["nome"] = {"$regex": f".*{str(nome)}.*", "$options": "i"}

        items: list[AgenteOutList] = []
        for doc in agente_coll.find(filtro):
            items.append(AgenteOutList.from_raw(doc))
        return items

    @staticmethod
    def obter(id: str) -> AgenteOutDetail:
        doc = get_agente_detail(id)

        if not doc:
            raise NotFoundError("Agente não encontrado")

        return AgenteOutDetail.from_raw(doc)

    @staticmethod
    def criar(id_contratante: UUID, payload: AgenteCreate) -> AgenteOutDetail:
        try:
            to_insert = payload.model_dump()
            to_insert["id_contratante"] = str(id_contratante)

            result = agente_coll.insert_one(to_insert)
            created = agente_coll.find_one({"_id": result.inserted_id})
            return AgenteOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um agente com este nome")

    @staticmethod
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
    def remover(id: str) -> bool:
        oid = ensure_object_id(id)
        result = agente_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Agente não encontrado")

        return True
