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

class ToolBase(BaseModel):
    name: str = Field(..., max_length=150)
    enabled: bool = Field(default=True)

class ToolCreate(ToolBase):
    scope: Optional[Scope] = None

class ToolUpdate(ToolBase):
    scope: Optional[Scope] = None

class ToolOutList(ToolBase):
    id: str

    @classmethod
    def from_raw(cls, doc: dict) -> "ToolOutList":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            enabled=doc.get("enabled", True)
        )

class ToolOutDetail(ToolBase):
    id: str
    scope: Optional[Scope] = None

    @classmethod
    def from_raw(cls, doc: dict) -> "ToolOutDetail":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            enabled=doc.get("enabled", True),
            scope=doc.get("scope")
        )
