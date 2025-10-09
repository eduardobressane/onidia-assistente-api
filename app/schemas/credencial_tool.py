from typing import Any, Optional, Union
from pydantic import BaseModel, Field
from uuid import UUID
from bson import ObjectId


class CredencialToolBase(BaseModel):
    descricao: str = Field(..., max_length=150)
    credencial: Any
    ativo: bool = True


class CredencialToolCreate(CredencialToolBase):
    pass


class CredencialToolUpdate(CredencialToolBase):
    pass


class CredencialToolOut(CredencialToolBase):
    id: str

    @classmethod
    def from_raw(cls, doc: Union[dict, "CredencialToolOut"]) -> Optional["CredencialToolOut"]:
        if not doc:
            return None
        if isinstance(doc, cls):  # já é um modelo
            return doc

        return cls(
            id=str(doc["_id"]) if isinstance(doc.get("_id"), (ObjectId, str)) else str(doc.get("_id")),
            descricao=doc.get("descricao"),
            credencial=doc.get("credencial"),
            ativo=doc.get("ativo", True),
        )
