from typing import Optional, List, Literal
from pydantic import BaseModel, Field

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=150)
    enabled: bool = Field(default=True)

class CategoryCreate(CategoryBase):
    category_type: Literal["agent"] = Field(...)

class CategoryUpdate(CategoryBase):
    pass

class CategoryOutList(CategoryBase):
    id: str

    @classmethod
    def from_raw(cls, doc: dict) -> "CategoryOutList":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            enabled=doc.get("enabled", True)
        )

class CategoryOutDetail(CategoryBase):
    id: str

    @classmethod
    def from_raw(cls, doc: dict) -> "CategoryOutDetail":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            enabled=doc.get("enabled", True)
        )
