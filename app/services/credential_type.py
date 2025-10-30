from typing import List, Literal
from bson import ObjectId
from pymongo import ASCENDING

from app.dataprovider.mongo.models.credential_type import collection as credential_type_coll
from app.dataprovider.mongo.models.credential import collection as credential_coll
from app.schemas.credential_type import (
    CredentialTypeCreate, CredentialTypeUpdate,
    CredentialTypeOutList, CredentialTypeOutDetail
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError, BadRequestError
from app.core.utils.mongo import ensure_object_id
from app.core.cache_decorators import cacheable, cache_evict
from pymongo.errors import DuplicateKeyError
from app.services.upload import UploadService
from fastapi import UploadFile
from app.schemas.http_response_advice import error

import os
from dotenv import load_dotenv

class CredentialTypeService:

    MAX_FILE_SIZE_KB = int(os.getenv("MAX_FILE_SIZE_KB_CREDENTIAL_TYPE", 1024))
    ALLOWED_CONTENT_TYPES = set(os.getenv("ALLOWED_CONTENT_TYPES_IMAGE").split(","))

    @cacheable("credentials_types:all", key_params=["kind"], ttl_seconds=0)
    @staticmethod
    def get_all(kind: Literal["ai_models", "tools"] = None) -> list[CredentialTypeOutList]:
        filtro = {"kind": kind} if kind else {}

        cursor = (
            credential_type_coll
            .find(filtro)
            .sort([("kind", ASCENDING), ("name", ASCENDING)])
        )

        return [CredentialTypeOutList.from_raw(doc) for doc in cursor]

    @staticmethod
    @cacheable("credentials_types", key_params=["id"], ttl_seconds=0)
    def get_by_id(id: str) -> CredentialTypeOutDetail:
        oid = ensure_object_id(id)
        doc = credential_type_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Tipo de Credencial não encontrado")

        return CredentialTypeOutDetail.from_raw(doc)

    @staticmethod
    @cache_evict("credentials_types:all", match_prefix=True)
    def create(payload: CredentialTypeCreate) -> CredentialTypeOutDetail:
        try:
            to_insert = payload.model_dump()
            to_insert["has_image"] = False

            result = credential_type_coll.insert_one(to_insert)
            created = credential_type_coll.find_one({"_id": result.inserted_id})
            return CredentialTypeOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um tipo de credencial com este nome")

    @staticmethod
    @cache_evict(["credentials_types:all", "credentials_types:id={id}"], key_params=["id"], match_prefix=True)
    def update(id: str, payload: CredentialTypeUpdate) -> CredentialTypeOutDetail:
        oid = ensure_object_id(id)
        data = payload.model_dump(exclude_none=True)

        try:
            updated = credential_type_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=True
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um tipo de credencial com este nome")

        if not updated:
            raise NotFoundError("Tipo de credencial não encontrado")

        return CredentialTypeOutDetail.from_raw(updated)

    @staticmethod
    @cache_evict(["credentials_types:all", "credentials_types:id={id}"], key_params=["id"], match_prefix=True)
    def delete(id: str) -> bool:
        # Verifica se existem credenciais vinculadas
        credentials_exists = credential_coll.find_one({"credential_type_id": id})
        if credentials_exists:
            raise BusinessDomainError("Existem credenciais cadastradas para este tipo de credencial. Exclua-as primeiro.")

        oid = ensure_object_id(id)
        result = credential_type_coll.delete_one({"_id": oid})

        s3 = S3Service()
        s3.delete_public_file("imgs/credentials_types", id)

        if result.deleted_count == 0:
            raise NotFoundError("Tipo de credencial não encontrado")

        return True

    @staticmethod
    @cache_evict(
        ["credentials_types:all", "credentials_types:id={id}"],
        key_params=["id"],
        match_prefix=True
    )
    def upload_image(id: str, file: UploadFile):
        oid = ensure_object_id(id)
        credential_type = credential_type_coll.find_one({"_id": oid})

        if not credential_type:
            raise NotFoundError("Tipo de credencial não encontrado")

        try:
            result = UploadService.upload_file(id=id, dir='credentials_types', file=file, max_file_size=CredentialTypeService.MAX_FILE_SIZE_KB, allowed_content_types=CredentialTypeService.ALLOWED_CONTENT_TYPES)
            credential_type_coll.update_one({"_id": oid}, {"$set": {"has_image": True}})

            return result
        except Exception as e:
            raise BadRequestError("Erro ao realizar o upload da imagem")

    @staticmethod
    @cache_evict(["credentials_types:all", "credentials_types:id={id}"], key_params=["id"], match_prefix=True)
    def delete_image(id: str):
        oid = ensure_object_id(id)
        credential_type = credential_type_coll.find_one({"_id": oid})

        if not credential_type:
            raise NotFoundError("Tipo de credencial não encontrado")

        try:
            result = UploadService.delete_file(id=id, dir='credentials_types')
            credential_type_coll.update_one({"_id": oid}, {"$set": {"has_image": False}})

            return result
        except Exception as e:
            raise BadRequestError("Erro ao excluir imagem")
