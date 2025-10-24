from bson import ObjectId
from decimal import Decimal
from datetime import date, time, datetime
from urllib.parse import urlparse

from app.core.exceptions.types import NotFoundError, BusinessDomainError

from app.dataprovider.mongo.models.credential_type import collection as credential_type_coll

class ValidateCredentialsUtils:

    @staticmethod
    def validate_credentials(credential_type_id: str, credentials: dict) -> dict:
        # Valida o payload.credentials de acordo com o credential_type.scope.fields
        credential_type = credential_type_coll.find_one({"_id": ObjectId(credential_type_id), "enabled": True})
        if not credential_type:
            raise NotFoundError("Tipo de credencial não encontrado ou desabilitado")

        expected_fields = {f["name"]: f for f in credential_type.get("scope", {}).get("fields", [])}

        return ValidateCredentialsUtils._validate_credentials(expected_fields, credentials)

    @staticmethod
    def _validate_credentials(expected_fields: dict, credentials: dict) -> dict:
        validated_credentials = {}

        # Validar todos os campos esperados
        for name, field in expected_fields.items():
            value = credentials.get(name)

            if value is None:
                if field.get("required") and field.get("value") is None:
                    raise BusinessDomainError(f"Campo obrigatório '{name}' não informado")
                value = field.get("value")

            field_type = field.get("field_type")

            # --- Validação por tipo (sempre acontece, com valor informado ou default) ---
            if field_type == "string":
                if not isinstance(value, str):
                    raise BusinessDomainError(f"Campo '{name}' deve ser string")

            elif field_type == "integer":
                if not isinstance(value, int):
                    raise BusinessDomainError(f"Campo '{name}' deve ser inteiro")

            elif field_type == "decimal":
                if not isinstance(value, (float, Decimal, int)):
                    raise BusinessDomainError(f"Campo '{name}' deve ser decimal")
                value = Decimal(str(value))  # normaliza para Decimal

            elif field_type == "boolean":
                if not isinstance(value, bool):
                    raise BusinessDomainError(f"Campo '{name}' deve ser booleano")

            elif field_type == "date":
                if isinstance(value, str):
                    try:
                        value = date.fromisoformat(value)
                    except Exception:
                        raise BusinessDomainError(f"Campo '{name}' deve ser uma data válida (YYYY-MM-DD)")
                elif not isinstance(value, date):
                    raise BusinessDomainError(f"Campo '{name}' deve ser uma data")

            elif field_type == "time":
                if isinstance(value, str):
                    try:
                        value = time.fromisoformat(value)
                    except Exception:
                        raise BusinessDomainError(f"Campo '{name}' deve ser uma hora válida (HH:MM[:SS])")
                elif not isinstance(value, time):
                    raise BusinessDomainError(f"Campo '{name}' deve ser uma hora")

            elif field_type == "datetime":
                if isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value)
                    except Exception:
                        raise BusinessDomainError(f"Campo '{name}' deve ser um datetime válido (YYYY-MM-DDTHH:MM:SS)")
                elif not isinstance(value, datetime):
                    raise BusinessDomainError(f"Campo '{name}' deve ser um datetime")

            elif field_type == "url":
                if not isinstance(value, str):
                    raise BusinessDomainError(f"Campo '{name}' deve ser uma URL (string)")
                parsed = urlparse(value)
                if not parsed.scheme or not parsed.netloc:
                    raise BusinessDomainError(f"Campo '{name}' deve ser uma URL válida")

            else:
                raise BusinessDomainError(f"Tipo de campo '{field_type}' não suportado para '{name}'")

            validated_credentials[name] = value

        # Garantir que não vieram extras
        for key in credentials.keys():
            if key not in expected_fields:
                raise BusinessDomainError(f"Campo extra '{key}' não permitido")

        return validated_credentials
