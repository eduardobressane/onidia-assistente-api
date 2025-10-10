from typing import Optional, Union, Dict, Any
from pydantic import BaseModel, Field, Json
from bson import ObjectId


class CredencialModeloAiBase(BaseModel):
    descricao: str = Field(..., max_length=150)
    credencial: Union[Dict[str, Any], list]  # aceita objeto JSON ou lista JSON
    ativo: bool = Field(default=True)


class CredencialModeloAiCreate(CredencialModeloAiBase):
    pass


class CredencialModeloAiUpdate(CredencialModeloAiBase):
    pass


class CredencialModeloAiInterna(CredencialModeloAiBase):
    id: str
    id_modelo_ai: Optional[str] = None
    id_contratante: Optional[str] = None

    @classmethod
    def from_raw(cls, doc: Union[dict, "CredencialModeloAiInterna"]) -> Optional["CredencialModeloAiInterna"]:
        if not doc:
            return None
        if isinstance(doc, cls):
            return doc

        return cls(
            id=str(doc["_id"]) if isinstance(doc.get("_id"), (ObjectId, str)) else str(doc.get("_id")),
            descricao=doc.get("descricao"),
            credencial=doc.get("credencial"),
            ativo=doc.get("ativo", True),
            id_modelo_ai=doc.get("id_modelo_ai"),
            id_contratante=doc.get("id_contratante"),
        )


class CredencialModeloAiOutList(BaseModel):   # listagem não mostra credencial
    id: str
    descricao: Optional[str] = None
    ativo: bool = True

    @classmethod
    def from_raw(cls, doc: Union[dict, "CredencialModeloAiOutList"]) -> Optional["CredencialModeloAiOutList"]:
        if not doc:
            return None
        if isinstance(doc, cls):
            return doc
        return cls(
            id=str(doc["_id"]) if isinstance(doc.get("_id"), (ObjectId, str)) else str(doc.get("_id")),
            descricao=doc.get("descricao"),
            ativo=doc.get("ativo", True),
        )


class CredencialModeloAiOutDetail(CredencialModeloAiBase):  # exibe a credencial
    id: str

    @classmethod
    def from_raw(cls, doc: Union[dict, "CredencialModeloAiOutDetail"]) -> Optional["CredencialModeloAiOutDetail"]:
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
