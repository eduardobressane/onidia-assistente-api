from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ======== MODELOS INTERNOS ========

class HeaderModel(BaseModel):
    name: str = Field(..., description="Nome do cabeçalho HTTP")
    value: str = Field(..., description="Valor do cabeçalho HTTP")


class SchemaProperty(BaseModel):
    type: str = Field(..., description="Tipo do campo (ex: string, number, object, etc.)")
    pattern: Optional[str] = Field(None, description="Expressão regular de validação, se aplicável")


class InputSubSchema(BaseModel):
    """Representa uma seção do schema (path, query ou body)"""
    type: str = Field(..., description="Deve ser sempre 'object'")
    properties: Dict[str, SchemaProperty] = Field(default_factory=dict)
    required: Optional[List[str]] = Field(default_factory=list)


class InputSchemaModel(BaseModel):
    """Schema completo de entrada conforme o padrão JSON Schema"""
    type: str = Field(..., description="Deve ser sempre 'object'")
    properties: Dict[str, InputSubSchema] = Field(
        ..., description="Contém os blocos path, query e body"
    )
    required: Optional[List[str]] = Field(default_factory=list)

    @field_validator("properties", mode="before")
    @classmethod
    def ensure_properties_dict(cls, v):
        if not isinstance(v, dict):
            raise ValueError("properties deve ser um objeto (dict)")
        return v


# ======== MODELOS BASE ========

class ServiceBase(BaseModel):
    name: str = Field(..., max_length=150, description="Nome do serviço")
    description: Optional[str] = Field(None, description="Descrição do serviço")
    url: str = Field(..., description="URL do endpoint externo")
    method: str = Field(..., pattern="^(GET|POST|PUT|DELETE|PATCH)$", description="Método HTTP (GET, POST, etc.)")
    headers: List[HeaderModel] = Field(default_factory=list, description="Cabeçalhos HTTP")
    authenticator_id: Optional[str] = Field(None, description="ID do autenticador associado")
    input_schema: Optional[InputSchemaModel] = Field(
        None,
        description="Schema de entrada detalhado (path/query/body) ou null",
    )

    @field_validator("headers", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("headers deve ser uma lista")
        return v


# ======== CREATE / UPDATE ========

class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(ServiceBase):
    pass


# ======== OUTPUT LIST ========

class ServiceOutList(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    url: str
    method: str

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
        )


# ======== OUTPUT DETAIL ========

class ServiceOutDetail(ServiceBase):
    id: str

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["ServiceOutDetail"]:
        if not doc:
            return None

        import copy
        data = copy.deepcopy(doc)

        # 🔹 Oculta valores dos headers
        try:
            if "headers" in data and isinstance(data["headers"], list):
                masked_headers = []
                for h in data["headers"]:
                    if isinstance(h, dict):
                        masked_headers.append({
                            "name": h.get("name"),
                            "value": "****" if "value" in h else None
                        })
                    else:
                        masked_headers.append(h)
                data["headers"] = masked_headers
        except Exception:
            pass

        return cls(
            id=str(data.get("_id")),
            name=data.get("name"),
            description=data.get("description"),
            url=data.get("url"),
            method=data.get("method"),
            headers=data.get("headers", []),
            authenticator_id=data.get("authenticator_id"),
            input_schema=data.get("input_schema"),
        )
