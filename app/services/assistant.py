from typing import List
from bson import ObjectId
from fastapi import HTTPException
import json
from uuid import UUID
import math

from app.dataprovider.mongo.models.assistant import collection as assistant_coll
from app.dataprovider.mongo.models.agent import collection as agent_coll
from app.dataprovider.mongo.models.assistant import get_assistant_detail, validate_tools, validate_ai_model
from app.schemas.assistant import (
    AssistantCreate, 
    AssistantUpdate, 
    AssistantOutList, 
    AssistantOutDetail, 
    AssistantOutInternal
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError
from app.core.utils.mongo import ensure_object_id
from pymongo.errors import DuplicateKeyError
from app.dataprovider.postgre.session import SessionLocal
from app.dataprovider.postgre.repository.contractor import contractor_exists


class AssistantService:

    @staticmethod
    def get_all(contractor_id: UUID, name: str = None, page: int = 1, rpp: int = 10) -> dict:
        with SessionLocal() as db:
            contractor_exists(db, contractor_id)

        filtro = {"contractor_id": str(contractor_id)}

        if name is not None and str(name).strip() != "":
            filtro["name"] = {"$regex": f".*{str(name)}.*", "$options": "i"}

        skip = (page - 1) * rpp

        cursor = assistant_coll.find(filtro).sort("name", 1).skip(skip).limit(rpp)

        items: list[AssistantOutList] = [AssistantOutList.from_raw(doc) for doc in cursor]

        total = assistant_coll.count_documents(filtro)
        total_pages = math.ceil(total / rpp) if rpp > 0 else 1

        return {
            "total": total,
            "pages": total_pages,
            "items": items,
        }


    @staticmethod
    def get_by_id(id: str) -> AssistantOutInternal:
        doc = get_assistant_detail(id)

        if not doc:
            raise NotFoundError("Assistente não encontrado")

        return AssistantOutInternal.from_raw(doc)

    @staticmethod
    def create(contractor_id: UUID, payload: AssistantCreate) -> AssistantOutDetail:
        try:
            with SessionLocal() as db:
                contractor_exists(db, contractor_id)

            to_insert = payload.model_dump()
            to_insert["contractor_id"] = str(contractor_id)

            #validando ai_model
            validate_ai_model(payload.ai_model.id)

            # Validando as tools cadastradas
            for agent_payload in payload.agents:
                agent_id = ensure_object_id(agent_payload.agent.id)
                agent_config = agent_coll.find_one({"_id": agent_id})
                if not agent_config:
                    raise NotFoundError(f"Agente {agent_id} não encontrado.")
                validate_tools(agent_config, agent_payload.model_dump())

            result = assistant_coll.insert_one(to_insert)
            created = assistant_coll.find_one({"_id": result.inserted_id})
            return AssistantOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma assistente com este nome")

    @staticmethod
    def update(id: str, payload: AssistantUpdate) -> AssistantOutDetail:
        oid = ensure_object_id(id)
        data = payload.model_dump(exclude_none=True)

        # Validando as tools cadastradas
        for agent_payload in payload.agents:
            agent_id = ensure_object_id(agent_payload.agent.id)
            agent_config = agent_coll.find_one({"_id": agent_id})
            if not agent_config:
                raise NotFoundError(f"Agente {agent_id} não encontrado.")
            validate_tools(agent_config, agent_payload.model_dump())

        try:
            updated = assistant_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=True
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma assistente com este nome")

        if not updated:
            raise NotFoundError("Assistente não encontrado")

        return AssistantOutDetail.from_raw(updated)

    @staticmethod
    def delete(id: str) -> bool:
        oid = ensure_object_id(id)
        result = assistant_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Assistente não encontrado")

        return True
