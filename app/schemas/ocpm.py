from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ======== MODELOS INTERNOS ========

class ToolModel(BaseModel):
    name: str = Field(..., description="Nome interno da tool")
    description: Optional[str] = Field(None, description="Descrição da função da tool")
    service_id: Optional[str] = Field(None, description="ID do service associado")


# ======== MODELOS BASE ========

class OCPMBase(BaseModel):
    name: str = Field(..., max_length=150)
    path: str = Field(..., description="Rota pública do MCP")
    description: Optional[str] = None
    tools: List[ToolModel] = Field(default_factory=list)

    @field_validator("tools", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("tools deve ser uma lista")
        return v


# ======== CREATE / UPDATE ========

class OCPMCreate(OCPMBase):
    pass


class OCPMUpdate(OCPMBase):
    pass


# ======== OUTPUT LIST ========

class OCPMOutList(BaseModel):
    id: str
    name: str
    path: str
    description: Optional[str] = None

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["OCPMOutList"]:
        if not doc:
            return None
        return cls(
            id=str(doc.get("_id")),
            name=doc.get("name"),
            path=doc.get("path"),
            description=doc.get("description"),
        )


# ======== OUTPUT DETAIL ========

class OCPMOutDetail(OCPMBase):
    id: str

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["OCPMOutDetail"]:
        if not doc:
            return None

        import copy
        data = copy.deepcopy(doc)

        return cls(
            id=str(data.get("_id")),
            name=data.get("name"),
            path=data.get("path"),
            description=data.get("description"),
            tools=data.get("tools", []),
        )
