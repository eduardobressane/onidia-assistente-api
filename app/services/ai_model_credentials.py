from typing import List
import json
from uuid import UUID
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument

from app.dataprovider.mongo.models.ai_model_credentials import collection as ai_model_credentials_coll
from app.dataprovider.mongo.models.ai_model import collection as ai_model_coll
from app.schemas.ai_model_credentials import (
    AiModelCredentialsCreate, AiModelCredentialsUpdate, AiModelCredentialsOutList, AiModelCredentialsOutDetail, AiModelCredentialsOutInternal
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.utils.mongo import ensure_object_id
from app.utils.validate_credentials import ValidateCredentialsUtils
from app.dataprovider.postgre.session import SessionLocal
from app.dataprovider.postgre.repository.contractor import contractor_exists

class AiModelCredentialsService:

    @staticmethod
    def get_all(ai_model_id: str, contractor_id: UUID) -> List[AiModelCredentialsOutList]:
        with SessionLocal() as db:
            contractor_exists(db, contractor_id)

        items: list[AiModelCredentialsOutList] = []

        for doc in ai_model_credentials_coll.find({
            "ai_model_id": ai_model_id,
            "contractor_id": str(contractor_id)
        }):
            items.append(AiModelCredentialsOutList.from_raw(doc))

        return items

    @staticmethod
    def get_by_id(id: str) -> AiModelCredentialsOutInternal:
        oid = ensure_object_id(id)
        doc = ai_model_credentials_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Credencial não encontrada")

        return AiModelCredentialsOutInternal.from_raw(doc)

    @staticmethod
    def create(ai_model_id: str, contractor_id: UUID, payload: AiModelCredentialsCreate) -> AiModelCredentialsOutDetail:
        try:
            with SessionLocal() as db:
                contractor_exists(db, contractor_id)

            validated_credentials = ValidateCredentialsUtils.validate_ai_model_credentials(ai_model_id, payload.credentials)

            to_insert = payload.model_dump()
            to_insert["ai_model_id"] = ai_model_id
            to_insert["contractor_id"] = str(contractor_id)
            to_insert["credentials"] = validated_credentials

            result = ai_model_credentials_coll.insert_one(to_insert)
            created = ai_model_credentials_coll.find_one({"_id": result.inserted_id})

            return AiModelCredentialsOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma credencial com esta descrição")

    @staticmethod
    def update(id: str, payload: AiModelCredentialsUpdate) -> AiModelCredentialsOutDetail:
        oid = ensure_object_id(id)
        doc = ai_model_credentials_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Credencial não encontrada")

        data = payload.model_dump(exclude_none=True)

        try:
            validated_credentials = ValidateCredentialsUtils.validate_ai_model_credentials(
                doc["ai_model_id"], 
                data["credentials"]
            )
            data["credentials"] = validated_credentials

            updated = ai_model_credentials_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=ReturnDocument.AFTER
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma credencial com esta descrição")

        return AiModelCredentialsOutDetail.from_raw(updated)

    @staticmethod
    def delete(id: str) -> bool:
        oid = ensure_object_id(id)
        doc = ai_model_credentials_coll.find_one({"_id": oid})

        if (not doc):
            raise NotFoundError("Credencial não encontrada")

        result = ai_model_credentials_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Credencial não encontrada")
            
        return True
