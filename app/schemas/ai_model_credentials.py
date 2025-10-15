from typing import Optional, Union, Dict, Any
from pydantic import BaseModel, Field, Json
from bson import ObjectId


class AiModelCredentialsBase(BaseModel):
    description: str = Field(..., max_length=150)
    credentials: Union[Dict[str, Any], list]
    enabled: bool = Field(default=True)


class AiModelCredentialsCreate(AiModelCredentialsBase):
    pass


class AiModelCredentialsUpdate(AiModelCredentialsBase):
    pass


class AiModelCredentialsOutInternal(AiModelCredentialsBase):
    id: str
    ai_model_id: Optional[str] = None
    contractor_id: Optional[str] = None

    @classmethod
    def from_raw(cls, doc: Union[dict, "AiModelCredentialsOutInternal"]) -> Optional["AiModelCredentialsOutInternal"]:
        if not doc:
            return None
        if isinstance(doc, cls):
            return doc

        return cls(
            id=str(doc["_id"]) if isinstance(doc.get("_id"), (ObjectId, str)) else str(doc.get("_id")),
            description=doc.get("description"),
            credentials=doc.get("credentials"),
            enabled=doc.get("enabled", True),
            ai_model_id=doc.get("ai_model_id"),
            contractor_id=doc.get("contractor_id"),
        )


class AiModelCredentialsOutList(BaseModel):
    id: str
    description: Optional[str] = None
    enabled: bool = True

    @classmethod
    def from_raw(cls, doc: Union[dict, "AiModelCredentialsOutList"]) -> Optional["AiModelCredentialsOutList"]:
        if not doc:
            return None
        if isinstance(doc, cls):
            return doc
        return cls(
            id=str(doc["_id"]) if isinstance(doc.get("_id"), (ObjectId, str)) else str(doc.get("_id")),
            description=doc.get("description"),
            enabled=doc.get("enabled", True),
        )


class AiModelCredentialsOutDetail(AiModelCredentialsBase):
    id: str

    @classmethod
    def from_raw(cls, doc: Union[dict, "AiModelCredentialsOutDetail"]) -> Optional["AiModelCredentialsOutDetail"]:
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
