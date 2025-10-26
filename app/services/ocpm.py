from uuid import UUID
import math
from pymongo.errors import DuplicateKeyError
from app.dataprovider.mongo.models.ocpm import collection as ocpm_coll
from app.schemas.ocpm import (
    OCPMCreate,
    OCPMUpdate,
    OCPMOutList,
    OCPMOutDetail,
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.utils.mongo import ensure_object_id


class OCPMService:

    # ========= GET ALL =========
    @staticmethod
    def get_all(contractor_id: UUID, name: str = None, page: int = 1, rpp: int = 10) -> dict:
        """
        Lista todos os OCP-Ms com paginação e filtro opcional por nome.
        """
        filtro = {"contractor_id": str(contractor_id)}

        if name and str(name).strip() != "":
            filtro["name"] = {"$regex": f".*{str(name)}.*", "$options": "i"}

        skip = (page - 1) * rpp
        cursor = ocpm_coll.find(filtro).sort("name", 1).skip(skip).limit(rpp)

        items: list[OCPMOutList] = [OCPMOutList.from_raw(doc) for doc in cursor]
        total = ocpm_coll.count_documents(filtro)
        total_pages = math.ceil(total / rpp) if rpp > 0 else 1

        return {
            "total": total,
            "pages": total_pages,
            "items": items,
        }

    # ========= GET BY ID =========
    @staticmethod
    def get_by_id(id: str) -> OCPMOutDetail:
        """
        Busca um OCP-M pelo ID.
        """
        oid = ensure_object_id(id)
        doc = ocpm_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("OCP-M não encontrado")

        return OCPMOutDetail.from_raw(doc)

    # ========= CREATE =========
    @staticmethod
    def create(contractor_id: UUID, payload: OCPMCreate) -> OCPMOutDetail:
        """
        Cria um novo OCP-M.
        """
        try:
            data = payload.model_dump()
            data["contractor_id"] = str(contractor_id)

            result = ocpm_coll.insert_one(data)
            created = ocpm_coll.find_one({"_id": result.inserted_id})
            return OCPMOutDetail.from_raw(created)

        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um OCP-M com este nome")

    # ========= UPDATE =========
    @staticmethod
    def update(id: str, payload: OCPMUpdate) -> OCPMOutDetail:
        """
        Atualiza um OCP-M existente.
        """
        oid = ensure_object_id(id)
        data = payload.model_dump()

        try:
            updated = ocpm_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=True
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um OCP-M com este nome")

        if not updated:
            raise NotFoundError("OCP-M não encontrado")

        return OCPMOutDetail.from_raw(updated)

    # ========= DELETE =========
    @staticmethod
    def delete(id: str) -> bool:
        """
        Exclui um OCP-M.
        """
        oid = ensure_object_id(id)
        doc = ocpm_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("OCP-M não encontrado")

        result = ocpm_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("OCP-M não encontrado")

        return True
