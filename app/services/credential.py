from typing import List
import json
from uuid import UUID
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument

from app.dataprovider.mongo.models.credential import collection as credential_coll
from app.schemas.credential import (
    CredentialCreate, CredentialUpdate, CredentialOutList, CredentialOutDetail, CredentialOutInternal
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.utils.mongo import ensure_object_id
from app.utils.validate_credentials import ValidateCredentialsUtils
from app.dataprovider.postgre.session import SessionLocal
from app.dataprovider.postgre.repository.contractor import contractor_exists

class CredentialService:

    @staticmethod
    def get_all(credential_type_id: str, contractor_id: UUID) -> List[CredentialOutList]:
        with SessionLocal() as db:
            contractor_exists(db, contractor_id)

        items: list[CredentialOutList] = []

        for doc in credential_coll.find({
            "credential_type_id": credential_type_id,
            "contractor_id": str(contractor_id)
        }):
            items.append(CredentialOutList.from_raw(doc))

        return items

    @staticmethod
    def get_by_id(id: str) -> CredentialOutInternal:
        oid = ensure_object_id(id)
        doc = credential_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Credencial não encontrada")

        return CredentialOutInternal.from_raw(doc)

    @staticmethod
    def create(credential_type_id: str, contractor_id: UUID, payload: CredentialCreate) -> CredentialOutDetail:
        try:
            with SessionLocal() as db:
                contractor_exists(db, contractor_id)

            validated_credentials = ValidateCredentialsUtils.validate_credentials(credential_type_id, payload.credentials)

            to_insert = payload.model_dump()
            to_insert["credential_type_id"] = credential_type_id
            to_insert["contractor_id"] = str(contractor_id)
            to_insert["credentials"] = validated_credentials

            result = credential_coll.insert_one(to_insert)
            created = credential_coll.find_one({"_id": result.inserted_id})

            return CredentialOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma credencial com esta descrição")

    @staticmethod
    def update(id: str, payload: CredentialUpdate) -> CredentialOutDetail:
        oid = ensure_object_id(id)
        doc = credential_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Credencial não encontrada")

        data = payload.model_dump(exclude_none=True)

        try:
            validated_credentials = ValidateCredentialsUtils.validate_credentials(
                doc["credential_type_id"], 
                data["credentials"]
            )
            data["credentials"] = validated_credentials

            updated = credential_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=ReturnDocument.AFTER
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma credencial com esta descrição")

        return CredentialOutDetail.from_raw(updated)

    @staticmethod
    def delete(id: str) -> bool:
        oid = ensure_object_id(id)
        doc = credential_coll.find_one({"_id": oid})

        if (not doc):
            raise NotFoundError("Credencial não encontrada")

        result = credential_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Credencial não encontrada")
            
        return True
