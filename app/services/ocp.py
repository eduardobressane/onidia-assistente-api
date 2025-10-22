
from uuid import UUID
import math
from app.dataprovider.mongo.models.ocp import collection as ocp_coll
from app.schemas.ocp import (
    OCPCreate, OCPUpdate, OCPOutList, OCPOutDetail
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.utils.mongo import ensure_object_id
from pymongo.errors import DuplicateKeyError
from app.core.ocp.ocp_converter import OCPConverter
from app.core.ocp.structure_fetcher import StructureFetcher

class OCPService:

    @staticmethod
    def get_all(contractor_id: UUID, name: str = None, page: int = 1, rpp: int = 10) -> dict:
        filtro = {"contractor_id": str(contractor_id)}

        if name is not None and str(name).strip() != "":
            filtro["name"] = {"$regex": f".*{str(name)}.*", "$options": "i"}

        skip = (page - 1) * rpp

        cursor = ocp_coll.find(filtro).sort("name", 1).skip(skip).limit(rpp)

        items: list[OCPOutList] = [OCPOutList.from_raw(doc) for doc in cursor]

        total = ocp_coll.count_documents(filtro)
        total_pages = math.ceil(total / rpp) if rpp > 0 else 1

        return {
            "total": total,
            "pages": total_pages,
            "items": items,
        }

    @staticmethod
    def get_by_id(id: str) -> OCPOutDetail:
        oid = ensure_object_id(id)
        doc = ocp_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("OCP não encontrado")

        return OCPOutDetail.from_raw(doc)

    @staticmethod
    def create(contractor_id: UUID, payload: OCPCreate) -> OCPOutDetail:
        try:
            payload_data = payload.model_dump()

            structure = StructureFetcher.get_structure(
                payload_data["source"]["type"],
                payload_data["source"]["url"],
                payload_data["source"]["headers"]
            )
            ocp = OCPConverter.ocp(payload_data["source"]["type"], structure, url=payload_data["source"]["url"], headers=payload_data["source"]["headers"])

            to_insert = {
                "name": payload_data["name"],
                "enabled": payload_data["enabled"],
                "contractor_id": contractor_id,
                "ocp": ocp
            }

            result = ocp_coll.insert_one(to_insert)
            created = ocp_coll.find_one({"_id": result.inserted_id})
            return OCPOutDetail.from_raw(created)

        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um OCP com este nome")

    @staticmethod
    def update(id: str, payload: OCPUpdate) -> OCPOutDetail:
        oid = ensure_object_id(id)
        payload_data = payload.model_dump()

        structure = StructureFetcher.get_structure(
            "mcp",
            payload_data["source"]["url"],
            payload_data["source"]["headers"]
        )
        ocp = OCPConverter.mcp_to_ocp(structure, url=payload_data["source"]["url"], headers=payload_data["source"]["headers"])

        data = {
            "name": payload_data["name"],
            "enabled": payload_data["enabled"],
            "ocp": ocp
        }

        try:
            updated = ocp_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=True
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um OCP com este nome")

        if not updated:
            raise NotFoundError("OCP não encontrada")

        return OCPOutDetail.from_raw(updated)

    @staticmethod
    def delete(id: str) -> bool:
        oid = ensure_object_id(id)
        doc = ocp_coll.find_one({"_id": oid})

        if (not doc):
            raise NotFoundError("OCP não encontrado")

        result = ocp_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("OCP não encontrado")
            
        return True