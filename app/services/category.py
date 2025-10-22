from typing import List
from bson import ObjectId
from fastapi import HTTPException
import json

from app.dataprovider.mongo.models.category import collection as category_coll
from app.dataprovider.mongo.models.agent import collection as agent_coll
from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryOutList, CategoryOutDetail
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError
from app.core.utils.mongo import ensure_object_id
from app.core.cache_decorators import cacheable, cache_evict
from app.core.cache import cache_delete
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError


class CategoryService:

    @staticmethod
    @cacheable("categories:all", key_params=["category_type"], ttl_seconds=0)
    def get_all(category_type: str) -> List[CategoryOutList]:
        items: list[CategoryOutList] = []
        cursor = category_coll.find(
            {"category_type": category_type}
        ).sort("name", 1)  # 1 = ascendente, -1 = descendente
        
        for doc in cursor:
            items.append(CategoryOutList.from_raw(doc))
        return items

    @staticmethod
    @cacheable("categories", key_params=["id"], ttl_seconds=0)
    def get_by_id(id: str) -> CategoryOutDetail:
        oid = ensure_object_id(id)
        doc = category_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Categoria não encontrada")

        return CategoryOutDetail.from_raw(doc)

    @staticmethod
    @cache_evict(["categories:all:category_type={payload.category_type}"])
    def create(payload: CategoryCreate) -> CategoryOutDetail:
        try:
            to_insert = payload.model_dump()
            result = category_coll.insert_one(to_insert)
            created = category_coll.find_one({"_id": result.inserted_id})
            return CategoryOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma categoria com este nome")

    @staticmethod
    def update(id: str, payload: CategoryUpdate) -> CategoryOutDetail:
        oid = ensure_object_id(id)

        doc = category_coll.find_one({"_id": oid})
        if not doc:
            raise NotFoundError("Categoria não encontrada")

        allowed_fields = {"name", "enabled"}
        data = payload.model_dump(include=allowed_fields, exclude_none=True)

        try:
            updated = category_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=ReturnDocument.AFTER
            )

            cache_delete(f"categories:all:category_type={doc['category_type']}")
            cache_delete(f"categories:id={id}")
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma categoria com este nome")

        if not updated:
            raise NotFoundError("Categoria não encontrada")

        return CategoryOutDetail.from_raw(updated)

    @staticmethod
    def delete(id: str) -> bool:
        oid = ensure_object_id(id)
        doc = category_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Categoria não encontrada")

        # Check if there are agents with this category linked
        if doc.get("category_type") == "agent":
            agente_vinculado = agent_coll.find_one({"categories.category.id": id})
            if agente_vinculado:
                raise BusinessDomainError("Existem agentes vinvulados a esta categoria.")

        result = category_coll.delete_one({"_id": oid})

        cache_delete(f"categories:all:category_type={doc['category_type']}")
        cache_delete(f"categories:id={id}")

        if result.deleted_count == 0:
            raise NotFoundError("Categoria não encontrada")

        return True
