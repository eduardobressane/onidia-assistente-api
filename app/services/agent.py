from typing import List
from bson import ObjectId
from fastapi import HTTPException
import json
from uuid import UUID
import math

from app.dataprovider.mongo.models.agent import collection as agent_coll
from app.dataprovider.mongo.models.agent import get_agent_detail, validate_tools, validate_ocps
from app.schemas.agent import (
    AgentCreate, AgentUpdate, AgentOutList, AgentOutDetail, AgentOutInternal
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError
from app.core.utils.mongo import ensure_object_id
from pymongo.errors import DuplicateKeyError

from app.dataprovider.postgre.session import SessionLocal
from app.dataprovider.mongo.base import db as mongo_db
from app.dataprovider.postgre.repository.contractor import contractor_exists, contractors_exists
from app.dataprovider.mongo.models.category import validate_existing_categories


class AgentService:

    @staticmethod
    def get_all(contractor_id: UUID, name: str = None, page: int = 1, rpp: int = 10) -> dict:
        with SessionLocal() as db:
            contractor_exists(db, contractor_id)

        filtro = {"contractor_id": str(contractor_id)}

        if name is not None and str(name).strip() != "":
            filtro["name"] = {"$regex": f".*{str(name)}.*", "$options": "i"}

        skip = (page - 1) * rpp

        cursor = agent_coll.find(filtro).sort("name", 1).skip(skip).limit(rpp)

        items: list[AgentOutList] = [AgentOutList.from_raw(doc) for doc in cursor]

        total = agent_coll.count_documents(filtro)
        total_pages = math.ceil(total / rpp) if rpp > 0 else 1

        return {
            "total": total,
            "pages": total_pages,
            "items": items,
        }

    @staticmethod
    def get_by_id(id: str) -> AgentOutInternal:
        doc = get_agent_detail(id)
        if not doc:
            raise NotFoundError("Agente não encontrado")

        # Remove de contratantes se for igual ao contractor_id
        if "contractors" in doc and "contractor_id" in doc:
            doc["contractors"] = [
                c for c in doc["contractors"]
                if str(c) != str(doc["contractor_id"])
            ]

        return AgentOutInternal.from_raw(doc)

    @staticmethod
    def create(contractor_id: UUID, payload: AgentCreate) -> AgentOutDetail:
        try:
            with SessionLocal() as db:
                contractor_exists(db, contractor_id)

            to_insert = payload.model_dump()
            to_insert["contractor_id"] = str(contractor_id)

            with SessionLocal() as db:
                contractors_exists(db, payload.contractors)

            validate_ocps(mongo_db, contractor_id, payload.ocps)
            validate_tools(mongo_db, payload.tools)

            if payload.categories:
                validate_existing_categories(payload.categories, "agent")

            result = agent_coll.insert_one(to_insert)
            created = get_agent_detail(result.inserted_id)
            return AgentOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um agente com este nome")

    @staticmethod
    def update(id: str, payload: AgentUpdate) -> AgentOutDetail:
        oid = ensure_object_id(id)
        data = payload.model_dump()

        with SessionLocal() as db:
            contractors_exists(db, payload.contractors)

        validate_ocps(mongo_db, None, payload.ocps)
        validate_tools(mongo_db, payload.tools)

        categories = payload.categories or []
        if categories:
            validate_existing_categories(categories, "agent")

        try:
            updated = agent_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=True
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um agente com este nome")

        if not updated:
            raise NotFoundError("Agente não encontrado")

        updated = get_agent_detail(oid)
        return AgentOutDetail.from_raw(updated)

    @staticmethod
    def delete(id: str) -> bool:
        oid = ensure_object_id(id)
        result = agent_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Agente não encontrado")

        return True
