from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ValidationInfo, field_validator


# ======== NOVO SCHEMA DE INPUT (LISTA) ========

class Authenticator(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None

class InputFieldModel(BaseModel):
    name: str = Field(..., description="Nome do campo")
    location: str = Field(..., pattern="^(PATH|QUERY|BODY)$", description="Onde o campo será inserido (PATH, QUERY, BODY)")
    type: str = Field(..., description="Tipo do campo (string, number, object, etc.)")
    required: bool = Field(default=False, description="Se o campo é obrigatório")
    input_mode: str = Field(..., pattern="^(external|fixed)$", description="Origem do valor (external = enviado pelo usuário, fixed = valor interno)")

    # campos opcionais
    description: Optional[str] = None
    default: Optional[Any] = Field(None, description="Valor default")
    path: Optional[str] = Field(None, description="Caminho JSON quando enviado no BODY (ex: $.user.id)")

    @field_validator("path")
    def validate_path(cls, v, info: ValidationInfo):
        location = info.data.get("location")
        if location == "BODY" and v is not None:
            raise ValueError("Path deve ser nulo quando location é BODY")
        return v


# ======== MODELOS BASE ========

class ServiceBase(BaseModel):
    name: str = Field(..., max_length=150, description="Nome do serviço")
    description: Optional[str] = Field(None, description="Descrição do serviço")
    url: str = Field(..., description="URL do endpoint externo")
    method: str = Field(..., pattern="^(GET|POST|PUT|DELETE|PATCH)$", description="Método HTTP")
    enabled: bool = Field(default=True)
    headers: Dict[str, Any] = Field(default_factory=dict)

    # NOVO SCHEMA
    input_schema: Optional[List[InputFieldModel]] = Field(
        None,
        description="Lista de campos de entrada do serviço (PATH, QUERY, BODY)"
    )

    @field_validator("headers", mode="before")
    @classmethod
    def ensure_dict(cls, v):
        if v in (None, []):
            return {}
        if not isinstance(v, dict):
            raise ValueError("headers deve ser um dicionário")
        return v


# ======== CREATE / UPDATE ========

class AuthenticatorCreateOrUpdate(BaseModel):
    id: str = Field(..., description="ID do autenticador associado")

class ServiceCreate(ServiceBase):
    authenticator: Optional[AuthenticatorCreateOrUpdate] = Field(None)
    pass


class ServiceUpdate(ServiceBase):
    authenticator: Optional[AuthenticatorCreateOrUpdate] = Field(None)
    pass


# ======== OUTPUT LIST ========

class ServiceOutList(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    url: str
    method: str
    enabled: bool = True

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["ServiceOutList"]:
        if not doc:
            return None
        return cls(
            id=str(doc.get("_id")),
            name=doc.get("name"),
            description=doc.get("description"),
            url=doc.get("url"),
            method=doc.get("method"),
            enabled=doc.get("enabled", True),
        )


# ======== OUTPUT DETAIL ========

class ServiceOutDetail(ServiceBase):
    id: str
    authenticator: Optional[Authenticator]

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["ServiceOutDetail"]:
        if not doc:
            return None

        import copy
        data = copy.deepcopy(doc)

        # Oculta valores sensíveis dos headers
        try:
            if isinstance(data.get("headers"), dict):
                data["headers"] = {k: "****" for k in data.get("headers", {}).keys()}
        except Exception:
            pass

        return cls(
            id=str(data.get("_id")),
            name=data.get("name"),
            description=data.get("description"),
            url=data.get("url"),
            method=data.get("method"),
            enabled=data.get("enabled", True),
            headers=data.get("headers", {}),
            authenticator=data.get("authenticator"),
            input_schema=data.get("input_schema"),
        )
