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
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError, BadRequestError
from app.core.utils.mongo import ensure_object_id
from pymongo.errors import DuplicateKeyError

from app.dataprovider.postgre.session import SessionLocal
from app.dataprovider.mongo.base import db as mongo_db
from app.dataprovider.postgre.repository.contractor import contractor_exists
from app.dataprovider.mongo.models.tag import validate_existing_tags
from app.services.upload import UploadService
from fastapi import UploadFile
from app.schemas.http_response_advice import error

import os
from dotenv import load_dotenv

class AgentService:

    MAX_FILE_SIZE_KB = int(os.getenv("MAX_FILE_SIZE_KB_AGENT", 1024))
    ALLOWED_CONTENT_TYPES = set(os.getenv("ALLOWED_CONTENT_TYPES_IMAGE").split(","))

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

        return AgentOutInternal.from_raw(doc)

    @staticmethod
    def create(contractor_id: UUID, payload: AgentCreate) -> AgentOutDetail:
        try:
            with SessionLocal() as db:
                contractor_exists(db, contractor_id)

            to_insert = payload.model_dump()
            to_insert["contractor_id"] = str(contractor_id)
            to_insert["has_image"] = False

            validate_ocps(mongo_db, contractor_id, payload.ocps)
            validate_tools(mongo_db, payload.tools)

            if payload.tags:
                validate_existing_tags(payload.tags, "agent")

            result = agent_coll.insert_one(to_insert)
            created = get_agent_detail(result.inserted_id)
            return AgentOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um agente com este nome")

    @staticmethod
    def update(id: str, payload: AgentUpdate) -> AgentOutDetail:
        oid = ensure_object_id(id)
        data = payload.model_dump()

        validate_ocps(mongo_db, None, payload.ocps)
        validate_tools(mongo_db, payload.tools)

        tags = payload.tags or []
        if tags:
            validate_existing_tags(tags, "agent")

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

    @staticmethod
    def upload_image(id: str, file: UploadFile):
        oid = ensure_object_id(id)
        agent = agent_coll.find_one({"_id": oid})

        if not agent:
            raise NotFoundError("Agente não encontrado")

        try:
            result = UploadService.upload_file(id=id, dir='agents', file=file, max_file_size=AgentService.MAX_FILE_SIZE_KB, allowed_content_types=AgentService.ALLOWED_CONTENT_TYPES)
            agent_coll.update_one({"_id": oid}, {"$set": {"has_image": True}})

            return result
        except Exception as e:
            return error(status_code=400, message=f"Erro ao realizar o upload da imagem")

    @staticmethod
    def delete_image(id: str):
        oid = ensure_object_id(id)
        agent = agent_coll.find_one({"_id": oid})

        if not agent:
            raise NotFoundError("Agente não encontrado")

        try:
            result = UploadService.delete_file(id=id, dir='agents')
            agent_coll.update_one({"_id": oid}, {"$set": {"has_image": False}})

            return result
        except Exception as e:
            return error(status_code=400, message=f"Erro ao excluir imagem")
