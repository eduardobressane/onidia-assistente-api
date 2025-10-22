from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict

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
    image: Optional[str]

    model_config = ConfigDict(populate_by_name=True, exclude_none=False)

    @classmethod
    def from_raw(cls, doc: dict) -> "AiModelOutList":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            image=f"http://blablabla/{doc.get('_id')}" if doc.get("has_image") else None,
            enabled=doc.get("enabled", True)
        )

class AiModelOutDetail(AiModelBase):
    id: str
    image: Optional[str]
    scope: Optional[Scope] = None

    model_config = ConfigDict(populate_by_name=True, exclude_none=False)

    @classmethod
    def from_raw(cls, doc: dict) -> "AiModelOutDetail":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            image=f"http://blablabla/{doc.get('_id')}" if doc.get("has_image") else None,
            enabled=doc.get("enabled", True),
            scope=doc.get("scope")
        )
