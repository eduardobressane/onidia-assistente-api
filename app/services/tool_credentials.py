from typing import List
import json
from uuid import UUID
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument

from app.dataprovider.mongo.models.tool_credentials import collection as tool_credentials_coll
from app.dataprovider.mongo.models.tool import collection as tool_coll
from app.schemas.tool_credentials import (
    ToolCredentialsCreate, ToolCredentialsUpdate, ToolCredentialsOutList, ToolCredentialsOutDetail, ToolCredentialsInternal
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.utils.mongo import ensure_object_id
from app.utils.validate_credentials import ValidateCredentialsUtils
from app.dataprovider.postgre.session import SessionLocal
from app.dataprovider.postgre.repository.contractor import contractor_exists

class ToolCredentialsService:

    @staticmethod
    def get_all(tool_id: str, contractor_id: UUID) -> List[ToolCredentialsOutList]:
        with SessionLocal() as db:
            contractor_exists(db, contractor_id)

        items: list[ToolCredentialsOutList] = []

        for doc in tool_credentials_coll.find({
            "tool_id": tool_id,
            "contractor_id": str(contractor_id)
        }):
            items.append(ToolCredentialsOutList.from_raw(doc))

        return items

    @staticmethod
    def get_by_id(id: str) -> ToolCredentialsInternal:
        oid = ensure_object_id(id)
        doc = tool_credentials_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Credencial não encontrada")

        return ToolCredentialsInternal.from_raw(doc)

    @staticmethod
    def create(tool_id: str, contractor_id: UUID, payload: ToolCredentialsCreate) -> ToolCredentialsOutDetail:
        try:
            with SessionLocal() as db:
                contractor_exists(db, contractor_id)

            validated_credentials = ValidateCredentialsUtils.validate_tool_credentials(tool_id, payload.credentials)

            to_insert = payload.model_dump()
            to_insert["tool_id"] = tool_id
            to_insert["contractor_id"] = str(contractor_id)
            to_insert["credentials"] = validated_credentials

            result = tool_credentials_coll.insert_one(to_insert)
            created = tool_credentials_coll.find_one({"_id": result.inserted_id})

            return ToolCredentialsOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma credencial com esta descrição")

    @staticmethod
    def update(id: str, payload: ToolCredentialsUpdate) -> ToolCredentialsOutDetail:
        oid = ensure_object_id(id)
        doc = tool_credentials_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Credencial não encontrada")

        data = payload.model_dump(exclude_none=True)

        try:
            validated_credentials = ValidateCredentialsUtils.validate_tool_credentials(
                doc["tool_id"], 
                data["credentials"]
            )
            data["credentials"] = validated_credentials

            updated = tool_credentials_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=ReturnDocument.AFTER
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma credencial com esta descrição")

        return ToolCredentialsOutDetail.from_raw(updated)

    @staticmethod
    def delete(id: str) -> bool:
        oid = ensure_object_id(id)
        doc = tool_credentials_coll.find_one({"_id": oid})

        if (not doc):
            raise NotFoundError("Credencial não encontrada")

        result = tool_credentials_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Credencial não encontrada")
            
        return True
