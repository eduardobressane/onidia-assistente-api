from typing import List
from bson import ObjectId
from fastapi import HTTPException
import json
from uuid import UUID
import math

from app.dataprovider.mongo.models.agente import collection as agente_coll
from app.dataprovider.mongo.models.agente import get_agente_detail
from app.schemas.agente import (
    AgenteCreate, AgenteUpdate, AgenteOutList, AgenteOutDetail, AgenteOutInterno
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError
from app.core.utils.mongo import ensure_object_id
from pymongo.errors import DuplicateKeyError

from app.dataprovider.postgre.session import SessionLocal
from app.dataprovider.postgre.repository.contratante import contratantes_exists


class AgenteService:

    @staticmethod
    def listar(id_contratante: UUID, nome: str = None, page: int = 1, rpp: int = 10) -> dict:
        filtro = {"id_contratante": str(id_contratante)}

        if nome is not None and str(nome).strip() != "":
            filtro["nome"] = {"$regex": f".*{str(nome)}.*", "$options": "i"}

        skip = (page - 1) * rpp

        cursor = agente_coll.find(filtro).sort("nome", 1).skip(skip).limit(rpp)

        items: list[AgenteOutList] = [AgenteOutList.from_raw(doc) for doc in cursor]

        total = agente_coll.count_documents(filtro)
        total_pages = math.ceil(total / rpp) if rpp > 0 else 1

        return {
            "total": total,
            "pages": total_pages,
            "items": items,
        }

    @staticmethod
    def obter(id: str) -> AgenteOutInterno:
        doc = get_agente_detail(id)

        if not doc:
            raise NotFoundError("Agente não encontrado")

        # Remove de contratantes se for igual ao id_contratante
        if "contratantes" in doc and "id_contratante" in doc:
            doc["contratantes"] = [
                c for c in doc["contratantes"]
                if str(c) != str(doc["id_contratante"])
            ]

        return AgenteOutInterno.from_raw(doc)

    @staticmethod
    def criar(id_contratante: UUID, payload: AgenteCreate) -> AgenteOutDetail:
        try:
            to_insert = payload.model_dump()
            to_insert["id_contratante"] = str(id_contratante)

            with SessionLocal() as db:
                contratantes_exists(db, payload.contratantes)

            result = agente_coll.insert_one(to_insert)
            created = agente_coll.find_one({"_id": result.inserted_id})
            return AgenteOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um agente com este nome")

    @staticmethod
    def atualizar(id: str, payload: AgenteUpdate) -> AgenteOutDetail:
        oid = ensure_object_id(id)
        data = payload.model_dump(exclude_none=True)

        with SessionLocal() as db:
            contratantes_exists(db, payload.contratantes)

        try:
            updated = agente_coll.find_one_and_update(
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
