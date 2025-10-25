import os
from dotenv import load_dotenv

from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict

URL_BASE_IMG_PUBLIC = os.getenv("URL_BASE_IMG_PUBLIC")

class ScopeField(BaseModel):
    name: str = Field(...)
    description: Optional[str] = Field(None)
    field_type: Literal["string", "integer", "decimal", "date", "datetime", "url"] = Field(...)
    required: bool = Field(...)
    tip: Optional[str] = Field(None)
    value: Optional[str] = Field(None)

class Scope(BaseModel):
    fields: List[ScopeField]

class CredentialTypeBase(BaseModel):
    name: str = Field(..., max_length=150)
    kind: Literal["ai_models", "tools"] = Field(...)
    enabled: bool = Field(default=True)

# Create e Update
class CredentialTypeCreate(CredentialTypeBase):
    scope: Optional[Scope] = None

class CredentialTypeUpdate(CredentialTypeBase):
    scope: Optional[Scope] = None

class CredentialTypeOutList(CredentialTypeBase):
    id: str
    image: Optional[str]

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_raw(cls, doc: dict) -> "CredentialTypeOutList":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            kind=doc.get("kind"),
            image=f"{URL_BASE_IMG_PUBLIC}/credentials_types/{doc.get('_id')}" if doc.get("has_image") else None,
            enabled=doc.get("enabled", True)
        )

class CredentialTypeOutDetail(CredentialTypeBase):
    id: str
    image: Optional[str]
    scope: Optional[Scope] = None

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_raw(cls, doc: dict) -> "CredentialTypeOutDetail":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            kind=doc.get("kind"),
            image=f"{URL_BASE_IMG_PUBLIC}/credentials_types/{doc.get('_id')}" if doc.get("has_image") else None,
            enabled=doc.get("enabled", True),
            scope=doc.get("scope")
        )
