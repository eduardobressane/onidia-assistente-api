from typing import List
from bson import ObjectId
from fastapi import HTTPException, UploadFile

from app.dataprovider.mongo.models.credential_type import collection as credential_type_coll
from app.dataprovider.mongo.models.credential import collection as credential_coll
from app.schemas.credential_type import (
    CredentialTypeCreate, CredentialTypeUpdate,
    CredentialTypeOutList, CredentialTypeOutDetail
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError
from app.core.utils.mongo import ensure_object_id
from app.core.cache_decorators import cacheable, cache_evict
from pymongo.errors import DuplicateKeyError
from app.services.s3 import S3Service


class CredentialTypeService:

    @staticmethod
    @cacheable("credentials_types:all", ttl_seconds=0)
    def get_all() -> List[CredentialTypeOutList]:
        items: list[CredentialTypeOutList] = []
        for doc in credential_type_coll.find():
            items.append(CredentialTypeOutList.from_raw(doc))
        return items

    @staticmethod
    @cacheable("credentials_types", key_params=["id"], ttl_seconds=0)
    def get_by_id(id: str) -> CredentialTypeOutDetail:
        oid = ensure_object_id(id)
        doc = credential_type_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Tipo de Credencial não encontrado")

        return CredentialTypeOutDetail.from_raw(doc)

    @staticmethod
    @cache_evict(["credentials_types:all"])
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
    @cache_evict(["credentials_types:all", "credentials_types:id={id}"], key_params=["id"])
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
    @cache_evict(["credentials_types:all", "credentials_types:id={id}"], key_params=["id"])
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
    @cache_evict(["credentials_types:all", "credentials_types:id={id}"], key_params=["id"])
    def upload_image(id: str, file: UploadFile):
        oid = ensure_object_id(id)
        credential_type = credential_type_coll.find_one({"_id": oid})

        if not credential_type:
            raise NotFoundError("Tipo de credencial não encontrado")

        s3 = S3Service()

        public_url = s3.upload_public_file(file, directory="imgs/credentials_types", filename=id)

        if not public_url:
            raise HTTPException(status_code=500, detail="Erro ao salvar a imagem")

        credential_type_coll.update_one({"_id": oid}, {"$set": {"has_image": True}})

        return {"public_url": public_url}

    @staticmethod
    @cache_evict(["credentials_types:all", "credentials_types:id={id}"], key_params=["id"])
    def delete_image(id: str):
        oid = ensure_object_id(id)
        credential_type = credential_type_coll.find_one({"_id": oid})

        if not credential_type:
            raise NotFoundError("Tipo de credencial não encontrado")

        s3 = S3Service()
        deleted = s3.delete_public_file("imgs/credentials_types", id)

        if not deleted:
            raise HTTPException(status_code=500, detail="Erro ao excluir a imagem")

        credential_type_coll.update_one({"_id": oid}, {"$set": {"has_image": False}})

        return {"deleted": True}
