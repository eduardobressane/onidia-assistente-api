from typing import Optional, List, Literal
from pydantic import BaseModel, Field

class TagBase(BaseModel):
    name: str = Field(..., max_length=150)
    enabled: bool = Field(default=True)

class TagCreate(TagBase):
    tag_type: Literal["agent"] = Field(...)

class TagUpdate(TagBase):
    pass

class TagOutList(TagBase):
    id: str

    @classmethod
    def from_raw(cls, doc: dict) -> "TagOutList":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            enabled=doc.get("enabled", True)
        )

class TagOutDetail(TagBase):
    id: str

    @classmethod
    def from_raw(cls, doc: dict) -> "TagOutDetail":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            enabled=doc.get("enabled", True)
        )
