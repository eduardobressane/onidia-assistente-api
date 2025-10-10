from typing import Optional, Union, Dict, Any
from pydantic import BaseModel, Field, Json
from bson import ObjectId


class CredencialToolBase(BaseModel):
    descricao: str = Field(..., max_length=150)
    credencial: Union[Dict[str, Any], list]  # aceita objeto JSON ou lista JSON
    ativo: bool = Field(default=True)


class CredencialToolCreate(CredencialToolBase):
    pass


class CredencialToolUpdate(CredencialToolBase):
    pass


class CredencialToolInterna(CredencialToolBase):
    id: str
    id_tool: Optional[str] = None
    id_contratante: Optional[str] = None

    @classmethod
    def from_raw(cls, doc: Union[dict, "CredencialToolInterna"]) -> Optional["CredencialToolInterna"]:
        if not doc:
            return None
        if isinstance(doc, cls):
            return doc

        return cls(
            id=str(doc["_id"]) if isinstance(doc.get("_id"), (ObjectId, str)) else str(doc.get("_id")),
            descricao=doc.get("descricao"),
            credencial=doc.get("credencial"),
            ativo=doc.get("ativo", True),
            id_tool=doc.get("id_tool"),
            id_contratante=doc.get("id_contratante"),
        )


class CredencialToolOutList(BaseModel):   # listagem não mostra credencial
    id: str
    descricao: Optional[str] = None
    ativo: bool = True

    @classmethod
    def from_raw(cls, doc: Union[dict, "CredencialToolOutList"]) -> Optional["CredencialToolOutList"]:
        if not doc:
            return None
        if isinstance(doc, cls):
            return doc
        return cls(
            id=str(doc["_id"]) if isinstance(doc.get("_id"), (ObjectId, str)) else str(doc.get("_id")),
            descricao=doc.get("descricao"),
            ativo=doc.get("ativo", True),
        )


class CredencialToolOutDetail(CredencialToolBase):  # exibe a credencial
    id: str

    @classmethod
    def from_raw(cls, doc: Union[dict, "CredencialToolOutDetail"]) -> Optional["CredencialToolOutDetail"]:
        if not doc:
            return None
        if isinstance(doc, cls):
            return doc

        return cls(
            id=str(doc["_id"]) if isinstance(doc.get("_id"), (ObjectId, str)) else str(doc.get("_id")),
            descricao=doc.get("descricao"),
            credencial=doc.get("credencial"),
            ativo=doc.get("ativo", True),
        )
