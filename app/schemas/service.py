from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, RootModel


# ======== MODELOS INTERNOS ========

class HeaderModel(BaseModel):
    name: str
    value: str


class InputSchemaModel(BaseModel):
    type: str = Field(..., description="Tipo do schema, normalmente 'object'")
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ["object"]:
            raise ValueError("input_schema.type deve ser 'object'")
        return v


# ======== MODELOS BASE ========

class ServiceBase(BaseModel):
    name: str = Field(..., max_length=150)
    description: Optional[str] = None
    url: str
    method: str = Field(..., pattern="^(GET|POST|PUT|DELETE|PATCH)$")
    headers: List[HeaderModel] = Field(default_factory=list)
    authenticator_id: Optional[str] = Field(default=None, description="Referência ao authenticator")
    input_schema: Optional[InputSchemaModel] = None

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
    url: str
    method: str
    authenticator_id: Optional[str] = None

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["ServiceOutList"]:
        if not doc:
            return None
        return cls(
            id=str(doc.get("_id")),
            name=doc.get("name"),
            url=doc.get("url"),
            method=doc.get("method"),
            authenticator_id=doc.get("authenticator_id")
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
