from typing import List
from bson import ObjectId
from fastapi import HTTPException
import json

from app.dataprovider.mongo.models.tag import collection as tag_coll
from app.dataprovider.mongo.models.agent import collection as agent_coll
from app.schemas.tag import (
    TagCreate, TagUpdate, TagOutList, TagOutDetail
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BusinessDomainError
from app.core.utils.mongo import ensure_object_id
from app.core.cache_decorators import cacheable, cache_evict
from app.core.cache import cache_delete
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError


class TagService:

    @staticmethod
    @cacheable("tags:all", key_params=["tag_type"], ttl_seconds=0)
    def get_all(tag_type: str) -> List[TagOutList]:
        items: list[TagOutList] = []
        cursor = tag_coll.find(
            {"tag_type": tag_type}
        ).sort("name", 1)  # 1 = ascendente, -1 = descendente
        
        for doc in cursor:
            items.append(TagOutList.from_raw(doc))
        return items

    @staticmethod
    @cacheable("tags", key_params=["id"], ttl_seconds=0)
    def get_by_id(id: str) -> TagOutDetail:
        oid = ensure_object_id(id)
        doc = tag_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Tag não encontrada")

        return TagOutDetail.from_raw(doc)

    @staticmethod
    @cache_evict(["tags:all:tag_type={payload.tag_type}"])
    def create(payload: TagCreate) -> TagOutDetail:
        try:
            to_insert = payload.model_dump()
            result = tag_coll.insert_one(to_insert)
            created = tag_coll.find_one({"_id": result.inserted_id})
            return TagOutDetail.from_raw(created)
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma tag com este nome")

    @staticmethod
    def update(id: str, payload: TagUpdate) -> TagOutDetail:
        oid = ensure_object_id(id)

        doc = tag_coll.find_one({"_id": oid})
        if not doc:
            raise NotFoundError("Tag não encontrada")

        allowed_fields = {"name", "enabled"}
        data = payload.model_dump(include=allowed_fields, exclude_none=True)

        try:
            updated = tag_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=ReturnDocument.AFTER
            )

            cache_delete(f"tags:all:tag_type={doc['tag_type']}")
            cache_delete(f"tags:id={id}")
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe uma tag com este nome")

        if not updated:
            raise NotFoundError("Tag não encontrada")

        return TagOutDetail.from_raw(updated)

    @staticmethod
    def delete(id: str) -> bool:
        oid = ensure_object_id(id)
        doc = tag_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Tag não encontrada")

        # Check if there are agents with this tag linked
        if doc.get("tag_type") == "agent":
            agente_vinculado = agent_coll.find_one({"tags.tag.id": id})
            if agente_vinculado:
                raise BusinessDomainError("Existem agentes vinvulados a esta tag.")

        result = tag_coll.delete_one({"_id": oid})

        cache_delete(f"tags:all:tag_type={doc['tag_type']}")
        cache_delete(f"tags:id={id}")

        if result.deleted_count == 0:
            raise NotFoundError("Tag não encontrada")

        return True
