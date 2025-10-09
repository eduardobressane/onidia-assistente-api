from typing import Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID

class CredencialModeloAiBase(BaseModel):
    descricao: str = Field(..., max_length=150)
    credencial: Any
    id_contratante: Optional[int] = None
    ativo: bool = True

class CredencialModeloAiCreate(CredencialModeloAiBase):
    pass

class CredencialModeloAiUpdate(CredencialModeloAiBase):
    pass

class CredencialModeloAiOut(CredencialModeloAiBase):
    id: int
    descricao: str
    credencial: Any
    id_contratante: Optional[int] = None
    ativo: bool = True

    class Config:
        from_attributes = True
        populate_by_name = True
        serialize_by_alias = True

    @classmethod
    def from_raw(cls, doc: dict) -> "CredencialToolOut":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            descricao=doc.get("descricao"),
            credencial=doc.get("credencial"),
            id_contratante=doc.get("id_contratante"),
            ativo=doc.get("ativo", True)
        )
