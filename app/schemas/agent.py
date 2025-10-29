from typing import List, Optional, Any, Literal
from uuid import UUID
from pydantic import ConfigDict, BaseModel, Field, model_validator, field_validator
from app.core.exceptions.types import NotFoundError, BadRequestError
from bson import ObjectId
import json

class OCP(BaseModel):
    id: str = Field(...)
    name: str = Field(...)
    type: str = Field(...)

class Tag(BaseModel):
    id: str = Field(...)
    name: str = Field(...)

class Function(BaseModel):
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=150)
    action_type: Optional[Literal["GET", "SET"]] = None
    description: Optional[str] = None
    system_message: Optional[str] = None

class Tool(BaseModel):
    id: str
    name: Optional[str] = None
    scope: Optional[dict[str, Any]] = None

class ToolInfo(BaseModel):
    tool: Tool
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=150)
    required: bool

class AgentBase(BaseModel):
    name: str = Field(..., max_length=150)
    description: str = Field(..., max_length=2048)
    system_message: str = Field(...)
    is_public: bool = Field(default=True)
    enabled: bool = Field(default=True)
    ocps: List[OCP]
    tags: List[Tag]
    functions: Optional[List[Function]] = None
    contractors: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_functions_unique(self):
        functions = self.functions or []
        codes = [f.code for f in functions]
        if len(codes) != len(set(codes)):
            raise BadRequestError("Os códigos das funções devem ser únicos dentro do agente.")
        return self

    @model_validator(mode="after")
    def validate_contractors_unique_and_uuid(self):
        contractors = self.contractors or []
        if not contractors:
            return self  # lista vazia = ok

        standardized = []
        for cid in contractors:
            try:
                # normaliza para UUID válido em lowercase
                standardized.append(str(UUID(str(cid).strip())))
            except ValueError:
                raise BadRequestError(f"Contratante '{cid}' não é um UUID válido.")

        if len(standardized) != len(set(standardized)):
            raise BadRequestError("Os ids dos contratantes devem ser únicos dentro do agente.")

        # sobrescreve padronizado
        self.contractors = standardized
        return self

#CREATE/UPDATE

class OCPCreateOrUpdate(BaseModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_object_id(cls, v: str) -> str:
        if not ObjectId.is_valid(v):
            raise NotFoundError(f"OCP com id {v} não existe")
        return v

class TagCreateOrUpdate(BaseModel):
    id: str = Field(...)

class ToolCreateOrUpdate(BaseModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_object_id(cls, v: str) -> str:
        if not ObjectId.is_valid(v):
            raise NotFoundError(f"Tool com id {v} não existe")
        return v

class ToolInfoCreateOrUpdate(BaseModel):
    tool: ToolCreateOrUpdate
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=150)
    required: bool = Field(...)

class AgentCreate(AgentBase):
    ocps: List[OCPCreateOrUpdate]
    tags: List[TagCreateOrUpdate]
    tools: Optional[List[ToolInfoCreateOrUpdate]] = None

class AgentUpdate(AgentBase):
    ocps: List[OCPCreateOrUpdate]
    tags: List[TagCreateOrUpdate]
    tools: Optional[List[ToolInfoCreateOrUpdate]] = None

#OUTPUTS
class AgentOutList(BaseModel):
    id: str
    name: str
    description: str
    is_public: bool
    enabled: bool

    model_config = ConfigDict(populate_by_name=True, exclude_none=False)

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AgentOutList"]:
        if not doc:
            return None

        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            description=doc.get("description"),
            is_public=doc.get("is_public"),
            enabled=doc.get("enabled"),
        )

class AgentOutDetail(AgentBase):
    id: str
    ocps: List[OCP]
    tools: List[ToolInfo]

    model_config = ConfigDict(populate_by_name=True, exclude_none=False)

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AgentOutDetail"]:
        if not doc:
            return None
        
        tags = []
        for c in doc.get("tags", []):
            tags.append({
                "id": str(c.get("id")) if isinstance(c.get("id"), ObjectId) else c.get("id"),
                "name": str(c.get("name"))
            })

        ocps = []
        for o in doc.get("ocps", []):
            ocps.append(
                OCP(
                    id=str(o.get("id")),
                    name=o.get("name"),
                    type=o.get("type")
                ))

        tools = []
        for t in doc.get("tools", []):
            if "tool" in t:
                tool_data = t["tool"]
                tools.append(
                    ToolInfo(
                        tool=Tool(
                            id=str(tool_data.get("id")),
                            name=tool_data.get("name"),
                            scope=tool_data.get("scope"),
                        ),
                        code=t.get("code"),
                        name=t.get("name"),
                        required=t.get("required", False)
                    )
                )

        # Normalizes contractors
        raw_contractors = doc.get("contractors") or []
        contractors: List[str] = []

        if isinstance(raw_contractors, str):
            try:
                raw_contractors = json.loads(raw_contractors)
            except Exception:
                raw_contractors = []

        if isinstance(raw_contractors, list):
            for c in raw_contractors:
                if isinstance(c, list):  # flatten lista de listas
                    for item in c:
                        if item:
                            contractors.append(str(item))
                elif c:
                    contractors.append(str(c))

        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            description=doc.get("description"),
            system_message=doc.get("system_message"),
            enabled=doc.get("enabled"),
            tags=tags,
            ocps=ocps,
            functions=doc.get("functions"),
            tools=tools,
            contractors=contractors,
        )

class AgentOutInternal(AgentBase):
    id: str
    contractor_id: Optional[str] = None
    ocps: List[OCP]
    tools: List[ToolInfo]

    model_config = ConfigDict(populate_by_name=True, exclude_none=False)

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AgentOutInternal"]:
        if not doc:
            return None
        
        tags = []
        for c in doc.get("tags", []):
            tags.append({
                "id": str(c.get("id")) if isinstance(c.get("id"), ObjectId) else c.get("id"),
                "name": str(c.get("name")),
            })

        ocps = []
        for o in doc.get("ocps", []):
            ocps.append(
                OCP(
                    id=str(o.get("id")),
                    name=o.get("name"),
                    type=o.get("type")
                ))

        tools = []
        for t in doc.get("tools", []):
            if "tool" in t:
                tool_data = t["tool"]
                tools.append(
                    ToolInfo(
                        tool=Tool(
                            id=str(tool_data.get("id")),
                            name=tool_data.get("name"),
                            scope=tool_data.get("scope"),
                        ),
                        code=t.get("code"),
                        name=t.get("name"),
                        required=t.get("required", False)
                    )
                )

        # Normalizes contractors
        raw_contractors = doc.get("contractors") or []
        contractors: List[str] = []

        if isinstance(raw_contractors, str):
            try:
                raw_contractors = json.loads(raw_contractors)
            except Exception:
                raw_contractors = []

        if isinstance(raw_contractors, list):
            for c in raw_contractors:
                if isinstance(c, list):  # flatten lista de listas
                    for item in c:
                        if item:
                            contractors.append(str(item))
                elif c:
                    contractors.append(str(c))

        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            description=doc.get("description"),
            system_message=doc.get("system_message"),
            contractor_id=doc.get("contractor_id"),
            enabled=doc.get("enabled"),
            tags=tags,
            ocps=ocps,
            functions=doc.get("functions"),
            tools=tools,
            contractors=contractors,
        )
