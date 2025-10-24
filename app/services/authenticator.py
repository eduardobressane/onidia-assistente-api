from uuid import UUID
import math
from pymongo.errors import DuplicateKeyError
from app.dataprovider.mongo.models.authenticator import collection as auth_coll
from app.schemas.authenticator import (
    AuthenticatorCreate,
    AuthenticatorUpdate,
    AuthenticatorOutList,
    AuthenticatorOutDetail,
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError
from app.core.utils.mongo import ensure_object_id


class AuthenticatorService:

    @staticmethod
    def get_all(contractor_id: UUID, name: str = None, page: int = 1, rpp: int = 10) -> dict:
        """
        Lista todos os Authenticators com paginação e filtro opcional por nome.
        """
        filtro = {"contractor_id": str(contractor_id)}

        if name and str(name).strip() != "":
            filtro["name"] = {"$regex": f".*{str(name)}.*", "$options": "i"}

        skip = (page - 1) * rpp
        cursor = auth_coll.find(filtro).sort("name", 1).skip(skip).limit(rpp)

        items: list[AuthenticatorOutList] = [AuthenticatorOutList.from_raw(doc) for doc in cursor]
        total = auth_coll.count_documents(filtro)
        total_pages = math.ceil(total / rpp) if rpp > 0 else 1

        return {
            "total": total,
            "pages": total_pages,
            "items": items,
        }

    @staticmethod
    def get_by_id(id: str) -> AuthenticatorOutDetail:
        """
        Busca um authenticator pelo ID.
        """
        oid = ensure_object_id(id)
        doc = auth_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Authenticator não encontrado")

        return AuthenticatorOutDetail.from_raw(doc)

    @staticmethod
    def create(contractor_id: UUID, payload: AuthenticatorCreate) -> AuthenticatorOutDetail:
        """
        Cria um novo authenticator.
        """
        try:
            data = payload.model_dump()
            data["contractor_id"] = str(contractor_id)

            result = auth_coll.insert_one(data)
            created = auth_coll.find_one({"_id": result.inserted_id})
            return AuthenticatorOutDetail.from_raw(created)

        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um authenticator com este nome")

    @staticmethod
    def update(id: str, payload: AuthenticatorUpdate) -> AuthenticatorOutDetail:
        """
        Atualiza um authenticator existente.
        """
        oid = ensure_object_id(id)
        data = payload.model_dump()

        try:
            updated = auth_coll.find_one_and_update(
                {"_id": oid},
                {"$set": data},
                return_document=True
            )
        except DuplicateKeyError:
            raise DuplicateKeyDomainError("Já existe um authenticator com este nome")

        if not updated:
            raise NotFoundError("Authenticator não encontrado")

        return AuthenticatorOutDetail.from_raw(updated)

    @staticmethod
    def delete(id: str) -> bool:
        """
        Exclui um authenticator.
        """
        oid = ensure_object_id(id)
        doc = auth_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Authenticator não encontrado")

        result = auth_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Authenticator não encontrado")

        return True
