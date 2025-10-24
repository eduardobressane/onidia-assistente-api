from typing import Optional, Union, Dict, Any
from pydantic import BaseModel, Field, Json
from bson import ObjectId


class CredentialBase(BaseModel):
    description: str = Field(..., max_length=150)
    credentials: Union[Dict[str, Any], list]
    enabled: bool = Field(default=True)


class CredentialCreate(CredentialBase):
    pass


class CredentialUpdate(CredentialBase):
    pass


class CredentialOutInternal(CredentialBase):
    id: str
    credential_type_id: Optional[str] = None
    contractor_id: Optional[str] = None

    @classmethod
    def from_raw(cls, doc: Union[dict, "CredentialOutInternal"]) -> Optional["CredentialOutInternal"]:
        if not doc:
            return None
        if isinstance(doc, cls):
            return doc

        return cls(
            id=str(doc["_id"]) if isinstance(doc.get("_id"), (ObjectId, str)) else str(doc.get("_id")),
            description=doc.get("description"),
            credentials=doc.get("credentials"),
            enabled=doc.get("enabled", True),
            credential_type_id=doc.get("credential_type_id"),
            contractor_id=doc.get("contractor_id"),
        )


class CredentialOutList(BaseModel):
    id: str
    description: Optional[str] = None
    enabled: bool = True

    @classmethod
    def from_raw(cls, doc: Union[dict, "CredentialOutList"]) -> Optional["CredentialOutList"]:
        if not doc:
            return None
        if isinstance(doc, cls):
            return doc
        return cls(
            id=str(doc["_id"]) if isinstance(doc.get("_id"), (ObjectId, str)) else str(doc.get("_id")),
            description=doc.get("description"),
            enabled=doc.get("enabled", True),
        )


class CredentialOutDetail(CredentialBase):
    id: str

    @classmethod
    def from_raw(cls, doc: Union[dict, "CredentialOutDetail"]) -> Optional["CredentialOutDetail"]:
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
