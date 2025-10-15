from typing import List
from bson import ObjectId
from fastapi import HTTPException
import json
from uuid import UUID
import math

from app.dataprovider.mongo.models.assistente import collection as assistente_coll
from app.dataprovider.mongo.models.assistente import get_assistente_detail
from app.schemas.assistente import (
    AssistenteCreate, 
    AssistenteUpdate, 
    AssistenteOutList, 
    AssistenteOutDetail, 
    AssistenteOutInterno
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError
from app.core.utils.mongo import ensure_object_id
from pymongo.errors import DuplicateKeyError

from app.dataprovider.postgre.session import SessionLocal
#from app.dataprovider.postgre.repository.contratante import contratantes_exists


class AssistenteService:

    @staticmethod
    def listar(id_contratante: UUID, nome: str = None, page: int = 1, rpp: int = 10) -> dict:
        filtro = {"id_contratante": str(id_contratante)}

        if nome is not None and str(nome).strip() != "":
            filtro["nome"] = {"$regex": f".*{str(nome)}.*", "$options": "i"}

        skip = (page - 1) * rpp

        cursor = assistente_coll.find(filtro).sort("nome", 1).skip(skip).limit(rpp)

        items: list[AssistenteOutList] = [AssistenteOutList.from_raw(doc) for doc in cursor]

        total = assistente_coll.count_documents(filtro)
        total_pages = math.ceil(total / rpp) if rpp > 0 else 1

        return {
            "total": total,
            "pages": total_pages,
            "items": items,
        }


    @staticmethod
    def obter(id: str) -> AssistenteOutInterno:
        doc = get_assistente_detail(id)

        if not doc:
            raise NotFoundError("Assistente não encontrado")

        return AssistenteOutInterno.from_raw(doc)

    @staticmethod
    def criar(id_contratante: UUID, payload: AssistenteCreate) -> AssistenteOutDetail:
        try:
            to_insert = payload.model_dump()
            to_insert["id_contratante"] = str(id_contratante)

            result = assistente_coll.insert_one(to_insert)
            created = assistente_coll.find_one({"_id": result.inserted_id})
            return AssistenteOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma assistente com este nome")

    @staticmethod
    def atualizar(id: str, payload: AssistenteUpdate) -> AssistenteOutDetail:
        oid = ensure_object_id(id)
        data = payload.model_dump(exclude_none=True)

        try:
            updated = assistente_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=True
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma assistente com este nome")

        if not updated:
            raise NotFoundError("Assistente não encontrado")

        return AssistenteOutDetail.from_raw(updated)

    @staticmethod
    def remover(id: str) -> bool:
        oid = ensure_object_id(id)
        result = assistente_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Assistente não encontrado")

        return True
