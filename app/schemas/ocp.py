from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

OCPType = Literal["mcp", "ocp-m", "langserve"]

class SourceModel(BaseModel):
    id: Optional[str] = None
    type: OCPType
    url: str
    headers: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("headers", mode="before")
    def ensure_dict(cls, v):
        if v in (None, []):
            return {}
        if not isinstance(v, dict):
            raise ValueError("headers deve ser um dicionário")
        return v


class MetadataModel(BaseModel):
    protocol: str
    version: str
    source: SourceModel


class ToolInputSchema(BaseModel):
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)
    additionalProperties: Optional[bool] = None


class ToolModel(BaseModel):
    name: str
    description: str = ""
    input_schema: ToolInputSchema


class StructureModel(BaseModel):
    description: str = ""
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    tools: List[ToolModel] = Field(default_factory=list)


class OCPModel(BaseModel):
    id: Optional[str] = None
    metadata: MetadataModel
    structure: StructureModel


class OCPBase(BaseModel):
    id: str
    name: str
    enabled: bool = Field(default=True)

#CREATE/UPDATE

class SourceCreate(BaseModel):
    type: OCPType
    url: str
    headers: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("headers", mode="before")
    def ensure_dict(cls, v):
        if v in (None, []):
            return {}
        if not isinstance(v, dict):
            raise ValueError("headers deve ser um dicionário")
        return v

class OCPCreate(BaseModel):
    name: str
    enabled: bool = Field(default=True)
    source: SourceCreate


class SourceUpdate(BaseModel):
    url: str
    headers: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("headers", mode="before")
    def ensure_dict(cls, v):
        if v in (None, []):
            return {}
        if not isinstance(v, dict):
            raise ValueError("headers deve ser um dicionário")
        return v

class OCPUpdate(BaseModel):
    name: str
    enabled: bool = Field(default=True)
    source: SourceUpdate

#OUTPUT

class OCPOutList(OCPBase):
    type: str

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["OCPOutList"]:
        if not doc:
            return None
        return cls(
            id=str(doc.get("_id")),
            name=doc.get("name"),
            type=doc.get("ocp").get("metadata").get("source").get("type"),
            enabled=doc.get("enabled", True),
            ocp=doc.get("ocp")
        )

class OCPOutDetail(OCPBase):
    ocp: OCPModel

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["OCPOutDetail"]:
        if not doc:
            return None

        # Faz uma cópia profunda de ocp (para não alterar o doc original)
        import copy
        ocp_data = copy.deepcopy(doc.get("ocp", {}))

        # Procura por headers em ocp.metadata.source.headers
        try:
            headers = ocp_data.get("metadata", {}).get("source", {}).get("headers", {})
            if isinstance(headers, dict):
                ocp_data["metadata"]["source"]["headers"] = {k: "****" for k in headers.keys()}
        except Exception:
            pass  # Evita erro caso alguma chave intermediária não exista

        return cls(
            id=str(doc.get("_id")),
            name=doc.get("name"),
            enabled=doc.get("enabled", True),
            ocp=ocp_data
        )
