from uuid import UUID
import math
import re
import requests
from pymongo.errors import DuplicateKeyError
from typing import Any, Dict
from bson import ObjectId
from app.dataprovider.mongo.models.service import collection as service_coll
from app.dataprovider.mongo.models.authenticator import collection as auth_coll
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
    def execute(id: str, inputs: dict | None = None) -> dict:
        """
        Executa um Service configurado.
        - Busca o service no banco
        - Executa o Authenticator (se existir)
        - Lê o response_map do Authenticator e aplica nos headers
        - Interpreta o input_schema (path, body, query)
        - Executa a requisição final e retorna o resultado
        """
        try:
            # 1️⃣ Busca o documento do service
            doc = service_coll.find_one({"_id": ObjectId(id)})
            if not doc:
                raise NotFoundError(f"Service com id={id} não encontrado")

            url = doc.get("url")
            method = doc.get("method", "GET").upper()
            headers = {h["name"]: h["value"] for h in doc.get("headers", [])}
            body = doc.get("body", {}) or {}
            authenticator_id = doc.get("authenticator_id")

            # 2️⃣ Executa Authenticator se existir
            if authenticator_id:
                auth_doc = auth_coll.find_one({"_id": ObjectId(authenticator_id)})
                if not auth_doc:
                    raise NotFoundError(f"Authenticator com id={authenticator_id} não encontrado")

                response_map = auth_doc.get("response_map", {}) or {}
                try:
                    auth_response = AuthenticatorService.execute(authenticator_id)
                    ServiceService._inject_response_map_into_headers(
                        headers, response_map, auth_response
                    )
                except Exception as e:
                    raise BadRequestError(f"Falha ao executar authenticator: {str(e)}")

            # 3️⃣ Monta a requisição conforme input_schema
            if inputs:
                url, body = ServiceService._apply_input_schema(
                    doc.get("input_schema"), url, body, inputs
                )

            # 4️⃣ Executa requisição principal
            try:
                response = requests.request(method, url, headers=headers, json=body if body else None)
                response.raise_for_status()
                try:
                    return response.json()
                except ValueError:
                    return {"status": "success", "text": response.text}

            except requests.HTTPError as e:
                return {
                    "status": "error",
                    "message": f"Erro HTTP {e.response.status_code}: {e.response.reason}",
                    "url": url,
                    "method": method,
                }
            except requests.ConnectionError:
                return {"status": "error", "message": f"Falha de conexão ao acessar {url}"}
            except requests.Timeout:
                return {"status": "error", "message": f"Timeout ao acessar {url}"}
            except Exception as e:
                return {"status": "error", "message": f"Erro inesperado: {str(e)}"}

        except NotFoundError as e:
            return {"status": "error", "message": str(e)}
        except BadRequestError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Erro crítico na execução: {str(e)}"}

    # ======================================================================
    @staticmethod
    def _inject_response_map_into_headers(headers: dict, response_map: dict, auth_response: dict):
        """
        Interpreta o response_map do Authenticator e injeta valores nos headers.
        Exemplo:
            response_map = { "Authorization": "Bearer $.token" }
        """
        
        for header_name, expr in response_map.items():
            final_value = expr
            # Localiza tokens do tipo $.campo
            matches = re.findall(r'\$\.[\w.]+', expr)
            for match in matches:
                value = ServiceService._resolve_jsonpath(auth_response, match)
                if value is not None:
                    final_value = final_value.replace(match, str(value))
            headers[header_name] = final_value

    # ======================================================================
    @staticmethod
    def _resolve_jsonpath(data: dict, path: str) -> Any:
        """Resolve $.campo ou $.a.b.c dentro do JSON."""

        path = path.replace("$.", "$.response.") #Ajuste para o retorno de authenticator
        keys = path.strip("$.").split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    # ======================================================================
    @staticmethod
    def _apply_input_schema(input_schema: dict, url: str, body: dict, inputs: dict):
        """
        Interpreta input_schema (padrão MCP/FastMCP) para preencher URL e body.
        Suporta parâmetros de path nos formatos:
        - :param
        - {param}

        Exemplo:
            schema: { path: { cnpj: {...} } }
            url: /api/cnpj/:cnpj ou /api/cnpj/{cnpj}
            inputs: { path: { "cnpj": "12345678000199" } }
        """
        if not input_schema or not inputs:
            return url, body

        # 🔹 Path parameters
        path_vars = inputs.get("path", {})
        for k, v in path_vars.items():
            # Substitui :param e {param}
            url = re.sub(fr":{k}\b", str(v), url)
            url = re.sub(fr"\{{{k}\}}", str(v), url)

        # 🔹 Body parameters
        body_vars = inputs.get("body", {})
        if body_vars:
            body = body_vars

        # 🔹 Query parameters
        query_vars = inputs.get("query", {})
        if query_vars:
            query_string = "&".join([f"{k}={v}" for k, v in query_vars.items()])
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{query_string}"

        return url, body