from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ======== MODELOS INTERNOS ========

class ServiceModel(BaseModel):
    id: str
    name: str
    description: Optional[str]

class ToolModel(BaseModel):
    name: str = Field(..., description="Internal name of the tool")
    description: Optional[str] = Field(None, description="Description of the tool's function")
    service: ServiceModel = Field(None, description="Associated service")


# ======== MODELOS BASE ========

class OCPMBase(BaseModel):
    name: str = Field(..., max_length=150)
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
class ServiceModelCreateOrUpdate(BaseModel):
    id: str

class ToolModelCreateOrUpdate(BaseModel):
    name: str = Field(..., description="Internal name of the tool")
    description: Optional[str] = Field(None, description="Description of the tool's function")
    service: ServiceModelCreateOrUpdate = Field(None, description="Associated service")

class OCPMCreate(OCPMBase):
    name: str = Field(..., max_length=150)
    description: Optional[str] = None
    tools: List[ToolModelCreateOrUpdate] = Field(default_factory=list)


class OCPMUpdate(OCPMBase):
    name: str = Field(..., max_length=150)
    description: Optional[str] = None
    tools: List[ToolModelCreateOrUpdate] = Field(default_factory=list)


# ======== OUTPUT LIST ========

class OCPMOutList(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["OCPMOutList"]:
        if not doc:
            return None
        return cls(
            id=str(doc.get("_id")),
            name=doc.get("name"),
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
            description=data.get("description"),
            tools=data.get("tools", []),
        )
