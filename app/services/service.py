from uuid import UUID
import math
import re
import requests
from pymongo.errors import DuplicateKeyError
from app.dataprovider.mongo.models.service import collection as service_coll
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceOutList,
    ServiceOutDetail,
)
from app.core.exceptions.types import NotFoundError, DuplicateKeyDomainError, BadRequestError
from app.core.utils.mongo import ensure_object_id
from app.services.authenticator import AuthenticatorService


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
        cursor = service_coll.find(filtro).sort("name", 1).skip(skip).limit(rpp)

        items: list[ServiceOutList] = [ServiceOutList.from_raw(doc) for doc in cursor]
        total = service_coll.count_documents(filtro)
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
        doc = service_coll.find_one({"_id": oid})

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

            result = service_coll.insert_one(data)
            created = service_coll.find_one({"_id": result.inserted_id})
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
            updated = service_coll.find_one_and_update(
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
        doc = service_coll.find_one({"_id": oid})

        if not doc:
            raise NotFoundError("Serviço não encontrado")

        result = service_coll.delete_one({"_id": oid})

        if result.deleted_count == 0:
            raise NotFoundError("Serviço não encontrado")

        return True

    @staticmethod
    def execute(id: str, inputs: dict = None) -> dict:
        """
        Executa um Service configurado.
        - Lê o input_schema para validar e preencher variáveis (ex: {cnpj} ou :cnpj na URL).
        - Se houver authenticator_id, executa o Authenticator antes
          e injeta no header os valores retornados do response_map.
        - Executa a requisição HTTP e retorna a resposta.
        """
        # ====== BUSCA O SERVICE NO BANCO ======
        doc = service_coll.find_one({"_id": ensure_object_id(id)})
        if not doc:
            raise NotFoundError("Service não encontrado")

        url = doc.get("url")
        method = doc.get("method", "GET").upper()
        headers = {h["name"]: h["value"] for h in doc.get("headers", [])}
        body = doc.get("body", {})
        response_map = doc.get("response_map", {})
        authenticator_id = doc.get("authenticator_id")
        input_schema = doc.get("input_schema", {})
        inputs = inputs or {}

        # ====== VALIDA INPUT_SCHEMA ======
        required = input_schema.get("required", [])
        props = input_schema.get("properties", {})

        # Valida obrigatórios
        missing = [field for field in required if field not in inputs]
        if missing:
            raise BadRequestError(f"Campos obrigatórios ausentes: {', '.join(missing)}")

        # Valida pattern e tipo básico
        for key, meta in props.items():
            if key not in inputs:
                continue
            value = inputs[key]
            if meta.get("type") == "string" and not isinstance(value, str):
                raise BadRequestError(f"O campo '{key}' deve ser string.")
            if pattern := meta.get("pattern"):
                if not re.match(pattern, str(value)):
                    raise BadRequestError(f"O campo '{key}' não segue o padrão esperado.")

        # ====== SUBSTITUI VARIÁVEIS NA URL ======
        for key, val in inputs.items():
            # Aceita {cnpj} ou :cnpj
            url = url.replace(f"{{{key}}}", str(val)).replace(f":{key}", str(val))

        # ====== ETAPA OPCIONAL: EXECUTA AUTHENTICATOR ======
        def get_value_by_path(source, path: str):
            """Navega em estruturas aninhadas tipo $.data.token"""
            value = source
            if not path or not isinstance(path, str):
                return None
            if path.startswith("$."):
                path = path[2:]

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

        if authenticator_id:
            try:
                auth_result = AuthenticatorService.execute(str(authenticator_id))
                auth_response = auth_result.get("response", {})
            except Exception as e:
                raise BadRequestError(f"Falha ao executar authenticator: {str(e)}")

            for key, path in (response_map or {}).items():
                if isinstance(path, str) and path.startswith("$."):
                    value = get_value_by_path(auth_response, path)
                    if value is not None:
                        headers[key] = str(value)

        # ====== EXECUTA O SERVICE PRINCIPAL ======
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

            return {
                "success": True,
                "status_code": response.status_code,
                "response": resp_json,
            }

        except requests.exceptions.Timeout:
            raise BadRequestError("Timeout ao executar o service")

        except requests.exceptions.ConnectionError:
            raise BadRequestError("Falha de conexão ao executar o service")

        except requests.exceptions.HTTPError as e:
            raise BadRequestError(f"Erro HTTP {e.response.status_code}: {e.response.text}")

        except Exception as e:
            raise BadRequestError(f"Erro ao executar service: {str(e)}")
