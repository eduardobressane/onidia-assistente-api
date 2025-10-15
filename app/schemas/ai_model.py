from typing import Optional, List, Literal
from pydantic import BaseModel, Field

class ScopeField(BaseModel):
    name: str = Field(...)
    description: Optional[str] = Field(None)
    field_type: Literal["string", "integer", "decimal", "date", "datetime", "url"] = Field(...)
    required: bool = Field(...)
    tip: Optional[str] = Field(None)
    value: Optional[str] = Field(None)

class Scope(BaseModel):
    fields: List[ScopeField]

class AiModelBase(BaseModel):
    name: str = Field(..., max_length=150)
    enabled: bool = Field(default=True)

# Create e Update
class AiModelCreate(AiModelBase):
    scope: Optional[Scope] = None

class AiModelUpdate(AiModelBase):
    scope: Optional[Scope] = None

class AiModelOutList(AiModelBase):
    id: str

    @classmethod
    def from_raw(cls, doc: dict) -> "AiModelOutList":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            enabled=doc.get("enabled", True)
        )

class AiModelOutDetail(AiModelBase):
    id: str
    scope: Optional[Scope] = None

    @classmethod
    def from_raw(cls, doc: dict) -> "AiModelOutDetail":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            enabled=doc.get("enabled", True),
            scope=doc.get("scope")
        )
