from typing import Optional, Union, Dict, Any
from pydantic import BaseModel, Field, Json
from bson import ObjectId


class ToolCredentialsBase(BaseModel):
    description: str = Field(..., max_length=150)
    credentials: Union[Dict[str, Any], list]
    enabled: bool = Field(default=True)


class ToolCredentialsCreate(ToolCredentialsBase):
    pass


class ToolCredentialsUpdate(ToolCredentialsBase):
    pass


class ToolCredentialsInternal(ToolCredentialsBase):
    id: str
    tool_id: Optional[str] = None
    contractor_id: Optional[str] = None

    @classmethod
    def from_raw(cls, doc: Union[dict, "ToolCredentialsInternal"]) -> Optional["ToolCredentialsInternal"]:
        if not doc:
            return None
        if isinstance(doc, cls):
            return doc

        return cls(
            id=str(doc["_id"]) if isinstance(doc.get("_id"), (ObjectId, str)) else str(doc.get("_id")),
            description=doc.get("description"),
            credentials=doc.get("credentials"),
            enabled=doc.get("enabled", True),
            tool_id=doc.get("tool_id"),
            contractor_id=doc.get("contractor_id"),
        )


class ToolCredentialsOutList(BaseModel):
    id: str
    description: Optional[str] = None
    enabled: bool = True

    @classmethod
    def from_raw(cls, doc: Union[dict, "ToolCredentialsOutList"]) -> Optional["ToolCredentialsOutList"]:
        if not doc:
            return None
        if isinstance(doc, cls):
            return doc
        return cls(
            id=str(doc["_id"]) if isinstance(doc.get("_id"), (ObjectId, str)) else str(doc.get("_id")),
            description=doc.get("description"),
            enabled=doc.get("enabled", True),
        )


class ToolCredentialsOutDetail(ToolCredentialsBase):
    id: str

    @classmethod
    def from_raw(cls, doc: Union[dict, "ToolCredentialsOutDetail"]) -> Optional["ToolCredentialsOutDetail"]:
        if not doc:
            return None
        if isinstance(doc, cls):
            return doc

        return cls(
            id=str(doc["_id"]) if isinstance(doc.get("_id"), (ObjectId, str)) else str(doc.get("_id")),
            description=doc.get("description"),
            credentials=doc.get("credentials"),
            enabled=doc.get("enabled", True),
        )
