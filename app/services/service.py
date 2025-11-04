from uuid import UUID
import math
import re
import requests
import json
from copy import deepcopy
from pymongo.errors import DuplicateKeyError
from typing import Any, Dict
from bson import ObjectId
from app.dataprovider.mongo.models.service import collection as service_coll
from app.dataprovider.mongo.models.service import get_service_detail
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
        doc = get_service_detail(id)
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
            created = get_service_detail(result.inserted_id)
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

        # Campos onde queremos aplicar a regra de mascarados
        sensitive_fields = ["headers"]

        for field in sensitive_fields:
            value = data.get(field)

            if value is not None:
                value_str = json.dumps(value)

                # Se contém **** descarta -> NÃO salva esse campo
                if "****" in value_str:
                    data.pop(field, None)
                else:
                    # Mantém o dict, NÃO transforma em string
                    data[field] = value

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

        updated = get_service_detail(oid)
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
        try:
            doc = service_coll.find_one({"_id": ObjectId(id)})
            if not doc:
                raise NotFoundError(f"Service com id={id} não encontrado")

            url = doc.get("url")
            method = doc.get("method", "GET").upper()
            raw_headers = doc.get("headers", {})
            headers = {}

            if isinstance(raw_headers, dict):
                if "name" in raw_headers and "value" in raw_headers:
                    headers[raw_headers["name"]] = raw_headers["value"]
                else:
                    headers = raw_headers

            elif isinstance(raw_headers, list):
                for h in raw_headers:
                    if isinstance(h, dict) and "name" in h and "value" in h:
                        headers[h["name"]] = h["value"]

            body = {}

            authenticator_id = doc.get("authenticator", {}).get("id")
            if authenticator_id:
                auth_doc = auth_coll.find_one({"_id": ObjectId(authenticator_id)})
                if not auth_doc:
                    raise NotFoundError(f"Authenticator com id={authenticator_id} não encontrado")

                response_map = auth_doc.get("response_map", {}) or {}
                auth_response = AuthenticatorService.execute(authenticator_id)
                ServiceService._inject_response_map_into_headers(headers, response_map, auth_response)

            # NProcessamento do input_schema
            url, body = ServiceService._apply_input_schema(
                doc.get("input_schema") or [],
                url,
                body,
                inputs or {}
            )

            response = requests.request(method, url, headers=headers, json=body if body else None)
            response.raise_for_status()

            try:
                return response.json()
            except ValueError:
                return {"status": "success", "response": response.text}

        except NotFoundError as e:
            return {"status": "error", "message": str(e)}

        except BadRequestError as e:
            return {"status": "error", "message": str(e)}

        except requests.HTTPError as e:
            return {
                "status": "error",
                "message": f"Erro HTTP {e.response.status_code}: {e.response.reason}",
                "url": url,
                "method": method,
            }

        except Exception as e:
            return {"status": "error", "message": f"Erro inesperado: {str(e)}"}

    # ===================================================================================
    @staticmethod
    def _apply_input_schema(input_schema: list, url: str, body: dict, inputs: dict):
        """
        Novo engine de input_schema suportando:
        - location: PATH | QUERY | BODY
        - input_mode: fixed | external
        - defaults
        - body completo ($)
        - paths JSON: $.a.b.c
        """

        final_body = deepcopy(body)
        query_params = {}

        for field in input_schema:
            name = field.get("name")
            location = field.get("location")
            input_mode = field.get("input_mode", "external")
            required = field.get("required", False)
            default = field.get("default")
            json_path = field.get("path")

            user_value = inputs.get(name)

            # Lógica do input_mode
            if input_mode == "fixed":
                value = default
            else:
                if user_value is not None:
                    value = user_value
                elif required and default is None:
                    raise BadRequestError(f"Campo '{name}' é obrigatório")
                else:
                    value = default

            # -------- PATH --------
            if location == "PATH":
                if value is None:
                    raise BadRequestError(f"Valor para '{name}' obrigatório para PATH")

                url = re.sub(fr":{name}\b", str(value), url)
                url = re.sub(fr"\{{{name}\}}", str(value), url)

            # -------- QUERY --------
            elif location == "QUERY":
                if value is not None:
                    query_params[name] = value

            # -------- BODY --------
            elif location == "BODY":
                if json_path == "$":  # body inteiro
                    if not isinstance(value, dict):
                        raise BadRequestError(f"O campo '{name}' com path '$' deve ser um objeto")
                    final_body = value
                else:
                    if value is not None:
                        keys = json_path.replace("$.", "").split(".")
                        ref = final_body
                        for k in keys[:-1]:
                            if k not in ref or not isinstance(ref[k], dict):
                                ref[k] = {}
                            ref = ref[k]
                        ref[keys[-1]] = value

        # aplica querystring
        if query_params:
            qs = "&".join(f"{k}={v}" for k, v in query_params.items())
            url += ("&" if "?" in url else "?") + qs

        return url, final_body

    # ===================================================================================
    @staticmethod
    def _inject_response_map_into_headers(headers: dict, response_map: dict, auth_response: dict):
        for header_name, expr in response_map.items():
            final_value = expr
            matches = re.findall(r'\$\.[\w.]+', expr)
            for match in matches:
                value = ServiceService._resolve_jsonpath(auth_response, match)
                if value is not None:
                    final_value = final_value.replace(match, str(value))
            headers[header_name] = final_value

    # ===================================================================================
    @staticmethod
    def _resolve_jsonpath(data: dict, path: str):
        matches = re.findall(r'\$\.[\w.]+', path)
        final_value = path

        for m in matches:
            keys = m.replace("$.", "").split(".")
            value = data
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    value = None
                    break

            if value is not None:
                final_value = final_value.replace(m, str(value))

        if final_value == path and matches and len(matches) == 1 and path.strip() == matches[0]:
            return value

        return final_value