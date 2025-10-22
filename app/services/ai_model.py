from typing import List
from bson import ObjectId
from fastapi import HTTPException, UploadFile

from app.dataprovider.mongo.models.ai_model import collection as ai_model_coll
from app.dataprovider.mongo.models.ai_model_credentials import collection as ai_model_credentials_coll
from app.schemas.ai_model import (
    AiModelCreate, AiModelUpdate,
    AiModelOutList, AiModelOutDetail
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError
from app.core.utils.mongo import ensure_object_id
from app.core.cache_decorators import cacheable, cache_evict
from pymongo.errors import DuplicateKeyError
from app.services.s3 import S3Service


class AiModelService:

    @staticmethod
    @cacheable("ai_models:all", ttl_seconds=0)
    def get_all() -> List[AiModelOutList]:
        items: list[AiModelOutList] = []
        for doc in ai_model_coll.find():
            items.append(AiModelOutList.from_raw(doc))
        return items

    @staticmethod
    @cacheable("ai_models", key_params=["id"], ttl_seconds=0)
    def get_by_id(id: str) -> AiModelOutDetail:
        oid = ensure_object_id(id)
        doc = ai_model_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Modelo não encontrado")

        return AiModelOutDetail.from_raw(doc)

    @staticmethod
    @cache_evict(["ai_models:all"])
    def create(payload: AiModelCreate) -> AiModelOutDetail:
        try:
            to_insert = payload.model_dump()
            to_insert["has_image"] = False

            result = ai_model_coll.insert_one(to_insert)
            created = ai_model_coll.find_one({"_id": result.inserted_id})
            return AiModelOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um modelo com este nome")

    @staticmethod
    @cache_evict(["ai_models:all", "ai_models:id={id}"], key_params=["id"])
    def update(id: str, payload: AiModelUpdate) -> AiModelOutDetail:
        oid = ensure_object_id(id)
        data = payload.model_dump(exclude_none=True)

        try:
            updated = ai_model_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=True
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um modelo com este nome")

        if not updated:
            raise NotFoundError("Modelo não encontrado")

        return AiModelOutDetail.from_raw(updated)

    @staticmethod
    @cache_evict(["ai_models:all", "ai_models:id={id}"], key_params=["id"])
    def delete(id: str) -> bool:
        # Verifica se existem credenciais vinculadas
        credencial_existente = ai_model_credentials_coll.find_one({"id_tool": id})
        if credencial_existente:
            raise BusinessDomainError("Existem credenciais cadastradas para este modelo. Exclua-as primeiro.")

        oid = ensure_object_id(id)
        result = ai_model_coll.delete_one({"_id": oid})

        s3 = S3Service()
        s3.delete_public_file("imgs/ai_models", id)

        if result.deleted_count == 0:
            raise NotFoundError("Modelo não encontrado")

        return True

    @staticmethod
    @cache_evict(["ai_models:all", "ai_models:id={id}"], key_params=["id"])
    def upload_image(id: str, file: UploadFile):
        oid = ensure_object_id(id)
        model = ai_model_coll.find_one({"_id": oid})

        if not model:
            raise NotFoundError("Modelo não encontrado")

        s3 = S3Service()

        public_url = s3.upload_public_file(file, directory="imgs/ai_models", filename=id)

        if not public_url:
            raise HTTPException(status_code=500, detail="Erro ao salvar a imagem")

        ai_model_coll.update_one({"_id": oid}, {"$set": {"has_image": True}})

        return {"public_url": public_url}

    @staticmethod
    @cache_evict(["ai_models:all", "ai_models:id={id}"], key_params=["id"])
    def delete_image(id: str):
        oid = ensure_object_id(id)
        model = ai_model_coll.find_one({"_id": oid})

        if not model:
            raise NotFoundError("Modelo não encontrado")

        s3 = S3Service()
        deleted = s3.delete_public_file("imgs/ai_models", id)

        if not deleted:
            raise HTTPException(status_code=500, detail="Erro ao excluir a imagem")

        ai_model_coll.update_one({"_id": oid}, {"$set": {"has_image": False}})

        return {"deleted": True}
