from uuid import UUID
import math
from pymongo.errors import DuplicateKeyError
import requests
from app.dataprovider.mongo.models.authenticator import collection as auth_coll
from app.schemas.authenticator import (
    AuthenticatorCreate,
    AuthenticatorUpdate,
    AuthenticatorOutList,
    AuthenticatorOutDetail,
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BadRequestError
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

    # ========= EXECUTE =========
    
    @staticmethod
    def execute(id: str) -> dict:
        doc = auth_coll.find_one({"_id": ensure_object_id(id)})
        if not doc:
            raise NotFoundError("Authenticator não encontrado")

        url = doc.get("url")
        method = doc.get("method", "GET").upper()

        raw_headers = doc.get("headers", {})

        # ✅ Compatível com o novo formato (dict) e com legacy (lista)
        if isinstance(raw_headers, dict):
            headers = {k: v for k, v in raw_headers.items()}
        elif isinstance(raw_headers, list):
            headers = {h["name"]: h["value"] for h in raw_headers if isinstance(h, dict)}
        else:
            headers = {}

        body = doc.get("body", {})
        response_map = doc.get("response_map", {})

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body else None,
                timeout=15
            )

            response.raise_for_status()

            try:
                resp_json = response.json()
            except Exception:
                resp_json = {"raw": response.text}

            # ===== função auxiliar de path =====
            def get_value_by_path(source, path: str):
                import re
                value = source
                parts = re.split(r'\.(?![^\[]*\])', path)
                for part in parts:
                    match = re.match(r'([^\[]+)\[(\d+)\]', part)
                    if match:
                        key, index = match.groups()
                        value = value.get(key) if isinstance(value, dict) else None
                        if isinstance(value, list):
                            idx = int(index)
                            value = value[idx] if idx < len(value) else None
                        else:
                            return None
                    else:
                        value = value.get(part) if isinstance(value, dict) else None

                    if value is None:
                        return None
                return value

            mapped = {}
            if response_map:
                for key, path in response_map.items():
                    if path and path.startswith("$response."):
                        field_path = path.replace("$response.", "")
                        mapped[key] = get_value_by_path(resp_json, field_path)
                    else:
                        mapped[key] = None

            return {
                "success": True,
                "status": response.status_code,
                "response": mapped if any(mapped.values()) else resp_json,
            }

        except requests.exceptions.Timeout:
            raise BadRequestError("Timeout ao executar o authenticator")

        except requests.exceptions.ConnectionError:
            raise BadRequestError("Falha de conexão ao executar o authenticator")

        except requests.exceptions.HTTPError as e:
            raise BadRequestError(f"Erro HTTP {e.response.status_code}: {e.response.text}")

        except Exception as e:
            raise BadRequestError(f"Erro ao executar authenticator: {str(e)}")

