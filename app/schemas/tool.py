from typing import Optional, List, Literal
from pydantic import BaseModel, Field

# Sub-schema para um campo do escopo
class EscopoCampo(BaseModel):
    nome: str = Field(..., title="Nome do Campo")
    descricao: Optional[str] = Field(None, title="Descrição do Campo")
    tipo: Literal["string", "integer", "decimal", "date", "datetime", "url"] = Field(..., title="Tipo")
    requerido: bool = Field(..., title="Requerido")
    observacao: Optional[str] = Field(None, title="Observação")
    valor: Optional[str] = Field(None, title="Valor")

class Escopo(BaseModel):
    campos: List[EscopoCampo]

# Base comum
class ToolBase(BaseModel):
    nome: str = Field(..., max_length=150)
    ativo: bool = True

# Create e Update
class ToolCreate(ToolBase):
    escopo: Optional[Escopo] = None

class ToolUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=150)
    ativo: Optional[bool] = None
    escopo: Optional[Escopo] = None

class ToolOutList(ToolBase):
    id: str

    @classmethod
    def from_raw(cls, doc: dict) -> "ToolOutList":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            nome=doc.get("nome"),
            ativo=doc.get("ativo", True)
        )

class ToolOutDetail(ToolBase):
    id: str
    escopo: Optional[Escopo] = None

    @classmethod
    def from_raw(cls, doc: dict) -> "ToolOutDetail":
        if not doc:
            return None
        return cls(
            id=str(doc["_id"]),
            nome=doc.get("nome"),
            ativo=doc.get("ativo", True),
            escopo=doc.get("escopo")
        )
