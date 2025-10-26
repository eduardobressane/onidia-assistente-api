from uuid import UUID
import math
from pymongo.errors import DuplicateKeyError
from app.dataprovider.mongo.models.service import collection as srv_coll
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceOutList,
    ServiceOutDetail,
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.utils.mongo import ensure_object_id


class ServiceService:

    # ========= GET ALL =========
    @staticmethod
    def get_all(contractor_id: UUID, name: str = None, page: int = 1, rpp: int = 10) -> dict:
        """
        Lista todos os serviços com paginação e filtro opcional por nome.
        """
        filtro = {"contractor_id": str(contractor_id)}

        if name and str(name).strip() != "":
            filtro["name"] = {"$regex": f".*{str(name)}.*", "$options": "i"}

        skip = (page - 1) * rpp
        cursor = srv_coll.find(filtro).sort("name", 1).skip(skip).limit(rpp)

        items: list[ServiceOutList] = [ServiceOutList.from_raw(doc) for doc in cursor]
        total = srv_coll.count_documents(filtro)
        total_pages = math.ceil(total / rpp) if rpp > 0 else 1

        return {
            "total": total,
            "pages": total_pages,
            "items": items,
        }

    # ========= GET BY ID =========
    @staticmethod
    def get_by_id(id: str) -> ServiceOutDetail:
        """
        Busca um serviço pelo ID.
        """
        oid = ensure_object_id(id)
        doc = srv_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Serviço não encontrado")

        return ServiceOutDetail.from_raw(doc)

    # ========= CREATE =========
    @staticmethod
    def create(contractor_id: UUID, payload: ServiceCreate) -> ServiceOutDetail:
        """
        Cria um novo serviço.
        """
        try:
            data = payload.model_dump()
            data["contractor_id"] = str(contractor_id)

            result = srv_coll.insert_one(data)
            created = srv_coll.find_one({"_id": result.inserted_id})
            return ServiceOutDetail.from_raw(created)

        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um serviço com este nome")

    # ========= UPDATE =========
    @staticmethod
    def update(id: str, payload: ServiceUpdate) -> ServiceOutDetail:
        """
        Atualiza um serviço existente.
        """
        oid = ensure_object_id(id)
        data = payload.model_dump()

        try:
            updated = srv_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=True
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um serviço com este nome")

        if not updated:
            raise NotFoundError("Serviço não encontrado")

        return ServiceOutDetail.from_raw(updated)

    # ========= DELETE =========
    @staticmethod
    def delete(id: str) -> bool:
        """
        Exclui um serviço.
        """
        oid = ensure_object_id(id)
        doc = srv_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Serviço não encontrado")

        result = srv_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Serviço não encontrado")

        return True
